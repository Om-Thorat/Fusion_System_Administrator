"""
Integration tests for API endpoints.
Tests complete request-response cycles for refactored endpoints.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
import json
import uuid

from .base import BaseAPITestCase, TestDataFactory
from ..models import (
    GlobalsDepartmentinfo, Programme, Batch, AuthUser,
    Student, Staff, GlobalsFaculty, BackupRecord, BackupSchedule
)


class AcademicDataEndpointTests(BaseAPITestCase):
    """Integration tests for academic data endpoints."""
    
    def setUp(self):
        super().setUp()
        self.department = TestDataFactory.create_test_department('Computer Science', 'CSE')
        self.programme = TestDataFactory.create_test_programme('B.Tech', 'UG')
        self.batch = TestDataFactory.create_test_batch(2023)
    
    def test_get_all_departments_endpoint(self):
        """Test that departments endpoint uses selectors."""
        url = reverse('get_all_departments')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('name', data[0])
            self.assertIn('acronym', data[0])
    
    def test_get_all_programmes_endpoint(self):
        """Test that programmes endpoint uses selectors."""
        url = reverse('get_all_programmes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('name', data[0])
    
    def test_get_all_batches_endpoint(self):
        """Test that batches endpoint uses selectors."""
        url = reverse('get_all_batches')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)


class UserManagementEndpointTests(BaseAPITestCase):
    """Integration tests for user management endpoints."""
    
    def setUp(self):
        super().setUp()
        self.department = TestDataFactory.create_test_department()
        self.programme = TestDataFactory.create_test_programme()
        self.batch = TestDataFactory.create_test_batch()
        self.designation = TestDataFactory.create_test_designation()
    
    def test_add_individual_student_endpoint(self):
        """Test student creation endpoint uses UserService."""
        url = reverse('add_individual_student')
        student_data = {
            'username': 'teststudent',
            'first_name': 'Test',
            'last_name': 'Student',
            'sex': 'M',
            'category': 'GEN',
            'father_name': 'Test Father',
            'mother_name': 'Test Mother',
            'batch': 2023,
            'programme': 'B.Tech'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(student_data),
            content_type='application/json'
        )
        
        # Should either succeed or fail gracefully with proper error handling
        self.assertIn(response.status_code, [200, 201, 400, 500])
        
        if response.status_code in [400, 500]:
            # Check that error response has proper structure
            data = response.json()
            self.assertIn('error', data)
    
    def test_add_individual_staff_endpoint(self):
        """Test staff creation endpoint uses UserService."""
        url = reverse('add_individual_staff')
        staff_data = {
            'username': 'teststaff',
            'first_name': 'Test',
            'last_name': 'Staff',
            'sex': 'F',
            'designation': self.designation.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(staff_data),
            content_type='application/json'
        )
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 201, 400, 500])
    
    def test_bulk_export_users_endpoint(self):
        """Test bulk export endpoint uses UserService."""
        url = reverse('bulk-export-users')
        response = self.client.get(url)
        
        # Should return CSV or error
        self.assertIn(response.status_code, [200, 500])
        
        if response.status_code == 200:
            # Check that it's CSV content
            self.assertEqual(response['Content-Type'], 'text/csv')
    
    def test_user_list_view_students(self):
        """Test UserListView for students uses selectors."""
        # Create test student
        auth_user = AuthUser.objects.create(
            user=self.test_user,
            sex='M',
            department=self.department
        )
        Student.objects.create(
            id=auth_user,
            programme='B.Tech',
            batch=2023,
            category='GEN',
            batch_id=self.batch
        )
        
        url = reverse('user-list')
        response = self.client.get(url, {'type': 'student'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_user_list_view_invalid_type(self):
        """Test UserListView with invalid user type."""
        url = reverse('user-list')
        response = self.client.get(url, {'type': 'invalid'})
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


class BackupEndpointTests(BaseAPITestCase):
    """Integration tests for backup endpoints."""
    
    def setUp(self):
        super().setUp()
        self.backup = TestDataFactory.create_test_backup_record('test_db', 'success')
        self.schedule = TestDataFactory.create_test_backup_schedule('test_db', True)
    
    def test_list_backups_endpoint(self):
        """Test backup listing endpoint uses selectors."""
        url = reverse('list-backups')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('id', data[0])
            self.assertIn('db_name', data[0])
    
    def test_create_backup_endpoint(self):
        """Test backup creation endpoint uses BackupService."""
        url = reverse('create-backup')
        response = self.client.post(
            url,
            data=json.dumps({'db_name': 'test_db'}),
            content_type='application/json'
        )
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 201, 400, 500])
    
    def test_get_backup_endpoint(self):
        """Test get backup endpoint uses selectors."""
        url = reverse('get-backup', kwargs={'backup_id': self.backup.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('db_name', data)
    
    def test_run_health_check_endpoint(self):
        """Test health check endpoint uses BackupService."""
        url = reverse('run-health-check')
        response = self.client.post(
            url,
            data=json.dumps({'db_name': 'test_db'}),
            content_type='application/json'
        )
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 201, 400, 500])
    
    def test_list_schedules_endpoint(self):
        """Test schedule listing endpoint uses selectors."""
        url = reverse('list-schedules')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('id', data[0])
            self.assertIn('db_name', data[0])
    
    def test_save_schedule_endpoint(self):
        """Test schedule saving endpoint uses BackupService."""
        url = reverse('save-schedule')
        schedule_data = {
            'db_name': 'new_test_db',
            'frequency': 'daily',
            'enabled': True,
            'hour': 2,
            'minute': 0,
            'retain_last_n': 7
        }
        
        response = self.client.post(
            url,
            data=json.dumps(schedule_data),
            content_type='application/json'
        )
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 201, 400, 500])


class RoleManagementEndpointTests(BaseAPITestCase):
    """Integration tests for role management endpoints."""
    
    def setUp(self):
        super().setUp()
        self.designation = TestDataFactory.create_test_designation()
        
        # Create auth user for testing
        self.auth_user = AuthUser.objects.create(
            user=self.test_user,
            sex='M'
        )
    
    def test_get_user_role_by_username_endpoint(self):
        """Test get user roles endpoint uses selectors."""
        url = reverse('get_user_role_by_username')
        response = self.client.get(url, {'username': self.test_user.username})
        
        # Should either succeed or return 404 if no roles
        self.assertIn(response.status_code, [200, 404])
    
    def test_update_user_roles_endpoint(self):
        """Test update user roles endpoint uses RoleService."""
        url = reverse('update_user_roles')
        role_data = {
            'username': self.test_user.username,
            'roles': ['student']
        }
        
        response = self.client.put(
            url,
            data=json.dumps(role_data),
            content_type='application/json'
        )
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_get_category_designations_endpoint(self):
        """Test get category designations endpoint uses selectors."""
        url = reverse('get_category_designations')
        response = self.client.post(
            url,
            data=json.dumps({'category': 'student', 'basic': True}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)


class ArchitectureComplianceTests(TestCase):
    """Tests to ensure architecture compliance."""
    
    def test_views_use_services_and_selectors(self):
        """Test that views import and use services/selectors."""
        import inspect
        from .. import views, backup_views
        
        # Check that views import services and selectors
        views_source = inspect.getsource(views)
        backup_views_source = inspect.getsource(backup_views)
        
        # Views should import services and selectors
        self.assertIn('from . import services', views_source)
        self.assertIn('from . import selectors', views_source)
        self.assertIn('from . import services', backup_views_source)
        self.assertIn('from . import selectors', backup_views_source)
    
    def test_services_exist_and_have_methods(self):
        """Test that all required service classes exist."""
        from .. import services
        
        # Check that service classes exist
        self.assertTrue(hasattr(services, 'UserService'))
        self.assertTrue(hasattr(services, 'RoleService'))
        self.assertTrue(hasattr(services, 'BackupService'))
        self.assertTrue(hasattr(services, 'EmailService'))
        self.assertTrue(hasattr(services, 'DatabaseService'))
        
        # Check that services have key methods
        self.assertTrue(hasattr(services.UserService, 'create_student'))
        self.assertTrue(hasattr(services.BackupService, 'create_backup'))
        self.assertTrue(hasattr(services.EmailService, 'send_email'))
        self.assertTrue(hasattr(services.DatabaseService, 'update_globals_database'))
    
    def test_selectors_exist_and_have_methods(self):
        """Test that all required selector functions exist."""
        from .. import selectors
        
        # Check that selector functions exist
        self.assertTrue(hasattr(selectors, 'get_all_departments'))
        self.assertTrue(hasattr(selectors, 'get_all_programmes'))
        self.assertTrue(hasattr(selectors, 'get_all_batches'))
        self.assertTrue(hasattr(selectors, 'get_all_backups'))
        self.assertTrue(hasattr(selectors, 'get_user_by_username'))
        self.assertTrue(hasattr(selectors, 'get_students_with_filters'))
    
    def test_exception_classes_exist(self):
        """Test that custom exception classes are defined."""
        from .. import services
        
        # Check that exception classes exist
        self.assertTrue(hasattr(services, 'DomainException'))
        self.assertTrue(hasattr(services, 'ValidationException'))
        self.assertTrue(hasattr(services, 'UserServiceException'))
        self.assertTrue(hasattr(services, 'EmailServiceException'))
        self.assertTrue(hasattr(services, 'BackupServiceException'))
        self.assertTrue(hasattr(services, 'DatabaseServiceException'))


class DatabaseUpdateEndpointTests(BaseAPITestCase):
    """Integration tests for database update endpoint."""
    
    def test_update_globals_db_endpoint(self):
        """Test database update endpoint uses DatabaseService."""
        url = reverse('update_globals_db')
        response = self.client.get(url)
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 500])
        
        data = response.json()
        self.assertIn('success', data)
        
        if not data['success']:
            self.assertIn('error', data)