"""
Unit tests for the services layer.
Tests all service classes with mocked dependencies.
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from io import StringIO
import uuid

from .base import BaseServiceTestCase, TestDataFactory, MockUtilities
from .. import services
from ..models import (
    AuthUser, GlobalsExtrainfo, Student, Staff, GlobalsFaculty,
    GlobalsDesignation, GlobalsHoldsdesignation, BackupRecord,
    BackupSchedule, HealthCheck, RestoreRecord
)


class UserServiceTest(BaseServiceTestCase):
    """Test cases for UserService."""
    
    def setUp(self):
        super().setUp()
        self.department = TestDataFactory.create_test_department()
        self.programme = TestDataFactory.create_test_programme()
        self.batch = TestDataFactory.create_test_batch()
        self.designation = TestDataFactory.create_test_designation()
    
    def test_create_student_success(self):
        """Test successful student creation."""
        student_data = {
            'username': 'john_doe',
            'first_name': 'John',
            'last_name': 'Doe',
            'sex': 'M',
            'category': 'GEN',
            'father_name': 'John Sr.',
            'mother_name': 'Jane Doe',
            'batch': 2023,
            'programme': 'B.Tech'
        }
        
        with patch('api.services.create_password') as mock_password:
            mock_password.return_value = 'test_password'
            
            student = services.UserService.create_student(student_data)
            
            self.assertIsNotNone(student)
            self.assertEqual(student.id.user.username, 'john_doe')
            self.assertEqual(student.id.user.first_name, 'John')
    
    def test_create_student_missing_required_field(self):
        """Test student creation with missing required field."""
        student_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            # Missing username
        }
        
        with self.assertRaises(services.ValidationException):
            services.UserService.create_student(student_data)
    
    def test_create_staff_success(self):
        """Test successful staff creation."""
        staff_data = {
            'username': 'jane_smith',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'sex': 'F',
            'designation': self.designation.id
        }
        
        with patch('api.services.create_password') as mock_password:
            mock_password.return_value = 'test_password'
            
            staff = services.UserService.create_staff(staff_data)
            
            self.assertIsNotNone(staff)
            self.assertEqual(staff.id.user.username, 'jane_smith')
    
    @patch('api.services.csv.DictReader')
    def test_bulk_import_students_from_csv(self, mock_csv_reader):
        """Test bulk import of students from CSV."""
        # Mock CSV data
        mock_csv_reader.return_value = [
            {
                'username': 'student1',
                'first_name': 'Student',
                'last_name': 'One',
                'sex': 'M',
                'category': 'GEN',
                'father_name': 'Father One',
                'mother_name': 'Mother One',
                'batch': '2023',
                'programme': 'B.Tech'
            }
        ]
        
        csv_file = SimpleUploadedFile("test.csv", b"test content", content_type="text/csv")
        
        with patch('api.services.create_password') as mock_password:
            mock_password.return_value = 'test_password'
            
            result = services.UserService.bulk_import_students_from_csv(csv_file)
            
            self.assertEqual(result['successful'], 1)
            self.assertEqual(result['failed'], 0)
    
    @patch('django.http.HttpResponse')
    def test_bulk_export_users_to_csv(self, mock_response):
        """Test bulk export of users to CSV."""
        # Create test student
        student_data = {
            'username': 'test_student',
            'first_name': 'Test',
            'last_name': 'Student',
            'sex': 'M',
            'category': 'GEN',
            'father_name': 'Test Father',
            'mother_name': 'Test Mother',
            'batch': 2023,
            'programme': 'B.Tech'
        }
        
        with patch('api.services.create_password'):
            services.UserService.create_student(student_data)
        
        response = services.UserService.bulk_export_users_to_csv()
        
        self.assertIsNotNone(response)


class RoleServiceTest(BaseServiceTestCase):
    """Test cases for RoleService."""
    
    def setUp(self):
        super().setUp()
        self.designation = TestDataFactory.create_test_designation()
    
    def test_update_user_roles_success(self):
        """Test successful user role update."""
        username = self.test_user.username
        roles = ['student']
        
        result = services.RoleService.update_user_roles(username, roles)
        
        self.assertTrue(result['success'])
        self.assertIn('updated successfully', result['message'])
    
    def test_update_user_roles_invalid_user(self):
        """Test role update with invalid user."""
        with self.assertRaises(services.UserServiceException):
            services.RoleService.update_user_roles('nonexistent', ['student'])
    
    def test_assign_designation_success(self):
        """Test successful designation assignment."""
        result = services.RoleService.assign_designation(
            self.test_user.id, 
            self.designation.id
        )
        
        self.assertTrue(result['success'])


class BackupServiceTest(BaseServiceTestCase):
    """Test cases for BackupService."""
    
    @patch('api.services.threading.Thread')
    def test_create_backup_success(self, mock_thread):
        """Test successful backup creation."""
        db_name = 'test_db'
        
        backup = services.BackupService.create_backup(db_name)
        
        self.assertIsNotNone(backup)
        self.assertEqual(backup.db_name, db_name)
        self.assertEqual(backup.status, 'in_progress')
        mock_thread.assert_called_once()
    
    def test_create_backup_missing_db_name(self):
        """Test backup creation with missing database name."""
        with self.assertRaises(services.ValidationException):
            services.BackupService.create_backup(None)
    
    def test_delete_backup_success(self):
        """Test successful backup deletion."""
        backup = TestDataFactory.create_test_backup_record()
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.remove') as mock_remove:
            mock_exists.return_value = True
            
            result = services.BackupService.delete_backup(str(backup.id))
            
            self.assertTrue(result['success'])
            mock_remove.assert_called_once()
    
    def test_delete_backup_not_found(self):
        """Test backup deletion with non-existent backup."""
        fake_id = str(uuid.uuid4())
        
        with self.assertRaises(services.UserServiceException):
            services.BackupService.delete_backup(fake_id)
    
    @patch('api.services.threading.Thread')
    def test_restore_backup_success(self, mock_thread):
        """Test successful backup restoration."""
        backup = TestDataFactory.create_test_backup_record()
        backup.status = 'success'
        backup.file_path = '/fake/path/backup.dump'
        backup.save()
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            restore_record = services.BackupService.restore_backup(str(backup.id))
            
            self.assertIsNotNone(restore_record)
            self.assertEqual(restore_record.status, 'in_progress')
            mock_thread.assert_called_once()
    
    def test_run_health_check_success(self):
        """Test successful health check."""
        db_name = 'test_db'
        
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = [1]
            
            health_check = services.BackupService.run_health_check(db_name)
            
            self.assertIsNotNone(health_check)
            self.assertEqual(health_check.db_name, db_name)
            self.assertEqual(health_check.status, 'healthy')
    
    def test_save_schedule_success(self):
        """Test successful schedule creation."""
        schedule_data = {
            'db_name': 'test_db',
            'frequency': 'daily',
            'enabled': True,
            'hour': 2,
            'minute': 0,
            'retain_last_n': 7
        }
        
        with patch('api.services.scheduler') as mock_scheduler:
            schedule = services.BackupService.save_schedule(schedule_data)
            
            self.assertIsNotNone(schedule)
            self.assertEqual(schedule.db_name, 'test_db')
            self.assertEqual(schedule.frequency, 'daily')


class EmailServiceTest(BaseServiceTestCase):
    """Test cases for EmailService."""
    
    @patch('django.core.mail.send_mail')
    def test_send_email_success(self, mock_send_mail):
        """Test successful email sending."""
        mock_send_mail.return_value = True
        
        result = services.EmailService.send_email(
            subject='Test Subject',
            message='Test Message',
            recipient_list=['test@example.com']
        )
        
        self.assertTrue(result['success'])
        mock_send_mail.assert_called_once()
    
    @patch('django.core.mail.send_mail')
    def test_send_email_failure(self, mock_send_mail):
        """Test email sending failure."""
        mock_send_mail.side_effect = Exception('SMTP Error')
        
        with self.assertRaises(services.EmailServiceException):
            services.EmailService.send_email(
                subject='Test Subject',
                message='Test Message',
                recipient_list=['test@example.com']
            )
    
    @patch('api.services.configure_password_mail')
    @patch('api.services.mail_to_user')
    def test_send_password_email_single(self, mock_mail_to_user, mock_configure):
        """Test sending password email to single user."""
        mock_configure.return_value = ('subject', 'message')
        mock_mail_to_user.return_value = True
        
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
        password = 'test_password'
        
        result = services.EmailService.send_password_email_single(user_data, password)
        
        self.assertTrue(result['success'])
        mock_mail_to_user.assert_called_once()
    
    def test_send_batch_emails_to_batch(self):
        """Test sending batch emails to a batch."""
        batch_id = 2023
        
        # Create test student in batch
        student_data = {
            'username': 'batch_student',
            'first_name': 'Batch',
            'last_name': 'Student',
            'sex': 'M',
            'category': 'GEN',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'batch': batch_id,
            'programme': 'B.Tech'
        }
        
        with patch('api.services.create_password'), \
             patch('api.services.configure_password_mail') as mock_configure, \
             patch('api.services.mail_to_user') as mock_mail:
            
            services.UserService.create_student(student_data)
            mock_configure.return_value = ('subject', 'message')
            mock_mail.return_value = True
            
            result = services.EmailService.send_batch_emails_to_batch(batch_id)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['sent'], 1)


class DatabaseServiceTest(BaseServiceTestCase):
    """Test cases for DatabaseService."""
    
    @patch('django.db.connection.cursor')
    def test_update_globals_database_success(self, mock_cursor):
        """Test successful database update."""
        mock_cursor.return_value.__enter__.return_value.execute.return_value = None
        
        result = services.DatabaseService.update_globals_database()
        
        self.assertTrue(result['success'])
        self.assertIn('completed successfully', result['message'])
    
    @patch('django.db.connection.cursor')
    def test_update_globals_database_failure(self, mock_cursor):
        """Test database update failure."""
        mock_cursor.return_value.__enter__.return_value.execute.side_effect = Exception('DB Error')
        
        with self.assertRaises(services.DatabaseServiceException):
            services.DatabaseService.update_globals_database()