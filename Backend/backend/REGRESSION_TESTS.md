# Regression Test Suite Documentation

This document describes the comprehensive regression test suite created to lock in current API behavior before the Django architecture refactor begins.

## Overview

The regression test suite in `api/tests.py` contains **over 40 test cases** that verify the exact behavior of all existing API endpoints. These tests ensure that the refactoring process maintains 100% functional compatibility.

## Test Structure

### Base Test Case
- `RegressionTestCase`: Provides common setup with test data for all test classes
- Creates test instances of: User, Department, Designation, Programme, Batch
- Provides consistent test environment across all test classes

### Test Classes

#### 1. AcademicDataEndpointsTest
Tests for basic academic data endpoints:
- `get_all_departments` - Verifies department list format
- `get_all_batches` - Verifies batch list format  
- `get_all_programmes` - Verifies programme list format

#### 2. UserRoleEndpointsTest
Tests for user and role management:
- `get_user_role_by_username` - Tests user role lookup with various scenarios
- `global_designation_list` - Tests designation listing
- `get_category_designations` - Tests filtered designation retrieval
- `get_module_access` - Tests module access queries

#### 3. UserCreationEndpointsTest
Tests for user creation endpoints:
- `add_individual_student` - Tests student creation validation
- `add_individual_staff` - Tests staff creation validation
- `add_individual_faculty` - Tests faculty creation validation
- `reset_password` - Tests password reset functionality

#### 4. BulkOperationEndpointsTest
Tests for bulk operations:
- `bulk_import_users` - Tests CSV import functionality
- `bulk_export_users` - Tests CSV export format
- `download_sample_csv` - Tests sample CSV download

#### 5. UserListViewTest
Tests for user listing with filters:
- Tests user list endpoint with different type parameters
- Verifies response format for student, faculty, staff types

#### 6. BackupEndpointsTest
Tests for backup management:
- `list_backups` - Tests backup listing
- `create_backup` - Tests backup creation (mocked)
- `get_backup` - Tests backup retrieval
- `list_restores` - Tests restore listing
- `list_schedules` - Tests schedule listing
- `save_schedule` - Tests schedule creation

#### 7. HealthCheckEndpointsTest
Tests for system health monitoring:
- `list_health_checks` - Tests health check listing
- `run_health_check` - Tests health check execution (mocked)
- `db_info` - Tests database info retrieval (mocked)

#### 8. RoleManagementEndpointsTest
Tests for role and permission management:
- `add_designation` - Tests role creation
- `update_designation` - Tests role modification
- `modify_moduleaccess` - Tests module access updates

#### 9. UpdateUserRolesEndpointTest
Tests for user role assignment:
- `update_user_roles` - Tests role assignment with validation

#### 10. UpdateGlobalDbEndpointTest
Tests for database schema updates:
- `update_globals_db` - Tests DDL execution (mocked)

#### 11. MailBatchEndpointTest
Tests for batch email functionality:
- `mail_to_whole_batch` - Tests batch email sending (mocked)

### Test Data Factory
- `TestDataFactory`: Provides factory methods for creating consistent test data
- Methods for creating users, designations, departments, programmes, batches

## Key Testing Strategies

### 1. Response Format Validation
- Verifies exact response structure and field presence
- Ensures JSON response format consistency
- Validates HTTP status codes

### 2. Error Scenario Testing
- Tests missing parameter scenarios
- Tests invalid data scenarios
- Tests not-found scenarios
- Verifies exact error message formats

### 3. Mocking External Dependencies
- Mocks database connections for DDL operations
- Mocks threading for background processes
- Mocks email sending functionality
- Ensures tests run in isolation

### 4. Status Code Verification
- Validates exact HTTP status codes (200, 201, 400, 404, 500)
- Ensures error responses match current behavior
- Tests both success and failure paths

## Running the Tests

### Prerequisites
1. Activate virtual environment: `venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up test database: `python manage.py migrate`

### Running All Tests
```bash
python manage.py test api.tests --verbosity=2
```

### Running Specific Test Classes
```bash
# Academic data tests
python manage.py test api.tests.AcademicDataEndpointsTest --verbosity=2

# User management tests
python manage.py test api.tests.UserCreationEndpointsTest --verbosity=2

# Backup tests
python manage.py test api.tests.BackupEndpointsTest --verbosity=2
```

### Using the Test Runner Script
```bash
# Run all tests
python test_runner.py --all

# Run specific test categories
python test_runner.py --academic
python test_runner.py --users
python test_runner.py --backup
python test_runner.py --health
python test_runner.py --roles
```

## Test Coverage

The regression test suite covers:
- ✅ **25+ API endpoints** across all domains
- ✅ **40+ test scenarios** including edge cases
- ✅ **All HTTP methods** (GET, POST, PUT, DELETE)
- ✅ **Error handling** and validation scenarios
- ✅ **Response format** verification
- ✅ **Status code** validation
- ✅ **Mocked external dependencies**

## Integration with Refactoring Process

### Phase 1: Baseline Establishment
1. Run full regression test suite before any changes
2. Document any failing tests and fix them first
3. Establish green baseline for all tests

### Phase 2: During Refactoring
1. Run tests after each major change
2. Ensure no regressions are introduced
3. Fix any failing tests immediately

### Phase 3: Post-Refactoring Validation
1. Run full test suite after refactoring completion
2. Verify all tests still pass with new architecture
3. Add additional unit tests for new layers (selectors, services)

## Expected Test Results

When the environment is properly set up, all tests should pass with output similar to:
```
test_get_all_departments_response_format (api.tests.AcademicDataEndpointsTest) ... ok
test_get_all_batches_response_format (api.tests.AcademicDataEndpointsTest) ... ok
test_get_all_programmes_response_format (api.tests.AcademicDataEndpointsTest) ... ok
...
Ran 40 tests in 2.345s

OK
```

## Troubleshooting

### Common Issues
1. **Django not found**: Ensure virtual environment is activated
2. **Database errors**: Run `python manage.py migrate` first
3. **Import errors**: Check that all model imports are correct
4. **Mock failures**: Verify mock patch paths match actual module structure

### Environment Setup
If tests fail to run due to environment issues:
1. Check virtual environment activation
2. Verify Django installation: `pip show django`
3. Check database connectivity
4. Ensure all required packages are installed

This regression test suite provides a solid foundation for the architecture refactor, ensuring that all existing functionality is preserved throughout the process.