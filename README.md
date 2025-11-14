# Semaphore Security Scan

Automated security vulnerability scanning for all container images in the Semaphore Helm chart using Trivy.

## Overview

This repository contains a Semaphore CI/CD pipeline that automatically scans all container images used in the [Semaphore](https://github.com/semaphoreio/semaphore) Helm chart for security vulnerabilities using [Trivy](https://github.com/aquasecurity/trivy).

**Current Version:** Semaphore Helm Chart v1.5.0

**Total Images Scanned:** 43 images
- 36 application images from `ghcr.io/semaphoreio/*`
- 7 infrastructure images (PostgreSQL, RabbitMQ, Redis, MinIO, etc.)

## Features

- **Automated Image Extraction**: Downloads and parses Semaphore Helm chart to extract all image references
- **Parallel Scanning**: Uses Semaphore job matrix to scan all 43 images in parallel
- **Comprehensive Coverage**: Scans both application and infrastructure images
- **Severity Filtering**: Focuses on HIGH and CRITICAL vulnerabilities
- **Detailed Reports**: Generates both JSON (machine-readable) and text (human-readable) outputs
- **Aggregated Summary**: Creates a consolidated security report across all images

## Pipeline Architecture

The pipeline consists of three blocks:

### 1. Extract Images from Helm Chart
- Downloads Semaphore Helm chart v1.5.0
- Extracts all container image references using Python script
- Generates a complete image list

### 2. Trivy Security Scan (Parallel)
- Uses job matrix to create 43 parallel jobs (one per image)
- Each job independently:
  - Installs Trivy
  - Scans assigned image for HIGH/CRITICAL vulnerabilities
  - Generates JSON and text reports
  - Uploads results as artifacts

### 3. Generate Security Report
- Aggregates all scan results
- Creates a comprehensive Markdown report
- Highlights images requiring attention
- Provides remediation recommendations

## Usage

### Running the Pipeline

The pipeline runs automatically on:
- Push to main branch
- Pull requests
- Manual trigger via Semaphore UI

### Viewing Results

After the pipeline completes:

1. **Individual Scan Results**: Download artifacts from each scan job
   - JSON format: `<image-name>.json` - for automated processing
   - Text format: `<image-name>.txt` - for human review

2. **Security Report**: Download the aggregated `security-report.md` artifact
   - Summary statistics
   - Vulnerability breakdown by image
   - Prioritized remediation recommendations

### Local Development

#### Extract Images Locally

```bash
# Download Helm chart
curl -L https://github.com/semaphoreio/semaphore/releases/download/v1.5.0/semaphore-v1.5.0.tgz -o semaphore-v1.5.0.tgz
tar -xzf semaphore-v1.5.0.tgz

# Extract images
python3 scripts/extract-images.py semaphore/values.yaml
```

#### Scan a Single Image

```bash
# Install Trivy (Ubuntu/Debian)
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Scan an image
trivy image --severity HIGH,CRITICAL ghcr.io/semaphoreio/auth:570873cccc0c443e433697a0efb7a3f33d6f3ecd
```

## Updating for New Helm Chart Versions

When a new version of the Semaphore Helm chart is released:

1. **Update the Pipeline Configuration**:
   - Edit `.semaphore/semaphore.yml`
   - Update the Helm chart download URL in the "Extract Images" block
   - Change version from `v1.5.0` to the new version

2. **Extract New Image List**:
   ```bash
   # Download new chart
   curl -L https://github.com/semaphoreio/semaphore/releases/download/vX.Y.Z/semaphore-vX.Y.Z.tgz -o semaphore.tgz
   tar -xzf semaphore.tgz

   # Extract images
   python3 scripts/extract-images.py semaphore/values.yaml > new-images.txt
   ```

3. **Update Job Matrix**:
   - Replace the `values` list in the "Trivy Security Scan" job matrix
   - Copy image names from the extraction output
   - Commit and push changes

4. **Alternative: Automated Update** (Future Enhancement):
   - Create a script to automatically update the matrix from `images-list.txt`
   - Use Semaphore's parameterized builds to specify Helm chart version

## Repository Structure

```
.
├── .semaphore/
│   └── semaphore.yml          # Main pipeline configuration
├── scripts/
│   ├── extract-images.py      # Extract images from Helm chart
│   └── generate-report.py     # Generate security summary report
└── README.md                  # This file
```

## Semaphore Images Scanned

### Application Images (36)

All images from `ghcr.io/semaphoreio/*` registry:

- artifacthub
- audit
- auth
- badges
- bootstrapper
- branch_hub
- dashboardhub
- encryptor
- front
- github-notifier
- github_hooks
- gofer
- guard
- hooks-processor
- hooks-receiver
- keycloak
- keycloak-setup
- loghub2
- notifications
- periodic-scheduler
- plumber
- plumber-public
- pre-flight-checks-hub
- projecthub
- projecthub-public
- public-api
- public-api-gateway
- rbac
- rbac_ee
- repohub
- repository_hub
- scouter
- secrethub
- self-hosted-hub
- statsd
- velocity-hub
- zebra

### Infrastructure Images (7)

Third-party images:

- PostgreSQL 14.15 (alpine)
- PostgreSQL 13 (init container)
- RabbitMQ 3.13.7 (alpine)
- Redis 7.2.4 (alpine)
- MinIO (RELEASE.2021-04-22T15-44-28Z)
- cURL (latest)
- Erlang 26 (default agent)

## Security Considerations

### Vulnerability Severities

The pipeline focuses on:
- **CRITICAL**: Severe vulnerabilities requiring immediate attention
- **HIGH**: Significant vulnerabilities requiring prompt remediation

Lower severity vulnerabilities (MEDIUM, LOW) are not reported by default to reduce noise.

### False Positives

Trivy may report vulnerabilities that don't apply to your specific use case:
- Review CVE details to understand exploitability
- Consider the attack surface of each container
- Some vulnerabilities may not be exploitable in containerized environments

### Regular Scanning

- Run the pipeline at least weekly
- Consider running after each Semaphore release
- Monitor for new CVEs affecting your images

## Contributing

To add features or improvements:

1. Fork the repository
2. Create a feature branch
3. Test changes locally
4. Submit a pull request

## Resources

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Semaphore CI Documentation](https://docs.semaphore.io/)
- [Semaphore Helm Chart](https://github.com/semaphoreio/semaphore)
- [Job Matrix Documentation](https://docs.semaphore.io/using-semaphore/jobs#matrix)

## License

This repository is provided as-is for scanning Semaphore container images.

## Support

For issues with:
- **This scanning pipeline**: Open an issue in this repository
- **Semaphore product**: Contact [Semaphore Support](https://semaphoreci.com/support)
- **Trivy scanner**: See [Trivy GitHub Issues](https://github.com/aquasecurity/trivy/issues)
