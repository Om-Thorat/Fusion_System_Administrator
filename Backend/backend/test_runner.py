#!/usr/bin/env python
"""
Test runner script for regression testing during Django architecture refactor.

This script provides utilities to run the comprehensive regression test suite
that locks in current API behavior before refactoring begins.

Usage:
    python test_runner.py --all                    # Run all regression tests
    python test_runner.py --academic              # Run academic data tests
    python test_runner.py --users                 # Run user management tests
    python test_runner.py --backup                # Run backup tests
    python test_runner.py --health                # Run health check tests
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner


def setup_django():
    """Setup Django environment for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()


def run_regression_tests(test_pattern=None):
    """Run regression tests with optional pattern filtering"""
    setup_django()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)
    
    if test_pattern:
        test_labels = [f'api.tests.{test_pattern}']
    else:
        test_labels = ['api.tests']
    
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        sys.exit(1)
    else:
        print("\n✅ All regression tests passed!")


def main():
    """Main test runner entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Django architecture refactor regression tests')
    parser.add_argument('--all', action='store_true', help='Run all regression tests')
    parser.add_argument('--academic', action='store_true', help='Run academic data endpoint tests')
    parser.add_argument('--users', action='store_true', help='Run user management tests')
    parser.add_argument('--backup', action='store_true', help='Run backup endpoint tests')
    parser.add_argument('--health', action='store_true', help='Run health check tests')
    parser.add_argument('--roles', action='store_true', help='Run role management tests')
    
    args = parser.parse_args()
    
    if args.academic:
        run_regression_tests('AcademicDataEndpointsTest')
    elif args.users:
        run_regression_tests('UserCreationEndpointsTest')
    elif args.backup:
        run_regression_tests('BackupEndpointsTest')
    elif args.health:
        run_regression_tests('HealthCheckEndpointsTest')
    elif args.roles:
        run_regression_tests('RoleManagementEndpointsTest')
    else:
        # Run all tests by default
        run_regression_tests()


if __name__ == '__main__':
    main()