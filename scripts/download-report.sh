#!/bin/bash
#
# Download security scan report from Semaphore workflow
#
# Usage:
#   ./download-report.sh <workflow-id> <pipeline-id> [output-file]
#
# Example:
#   ./download-report.sh d41afe3f-9489-43c8-aaec-0d54c939d6b4 cb12d54a-f1aa-4476-89b4-320109be4237
#

set -e

# Configuration
SEMAPHORE_API_TOKEN="${SEMAPHORE_API_TOKEN:-}"
SEMAPHORE_ORG="${SEMAPHORE_ORG:-hamir-certain}"
SEMAPHORE_PROJECT_ID="${SEMAPHORE_PROJECT_ID:-}"
API_BASE_URL="https://semaphore.hamir.online/api/v1alpha"

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

if [ -z "$SEMAPHORE_API_TOKEN" ]; then
    echo "Error: SEMAPHORE_API_TOKEN environment variable is not set"
    echo "Please set it with: export SEMAPHORE_API_TOKEN=<your-token>"
    exit 1
fi

echo "=== Semaphore Security Scan Report Downloader ==="
echo "Workflow ID: $WORKFLOW_ID"
echo "Pipeline ID: $PIPELINE_ID"
echo "Output file: $OUTPUT_FILE"
echo ""

# Get workflow artifacts
echo "Fetching workflow artifacts..."
ARTIFACTS_URL="${API_BASE_URL}/artifacts?workflow_id=${WORKFLOW_ID}&pipeline_id=${PIPELINE_ID}"

ARTIFACTS_RESPONSE=$(curl -s -H "Authorization: Token ${SEMAPHORE_API_TOKEN}" "$ARTIFACTS_URL")

# Check if we got a valid response
if echo "$ARTIFACTS_RESPONSE" | grep -q "error"; then
    echo "Error: Failed to fetch artifacts"
    echo "$ARTIFACTS_RESPONSE"
    exit 1
fi

# Find REPORT.md artifact
REPORT_ARTIFACT=$(echo "$ARTIFACTS_RESPONSE" | jq -r '.artifacts[] | select(.name | contains("REPORT.md")) | .id' | head -1)

if [ -z "$REPORT_ARTIFACT" ]; then
    echo "Error: REPORT.md artifact not found in workflow"
    echo "Available artifacts:"
    echo "$ARTIFACTS_RESPONSE" | jq -r '.artifacts[].name'
    exit 1
fi

echo "Found REPORT.md artifact: $REPORT_ARTIFACT"

# Download the artifact
echo "Downloading report..."
DOWNLOAD_URL="${API_BASE_URL}/artifacts/${REPORT_ARTIFACT}"

curl -s -H "Authorization: Token ${SEMAPHORE_API_TOKEN}" "$DOWNLOAD_URL" -o "$OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
    if [ "$FILE_SIZE" -gt 0 ]; then
        echo "✓ Report downloaded successfully to: $OUTPUT_FILE"
        echo "  Size: $FILE_SIZE bytes"
        echo ""
        echo "Preview (first 50 lines):"
        head -50 "$OUTPUT_FILE"
    else
        echo "Error: Downloaded file is empty"
        exit 1
    fi
else
    echo "Error: Failed to download report"
    exit 1
fi
