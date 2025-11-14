#!/bin/bash
#
# Collect all Trivy scan results from Semaphore job logs and generate REPORT.md
#
# Usage:
#   ./collect-scan-results.sh <pipeline-id> [output-file]
#
# Example:
#   ./collect-scan-results.sh cb12d54a-f1aa-4476-89b4-320109be4237
#

set -e

PIPELINE_ID="${1:-}"
OUTPUT_FILE="${2:-REPORT.md}"
TEMP_DIR=$(mktemp -d)

if [ -z "$PIPELINE_ID" ]; then
    echo "Usage: $0 <pipeline-id> [output-file]"
    echo ""
    echo "Example:"
    echo "  $0 cb12d54a-f1aa-4476-89b4-320109be4237"
    exit 1
fi

# Check if sem CLI is installed
if ! command -v sem &> /dev/null; then
    echo "Error: 'sem' CLI not found"
    echo "Please install it from: https://docs.semaphore.io/cli/install/"
    exit 1
fi

echo "=== Semaphore Security Scan Report Collector ==="
echo "Pipeline ID: $PIPELINE_ID"
echo "Output file: $OUTPUT_FILE"
echo "Temp directory: $TEMP_DIR"
echo ""

# Get pipeline details to find all scan jobs
echo "Fetching pipeline details..."
PIPELINE_YAML=$(sem get pipelines "$PIPELINE_ID")

# Extract job IDs from the "Trivy Security Scan" block
JOB_IDS=$(echo "$PIPELINE_YAML" | grep -A 1 "name: Scan Image" | grep "jobid:" | awk '{print $2}')

JOB_COUNT=$(echo "$JOB_IDS" | wc -l)
echo "Found $JOB_COUNT scan jobs"
echo ""

# Create report header
cat > "$OUTPUT_FILE" << HEADER_EOF
# Semaphore Security Scan Report

**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Helm Chart Version:** v1.5.0
**Total Images Scanned:** $JOB_COUNT

---

HEADER_EOF

# Process each job
COUNTER=0
for JOB_ID in $JOB_IDS; do
    COUNTER=$((COUNTER + 1))
    echo "[$COUNTER/$JOB_COUNT] Processing job $JOB_ID..."

    # Get job logs
    LOG_FILE="$TEMP_DIR/$JOB_ID.log"
    sem logs "$JOB_ID" > "$LOG_FILE" 2>&1 || {
        echo "  Warning: Failed to get logs for job $JOB_ID"
        continue
    }

    # Extract the markdown report from the logs
    # The report is printed after "cat scan-results/*.md" command
    # Look for the pattern starting with "## Image:" and ending before "Scan complete"

    # Find the start of the markdown output
    if grep -q "^## Image:" "$LOG_FILE"; then
        # Extract everything from "## Image:" to just before "Scan complete"
        awk '/^## Image:/{flag=1} flag; /Scan complete for/{flag=0}' "$LOG_FILE" | \
            grep -v "Scan complete for" | \
            grep -v "exit status:" | \
            sed 's/\x1b\[[0-9;]*m//g' >> "$OUTPUT_FILE"  # Remove ANSI color codes

        echo "" >> "$OUTPUT_FILE"
        echo "---" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "  ✓ Extracted report"
    else
        echo "  ⚠ No scan results found in logs"
    fi
done

# Add recommendations footer
cat >> "$OUTPUT_FILE" << 'FOOTER_EOF'

## Recommendations

1. **Critical Vulnerabilities**: Prioritize images with CRITICAL vulnerabilities for immediate remediation
2. **High Vulnerabilities**: Schedule updates for images with HIGH vulnerabilities
3. **Regular Scans**: Run this pipeline regularly (e.g., weekly) to catch new vulnerabilities
4. **Image Updates**: Consider updating base images and dependencies
5. **Vulnerability Database**: Ensure Trivy vulnerability database is up to date

## Next Steps

- Review individual image sections above for detailed vulnerability information
- Create tickets for images requiring updates
- Monitor CVE feeds for newly disclosed vulnerabilities
- Consider implementing automated image rebuilds when vulnerabilities are patched

FOOTER_EOF

# Cleanup
rm -rf "$TEMP_DIR"

# Display summary
FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
echo ""
echo "=== Report Generation Complete ==="
echo "✓ Report saved to: $OUTPUT_FILE"
echo "  Size: $FILE_SIZE bytes"
echo "  Total scans processed: $JOB_COUNT"
echo ""
echo "Preview (first 50 lines):"
echo "----------------------------------------"
head -50 "$OUTPUT_FILE"
echo "----------------------------------------"
