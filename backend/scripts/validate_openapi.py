#!/usr/bin/env python3
"""
Script to validate OpenAPI schema and generate API documentation.
Used as part of CI/CD pipeline to ensure API consistency.
"""
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import subprocess
import tempfile
import os

try:
    from fastapi import FastAPI
    from fastapi.openapi.utils import get_openapi
    import uvicorn
    import requests
except ImportError as e:
    print(f"Required packages not installed: {e}")
    print("Install with: pip install fastapi uvicorn requests")
    sys.exit(1)


class OpenAPIValidator:
    """Validates OpenAPI schema and API endpoints."""

    def __init__(self, app_module: str = "app.main:app"):
        self.app_module = app_module
        self.issues = []
        self.schema = None

    def load_app_schema(self) -> Dict[str, Any]:
        """Load OpenAPI schema from FastAPI app."""
        try:
            # Import the FastAPI app
            module_path, app_name = self.app_module.split(':')
            module = __import__(module_path, fromlist=[app_name])
            app = getattr(module, app_name)

            if not isinstance(app, FastAPI):
                raise ValueError(f"{app_name} is not a FastAPI instance")

            # Generate OpenAPI schema
            self.schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )

            return self.schema

        except Exception as e:
            self.issues.append({
                'type': 'SCHEMA_LOAD_ERROR',
                'severity': 'HIGH',
                'message': f"Cannot load OpenAPI schema: {e}"
            })
            return {}

    def validate_schema_structure(self) -> None:
        """Validate OpenAPI schema structure."""
        if not self.schema:
            return

        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in self.schema:
                self.issues.append({
                    'type': 'MISSING_REQUIRED_FIELD',
                    'severity': 'HIGH',
                    'field': field,
                    'message': f"Missing required OpenAPI field: {field}"
                })

        # Validate info section
        if 'info' in self.schema:
            info_required = ['title', 'version']
            for field in info_required:
                if field not in self.schema['info']:
                    self.issues.append({
                        'type': 'MISSING_INFO_FIELD',
                        'severity': 'MEDIUM',
                        'field': field,
                        'message': f"Missing required info field: {field}"
                    })

            # Check for description
            if 'description' not in self.schema['info']:
                self.issues.append({
                    'type': 'MISSING_DESCRIPTION',
                    'severity': 'LOW',
                    'message': "API description is recommended"
                })

    def validate_paths(self) -> None:
        """Validate API paths and operations."""
        if not self.schema or 'paths' not in self.schema:
            return

        paths = self.schema['paths']
        if not paths:
            self.issues.append({
                'type': 'NO_PATHS',
                'severity': 'HIGH',
                'message': "No API paths defined"
            })
            return

        for path, methods in paths.items():
            self._validate_path(path, methods)

    def _validate_path(self, path: str, methods: Dict[str, Any]) -> None:
        """Validate individual path and its operations."""
        for method, operation in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                continue

            # Check for operation ID
            if 'operationId' not in operation:
                self.issues.append({
                    'type': 'MISSING_OPERATION_ID',
                    'severity': 'MEDIUM',
                    'path': path,
                    'method': method,
                    'message': f"Missing operationId for {method.upper()} {path}"
                })

            # Check for summary and description
            if 'summary' not in operation:
                self.issues.append({
                    'type': 'MISSING_SUMMARY',
                    'severity': 'LOW',
                    'path': path,
                    'method': method,
                    'message': f"Missing summary for {method.upper()} {path}"
                })

            if 'description' not in operation:
                self.issues.append({
                    'type': 'MISSING_DESCRIPTION',
                    'severity': 'LOW',
                    'path': path,
                    'method': method,
                    'message': f"Missing description for {method.upper()} {path}"
                })

            # Validate responses
            self._validate_responses(path, method, operation.get('responses', {}))

            # Validate parameters
            self._validate_parameters(path, method, operation.get('parameters', []))

    def _validate_responses(self, path: str, method: str, responses: Dict[str, Any]) -> None:
        """Validate operation responses."""
        if not responses:
            self.issues.append({
                'type': 'NO_RESPONSES',
                'severity': 'HIGH',
                'path': path,
                'method': method,
                'message': f"No responses defined for {method.upper()} {path}"
            })
            return

        # Check for success response
        success_codes = ['200', '201', '202', '204']
        has_success = any(code in responses for code in success_codes)

        if not has_success:
            self.issues.append({
                'type': 'NO_SUCCESS_RESPONSE',
                'severity': 'MEDIUM',
                'path': path,
                'method': method,
                'message': f"No success response defined for {method.upper()} {path}"
            })

        # Check for error responses
        if method.upper() != 'GET' and '400' not in responses:
            self.issues.append({
                'type': 'MISSING_ERROR_RESPONSE',
                'severity': 'LOW',
                'path': path,
                'method': method,
                'message': f"Consider adding 400 error response for {method.upper()} {path}"
            })

        # Validate response schemas
        for status_code, response in responses.items():
            if 'content' in response:
                for media_type, content in response['content'].items():
                    if 'schema' not in content:
                        self.issues.append({
                            'type': 'MISSING_RESPONSE_SCHEMA',
                            'severity': 'MEDIUM',
                            'path': path,
                            'method': method,
                            'status_code': status_code,
                            'media_type': media_type,
                            'message': f"Missing schema for {status_code} response in {method.upper()} {path}"
                        })

    def _validate_parameters(self, path: str, method: str, parameters: List[Dict[str, Any]]) -> None:
        """Validate operation parameters."""
        for param in parameters:
            # Check required fields
            required_param_fields = ['name', 'in']
            for field in required_param_fields:
                if field not in param:
                    self.issues.append({
                        'type': 'MISSING_PARAMETER_FIELD',
                        'severity': 'HIGH',
                        'path': path,
                        'method': method,
                        'parameter': param.get('name', 'unknown'),
                        'field': field,
                        'message': f"Missing {field} in parameter for {method.upper()} {path}"
                    })

            # Check for description
            if 'description' not in param:
                self.issues.append({
                    'type': 'MISSING_PARAMETER_DESCRIPTION',
                    'severity': 'LOW',
                    'path': path,
                    'method': method,
                    'parameter': param.get('name', 'unknown'),
                    'message': f"Missing description for parameter {param.get('name')} in {method.upper()} {path}"
                })

            # Check for schema
            if 'schema' not in param and 'content' not in param:
                self.issues.append({
                    'type': 'MISSING_PARAMETER_SCHEMA',
                    'severity': 'MEDIUM',
                    'path': path,
                    'method': method,
                    'parameter': param.get('name', 'unknown'),
                    'message': f"Missing schema for parameter {param.get('name')} in {method.upper()} {path}"
                })

    def validate_components(self) -> None:
        """Validate OpenAPI components."""
        if not self.schema or 'components' not in self.schema:
            return

        components = self.schema['components']

        # Validate schemas
        if 'schemas' in components:
            for schema_name, schema_def in components['schemas'].items():
                self._validate_schema_definition(schema_name, schema_def)

        # Check for security schemes
        if 'securitySchemes' not in components:
            self.issues.append({
                'type': 'NO_SECURITY_SCHEMES',
                'severity': 'MEDIUM',
                'message': "No security schemes defined. Consider adding authentication."
            })

    def _validate_schema_definition(self, name: str, schema_def: Dict[str, Any]) -> None:
        """Validate individual schema definition."""
        # Check for type
        if 'type' not in schema_def and '$ref' not in schema_def:
            self.issues.append({
                'type': 'MISSING_SCHEMA_TYPE',
                'severity': 'MEDIUM',
                'schema': name,
                'message': f"Schema {name} missing type definition"
            })

        # Check for description
        if 'description' not in schema_def:
            self.issues.append({
                'type': 'MISSING_SCHEMA_DESCRIPTION',
                'severity': 'LOW',
                'schema': name,
                'message': f"Schema {name} missing description"
            })

        # Validate object properties
        if schema_def.get('type') == 'object' and 'properties' in schema_def:
            properties = schema_def['properties']
            required = schema_def.get('required', [])

            for prop_name, prop_def in properties.items():
                if 'type' not in prop_def and '$ref' not in prop_def:
                    self.issues.append({
                        'type': 'MISSING_PROPERTY_TYPE',
                        'severity': 'MEDIUM',
                        'schema': name,
                        'property': prop_name,
                        'message': f"Property {prop_name} in schema {name} missing type"
                    })

                # Check for description on required properties
                if prop_name in required and 'description' not in prop_def:
                    self.issues.append({
                        'type': 'MISSING_PROPERTY_DESCRIPTION',
                        'severity': 'LOW',
                        'schema': name,
                        'property': prop_name,
                        'message': f"Required property {prop_name} in schema {name} missing description"
                    })

    def test_api_endpoints(self, base_url: str = "http://localhost:8000") -> None:
        """Test API endpoints for basic functionality."""
        if not self.schema or 'paths' not in self.schema:
            return

        try:
            # Test health endpoint first
            health_response = requests.get(f"{base_url}/health", timeout=5)
            if health_response.status_code != 200:
                self.issues.append({
                    'type': 'HEALTH_CHECK_FAILED',
                    'severity': 'HIGH',
                    'message': f"Health check failed: {health_response.status_code}"
                })
                return

        except requests.exceptions.RequestException as e:
            self.issues.append({
                'type': 'API_UNREACHABLE',
                'severity': 'HIGH',
                'message': f"Cannot reach API at {base_url}: {e}"
            })
            return

        # Test GET endpoints
        paths = self.schema['paths']
        for path, methods in paths.items():
            if 'get' in methods:
                self._test_endpoint('GET', f"{base_url}{path}", path)

    def _test_endpoint(self, method: str, url: str, path: str) -> None:
        """Test individual API endpoint."""
        try:
            response = requests.request(method, url, timeout=10)

            # Check for expected response codes
            if response.status_code >= 500:
                self.issues.append({
                    'type': 'SERVER_ERROR',
                    'severity': 'HIGH',
                    'path': path,
                    'method': method,
                    'status_code': response.status_code,
                    'message': f"{method} {path} returned server error: {response.status_code}"
                })

        except requests.exceptions.RequestException as e:
            self.issues.append({
                'type': 'ENDPOINT_ERROR',
                'severity': 'MEDIUM',
                'path': path,
                'method': method,
                'message': f"Error testing {method} {path}: {e}"
            })

    def save_schema(self, output_path: str = "openapi.json") -> None:
        """Save OpenAPI schema to file."""
        if not self.schema:
            return

        try:
            with open(output_path, 'w') as f:
                json.dump(self.schema, f, indent=2)
            print(f"OpenAPI schema saved to: {output_path}")

            # Also save as YAML
            yaml_path = output_path.replace('.json', '.yaml')
            with open(yaml_path, 'w') as f:
                yaml.dump(self.schema, f, default_flow_style=False)
            print(f"OpenAPI schema saved to: {yaml_path}")

        except Exception as e:
            self.issues.append({
                'type': 'SCHEMA_SAVE_ERROR',
                'severity': 'LOW',
                'message': f"Cannot save schema: {e}"
            })

    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        issues_by_severity = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        issues_by_type = {}

        for issue in self.issues:
            severity = issue['severity']
            issue_type = issue['type']

            issues_by_severity[severity] += 1
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1

        # Determine status
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
            'schema_valid': bool(self.schema),
            'issues': self.issues
        }


def main():
    """Main function to run OpenAPI validation."""
    validator = OpenAPIValidator()

    print("OpenAPI Schema Validation")
    print("=" * 40)

    # Load schema
    print("Loading OpenAPI schema...")
    schema = validator.load_app_schema()

    if schema:
        print(f"✓ Schema loaded successfully")
        print(f"  Title: {schema.get('info', {}).get('title', 'Unknown')}")
        print(f"  Version: {schema.get('info', {}).get('version', 'Unknown')}")
        print(f"  Paths: {len(schema.get('paths', {}))}")

        # Run validations
        print("\nRunning validations...")
        validator.validate_schema_structure()
        validator.validate_paths()
        validator.validate_components()

        # Save schema
        validator.save_schema()

        # Test endpoints if requested
        if '--test-endpoints' in sys.argv:
            print("\nTesting API endpoints...")
            validator.test_api_endpoints()

    else:
        print("✗ Failed to load schema")

    # Generate report
    report = validator.generate_report()

    print(f"\nValidation Results:")
    print(f"Status: {report['status']}")
    print(f"Total Issues: {report['total_issues']}")
    print(f"By Severity: HIGH({report['issues_by_severity']['HIGH']}) "
          f"MEDIUM({report['issues_by_severity']['MEDIUM']}) "
          f"LOW({report['issues_by_severity']['LOW']})")

    if report['issues']:
        print("\nIssues Found:")
        for issue in report['issues'][:10]:
            path_info = f" - {issue.get('path', '')}" if issue.get('path') else ""
            method_info = f" {issue.get('method', '')}" if issue.get('method') else ""
            print(f"  {issue['severity']} - {issue['type']}{method_info}{path_info}")
            print(f"    {issue['message']}")

        if len(report['issues']) > 10:
            print(f"  ... and {len(report['issues']) - 10} more issues")

        # Save report
        with open('openapi-validation-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report saved to: openapi-validation-report.json")

    # Exit with appropriate code
    if report['status'] == 'FAIL':
        print("\nFAILURE: Critical OpenAPI issues found!")
        sys.exit(1)
    elif report['status'] == 'WARN':
        print("\nWARNING: OpenAPI issues found. Review recommended.")
        sys.exit(0)
    else:
        print("\nSUCCESS: OpenAPI validation passed.")
        sys.exit(0)


if __name__ == '__main__':
    main()