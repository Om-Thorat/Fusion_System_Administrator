"""
Unit tests for the selectors layer.
Tests all selector functions with real database queries.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
import uuid

from .base import BaseSelectorTestCase, TestDataFactory
from .. import selectors
from ..models import (
    GlobalsDepartmentinfo, Programme, Batch, Discipline,
    AuthUser, Student, Staff, GlobalsFaculty, GlobalsDesignation,
    GlobalsHoldsdesignation, BackupRecord, BackupSchedule,
    HealthCheck, RestoreRecord
)


class AcademicDataSelectorsTest(BaseSelectorTestCase):
    """Test cases for academic data selectors."""
    
    def create_test_data(self):
        """Create test data for academic selectors."""
        self.department1 = TestDataFactory.create_test_department('Computer Science', 'CSE')
        self.department2 = TestDataFactory.create_test_department('Electronics', 'ECE')
        
        self.programme1 = TestDataFactory.create_test_programme('B.Tech', 'UG')
        self.programme2 = TestDataFactory.create_test_programme('M.Tech', 'PG')
        
        self.discipline1 = TestDataFactory.create_test_discipline('Computer Science', 'CSE')
        self.discipline2 = TestDataFactory.create_test_discipline('Electronics', 'ECE')
        
        self.batch1 = TestDataFactory.create_test_batch(2023, self.discipline1)
        self.batch2 = TestDataFactory.create_test_batch(2022, self.discipline2)
    
    def test_get_all_departments(self):
        """Test getting all departments."""
        departments = selectors.get_all_departments()
        
        self.assertEqual(departments.count(), 2)
        dept_names = [dept.name for dept in departments]
        self.assertIn('Computer Science', dept_names)
        self.assertIn('Electronics', dept_names)
    
    def test_get_department_by_name(self):
        """Test getting department by name."""
        department = selectors.get_department_by_name('Computer Science')
        
        self.assertEqual(department.name, 'Computer Science')
        self.assertEqual(department.acronym, 'CSE')
    
    def test_get_department_by_name_not_found(self):
        """Test getting non-existent department."""
        with self.assertRaises(GlobalsDepartmentinfo.DoesNotExist):
            selectors.get_department_by_name('Non-existent')
    
    def test_get_all_programmes(self):
        """Test getting all programmes."""
        programmes = selectors.get_all_programmes()
        
        self.assertEqual(programmes.count(), 2)
        prog_names = [prog.name for prog in programmes]
        self.assertIn('B.Tech', prog_names)
        self.assertIn('M.Tech', prog_names)
    
    def test_get_programme_by_name(self):
        """Test getting programme by name."""
        programme = selectors.get_programme_by_name('B.Tech')
        
        self.assertEqual(programme.name, 'B.Tech')
        self.assertEqual(programme.category, 'UG')
    
    def test_get_all_batches(self):
        """Test getting all batches."""
        batches = selectors.get_all_batches()
        
        self.assertEqual(batches.count(), 2)
        batch_years = [batch.year for batch in batches]
        self.assertIn(2023, batch_years)
        self.assertIn(2022, batch_years)
    
    def test_get_batch_by_year(self):
        """Test getting batch by year."""
        batches = selectors.get_batch_by_year(2023)
        
        self.assertEqual(batches.count(), 1)
        self.assertEqual(batches.first().year, 2023)
    
    def test_get_batch_by_criteria(self):
        """Test getting batch by multiple criteria."""
        batches = selectors.get_batch_by_criteria(
            year=2023,
            discipline_acronym='CSE'
        )
        
        self.assertEqual(batches.count(), 1)
        batch = batches.first()
        self.assertEqual(batch.year, 2023)
        self.assertEqual(batch.discipline.acronym, 'CSE')


class UserAndRoleSelectorsTest(BaseSelectorTestCase):
    """Test cases for user and role selectors."""
    
    def create_test_data(self):
        """Create test data for user and role selectors."""
        # Create test users
        self.auth_user1 = AuthUser.objects.create(
            user=self.test_user,
            sex='M'
        )
        
        self.test_user2 = self.create_test_user('testuser2')
        self.auth_user2 = AuthUser.objects.create(
            user=self.test_user2,
            sex='F'
        )
        
        # Create designations
        self.student_designation = TestDataFactory.create_test_designation(
            'student', 'student', True
        )
        self.faculty_designation = TestDataFactory.create_test_designation(
            'Professor', 'faculty', True
        )
        
        # Create role assignments
        GlobalsHoldsdesignation.objects.create(
            user=self.test_user,
            designation=self.student_designation
        )
        GlobalsHoldsdesignation.objects.create(
            user=self.test_user2,
            designation=self.faculty_designation
        )
    
    def test_get_user_by_username(self):
        """Test getting user by username."""
        user = selectors.get_user_by_username('testuser')
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
    
    def test_get_user_by_username_not_found(self):
        """Test getting non-existent user."""
        with self.assertRaises(AuthUser.DoesNotExist):
            selectors.get_user_by_username('nonexistent')
    
    def test_get_user_by_username_upper(self):
        """Test getting user with uppercase annotation."""
        user = selectors.get_user_by_username_upper('testuser')
        
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(hasattr(user, 'username_upper'))
    
    def test_get_users_by_role(self):
        """Test getting users by role."""
        users = selectors.get_users_by_role('student')
        
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().user.username, 'testuser')
    
    def test_get_user_roles(self):
        """Test getting user roles."""
        roles = selectors.get_user_roles(self.test_user)
        
        self.assertEqual(roles.count(), 1)
        self.assertEqual(roles.first().designation.name, 'student')
    
    def test_get_designations_by_category(self):
        """Test getting designations by category."""
        designations = selectors.get_designations_by_category('student', True)
        
        self.assertEqual(designations.count(), 1)
        self.assertEqual(designations.first().name, 'student')
    
    def test_get_designations_by_ids(self):
        """Test getting designations by IDs."""
        designation_ids = [self.student_designation.id, self.faculty_designation.id]
        designations = selectors.get_designations_by_ids(designation_ids)
        
        self.assertEqual(designations.count(), 2)
        names = [d.name for d in designations]
        self.assertIn('student', names)
        self.assertIn('Professor', names)


class UserFilterSelectorsTest(BaseSelectorTestCase):
    """Test cases for user filtering selectors."""
    
    def create_test_data(self):
        """Create test data for user filtering."""
        # Create departments and programmes
        self.department = TestDataFactory.create_test_department()
        self.programme = TestDataFactory.create_test_programme()
        self.batch = TestDataFactory.create_test_batch()
        
        # Create auth users
        self.auth_user1 = AuthUser.objects.create(
            user=self.test_user,
            sex='M',
            department=self.department
        )
        
        self.test_user2 = self.create_test_user('testuser2')
        self.auth_user2 = AuthUser.objects.create(
            user=self.test_user2,
            sex='F',
            department=self.department
        )
        
        # Create student
        self.student = Student.objects.create(
            id=self.auth_user1,
            programme='B.Tech',
            batch=2023,
            category='GEN',
            batch_id=self.batch
        )
        
        # Create staff
        self.staff = Staff.objects.create(
            id=self.auth_user2
        )
        
        # Create faculty
        self.faculty = GlobalsFaculty.objects.create(
            id=self.auth_user2
        )
    
    def test_get_students_with_filters_no_filters(self):
        """Test getting students without filters."""
        students = selectors.get_students_with_filters()
        
        self.assertEqual(students.count(), 1)
        self.assertEqual(students.first().id.user.username, 'testuser')
    
    def test_get_students_with_filters_programme(self):
        """Test getting students filtered by programme."""
        students = selectors.get_students_with_filters(programme='B.Tech')
        
        self.assertEqual(students.count(), 1)
        self.assertEqual(students.first().programme, 'B.Tech')
    
    def test_get_students_with_filters_batch(self):
        """Test getting students filtered by batch."""
        students = selectors.get_students_with_filters(batch='2023')
        
        self.assertEqual(students.count(), 1)
        self.assertEqual(students.first().batch, 2023)
    
    def test_get_students_with_filters_gender(self):
        """Test getting students filtered by gender."""
        students = selectors.get_students_with_filters(gender='M')
        
        self.assertEqual(students.count(), 1)
        self.assertEqual(students.first().id.sex, 'M')
    
    def test_get_faculty_with_filters(self):
        """Test getting faculty with filters."""
        faculty = selectors.get_faculty_with_filters()
        
        self.assertEqual(faculty.count(), 1)
        self.assertEqual(faculty.first().id.user.username, 'testuser2')
    
    def test_get_staff_with_filters(self):
        """Test getting staff with filters."""
        staff = selectors.get_staff_with_filters()
        
        self.assertEqual(staff.count(), 1)
        self.assertEqual(staff.first().id.user.username, 'testuser2')


class BackupSelectorsTest(BaseSelectorTestCase):
    """Test cases for backup-related selectors."""
    
    def create_test_data(self):
        """Create test data for backup selectors."""
        self.backup1 = TestDataFactory.create_test_backup_record('db1', 'success')
        self.backup2 = TestDataFactory.create_test_backup_record('db2', 'failed')
        self.backup3 = TestDataFactory.create_test_backup_record('db1', 'in_progress')
        
        self.schedule1 = TestDataFactory.create_test_backup_schedule('db1', True)
        self.schedule2 = TestDataFactory.create_test_backup_schedule('db2', False)
        
        # Create health check
        self.health_check = HealthCheck.objects.create(
            id=uuid.uuid4(),
            db_name='db1',
            status='healthy',
            response_time_ms=100
        )
        
        # Create restore record
        self.restore_record = RestoreRecord.objects.create(
            id=uuid.uuid4(),
            db_name='db1',
            source_backup=self.backup1,
            status='success'
        )
    
    def test_get_all_backups(self):
        """Test getting all backups."""
        backups = selectors.get_all_backups()
        
        self.assertEqual(backups.count(), 3)
    
    def test_get_backups_by_db_name(self):
        """Test getting backups by database name."""
        backups = selectors.get_backups_by_db_name('db1')
        
        self.assertEqual(backups.count(), 2)
        for backup in backups:
            self.assertEqual(backup.db_name, 'db1')
    
    def test_get_backup_by_id(self):
        """Test getting backup by ID."""
        backup = selectors.get_backup_by_id(self.backup1.id)
        
        self.assertEqual(backup.id, self.backup1.id)
        self.assertEqual(backup.db_name, 'db1')
    
    def test_get_backup_by_id_not_found(self):
        """Test getting non-existent backup."""
        fake_id = uuid.uuid4()
        
        with self.assertRaises(BackupRecord.DoesNotExist):
            selectors.get_backup_by_id(fake_id)
    
    def test_get_all_backup_schedules(self):
        """Test getting all backup schedules."""
        schedules = selectors.get_all_backup_schedules()
        
        self.assertEqual(schedules.count(), 2)
    
    def test_get_enabled_backup_schedules(self):
        """Test getting enabled backup schedules."""
        schedules = selectors.get_enabled_backup_schedules()
        
        self.assertEqual(schedules.count(), 1)
        self.assertTrue(schedules.first().enabled)
    
    def test_get_backup_schedule_by_id(self):
        """Test getting backup schedule by ID."""
        schedule = selectors.get_backup_schedule_by_id(self.schedule1.id)
        
        self.assertEqual(schedule.id, self.schedule1.id)
        self.assertEqual(schedule.db_name, 'db1')
    
    def test_get_recent_health_checks(self):
        """Test getting recent health checks."""
        health_checks = selectors.get_recent_health_checks('db1', days=30)
        
        self.assertEqual(health_checks.count(), 1)
        self.assertEqual(health_checks.first().db_name, 'db1')
    
    def test_get_all_restore_records(self):
        """Test getting all restore records."""
        restores = selectors.get_all_restore_records()
        
        self.assertEqual(restores.count(), 1)
    
    def test_get_restore_records_by_db_name(self):
        """Test getting restore records by database name."""
        restores = selectors.get_restore_records_by_db_name('db1')
        
        self.assertEqual(restores.count(), 1)
        self.assertEqual(restores.first().db_name, 'db1')
    
    def test_get_restore_record_by_id(self):
        """Test getting restore record by ID."""
        restore = selectors.get_restore_record_by_id(self.restore_record.id)
        
        self.assertEqual(restore.id, self.restore_record.id)
        self.assertEqual(restore.db_name, 'db1')