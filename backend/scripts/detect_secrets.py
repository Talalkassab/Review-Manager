#!/usr/bin/env python3
"""
Script to detect secrets and sensitive information in the codebase.
Used as part of pre-commit hooks to prevent accidental secret commits.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import json

# Secret patterns to detect
SECRET_PATTERNS = {
    'api_key': [
        r'api[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-]{16,}',
        r'apikey["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-]{16,}',
    ],
    'secret_key': [
        r'secret[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-]{16,}',
        r'secretkey["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-]{16,}',
    ],
    'password': [
        r'password["\'\s]*[:=]["\'\s]*[^\s"\']{8,}',
        r'passwd["\'\s]*[:=]["\'\s]*[^\s"\']{8,}',
        r'pwd["\'\s]*[:=]["\'\s]*[^\s"\']{8,}',
    ],
    'database_url': [
        r'database[_-]?url["\'\s]*[:=]["\'\s]*[^\s"\']+',
        r'db[_-]?url["\'\s]*[:=]["\'\s]*[^\s"\']+',
    ],
    'jwt_secret': [
        r'jwt[_-]?secret["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-]{16,}',
        r'jwt[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-]{16,}',
    ],
    'private_key': [
        r'-----BEGIN[A-Z\s]+PRIVATE KEY-----',
        r'private[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-/+=]{100,}',
    ],
    'aws_access_key': [
        r'AKIA[0-9A-Z]{16}',
        r'aws[_-]?access[_-]?key[_-]?id["\'\s]*[:=]["\'\s]*AKIA[0-9A-Z]{16}',
    ],
    'aws_secret_key': [
        r'aws[_-]?secret[_-]?access[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9/+=]{40}',
    ],
    'github_token': [
        r'gh[ps]_[a-zA-Z0-9_]{36,255}',
        r'github[_-]?token["\'\s]*[:=]["\'\s]*gh[ps]_[a-zA-Z0-9_]{36,255}',
    ],
    'slack_token': [
        r'xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}',
    ],
    'discord_token': [
        r'[MN][a-zA-Z0-9_-]{23}\.[a-zA-Z0-9_-]{6}\.[a-zA-Z0-9_-]{27}',
    ],
    'generic_token': [
        r'token["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_\-]{32,}',
        r'bearer["\'\s]+[a-zA-Z0-9_\-\.]{20,}',
    ]
}

# Files and directories to exclude
EXCLUDE_PATTERNS = [
    r'\.git/',
    r'__pycache__/',
    r'\.pytest_cache/',
    r'\.venv/',
    r'venv/',
    r'node_modules/',
    r'\.env\.example',
    r'\.env\.template',
    r'test_.*\.py',
    r'.*_test\.py',
    r'tests/.*\.py',
    r'migrations/',
    r'alembic/versions/',
    r'\.md$',
    r'\.txt$',
    r'\.log$',
    r'\.json$' # Exclude JSON files as they might contain test data
]

# Whitelisted patterns that look like secrets but are safe
WHITELIST_PATTERNS = [
    r'your[_-]?api[_-]?key[_-]?here',
    r'replace[_-]?with[_-]?actual',
    r'example[_-]?secret',
    r'fake[_-]?token',
    r'test[_-]?password',
    r'dummy[_-]?key',
    r'placeholder',
    r'changeme',
    r'<.*>',  # Template placeholders
    r'\${.*}',  # Environment variable placeholders
    r'XXXXXXXX',
    r'xxxxxxxxxx',
    r'abcd1234',
    r'1234567890',
]


class SecretDetector:
    """Detects secrets and sensitive information in files."""

    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir)
        self.findings: List[Dict] = []

    def is_excluded_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning."""
        relative_path = file_path.relative_to(self.root_dir)
        path_str = str(relative_path)

        for pattern in EXCLUDE_PATTERNS:
            if re.search(pattern, path_str, re.IGNORECASE):
                return True

        return False

    def is_whitelisted(self, match_text: str) -> bool:
        """Check if the matched text is whitelisted."""
        for pattern in WHITELIST_PATTERNS:
            if re.search(pattern, match_text, re.IGNORECASE):
                return True
        return False

    def scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for secrets."""
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Skip binary files or very large files
            if len(content) > 1024 * 1024:  # 1MB limit
                return findings

            lines = content.split('\n')

            for secret_type, patterns in SECRET_PATTERNS.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1].strip()

                        # Skip if whitelisted
                        if self.is_whitelisted(match.group()):
                            continue

                        finding = {
                            'file': str(file_path.relative_to(self.root_dir)),
                            'line': line_num,
                            'column': match.start() - content.rfind('\n', 0, match.start()) - 1,
                            'type': secret_type,
                            'pattern': pattern,
                            'match': match.group(),
                            'line_content': line_content,
                            'severity': self._get_severity(secret_type)
                        }
                        findings.append(finding)

        except Exception as e:
            print(f"Error scanning {file_path}: {e}", file=sys.stderr)

        return findings

    def _get_severity(self, secret_type: str) -> str:
        """Get severity level for secret type."""
        high_severity = ['private_key', 'aws_secret_key', 'database_url', 'jwt_secret']
        medium_severity = ['api_key', 'secret_key', 'password', 'aws_access_key']

        if secret_type in high_severity:
            return 'HIGH'
        elif secret_type in medium_severity:
            return 'MEDIUM'
        else:
            return 'LOW'

    def scan_directory(self) -> List[Dict]:
        """Scan entire directory for secrets."""
        all_findings = []

        # Get all Python files
        python_files = list(self.root_dir.rglob('*.py'))

        # Add other file types
        for pattern in ['*.yaml', '*.yml', '*.json', '*.env*', '*.conf', '*.ini']:
            python_files.extend(self.root_dir.rglob(pattern))

        for file_path in python_files:
            if self.is_excluded_file(file_path):
                continue

            findings = self.scan_file(file_path)
            all_findings.extend(findings)

        self.findings = all_findings
        return all_findings

    def generate_report(self) -> Dict:
        """Generate summary report."""
        if not self.findings:
            return {
                'status': 'PASS',
                'total_findings': 0,
                'findings_by_severity': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'findings_by_type': {},
                'files_scanned': len(list(self.root_dir.rglob('*.py'))),
                'findings': []
            }

        findings_by_severity = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        findings_by_type = {}

        for finding in self.findings:
            severity = finding['severity']
            secret_type = finding['type']

            findings_by_severity[severity] += 1
            findings_by_type[secret_type] = findings_by_type.get(secret_type, 0) + 1

        status = 'FAIL' if findings_by_severity['HIGH'] > 0 or findings_by_severity['MEDIUM'] > 0 else 'WARN'

        return {
            'status': status,
            'total_findings': len(self.findings),
            'findings_by_severity': findings_by_severity,
            'findings_by_type': findings_by_type,
            'files_scanned': len(list(self.root_dir.rglob('*.py'))),
            'findings': self.findings
        }


def main():
    """Main function to run secret detection."""
    detector = SecretDetector()
    findings = detector.scan_directory()
    report = detector.generate_report()

    # Print summary
    print(f"Secret Detection Report")
    print(f"Status: {report['status']}")
    print(f"Files Scanned: {report['files_scanned']}")
    print(f"Total Findings: {report['total_findings']}")
    print(f"By Severity: HIGH({report['findings_by_severity']['HIGH']}) "
          f"MEDIUM({report['findings_by_severity']['MEDIUM']}) "
          f"LOW({report['findings_by_severity']['LOW']})")

    if findings:
        print("\nFindings:")
        for finding in findings[:10]:  # Show first 10 findings
            print(f"  {finding['severity']} - {finding['file']}:{finding['line']} "
                  f"- {finding['type']} - {finding['match'][:50]}...")

        if len(findings) > 10:
            print(f"  ... and {len(findings) - 10} more findings")

        # Save full report to file
        with open('secret-scan-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report saved to: secret-scan-report.json")

    # Exit with appropriate code
    if report['status'] == 'FAIL':
        print("\nFAILURE: High or medium severity secrets detected!")
        sys.exit(1)
    elif report['status'] == 'WARN':
        print("\nWARNING: Low severity potential secrets detected. Review manually.")
        sys.exit(0)
    else:
        print("\nSUCCESS: No secrets detected.")
        sys.exit(0)


if __name__ == '__main__':
    main()