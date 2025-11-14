#!/usr/bin/env python3
"""
Extract all container images from Semaphore Helm chart.

This script parses the values.yaml file from a Semaphore Helm chart
and extracts all container image references, including both application
images and infrastructure images.

Usage:
    python3 extract-images.py <path-to-values.yaml>
"""

import re
import sys
from typing import List, Tuple


def extract_app_images(content: str, registry: str) -> List[str]:
    """Extract application images with imageTag from values.yaml."""
    pattern = r'^([a-z_-]+):\s*\n\s*imageTag:\s*(\S+)'
    matches = re.findall(pattern, content, re.MULTILINE)

    images = []
    for service_name, tag in matches:
        images.append(f"{registry}/{service_name}:{tag}")

    # Also check for sidecar images
    sidecar_pattern = r'sidecarEncryptor:\s*\n\s*image:\s*(\S+)\s*\n\s*imageTag:\s*(\S+)'
    sidecar_match = re.search(sidecar_pattern, content)
    if sidecar_match:
        images.append(f"{registry}/{sidecar_match.group(1)}:{sidecar_match.group(2)}")

    # Check for statsd
    statsd_pattern = r'statsd:.*?image:\s*(\S+)\s*.*?imageTag:\s*(\S+)'
    statsd_match = re.search(statsd_pattern, content, re.DOTALL)
    if statsd_match:
        images.append(f"{registry}/{statsd_match.group(1)}:{statsd_match.group(2)}")

    return sorted(images)


def extract_infra_images(content: str) -> List[str]:
    """Extract infrastructure images (postgres, redis, rabbitmq, minio, etc.)."""
    images = []

    # PostgreSQL
    pg_match = re.search(r'database:.*?local:.*?version:\s*(\S+)', content, re.DOTALL)
    if pg_match:
        images.append(f"postgres:{pg_match.group(1)}")

    # RabbitMQ
    rmq_match = re.search(r'rabbitmq:.*?local:.*?version:\s*(\S+)', content, re.DOTALL)
    if rmq_match:
        images.append(f"rabbitmq:{rmq_match.group(1)}")

    # Redis
    redis_match = re.search(r'redis:.*?local:.*?version:\s*(\S+)', content, re.DOTALL)
    if redis_match:
        images.append(f"redis:{redis_match.group(1)}")

    # MinIO (artifacts, cache, logs use same version)
    minio_match = re.search(r'artifacts:.*?local:.*?version:\s*(\S+)', content, re.DOTALL)
    if minio_match:
        images.append(f"minio/minio:{minio_match.group(1)}")

    # Init container images
    images.append("postgres:13")
    images.append("curlimages/curl:latest")

    # Default agent image
    agent_match = re.search(r'defaultImage:\s*"([^"]+)"', content)
    if agent_match:
        images.append(agent_match.group(1))

    return images


def main():
    """Main function to extract and print all images."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-values.yaml>", file=sys.stderr)
        sys.exit(1)

    values_file = sys.argv[1]
    registry = "ghcr.io/semaphoreio"

    try:
        with open(values_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {values_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract images
    app_images = extract_app_images(content, registry)
    infra_images = extract_infra_images(content)

    # Print results
    print("# Application Images")
    for img in app_images:
        print(img)

    print("\n# Infrastructure Images")
    for img in infra_images:
        print(img)

    print(f"\n# Total: {len(app_images)} app images + {len(infra_images)} infrastructure images = {len(app_images) + len(infra_images)} images")


if __name__ == "__main__":
    main()
