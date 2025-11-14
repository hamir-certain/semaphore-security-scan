#!/usr/bin/env python3
"""
Download REPORT.md from Semaphore workflow using direct API calls.

Usage:
    export SEMAPHORE_API_TOKEN="your-token"
    python3 download-report-api.py <workflow-id> [output-file]
"""

import os
import sys
import requests

def download_report(workflow_id, output_file="REPORT.md"):
    """Download REPORT.md from Semaphore workflow."""

    # Get API token from environment
    api_token = os.environ.get("SEMAPHORE_API_TOKEN")
    if not api_token:
        print("Error: SEMAPHORE_API_TOKEN environment variable not set")
        sys.exit(1)

    # Semaphore self-hosted instance
    base_url = "https://semaphore.hamir.online"

    # The artifact was pushed to: artifacts/workflows/{workflow_id}/.semaphore/REPORT.md
    artifact_path = f"artifacts/workflows/{workflow_id}/.semaphore/REPORT.md"
    artifact_url = f"{base_url}/{artifact_path}"

    print(f"=== Semaphore Report Downloader ===")
    print(f"Workflow ID: {workflow_id}")
    print(f"Artifact URL: {artifact_url}")
    print(f"Output file: {output_file}")
    print()

    # Try to download the artifact
    print("Downloading report...")
    headers = {
        "Authorization": f"Token {api_token}"
    }

    try:
        response = requests.get(artifact_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save to file
        with open(output_file, 'wb') as f:
            f.write(response.content)

        file_size = len(response.content)
        print(f"✓ Report downloaded successfully!")
        print(f"  Size: {file_size} bytes")
        print(f"  Saved to: {output_file}")
        print()

        # Show preview
        print("Preview (first 50 lines):")
        print("-" * 80)
        with open(output_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 50:
                    break
                print(line, end='')
        print("-" * 80)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <workflow-id> [output-file]")
        print()
        print("Example:")
        print(f"  export SEMAPHORE_API_TOKEN='your-token'")
        print(f"  {sys.argv[0]} d41afe3f-9489-43c8-aaec-0d54c939d6b4")
        sys.exit(1)

    workflow_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "REPORT.md"

    download_report(workflow_id, output_file)
