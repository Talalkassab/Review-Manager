#!/usr/bin/env python3
"""
Script to check database migrations for consistency and safety.
Used as part of pre-commit hooks to ensure migration quality.
"""
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
import json
from datetime import datetime
import subprocess


class MigrationChecker:
    """Checks database migrations for consistency and safety."""

    def __init__(self, alembic_dir: str = 'alembic'):
        self.alembic_dir = Path(alembic_dir)
        self.versions_dir = self.alembic_dir / 'versions'
        self.issues = []

    def check_migration_files(self) -> List[Dict]:
        """Check all migration files for issues."""
        if not self.versions_dir.exists():
            self.issues.append({
                'type': 'MISSING_DIRECTORY',
                'severity': 'HIGH',
                'message': f"Migrations directory {self.versions_dir} does not exist"
            })
            return self.issues

        migration_files = list(self.versions_dir.glob('*.py'))
        if not migration_files:
            self.issues.append({
                'type': 'NO_MIGRATIONS',
                'severity': 'INFO',
                'message': "No migration files found"
            })
            return self.issues

        for migration_file in migration_files:
            self._check_migration_file(migration_file)

        self._check_migration_sequence(migration_files)
        return self.issues

    def _check_migration_file(self, file_path: Path) -> None:
        """Check individual migration file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check file structure
            self._check_file_structure(file_path, content)

            # Check for dangerous operations
            self._check_dangerous_operations(file_path, content)

            # Check for best practices
            self._check_best_practices(file_path, content)

        except Exception as e:
            self.issues.append({
                'type': 'FILE_READ_ERROR',
                'severity': 'HIGH',
                'file': str(file_path),
                'message': f"Cannot read migration file: {e}"
            })

    def _check_file_structure(self, file_path: Path, content: str) -> None:
        """Check migration file has required structure."""
        required_elements = [
            ('revision', r'revision\s*=\s*[\'"][^\'\"]+[\'"]'),
            ('down_revision', r'down_revision\s*=\s*[\'"][^\'\"]*[\'"]'),
            ('upgrade_function', r'def\s+upgrade\(\s*\):'),
            ('downgrade_function', r'def\s+downgrade\(\s*\):')
        ]

        for element_name, pattern in required_elements:
            if not re.search(pattern, content):
                self.issues.append({
                    'type': 'MISSING_ELEMENT',
                    'severity': 'HIGH',
                    'file': str(file_path),
                    'message': f"Missing required element: {element_name}"
                })

        # Check for docstring
        if not re.search(r'""".*"""', content, re.DOTALL):
            self.issues.append({
                'type': 'MISSING_DOCSTRING',
                'severity': 'MEDIUM',
                'file': str(file_path),
                'message': "Migration file should have a docstring describing changes"
            })

    def _check_dangerous_operations(self, file_path: Path, content: str) -> None:
        """Check for dangerous database operations."""
        dangerous_operations = [
            ('DROP_TABLE', r'drop_table\s*\([\'"].*[\'"]', 'HIGH'),
            ('DROP_COLUMN', r'drop_column\s*\([\'"].*[\'"],\s*[\'"].*[\'"]', 'HIGH'),
            ('DROP_INDEX', r'drop_index\s*\([\'"].*[\'"]', 'MEDIUM'),
            ('DROP_CONSTRAINT', r'drop_constraint\s*\([\'"].*[\'"]', 'MEDIUM'),
            ('ALTER_COLUMN_TYPE', r'alter_column\s*\([^)]*type_[^)]*\)', 'HIGH'),
            ('TRUNCATE_TABLE', r'truncate\s+table', 'HIGH'),
            ('DELETE_WITHOUT_WHERE', r'DELETE\s+FROM\s+\w+\s*;', 'HIGH'),
            ('UPDATE_WITHOUT_WHERE', r'UPDATE\s+\w+\s+SET.*(?!WHERE)', 'HIGH'),
        ]

        for op_name, pattern, severity in dangerous_operations:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'type': 'DANGEROUS_OPERATION',
                    'severity': severity,
                    'file': str(file_path),
                    'line': line_num,
                    'operation': op_name,
                    'message': f"Potentially dangerous operation: {op_name} at line {line_num}"
                })

    def _check_best_practices(self, file_path: Path, content: str) -> None:
        """Check for migration best practices."""
        # Check for concurrent index creation
        index_matches = re.finditer(r'create_index\s*\([^)]*\)', content, re.IGNORECASE)
        for match in matches:
            if 'postgresql_concurrently=True' not in match.group():
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'type': 'NON_CONCURRENT_INDEX',
                    'severity': 'MEDIUM',
                    'file': str(file_path),
                    'line': line_num,
                    'message': f"Index creation should use postgresql_concurrently=True at line {line_num}"
                })

        # Check for missing NOT NULL constraints with defaults
        add_column_matches = re.finditer(r'add_column\s*\([^)]+\)', content, re.IGNORECASE)
        for match in add_column_matches:
            column_def = match.group()
            if 'nullable=False' in column_def and 'default=' not in column_def:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'type': 'NOT_NULL_WITHOUT_DEFAULT',
                    'severity': 'HIGH',
                    'file': str(file_path),
                    'line': line_num,
                    'message': f"NOT NULL column should have a default value at line {line_num}"
                })

        # Check for missing transaction control
        if 'BEGIN;' not in content and 'COMMIT;' not in content:
            if any(op in content.lower() for op in ['drop_', 'alter_', 'create_']):
                self.issues.append({
                    'type': 'MISSING_TRANSACTION',
                    'severity': 'MEDIUM',
                    'file': str(file_path),
                    'message': "Consider using explicit transactions for safety"
                })

        # Check for proper downgrade implementation
        downgrade_match = re.search(r'def\s+downgrade\(\s*\):\s*(.*?)(?=def|\Z)', content, re.DOTALL)
        if downgrade_match:
            downgrade_body = downgrade_match.group(1).strip()
            if downgrade_body == 'pass' or 'raise NotImplementedError' in downgrade_body:
                self.issues.append({
                    'type': 'INCOMPLETE_DOWNGRADE',
                    'severity': 'MEDIUM',
                    'file': str(file_path),
                    'message': "Downgrade function should properly reverse upgrade operations"
                })

    def _check_migration_sequence(self, migration_files: List[Path]) -> None:
        """Check migration sequence consistency."""
        revisions = {}
        down_revisions = {}

        for file_path in migration_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract revision and down_revision
                revision_match = re.search(r'revision\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                down_revision_match = re.search(r'down_revision\s*=\s*[\'"]([^\'"]*)[\'"]', content)

                if revision_match:
                    revision = revision_match.group(1)
                    revisions[revision] = str(file_path)

                if down_revision_match:
                    down_revision = down_revision_match.group(1)
                    down_revisions[revision] = down_revision

            except Exception as e:
                self.issues.append({
                    'type': 'SEQUENCE_CHECK_ERROR',
                    'severity': 'MEDIUM',
                    'file': str(file_path),
                    'message': f"Cannot check migration sequence: {e}"
                })

        # Check for orphaned migrations
        for revision, down_revision in down_revisions.items():
            if down_revision and down_revision not in revisions and down_revision != 'None':
                self.issues.append({
                    'type': 'ORPHANED_MIGRATION',
                    'severity': 'HIGH',
                    'file': revisions.get(revision, 'unknown'),
                    'message': f"Migration {revision} references non-existent down_revision {down_revision}"
                })

    def check_alembic_config(self) -> None:
        """Check alembic configuration."""
        alembic_ini = self.alembic_dir.parent / 'alembic.ini'
        if not alembic_ini.exists():
            self.issues.append({
                'type': 'MISSING_CONFIG',
                'severity': 'HIGH',
                'message': "alembic.ini configuration file not found"
            })
            return

        try:
            with open(alembic_ini, 'r') as f:
                config_content = f.read()

            # Check for essential configurations
            essential_configs = [
                ('script_location', r'script_location\s*='),
                ('sqlalchemy.url', r'sqlalchemy\.url\s*='),
            ]

            for config_name, pattern in essential_configs:
                if not re.search(pattern, config_content):
                    self.issues.append({
                        'type': 'MISSING_CONFIG_OPTION',
                        'severity': 'HIGH',
                        'message': f"Missing required configuration: {config_name}"
                    })

        except Exception as e:
            self.issues.append({
                'type': 'CONFIG_READ_ERROR',
                'severity': 'HIGH',
                'message': f"Cannot read alembic.ini: {e}"
            })

    def check_current_migration_status(self) -> None:
        """Check if migrations are up to date."""
        try:
            result = subprocess.run(
                ['alembic', 'current', '--verbose'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.issues.append({
                    'type': 'ALEMBIC_STATUS_ERROR',
                    'severity': 'MEDIUM',
                    'message': f"Cannot check alembic status: {result.stderr}"
                })
                return

            # Check if there are pending migrations
            heads_result = subprocess.run(
                ['alembic', 'heads'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if heads_result.returncode == 0:
                current = result.stdout.strip()
                heads = heads_result.stdout.strip()

                if current != heads:
                    self.issues.append({
                        'type': 'PENDING_MIGRATIONS',
                        'severity': 'INFO',
                        'message': f"Database may not be up to date. Current: {current}, Heads: {heads}"
                    })

        except subprocess.TimeoutExpired:
            self.issues.append({
                'type': 'ALEMBIC_TIMEOUT',
                'severity': 'MEDIUM',
                'message': "Alembic command timed out"
            })
        except FileNotFoundError:
            self.issues.append({
                'type': 'ALEMBIC_NOT_FOUND',
                'severity': 'MEDIUM',
                'message': "Alembic command not found. Is it installed?"
            })
        except Exception as e:
            self.issues.append({
                'type': 'ALEMBIC_CHECK_ERROR',
                'severity': 'MEDIUM',
                'message': f"Error checking alembic status: {e}"
            })

    def generate_report(self) -> Dict:
        """Generate migration check report."""
        issues_by_severity = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        issues_by_type = {}

        for issue in self.issues:
            severity = issue['severity']
            issue_type = issue['type']

            issues_by_severity[severity] += 1
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1

        # Determine overall status
        if issues_by_severity['HIGH'] > 0:
            status = 'FAIL'
        elif issues_by_severity['MEDIUM'] > 0:
            status = 'WARN'
        else:
            status = 'PASS'

        return {
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'total_issues': len(self.issues),
            'issues_by_severity': issues_by_severity,
            'issues_by_type': issues_by_type,
            'issues': self.issues
        }


def main():
    """Main function to run migration checks."""
    checker = MigrationChecker()

    # Run all checks
    checker.check_migration_files()
    checker.check_alembic_config()
    checker.check_current_migration_status()

    # Generate report
    report = checker.generate_report()

    # Print summary
    print("Migration Check Report")
    print(f"Status: {report['status']}")
    print(f"Total Issues: {report['total_issues']}")
    print(f"By Severity: HIGH({report['issues_by_severity']['HIGH']}) "
          f"MEDIUM({report['issues_by_severity']['MEDIUM']}) "
          f"LOW({report['issues_by_severity']['LOW']}) "
          f"INFO({report['issues_by_severity']['INFO']})")

    if report['issues']:
        print("\nIssues Found:")
        for issue in report['issues'][:10]:  # Show first 10 issues
            file_info = f" - {issue.get('file', '')}" if issue.get('file') else ""
            line_info = f":{issue.get('line', '')}" if issue.get('line') else ""
            print(f"  {issue['severity']} - {issue['type']}{file_info}{line_info}")
            print(f"    {issue['message']}")

        if len(report['issues']) > 10:
            print(f"  ... and {len(report['issues']) - 10} more issues")

        # Save full report
        with open('migration-check-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report saved to: migration-check-report.json")

    # Exit with appropriate code
    if report['status'] == 'FAIL':
        print("\nFAILURE: Critical migration issues found!")
        sys.exit(1)
    elif report['status'] == 'WARN':
        print("\nWARNING: Migration issues found. Review before proceeding.")
        sys.exit(0)
    else:
        print("\nSUCCESS: All migration checks passed.")
        sys.exit(0)


if __name__ == '__main__':
    main()