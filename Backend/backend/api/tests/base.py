"""
Base test classes and common fixtures for the Django architecture refactor tests.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from unittest.mock import Mock, patch
import uuid


class BaseTestCase(TestCase):
    """Base test case with common setup for unit tests."""
    
    def setUp(self):
        """Set up test data."""
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def create_test_user(self, username='testuser2', email='test2@example.com'):
        """Helper to create additional test users."""
        return User.objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )


class BaseAPITestCase(APITestCase):
    """Base API test case with authentication setup."""
    
    def setUp(self):
        """Set up test data for API tests."""
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.test_user)


class BaseServiceTestCase(BaseTestCase):
    """Base test case for service layer tests with mocking utilities."""
    
    def setUp(self):
        super().setUp()
        # Common mocks can be set up here
        
    def mock_database_operations(self):
        """Helper to mock database operations."""
        return patch('django.db.models.QuerySet')
        
    def create_mock_queryset(self, return_value=None):
        """Create a mock QuerySet."""
        mock_qs = Mock()
        if return_value is not None:
            mock_qs.return_value = return_value
        return mock_qs


class BaseSelectorTestCase(BaseTestCase):
    """Base test case for selector layer tests."""
    
    def setUp(self):
        super().setUp()
        # Set up test data for selectors
        self.create_test_data()
        
    def create_test_data(self):
        """Create test data for selector tests."""
        # This will be overridden by specific test classes
        pass


class BaseIntegrationTestCase(TransactionTestCase):
    """Base test case for integration tests that need database transactions."""
    
    def setUp(self):
        """Set up test data for integration tests."""
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )


# Test data factories
class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_test_department(name='Computer Science', acronym='CSE'):
        """Create a test department."""
        from ..models import GlobalsDepartmentinfo
        return GlobalsDepartmentinfo.objects.create(
            name=name,
            acronym=acronym
        )
    
    @staticmethod
    def create_test_programme(name='B.Tech', category='UG'):
        """Create a test programme."""
        from ..models import Programme
        return Programme.objects.create(
            name=name,
            category=category
        )
    
    @staticmethod
    def create_test_batch(year=2023, discipline=None):
        """Create a test batch."""
        from ..models import Batch
        if discipline is None:
            discipline = TestDataFactory.create_test_discipline()
        return Batch.objects.create(
            year=year,
            discipline=discipline
        )
    
    @staticmethod
    def create_test_discipline(name='Computer Science', acronym='CSE'):
        """Create a test discipline."""
        from ..models import Discipline
        return Discipline.objects.create(
            name=name,
            acronym=acronym
        )
    
    @staticmethod
    def create_test_designation(name='student', category='student', basic=True):
        """Create a test designation."""
        from ..models import GlobalsDesignation
        return GlobalsDesignation.objects.create(
            name=name,
            category=category,
            basic=basic
        )
    
    @staticmethod
    def create_test_backup_record(db_name='test_db', status='success'):
        """Create a test backup record."""
        from ..models import BackupRecord
        return BackupRecord.objects.create(
            id=uuid.uuid4(),
            db_name=db_name,
            status=status,
            size_bytes=1024,
            duration_ms=1000
        )
    
    @staticmethod
    def create_test_backup_schedule(db_name='test_db', enabled=True):
        """Create a test backup schedule."""
        from ..models import BackupSchedule
        return BackupSchedule.objects.create(
            id=uuid.uuid4(),
            db_name=db_name,
            enabled=enabled,
            frequency='daily',
            hour=2,
            minute=0,
            retain_last_n=7
        )


# Mock utilities
class MockUtilities:
    """Utilities for creating mocks in tests."""
    
    @staticmethod
    def mock_email_backend():
        """Mock the email backend."""
        return patch('django.core.mail.backends.smtp.EmailBackend.send_messages')
    
    @staticmethod
    def mock_subprocess_run():
        """Mock subprocess.run for backup operations."""
        return patch('subprocess.run')
    
    @staticmethod
    def mock_file_operations():
        """Mock file system operations."""
        return patch('os.path.exists'), patch('os.remove'), patch('os.path.getsize')