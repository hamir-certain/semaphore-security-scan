#!/usr/bin/env python3
"""
Extract all container images from Semaphore Helm chart.

This script parses both the parent values.yaml and subchart values.yaml files
to extract all container image references with correct image names.

Usage:
    python3 extract-images.py <path-to-helm-chart-directory>
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import List, Dict


def load_yaml(file_path: Path) -> Dict:
    """Load a YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Failed to load {file_path}: {e}", file=sys.stderr)
        return {}


def extract_app_images_from_charts(chart_dir: Path, parent_values: Dict, registry: str) -> List[str]:
    """Extract application images by reading subchart values.yaml for image names."""
    images = []
    charts_path = chart_dir / "charts"

    if not charts_path.exists():
        print(f"Warning: charts directory not found: {charts_path}", file=sys.stderr)
        return images

    # Iterate through all subcharts
    for subchart_dir in sorted(charts_path.iterdir()):
        if not subchart_dir.is_dir():
            continue

        subchart_name = subchart_dir.name
        subchart_values_file = subchart_dir / "values.yaml"

        if not subchart_values_file.exists():
            continue

        # Load subchart values to get the actual image name
        subchart_values = load_yaml(subchart_values_file)
        image_name = subchart_values.get('image')

        if not image_name:
            continue

        # Get imageTag from parent values.yaml
        # The parent values use the subchart name (with dashes and underscores)
        image_tag = parent_values.get(subchart_name, {}).get('imageTag')

        if image_tag:
            full_image = f"{registry}/{image_name}:{image_tag}"
            images.append(full_image)

    # Also check for sidecar images in global section
    global_vals = parent_values.get('global', {})

    # Sidecar encryptor
    sidecar = global_vals.get('sidecarEncryptor', {})
    if sidecar.get('image') and sidecar.get('imageTag'):
        images.append(f"{registry}/{sidecar['image']}:{sidecar['imageTag']}")

    # Statsd
    statsd = global_vals.get('statsd', {})
    if statsd.get('image') and statsd.get('imageTag'):
        images.append(f"{registry}/{statsd['image']}:{statsd['imageTag']}")

    return sorted(images)


def extract_infra_images(parent_values: Dict) -> List[str]:
    """Extract infrastructure images (postgres, redis, rabbitmq, minio, etc.)."""
    images = []
    global_vals = parent_values.get('global', {})

    # PostgreSQL
    db_config = global_vals.get('database', {}).get('local', {})
    if db_config.get('version'):
        images.append(f"postgres:{db_config['version']}")

    # RabbitMQ
    rmq_config = global_vals.get('rabbitmq', {}).get('local', {})
    if rmq_config.get('version'):
        images.append(f"rabbitmq:{rmq_config['version']}")

    # Redis
    redis_config = global_vals.get('redis', {}).get('local', {})
    if redis_config.get('version'):
        images.append(f"redis:{redis_config['version']}")

    # MinIO (artifacts, cache, logs use same version)
    minio_config = global_vals.get('artifacts', {}).get('local', {})
    if minio_config.get('version'):
        images.append(f"minio/minio:{minio_config['version']}")

    # Init container images (from templates/init-containers.tpl)
    images.append("postgres:13")
    images.append("curlimages/curl:latest")

    # Default agent image (from controller values)
    agent_config = global_vals.get('agent', {})
    if not agent_config:
        # Fallback to default from documentation
        images.append("docker.io/erlang:26")
    else:
        default_image = agent_config.get('defaultImage')
        if default_image:
            images.append(default_image)

    return images


def main():
    """Main function to extract and print all images."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-helm-chart-directory>", file=sys.stderr)
        sys.exit(1)

    chart_path = Path(sys.argv[1])

    if not chart_path.exists():
        print(f"Error: Path not found: {chart_path}", file=sys.stderr)
        sys.exit(1)

    # Load parent values.yaml
    values_file = chart_path / "values.yaml"
    if not values_file.exists():
        print(f"Error: values.yaml not found: {values_file}", file=sys.stderr)
        sys.exit(1)

    parent_values = load_yaml(values_file)
    registry = parent_values.get('global', {}).get('image', {}).get('registry', 'ghcr.io/semaphoreio')

    # Extract images
    app_images = extract_app_images_from_charts(chart_path, parent_values, registry)
    infra_images = extract_infra_images(parent_values)

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
