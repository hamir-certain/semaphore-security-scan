#!/bin/bash
#
# Download security scan report from Semaphore workflow using sem CLI
#
# Prerequisites:
#   - sem CLI installed (https://docs.semaphore.io/cli/install/)
#   - sem CLI configured with: sem connect <your-org>.semaphore.io <api-token>
#
# Usage:
#   ./download-report-cli.sh <workflow-id> <pipeline-id> [output-file]
#
# Example:
#   ./download-report-cli.sh d41afe3f-9489-43c8-aaec-0d54c939d6b4 cb12d54a-f1aa-4476-89b4-320109be4237
#

set -e

# Parse arguments
WORKFLOW_ID="${1:-}"
PIPELINE_ID="${2:-}"
OUTPUT_FILE="${3:-REPORT.md}"

if [ -z "$WORKFLOW_ID" ] || [ -z "$PIPELINE_ID" ]; then
    echo "Usage: $0 <workflow-id> <pipeline-id> [output-file]"
    echo ""
    echo "Example:"
    echo "  $0 d41afe3f-9489-43c8-aaec-0d54c939d6b4 cb12d54a-f1aa-4476-89b4-320109be4237"
    exit 1
fi

# Check if sem CLI is installed
if ! command -v sem &> /dev/null; then
    echo "Error: 'sem' CLI not found"
    echo "Please install it from: https://docs.semaphore.io/cli/install/"
    exit 1
fi

echo "=== Semaphore Security Scan Report Downloader (CLI) ==="
echo "Workflow ID: $WORKFLOW_ID"
echo "Pipeline ID: $PIPELINE_ID"
echo "Output file: $OUTPUT_FILE"
echo ""

# Get artifacts using sem CLI
echo "Fetching artifacts list..."
ARTIFACTS=$(sem get artifacts --workflow-id "$WORKFLOW_ID" --pipeline-id "$PIPELINE_ID" --output json 2>&1)

if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch artifacts"
    echo "$ARTIFACTS"
    echo ""
    echo "Make sure sem CLI is configured with:"
    echo "  sem connect <your-org>.semaphore.io <api-token>"
    exit 1
fi

# Find REPORT.md artifact
REPORT_ID=$(echo "$ARTIFACTS" | jq -r '.[] | select(.name | contains("REPORT.md")) | .id' | head -1)

if [ -z "$REPORT_ID" ]; then
    echo "Error: REPORT.md artifact not found"
    echo "Available artifacts:"
    echo "$ARTIFACTS" | jq -r '.[].name'
    exit 1
fi

echo "Found REPORT.md artifact ID: $REPORT_ID"

# Download artifact
echo "Downloading report..."
sem get artifact "$REPORT_ID" --output "$OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
    echo "✓ Report downloaded successfully to: $OUTPUT_FILE"
    echo "  Size: $FILE_SIZE bytes"
    echo ""
    echo "Preview (first 50 lines):"
    head -50 "$OUTPUT_FILE"
else
    echo "Error: Failed to download report"
    exit 1
fi
