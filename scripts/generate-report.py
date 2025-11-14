#!/usr/bin/env python3
"""
Generate a security report from Trivy scan results.

This script aggregates all Trivy JSON scan results and creates
a comprehensive security report in Markdown format.

Usage:
    python3 generate-report.py <scan-results-directory>
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def load_scan_result(file_path: Path) -> Dict:
    """Load a single Trivy JSON scan result."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load {file_path}: {e}", file=sys.stderr)
        return {}


def extract_image_name(filename: str) -> str:
    """Convert sanitized filename back to image name."""
    # Remove .json extension
    name = filename.replace('.json', '')
    # This is a simplified conversion - the actual image name structure
    # would need proper parsing
    return name.replace('_', '/', 2).replace('_', ':', 1)


def analyze_vulnerabilities(scan_results: Dict) -> Tuple[int, int, Dict[str, int]]:
    """Analyze vulnerabilities in a scan result.

    Returns:
        Tuple of (high_count, critical_count, vulnerability_details)
    """
    high_count = 0
    critical_count = 0
    vuln_details = defaultdict(int)

    if not scan_results or 'Results' not in scan_results:
        return 0, 0, {}

    for result in scan_results.get('Results', []):
        for vuln in result.get('Vulnerabilities', []):
            severity = vuln.get('Severity', 'UNKNOWN')
            if severity == 'HIGH':
                high_count += 1
            elif severity == 'CRITICAL':
                critical_count += 1
            vuln_details[severity] += 1

    return high_count, critical_count, dict(vuln_details)


def generate_report(results_dir: str) -> str:
    """Generate a comprehensive security report."""
    results_path = Path(results_dir)

    if not results_path.exists():
        return f"Error: Directory {results_dir} does not exist"

    # Load all JSON scan results
    scan_files = list(results_path.glob('*.json'))

    if not scan_files:
        return "No scan results found"

    # Analyze all results
    image_results = []
    total_high = 0
    total_critical = 0

    for scan_file in sorted(scan_files):
        scan_data = load_scan_result(scan_file)
        image_name = extract_image_name(scan_file.name)
        high, critical, details = analyze_vulnerabilities(scan_data)

        total_high += high
        total_critical += critical

        image_results.append({
            'image': image_name,
            'high': high,
            'critical': critical,
            'details': details
        })

    # Generate markdown report
    report_lines = [
        "# Semaphore Security Scan Report",
        "",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Total Images Scanned:** {len(image_results)}",
        f"**Total Critical Vulnerabilities:** {total_critical}",
        f"**Total High Vulnerabilities:** {total_high}",
        "",
        "## Summary",
        "",
        "| Image | Critical | High | Status |",
        "|-------|----------|------|--------|"
    ]

    # Sort by critical then high vulnerability counts
    sorted_results = sorted(
        image_results,
        key=lambda x: (x['critical'], x['high']),
        reverse=True
    )

    for result in sorted_results:
        status = "✅ PASS" if result['critical'] == 0 and result['high'] == 0 else "⚠️ REVIEW"
        report_lines.append(
            f"| `{result['image']}` | {result['critical']} | {result['high']} | {status} |"
        )

    # Add details section for images with vulnerabilities
    images_with_vulns = [r for r in sorted_results if r['critical'] > 0 or r['high'] > 0]

    if images_with_vulns:
        report_lines.extend([
            "",
            "## Detailed Findings",
            "",
            "### Images Requiring Attention",
            ""
        ])

        for result in images_with_vulns:
            report_lines.extend([
                f"#### {result['image']}",
                "",
                "**Vulnerability Breakdown:**",
                ""
            ])

            for severity, count in sorted(result['details'].items(), reverse=True):
                report_lines.append(f"- {severity}: {count}")

            report_lines.append("")

    # Add recommendations
    report_lines.extend([
        "## Recommendations",
        "",
        "1. **Critical Vulnerabilities**: Prioritize images with CRITICAL vulnerabilities for immediate remediation",
        "2. **High Vulnerabilities**: Schedule updates for images with HIGH vulnerabilities",
        "3. **Regular Scans**: Run this pipeline regularly (e.g., weekly) to catch new vulnerabilities",
        "4. **Image Updates**: Consider updating base images and dependencies",
        "5. **Vulnerability Database**: Ensure Trivy vulnerability database is up to date",
        "",
        "## Next Steps",
        "",
        "- Review individual scan result files for detailed vulnerability information",
        "- Create tickets for images requiring updates",
        "- Monitor CVE feeds for newly disclosed vulnerabilities",
        "- Consider implementing automated image rebuilds when vulnerabilities are patched",
        ""
    ])

    return '\n'.join(report_lines)


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <scan-results-directory>", file=sys.stderr)
        sys.exit(1)

    results_dir = sys.argv[1]
    report = generate_report(results_dir)
    print(report)


if __name__ == "__main__":
    main()
