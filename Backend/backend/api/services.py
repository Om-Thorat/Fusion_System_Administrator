"""
Services module for business logic and write operations.

This module contains all business logic, write operations, and side effects.
Services encapsulate complex operations and maintain transactional integrity.

Design Principles:
- Encapsulate business rules and validation
- Handle all write operations and side effects
- Raise domain-specific exceptions
- Maintain transactional integrity
- No direct HTTP concerns
"""

import csv
import datetime
import random
import string
import os
import concurrent.futures
from io import StringIO
from typing import Dict, List, Optional, Tuple, Any

from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status

from .models import (
    AuthUser, GlobalsDepartmentinfo, GlobalsDesignation, GlobalsHoldsdesignation,
    GlobalsModuleaccess, Batch, Student, GlobalsFaculty, Staff, Programme
)
from .serializers import (
    AuthUserSerializer, GlobalExtraInfoSerializer, GlobalsHoldsDesignationSerializer,
    StudentSerializer, GlobalsFacultySerializer, StaffSerializer
)
from . import selectors


# Custom Exceptions
class DomainException(Exception):
    """Base exception for domain-specific errors"""
    pass


class UserServiceException(DomainException):
    """User-related business logic errors"""
    pass


class ValidationException(UserServiceException):
    """Validation errors in user operations"""
    pass


class EmailServiceException(DomainException):
    """Email-related errors"""
    pass


# UserService Class
class UserService:
    """Service class for user management operations"""
    
    @staticmethod
    def create_password(data: Dict[str, Any]) -> str:
        """
        Create a password based on username and random special characters.
        
        Args:
            data: Dictionary containing username
            
        Returns:
            Generated password string
        """
        user_name = data.get('username', '').lower().capitalize()
        special_characters = string.punctuation
        random_specials = ''.join(random.choice(special_characters) for _ in range(3))
        return f"{user_name}{random_specials}"
    
    @staticmethod
    def create_password_from_authuser(student: AuthUser) -> Tuple[str, str]:
        """
        Create password from existing AuthUser for email purposes.
        
        Args:
            student: AuthUser instance
            
        Returns:
            Tuple of (plain_password, hashed_password)
        """
        special_characters = string.punctuation
        random_specials = "".join(random.choice(special_characters) for _ in range(2))
        roll_no = student.email[5:-14].upper()
        password = f"{student.first_name.lower().capitalize().split(' ')[0]}{roll_no}{random_specials}"
        hashed_password = make_password(password)
        return password, hashed_password
    
    @staticmethod
    def convert_to_iso(date_str: str) -> str:
        """
        Convert date string to ISO format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            ISO formatted date string
        """
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%y"):
            try:
                date = datetime.datetime.strptime(date_str, fmt)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # Default fallback date
        dummy_date = datetime.datetime.strptime("01-01-2004", "%d-%m-%Y")
        return dummy_date.strftime("%Y-%m-%d")
    
    @staticmethod
    @transaction.atomic
    def create_student(data: Dict[str, Any]) -> Student:
        """
        Create a new student with all required records.
        
        Args:
            data: Dictionary containing student data
            
        Returns:
            Created Student instance
            
        Raises:
            ValidationException: If required fields are missing or invalid
            UserServiceException: If creation fails
        """
        required_fields = [
            "username", "first_name", "last_name", "sex", "category", 
            "father_name", "mother_name", "batch", "programme"
        ]
        
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            raise ValidationException(f"Missing required fields: {missing_fields}")
        
        try:
            # Generate password
            user_password = UserService.create_password(data)
            
            # Create AuthUser
            auth_user_data = {
                "password": make_password(user_password),
                "username": data['username'].upper(),
                "first_name": data['first_name'],
                "last_name": data.get('last_name', ""),
                "email": f"{data['username'].lower()}@iiitdmj.ac.in",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
            }
            
            auth_serializer = AuthUserSerializer(data=auth_user_data)
            if not auth_serializer.is_valid():
                raise ValidationException(f"Auth user validation failed: {auth_serializer.errors}")
            
            user = auth_serializer.save()
            
            # Get default department
            default_department = selectors.get_department_by_name('CSE')
            
            # Create ExtraInfo
            extra_info_data = {
                'id': data['username'].upper(),
                'title': data.get('title') if data.get('title') else 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.',
                'sex': data['sex'][0].upper(),
                'date_of_birth': data.get("dob") if data.get("dob") else "2025-01-01",
                'user_status': "PRESENT",
                'address': data.get("address") if data.get("address") else "NA",
                'phone_no': data.get("phone") if data.get("phone") else 9999999999,
                'about_me': "NA",
                'user_type': 'student',
                'profile_picture': None,
                'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
                'department': data.get("department") if data.get("department") else default_department.id,
                'user': user.id,
            }
            
            extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
            if not extra_info_serializer.is_valid():
                raise ValidationException(f"Extra info validation failed: {extra_info_serializer.errors}")
            
            extra_info = extra_info_serializer.save()
            
            # Create role assignment
            student_designation = selectors.get_designation_by_name('student')
            holds_designation_data = {
                'designation': student_designation.id,
                'user': user.id,
                'working': user.id,
            }
            
            holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
            if not holds_designation_serializer.is_valid():
                raise ValidationException(f"Role assignment validation failed: {holds_designation_serializer.errors}")
            
            holds_designation_serializer.save()
            
            # Create Student record
            batch = selectors.get_batch_by_filters(
                name=data.get('programme'),
                discipline_acronym=extra_info.department.name,
                year=data.get('batch')
            )
            
            student_data = {
                'id': extra_info.id,
                'programme': data.get('programme') if data.get('programme') else 'B.Tech',
                'batch': data.get('batch') if data.get('batch') else datetime.datetime.now().year,
                'batch_id': batch.id if batch else None,
                'cpi': 0.0,
                'category': data['category'].upper() if data['category'].upper() else 'GEN',
                'father_name': data.get('father_name') if data.get('father_name') else None,
                'mother_name': data.get('mother_name') if data.get('mother_name') else None,
                'hall_no': data.get('hall_no') if data.get('hall_no') else 3,
                'room_no': None,
                'specialization': None,
                'curr_semester_no': 2*(datetime.datetime.now().year - data.get('batch')) + datetime.datetime.now().month // 7,
            }
            
            student_serializer = StudentSerializer(data=student_data)
            if not student_serializer.is_valid():
                raise ValidationException(f"Student data validation failed: {student_serializer.errors}")
            
            student = student_serializer.save()
            return student
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to create student: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def create_staff(data: Dict[str, Any]) -> Staff:
        """
        Create a new staff member with all required records.
        
        Args:
            data: Dictionary containing staff data
            
        Returns:
            Created Staff instance
            
        Raises:
            ValidationException: If required fields are missing or invalid
            UserServiceException: If creation fails
        """
        required_fields = ["username", "first_name", "last_name", "sex", "designation"]
        
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            raise ValidationException(f"Missing required fields: {missing_fields}")
        
        try:
            # Generate password
            user_password = UserService.create_password(data)
            
            # Create AuthUser
            auth_user_data = {
                "password": make_password(user_password),
                "username": data['username'].lower(),
                "first_name": data['first_name'],
                "last_name": data.get('last_name', ""),
                "email": f"{data['username'].lower()}@iiitdmj.ac.in",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
            }
            
            auth_serializer = AuthUserSerializer(data=auth_user_data)
            if not auth_serializer.is_valid():
                raise ValidationException(f"Auth user validation failed: {auth_serializer.errors}")
            
            user = auth_serializer.save()
            
            # Get default department
            default_department = selectors.get_department_by_name('CSE')
            
            # Create ExtraInfo
            extra_info_data = {
                'id': data['username'].lower(),
                'title': data.get('title') if data.get('title') else 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.',
                'sex': data['sex'][0].upper(),
                'date_of_birth': data.get("dob") if data.get("dob") else "2025-01-01",
                'user_status': "PRESENT",
                'address': data.get("address") if data.get("address") else "NA",
                'phone_no': data.get("phone") if data.get("phone") else 9999999999,
                'about_me': "NA",
                'user_type': 'staff',
                'profile_picture': None,
                'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
                'department': data.get("department") if data.get("department") else default_department.id,
                'user': user.id,
            }
            
            extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
            if not extra_info_serializer.is_valid():
                raise ValidationException(f"Extra info validation failed: {extra_info_serializer.errors}")
            
            extra_info = extra_info_serializer.save()
            
            # Create role assignment
            designation = selectors.get_designation_by_name(data['designation'])
            holds_designation_data = {
                'designation': designation.id,
                'user': user.id,
                'working': user.id,
            }
            
            holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
            if not holds_designation_serializer.is_valid():
                raise ValidationException(f"Role assignment validation failed: {holds_designation_serializer.errors}")
            
            holds_designation_serializer.save()
            
            # Create Staff record
            staff_data = {
                'id': extra_info.id,
                'emp_id': data.get('emp_id') if data.get('emp_id') else None,
            }
            
            staff_serializer = StaffSerializer(data=staff_data)
            if not staff_serializer.is_valid():
                raise ValidationException(f"Staff data validation failed: {staff_serializer.errors}")
            
            staff = staff_serializer.save()
            return staff
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to create staff: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def create_faculty(data: Dict[str, Any]) -> GlobalsFaculty:
        """
        Create a new faculty member with all required records.
        
        Args:
            data: Dictionary containing faculty data
            
        Returns:
            Created GlobalsFaculty instance
            
        Raises:
            ValidationException: If required fields are missing or invalid
            UserServiceException: If creation fails
        """
        required_fields = ["username", "first_name", "last_name", "sex", "designation"]
        
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            raise ValidationException(f"Missing required fields: {missing_fields}")
        
        try:
            # Generate password
            user_password = UserService.create_password(data)
            
            # Create AuthUser
            auth_user_data = {
                "password": make_password(user_password),
                "username": data['username'].lower(),
                "first_name": data['first_name'],
                "last_name": data.get('last_name', ""),
                "email": f"{data['username'].lower()}@iiitdmj.ac.in",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
            }
            
            auth_serializer = AuthUserSerializer(data=auth_user_data)
            if not auth_serializer.is_valid():
                raise ValidationException(f"Auth user validation failed: {auth_serializer.errors}")
            
            user = auth_serializer.save()
            
            # Get default department
            default_department = selectors.get_department_by_name('CSE')
            
            # Create ExtraInfo
            extra_info_data = {
                'id': data['username'].lower(),
                'title': data.get('title') if data.get('title') else 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.',
                'sex': data['sex'][0].upper(),
                'date_of_birth': data.get("dob") if data.get("dob") else "2025-01-01",
                'user_status': "PRESENT",
                'address': data.get("address") if data.get("address") else "NA",
                'phone_no': data.get("phone") if data.get("phone") else 9999999999,
                'about_me': "NA",
                'user_type': 'faculty',
                'profile_picture': None,
                'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
                'department': data.get("department") if data.get("department") else default_department.id,
                'user': user.id,
            }
            
            extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
            if not extra_info_serializer.is_valid():
                raise ValidationException(f"Extra info validation failed: {extra_info_serializer.errors}")
            
            extra_info = extra_info_serializer.save()
            
            # Create role assignment
            designation = selectors.get_designation_by_name(data['designation'])
            holds_designation_data = {
                'designation': designation.id,
                'user': user.id,
                'working': user.id,
            }
            
            holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
            if not holds_designation_serializer.is_valid():
                raise ValidationException(f"Role assignment validation failed: {holds_designation_serializer.errors}")
            
            holds_designation_serializer.save()
            
            # Create Faculty record
            faculty_data = {
                'id': extra_info.id,
                'emp_id': data.get('emp_id') if data.get('emp_id') else None,
            }
            
            faculty_serializer = GlobalsFacultySerializer(data=faculty_data)
            if not faculty_serializer.is_valid():
                raise ValidationException(f"Faculty data validation failed: {faculty_serializer.errors}")
            
            faculty = faculty_serializer.save()
            return faculty
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to create faculty: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def reset_user_password(username: str) -> str:
        """
        Reset user password and return the new password.
        
        Args:
            username: Username of the user to reset password for
            
        Returns:
            New password string
            
        Raises:
            UserServiceException: If user not found or reset fails
        """
        try:
            user = selectors.get_user_by_username_upper(username)
            
            # Generate new password
            new_password = UserService.create_password({'username': username})
            
            # Ensure new password is different from current
            while new_password == user.password:
                new_password = UserService.create_password({'username': username})
            
            # Update password
            user.password = make_password(new_password)
            user.save()
            
            return new_password
            
        except AuthUser.DoesNotExist:
            raise UserServiceException("User not found")
        except Exception as e:
            raise UserServiceException(f"Failed to reset password: {str(e)}")
    
    @staticmethod
    def bulk_export_users() -> str:
        """
        Export all users to CSV format.
        
        Returns:
            CSV string containing all user data
        """
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser'])
        
        users = selectors.get_all_users()
        
        for user in users:
            writer.writerow([
                user.username,
                user.first_name,
                user.last_name,
                user.email,
                user.is_staff,
                user.is_superuser
            ])
        
        return output.getvalue()  
  
    @staticmethod
    @transaction.atomic
    def bulk_import_users(csv_content: str, user_type: str = 'student') -> Dict[str, Any]:
        """
        Import users from CSV content.
        
        Args:
            csv_content: CSV file content as string
            user_type: Type of users to import ('student', 'staff', 'faculty')
            
        Returns:
            Dictionary with import results
            
        Raises:
            ValidationException: If CSV format is invalid
            UserServiceException: If import fails
        """
        if not csv_content:
            raise ValidationException("No CSV content provided")
        
        try:
            csv_reader = csv.reader(StringIO(csv_content))
            rows = list(csv_reader)
            
            if not rows:
                raise ValidationException("CSV file is empty")
            
            created_users = []
            skipped_users = []
            
            for row_num, row in enumerate(rows, 1):
                if len(row) < 14:  # Minimum required columns
                    skipped_users.append(f"Row {row_num}: Insufficient columns")
                    continue
                
                try:
                    # Extract user data from CSV row
                    user_data = UserService._extract_user_data_from_csv_row(row, user_type)
                    
                    # Check if user already exists
                    if selectors.check_user_exists_by_username(user_data['username']):
                        skipped_users.append(f"Row {row_num}: User {user_data['username']} already exists")
                        continue
                    
                    # Create user based on type
                    if user_type == 'student':
                        created_user = UserService.create_student(user_data)
                    elif user_type == 'staff':
                        created_user = UserService.create_staff(user_data)
                    elif user_type == 'faculty':
                        created_user = UserService.create_faculty(user_data)
                    else:
                        raise ValidationException(f"Invalid user type: {user_type}")
                    
                    created_users.append(created_user)
                    
                except Exception as e:
                    skipped_users.append(f"Row {row_num}: {str(e)}")
                    continue
            
            return {
                "message": f"{len(created_users)} users created successfully.",
                "created_users_count": len(created_users),
                "skipped_users_count": len(skipped_users),
                "skipped_users": skipped_users
            }
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Bulk import failed: {str(e)}")
    
    @staticmethod
    def _extract_user_data_from_csv_row(row: List[str], user_type: str) -> Dict[str, Any]:
        """
        Extract user data from CSV row based on expected format.
        
        Args:
            row: CSV row data
            user_type: Type of user being created
            
        Returns:
            Dictionary with extracted user data
        """
        # CSV format: username, first_name, last_name, email, sex, category, father_name, 
        # mother_name, batch, programme, dob, address, phone, department
        
        base_data = {
            'username': row[0].strip() if row[0] else '',
            'first_name': row[1].strip() if row[1] else '',
            'last_name': row[2].strip() if row[2] else '',
            'sex': row[4].strip() if row[4] else 'M',
        }
        
        if user_type == 'student':
            base_data.update({
                'category': row[5].strip() if row[5] else 'GEN',
                'father_name': row[6].strip() if row[6] else '',
                'mother_name': row[7].strip() if row[7] else '',
                'batch': int(row[8]) if row[8] and row[8].isdigit() else datetime.datetime.now().year,
                'programme': row[9].strip() if row[9] else 'B.Tech',
                'dob': UserService.convert_to_iso(row[10]) if row[10] else "2004-01-01",
                'address': row[11].strip() if row[11] else 'NA',
                'phone': row[12].strip() if row[12] else '9999999999',
                'department': row[13].strip() if row[13] else 'CSE',
            })
        else:
            # For staff and faculty
            base_data.update({
                'designation': row[5].strip() if row[5] else 'staff',
                'dob': UserService.convert_to_iso(row[10]) if row[10] else "1980-01-01",
                'address': row[11].strip() if row[11] else 'NA',
                'phone': row[12].strip() if row[12] else '9999999999',
                'department': row[13].strip() if row[13] else 'CSE',
                'emp_id': row[14].strip() if len(row) > 14 and row[14] else None,
            })
        
        return base_data
    
    @staticmethod
    def get_sample_csv_content() -> str:
        """
        Generate sample CSV content for user import.
        
        Returns:
            Sample CSV content as string
        """
        sample_data = [
            ['username', 'first_name', 'last_name', 'email', 'sex', 'category/designation', 
             'father_name', 'mother_name', 'batch', 'programme', 'dob', 'address', 'phone', 'department'],
            ['student1', 'John', 'Doe', 'student1@iiitdmj.ac.in', 'M', 'GEN', 
             'Father Name', 'Mother Name', '2024', 'B.Tech', '01-01-2004', 'Address', '9999999999', 'CSE'],
            ['staff1', 'Jane', 'Smith', 'staff1@iiitdmj.ac.in', 'F', 'Registrar', 
             '', '', '', '', '01-01-1980', 'Address', '9999999999', 'CSE'],
        ]
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(sample_data)
        return output.getvalue()


# EmailService Class
class EmailService:
    """Service class for email operations"""
    
    @staticmethod
    def send_email(subject: str, message: str, recipient_list: List[str], 
                   from_email: Optional[str] = None) -> None:
        """
        Send email to recipients.
        
        Args:
            subject: Email subject
            message: Email message body
            recipient_list: List of recipient email addresses
            from_email: Sender email (optional, uses default from settings)
            
        Raises:
            EmailServiceException: If email sending fails
        """
        if not from_email:
            from_email = settings.EMAIL_HOST_USER
        
        if not from_email:
            raise EmailServiceException("No sender email provided")
        
        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            raise EmailServiceException(f"Failed to send email: {str(e)}")
    
    @staticmethod
    def send_password_email(user: AuthUser, password: str) -> None:
        """
        Send password email to a single user.
        
        Args:
            user: AuthUser instance
            password: Plain text password to send
            
        Raises:
            EmailServiceException: If email sending fails
        """
        subject = "Fusion Portal Credentials"
        
        message = (
            f"Dear Student,\n\n"
            "We are excited to introduce Fusion, our new ERP software, being developed by our own students, "
            "which is now live for the Pre-Registration Process. "
            "This platform will streamline your academic journey and provide a seamless experience for course registrations "
            "and other academic-related activities.\n\n"
            "Please find your login credentials below:\n\n"
            "Portal Link: \n http://fusion.iiitdmj.ac.in:8000 \n http://fusion.iiitdmj.ac.in/ \n http://172.27.16.216:8000/  (On LAN Only) /\n"
            f"Username: {user.username.upper()}\n"
            f"Password: {password}\n\n"
            "Important Instructions:\n"
            "1. Initial Login: Use the credentials provided above to log in to the portal.\n"
            "2. Change Password: Upon first login, change your password with the following steps:\n"
            "   - Log Out\n"
            "   - Change Password\n"
            "   - Create a new password.\n\n"
            "Please choose a strong password and keep it confidential.\n\n"
            "Help & Support:\n"
            "If you encounter any issues, feel free to reach out to the support team at fusion@iiitdmj.ac.in, "
            "or fill out the Google form at: https://forms.gle/aHvzGoS9XAAoHyix6\n\n"
            "We look forward to your smooth experience with Fusion!\n\n"
            "Best regards,\n"
            "Fusion Development Team,\n"
            "PDPM IIITDM Jabalpur"
        )
        
        recipient_list = [user.email]
        if int(settings.EMAIL_TEST_MODE) == 1:
            recipient_list = [settings.EMAIL_TEST_USER]
        
        EmailService.send_email(subject, message, recipient_list)
    
    @staticmethod
    def send_batch_email(batch_id: int, subject: str, message: str, 
                        email_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send email to a batch of students.
        
        Args:
            batch_id: Batch ID to send emails to
            subject: Email subject
            message: Email message
            email_list: Optional list of specific emails to send to
            
        Returns:
            Dictionary with email sending results
            
        Raises:
            EmailServiceException: If batch email sending fails
        """
        try:
            # Get students for the batch
            students = selectors.get_students_by_batch_and_emails(batch_id, email_list)
            
            if not students.exists():
                raise EmailServiceException(f"No students found for batch {batch_id}")
            
            # Extract user data
            student_users = [student.id.user for student in students]
            
            # Configure and send emails
            return EmailService.configure_password_mail(student_users, subject, message)
            
        except Exception as e:
            if isinstance(e, EmailServiceException):
                raise
            raise EmailServiceException(f"Failed to send batch email: {str(e)}")
    
    @staticmethod
    def configure_password_mail(students: List[AuthUser], 
                               subject: Optional[str] = None, 
                               message: Optional[str] = None) -> Dict[str, Any]:
        """
        Configure and send password emails to multiple students.
        
        Args:
            students: List of AuthUser instances
            subject: Optional custom subject
            message: Optional custom message
            
        Returns:
            Dictionary with email results
            
        Raises:
            EmailServiceException: If email configuration fails
        """
        count = len(students)
        if int(settings.EMAIL_TEST_MODE) == 1:
            count = int(settings.EMAIL_TEST_COUNT)
        
        failed_emails = []
        successful_emails = 0
        
        try:
            for student in students[:count]:
                try:
                    # Generate new password
                    plain_password, hashed_password = UserService.create_password_from_authuser(student)
                    
                    # Save new password
                    student.password = hashed_password
                    student.save()
                    
                    # Send email
                    if subject and message:
                        EmailService.send_email(subject, message, [student.email])
                    else:
                        EmailService.send_password_email(student, plain_password)
                    
                    successful_emails += 1
                    
                except Exception as e:
                    EmailService.log_failed_email(student, plain_password, hashed_password, str(e))
                    failed_emails.append({
                        'email': student.email,
                        'username': student.username,
                        'error': str(e)
                    })
            
            return {
                "message": f"Email sent to {successful_emails} users successfully.",
                "successful_count": successful_emails,
                "failed_count": len(failed_emails),
                "failed_emails": failed_emails
            }
            
        except Exception as e:
            raise EmailServiceException(f"Failed to configure password emails: {str(e)}")
    
    @staticmethod
    def log_failed_email(student: AuthUser, plain_password: str, 
                        hashed_password: str, error: str) -> None:
        """
        Log failed email attempts to file.
        
        Args:
            student: AuthUser instance
            plain_password: Plain text password
            hashed_password: Hashed password
            error: Error message
        """
        log_dir = "failed_emails"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "failed_emails.txt")
        
        with open(log_file, "a") as f:
            f.write(f"Failed to send email to: {student.email}\n")
            f.write(f"Username: {student.username}\n")
            f.write(f"Plain Password: {plain_password}\n")
            f.write(f"Hashed Password: {hashed_password}\n")
            f.write(f"Error: {error}\n")
            f.write(f"Timestamp: {datetime.datetime.now()}\n")
            f.write("\n")


# RoleService Class
class RoleService:
    """Service class for role and permission management operations"""
    
    @staticmethod
    @transaction.atomic
    def update_user_roles(username: str, roles_to_add: List[Any]) -> Dict[str, Any]:
        """
        Update user roles by replacing existing roles with new ones.
        
        Args:
            username: Username of the user to update roles for
            roles_to_add: List of roles to assign (can be strings or dicts with 'name' key)
            
        Returns:
            Dictionary with update results
            
        Raises:
            ValidationException: If username or roles are missing
            UserServiceException: If user not found or update fails
        """
        if not username or not roles_to_add:
            raise ValidationException("Username and roles are required.")
        
        try:
            user = selectors.get_user_by_username(username)
            
            # Get existing roles
            existing_role_names = selectors.get_user_role_names(user)
            
            # Process roles to add (handle both string and dict formats)
            processed_roles_to_add = set()
            for role in roles_to_add:
                if isinstance(role, dict) and 'name' in role:
                    processed_roles_to_add.add(role['name'])
                elif isinstance(role, str):
                    processed_roles_to_add.add(role)
            
            # Determine roles to remove
            roles_to_remove = existing_role_names - processed_roles_to_add
            
            # Remove old roles
            if roles_to_remove:
                deleted_count = selectors.delete_user_roles_by_names(user, list(roles_to_remove))
            
            # Add new roles
            added_roles = []
            for role_name in processed_roles_to_add:
                if role_name not in existing_role_names:
                    designation = selectors.get_designation_by_name(role_name)
                    
                    # Create role assignment
                    GlobalsHoldsdesignation.objects.create(
                        held_at=timezone.now(),
                        designation=designation,
                        user=user,
                        working=user
                    )
                    added_roles.append(role_name)
            
            return {
                "message": "User roles updated successfully.",
                "user": user.username,
                "roles_added": added_roles,
                "roles_removed": list(roles_to_remove),
                "current_roles": list(processed_roles_to_add)
            }
            
        except AuthUser.DoesNotExist:
            raise UserServiceException("User not found")
        except GlobalsDesignation.DoesNotExist as e:
            raise ValidationException(f"Designation not found: {str(e)}")
        except Exception as e:
            raise UserServiceException(f"Failed to update user roles: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def create_designation(data: Dict[str, Any]) -> Tuple[GlobalsDesignation, GlobalsModuleaccess]:
        """
        Create a new designation with default module access.
        
        Args:
            data: Dictionary containing designation data
            
        Returns:
            Tuple of (created GlobalsDesignation, created GlobalsModuleaccess)
            
        Raises:
            ValidationException: If designation data is invalid
            UserServiceException: If creation fails
        """
        try:
            # Create designation
            designation_serializer = GlobalsDesignationSerializer(data=data)
            if not designation_serializer.is_valid():
                raise ValidationException(f"Designation validation failed: {designation_serializer.errors}")
            
            designation = designation_serializer.save()
            
            # Create default module access
            max_id = selectors.get_max_module_access_id()
            new_id = max_id + 1
            
            module_access_data = {
                'id': new_id,
                'designation': designation.name,
                'program_and_curriculum': False,
                'course_registration': False,
                'course_management': False,
                'other_academics': False,
                'spacs': False,
                'department': False,
                'examinations': False,
                'hr': False,
                'iwd': False,
                'complaint_management': False,
                'fts': False,
                'purchase_and_store': False,
                'rspc': False,
                'hostel_management': False,
                'mess_management': False,
                'gymkhana': False,
                'placement_cell': False,
                'visitor_hostel': False,
                'phc': False,
                'inventory_management': False,
            }
            
            module_serializer = GlobalsModuleaccessSerializer(data=module_access_data)
            if not module_serializer.is_valid():
                raise ValidationException(f"Module access validation failed: {module_serializer.errors}")
            
            module_access = module_serializer.save()
            
            return designation, module_access
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to create designation: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def update_designation(name: str, data: Dict[str, Any], partial: bool = False) -> GlobalsDesignation:
        """
        Update an existing designation.
        
        Args:
            name: Name of the designation to update
            data: Dictionary containing updated designation data
            partial: Whether to perform partial update
            
        Returns:
            Updated GlobalsDesignation instance
            
        Raises:
            ValidationException: If name is missing or data is invalid
            UserServiceException: If designation not found or update fails
        """
        if not name:
            raise ValidationException("No name provided.")
        
        try:
            designation = selectors.get_designation_by_name(name)
            
            serializer = GlobalsDesignationSerializer(designation, data=data, partial=partial)
            if not serializer.is_valid():
                raise ValidationException(f"Designation validation failed: {serializer.errors}")
            
            updated_designation = serializer.save()
            return updated_designation
            
        except GlobalsDesignation.DoesNotExist:
            raise UserServiceException(f"Designation with name '{name}' not found.")
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to update designation: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def modify_module_access(designation_name: str, access_data: Dict[str, Any]) -> GlobalsModuleaccess:
        """
        Modify module access permissions for a designation.
        
        Args:
            designation_name: Name of the designation to modify access for
            access_data: Dictionary containing module access permissions
            
        Returns:
            Updated GlobalsModuleaccess instance
            
        Raises:
            ValidationException: If designation name is missing or data is invalid
            UserServiceException: If designation not found or update fails
        """
        if not designation_name:
            raise ValidationException("No role provided.")
        
        try:
            module_access = selectors.get_module_access_by_designation(designation_name)
            
            serializer = GlobalsModuleaccessSerializer(module_access, data=access_data, partial=True)
            if not serializer.is_valid():
                raise ValidationException(f"Module access validation failed: {serializer.errors}")
            
            updated_access = serializer.save()
            return updated_access
            
        except GlobalsModuleaccess.DoesNotExist:
            raise UserServiceException(f"Designation with name '{designation_name}' not found.")
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to modify module access: {str(e)}")
    
    @staticmethod
    def get_user_roles_info(username: str) -> Dict[str, Any]:
        """
        Get comprehensive role information for a user.
        
        Args:
            username: Username to get role information for
            
        Returns:
            Dictionary containing user and role information
            
        Raises:
            UserServiceException: If user not found
        """
        try:
            user, roles = selectors.get_user_with_roles(username)
            
            if not roles.exists():
                raise UserServiceException("User has no designations.")
            
            roles_data = []
            for role in roles:
                roles_data.append({
                    'id': role.id,
                    'name': role.name,
                    'full_name': role.full_name,
                    'type': role.type,
                    'category': role.category,
                    'basic': role.basic
                })
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email
                },
                "roles": roles_data
            }
            
        except AuthUser.DoesNotExist:
            raise UserServiceException("User not found")
        except Exception as e:
            if isinstance(e, UserServiceException):
                raise
            raise UserServiceException(f"Failed to get user roles info: {str(e)}")
    
    @staticmethod
    def assign_role_to_user(username: str, role_name: str) -> GlobalsHoldsdesignation:
        """
        Assign a single role to a user.
        
        Args:
            username: Username to assign role to
            role_name: Name of the role to assign
            
        Returns:
            Created GlobalsHoldsdesignation instance
            
        Raises:
            ValidationException: If user already has the role
            UserServiceException: If user or role not found
        """
        try:
            user = selectors.get_user_by_username(username)
            designation = selectors.get_designation_by_name(role_name)
            
            # Check if user already has this role
            if selectors.user_has_role(user, role_name):
                raise ValidationException(f"User already has role '{role_name}'")
            
            # Create role assignment
            role_assignment = GlobalsHoldsdesignation.objects.create(
                held_at=timezone.now(),
                designation=designation,
                user=user,
                working=user
            )
            
            return role_assignment
            
        except AuthUser.DoesNotExist:
            raise UserServiceException("User not found")
        except GlobalsDesignation.DoesNotExist:
            raise UserServiceException(f"Role '{role_name}' not found")
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to assign role: {str(e)}")
    
    @staticmethod
    def remove_role_from_user(username: str, role_name: str) -> bool:
        """
        Remove a single role from a user.
        
        Args:
            username: Username to remove role from
            role_name: Name of the role to remove
            
        Returns:
            True if role was removed, False if user didn't have the role
            
        Raises:
            UserServiceException: If user not found
        """
        try:
            user = selectors.get_user_by_username(username)
            
            # Check if user has this role
            if not selectors.user_has_role(user, role_name):
                return False
            
            # Remove the role
            deleted_count = selectors.delete_user_roles_by_names(user, [role_name])
            return deleted_count > 0
            
        except AuthUser.DoesNotExist:
            raise UserServiceException("User not found")
        except Exception as e:
            if isinstance(e, UserServiceException):
                raise
            raise UserServiceException(f"Failed to remove role: {str(e)}")
    
    @staticmethod
    def get_users_with_role(role_name: str) -> List[Dict[str, Any]]:
        """
        Get all users who have a specific role.
        
        Args:
            role_name: Name of the role to search for
            
        Returns:
            List of user dictionaries with role information
            
        Raises:
            UserServiceException: If role not found
        """
        try:
            # Verify role exists
            selectors.get_designation_by_name(role_name)
            
            users = selectors.get_users_by_role(role_name)
            
            users_data = []
            for user in users:
                users_data.append({
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "is_active": user.is_active
                })
            
            return users_data
            
        except GlobalsDesignation.DoesNotExist:
            raise UserServiceException(f"Role '{role_name}' not found")
        except Exception as e:
            if isinstance(e, UserServiceException):
                raise
            raise UserServiceException(f"Failed to get users with role: {str(e)}")


class RoleServiceException(DomainException):
    """Role and permission related errors"""
    pass

#
 BackupService Class
class BackupService:
    """Service class for backup and restore operations"""
    
    @staticmethod
    def create_backup(db_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new backup record and start backup process in background thread.
        
        Args:
            db_name: Database name to backup (optional, uses default from config)
            
        Returns:
            Dictionary with backup record information
            
        Raises:
            UserServiceException: If backup creation fails
        """
        try:
            from .backup_views import _get_db_config, _run_backup
            import threading
            
            cfg = _get_db_config()
            if not db_name:
                db_name = cfg["name"]
            
            # Create backup record
            from .models import BackupRecord
            record = BackupRecord.objects.create(
                db_name=db_name,
                status="in_progress",
            )
            
            # Start backup in background thread
            thread = threading.Thread(target=_run_backup, args=(record.id,), daemon=True)
            thread.start()
            
            return {
                "id": str(record.id),
                "db_name": record.db_name,
                "created_at": record.created_at.isoformat(),
                "status": record.status,
                "size_bytes": record.size_bytes,
                "duration_ms": record.duration_ms,
            }
            
        except Exception as e:
            raise UserServiceException(f"Failed to create backup: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def delete_backup(backup_id) -> Dict[str, str]:
        """
        Delete a backup record and its associated file from disk.
        
        Args:
            backup_id: UUID of the backup to delete
            
        Returns:
            Dictionary with success message
            
        Raises:
            UserServiceException: If backup not found or deletion fails
            ValidationException: If backup is in progress
        """
        try:
            backup = selectors.get_backup_by_id(backup_id)
            
            if backup.status == "in_progress":
                raise ValidationException("Cannot delete an in-progress backup.")
            
            # Remove file from disk
            if backup.file_path and os.path.exists(backup.file_path):
                try:
                    os.remove(backup.file_path)
                except OSError:
                    pass  # File removal failure is not critical
            
            backup.delete()
            return {"message": "Backup deleted."}
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to delete backup: {str(e)}")
    
    @staticmethod
    def restore_backup(backup_id) -> Dict[str, Any]:
        """
        Start database restore from backup in background thread.
        
        Args:
            backup_id: UUID of the backup to restore from
            
        Returns:
            Dictionary with restore record information
            
        Raises:
            UserServiceException: If backup not found or restore fails
            ValidationException: If backup is not suitable for restore
        """
        try:
            from .backup_views import _run_restore
            from .models import RestoreRecord
            import threading
            
            backup = selectors.get_backup_by_id(backup_id)
            
            if backup.status != "success":
                raise ValidationException("Can only restore from a successful backup.")
            
            if not backup.file_path or not os.path.exists(backup.file_path):
                raise ValidationException("Backup file not found on disk.")
            
            # Create restore record
            restore_record = RestoreRecord.objects.create(
                db_name=backup.db_name,
                source_backup=backup,
                source_backup_created_at=backup.created_at,
                status="in_progress",
            )
            
            # Start restore in background thread
            thread = threading.Thread(
                target=_run_restore,
                args=(backup.file_path, restore_record.id),
                daemon=True,
            )
            thread.start()
            
            return {
                "id": str(restore_record.id),
                "db_name": restore_record.db_name,
                "status": restore_record.status,
                "source_backup_id": str(backup.id),
                "created_at": restore_record.created_at.isoformat(),
            }
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to restore backup: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def save_schedule(schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a backup schedule.
        
        Args:
            schedule_data: Dictionary containing schedule configuration
            
        Returns:
            Dictionary with schedule information
            
        Raises:
            ValidationException: If required fields are missing or invalid
            UserServiceException: If schedule save fails
        """
        try:
            from .models import BackupSchedule
            from . import scheduler as sched_module
            
            db_name = schedule_data.get("db_name")
            if not db_name:
                raise ValidationException("db_name is required.")
            
            frequency = schedule_data.get("frequency", "daily")
            enabled = schedule_data.get("enabled", True)
            hour = int(schedule_data.get("hour", 2))
            minute = int(schedule_data.get("minute", 0))
            day_of_week = schedule_data.get("day_of_week")
            day_of_month = schedule_data.get("day_of_month")
            cron_expression = schedule_data.get("cron_expression", "")
            retain_last_n = int(schedule_data.get("retain_last_n", 7))
            
            if day_of_week is not None:
                day_of_week = int(day_of_week)
            if day_of_month is not None:
                day_of_month = int(day_of_month)
            
            # Validate cron expression if custom
            if frequency == "custom" and cron_expression:
                parts = cron_expression.strip().split()
                if len(parts) != 5:
                    raise ValidationException(
                        "Custom cron expression must have exactly 5 fields: minute hour day month weekday."
                    )
            
            # Create or update schedule
            schedule, created = BackupSchedule.objects.update_or_create(
                db_name=db_name,
                defaults={
                    "frequency": frequency,
                    "enabled": enabled,
                    "hour": hour,
                    "minute": minute,
                    "day_of_week": day_of_week,
                    "day_of_month": day_of_month,
                    "cron_expression": cron_expression,
                    "retain_last_n": retain_last_n,
                }
            )
            
            # Update scheduler if enabled
            if enabled:
                sched_module.register_schedule(schedule)
            else:
                sched_module.unregister_schedule(schedule)
            
            return {
                "id": str(schedule.id),
                "db_name": schedule.db_name,
                "frequency": schedule.frequency,
                "enabled": schedule.enabled,
                "created": created,
                "message": "Schedule created successfully." if created else "Schedule updated successfully."
            }
            
        except Exception as e:
            if isinstance(e, (ValidationException, UserServiceException)):
                raise
            raise UserServiceException(f"Failed to save schedule: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def toggle_schedule(schedule_id, enabled: Optional[bool] = None) -> Dict[str, Any]:
        """
        Enable or disable a backup schedule.
        
        Args:
            schedule_id: UUID of the schedule to toggle
            enabled: Optional boolean to set enabled state (if None, toggles current state)
            
        Returns:
            Dictionary with updated schedule information
            
        Raises:
            UserServiceException: If schedule not found or toggle fails
        """
        try:
            from . import scheduler as sched_module
            
            schedule = selectors.get_backup_schedule_by_id(schedule_id)
            
            # Toggle or set enabled state
            if enabled is None:
                schedule.enabled = not schedule.enabled
            else:
                schedule.enabled = enabled
            
            schedule.save()
            
            # Update scheduler
            if schedule.enabled:
                sched_module.register_schedule(schedule)
            else:
                sched_module.unregister_schedule(schedule)
            
            return {
                "id": str(schedule.id),
                "db_name": schedule.db_name,
                "enabled": schedule.enabled,
                "message": f"Schedule {'enabled' if schedule.enabled else 'disabled'} successfully."
            }
            
        except Exception as e:
            if isinstance(e, UserServiceException):
                raise
            raise UserServiceException(f"Failed to toggle schedule: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def delete_schedule(schedule_id) -> Dict[str, str]:
        """
        Delete a backup schedule and remove from scheduler.
        
        Args:
            schedule_id: UUID of the schedule to delete
            
        Returns:
            Dictionary with success message
            
        Raises:
            UserServiceException: If schedule not found or deletion fails
        """
        try:
            from . import scheduler as sched_module
            
            schedule = selectors.get_backup_schedule_by_id(schedule_id)
            
            # Remove from scheduler
            sched_module.unregister_schedule(schedule)
            
            # Delete from database
            schedule.delete()
            
            return {"message": "Schedule deleted successfully."}
            
        except Exception as e:
            if isinstance(e, UserServiceException):
                raise
            raise UserServiceException(f"Failed to delete schedule: {str(e)}")
    
    @staticmethod
    def run_health_check(db_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a health check on the database and record the result.
        
        Args:
            db_name: Database name to check (optional, uses default from config)
            
        Returns:
            Dictionary with health check results
            
        Raises:
            UserServiceException: If health check fails
        """
        try:
            from .backup_views import _get_db_config
            from .models import HealthCheck
            from django.db import connection
            import time
            
            cfg = _get_db_config()
            if not db_name:
                db_name = cfg["name"]
            
            start = time.time()
            
            try:
                # Simple database ping
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                
                elapsed_ms = int((time.time() - start) * 1000)
                
                record = HealthCheck.objects.create(
                    db_name=db_name,
                    status="success",
                    response_time_ms=elapsed_ms,
                )
                
                return {
                    "id": str(record.id),
                    "db_name": record.db_name,
                    "status": record.status,
                    "response_time_ms": record.response_time_ms,
                    "checked_at": record.checked_at.isoformat(),
                }
                
            except Exception as e:
                elapsed_ms = int((time.time() - start) * 1000)
                record = HealthCheck.objects.create(
                    db_name=db_name,
                    status="failed",
                    response_time_ms=elapsed_ms,
                    error_message=str(e)[:500],
                )
                
                return {
                    "id": str(record.id),
                    "db_name": record.db_name,
                    "status": record.status,
                    "response_time_ms": record.response_time_ms,
                    "error_message": record.error_message,
                    "checked_at": record.checked_at.isoformat(),
                }
                
        except Exception as e:
            raise UserServiceException(f"Failed to run health check: {str(e)}")
    
    @staticmethod
    def get_database_info() -> List[Dict[str, Any]]:
        """
        Get database information including backup counts and last backup.
        
        Returns:
            List of database information dictionaries
            
        Raises:
            UserServiceException: If database info retrieval fails
        """
        try:
            from .backup_views import _get_db_config
            from django.db import connection
            
            cfg = _get_db_config()
            db_name = cfg["name"]
            
            # Get database size
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_database_size(current_database())")
                    size_bytes = cursor.fetchone()[0]
            except Exception:
                size_bytes = 0
            
            # Get backup statistics
            backup_count = selectors.get_backup_count_by_db(db_name)
            last_backup = selectors.get_last_successful_backup(db_name)
            
            db_info = {
                "id": 1,
                "name": db_name,
                "status": "online",
                "size_bytes": size_bytes,
                "backup_count": backup_count,
                "last_backup_at": last_backup.created_at.isoformat() if last_backup else None,
                "last_backup_id": str(last_backup.id) if last_backup else None,
            }
            
            return [db_info]
            
        except Exception as e:
            raise UserServiceException(f"Failed to get database info: {str(e)}")
    
    @staticmethod
    def cleanup_old_backups(db_name: str, retain_count: int = 7) -> Dict[str, Any]:
        """
        Clean up old backup records and files, keeping only the most recent ones.
        
        Args:
            db_name: Database name to clean up backups for
            retain_count: Number of recent backups to keep
            
        Returns:
            Dictionary with cleanup results
            
        Raises:
            UserServiceException: If cleanup fails
        """
        try:
            backups = selectors.get_all_backup_records(db_name).filter(
                status="success"
            ).order_by('-created_at')
            
            if backups.count() <= retain_count:
                return {
                    "message": "No cleanup needed.",
                    "deleted_count": 0,
                    "retained_count": backups.count()
                }
            
            # Get backups to delete (all except the most recent retain_count)
            backups_to_delete = backups[retain_count:]
            deleted_count = 0
            
            for backup in backups_to_delete:
                try:
                    # Remove file from disk
                    if backup.file_path and os.path.exists(backup.file_path):
                        os.remove(backup.file_path)
                    
                    # Delete record
                    backup.delete()
                    deleted_count += 1
                    
                except Exception as e:
                    # Log error but continue with other backups
                    print(f"Failed to delete backup {backup.id}: {str(e)}")
                    continue
            
            return {
                "message": f"Cleanup completed. Deleted {deleted_count} old backups.",
                "deleted_count": deleted_count,
                "retained_count": retain_count
            }
            
        except Exception as e:
            raise UserServiceException(f"Failed to cleanup old backups: {str(e)}")


class BackupServiceException(DomainException):
    """Backup operation errors"""
    pass

# Ema
ilService Class
class EmailService:
    """Service class for email operations"""
    
    @staticmethod
    def send_email(subject: str, message: str, recipient_list: List[str], 
                   from_email: Optional[str] = None) -> None:
        """
        Send email to recipients.
        
        Args:
            subject: Email subject
            message: Email message body
            recipient_list: List of recipient email addresses
            from_email: Sender email (uses default if not provided)
            
        Raises:
            EmailServiceException: If email sending fails
        """
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            if not from_email:
                from_email = settings.EMAIL_HOST_USER
            
            if not from_email:
                raise EmailServiceException("No sender email provided.")
            
            send_mail(subject, message, from_email, recipient_list)
            
        except Exception as e:
            raise EmailServiceException(f"Failed to send email: {str(e)}")
    
    @staticmethod
    def send_password_email_single(student_data: Dict[str, Any], password: str) -> None:
        """
        Send password email to a single student.
        
        Args:
            student_data: Dictionary containing student information (username, email)
            password: Plain text password to send
            
        Raises:
            EmailServiceException: If email sending fails
        """
        try:
            from django.conf import settings
            
            subject = "Fusion Portal Credentials"
            
            message = (
                f"Dear Student,\\n\\n"
                "We are excited to introduce Fusion, our new ERP software, being developed by our own students, "
                "which is now live for the Pre-Registration Process. "
                "This platform will streamline your academic journey and provide a seamless experience for course registrations "
                "and other academic-related activities.\\n\\n"
                "Please find your login credentials below:\\n\\n"
                "Portal Link: \\n http://fusion.iiitdmj.ac.in:8000 \\n http://fusion.iiitdmj.ac.in/ \\n http://172.27.16.216:8000/  (On LAN Only) /\\n"
                f"Username: {student_data['username'].upper()}\\n"
                f"Password: {password}\\n\\n"
                "Important Instructions:\\n"
                "1. Initial Login: Use the credentials provided above to log in to the portal.\\n"
                "2. Change Password: Upon first login, change your password with the following steps:\\n"
                "   - Log Out\\n"
                "   - Change Password\\n"
                "   - Create a new password.\\n\\n"
                "Please choose a strong password and keep it confidential.\\n\\n"
                "Help & Support:\\n"
                "If you encounter any issues, feel free to reach out to the support team at fusion@iiitdmj.ac.in, "
                "or fill out the Google form at: https://forms.gle/aHvzGoS9XAAoHyix6\\n\\n"
                "We look forward to your smooth experience with Fusion!\\n\\n"
                "Best regards,\\n"
                "Fusion Development Team,\\n"
                "PDPM IIITDM Jabalpur"
            )
            
            recipient_list = [student_data['email']]
            
            # Use test email if in test mode
            if int(settings.EMAIL_TEST_MODE) == 1:
                recipient_list = [settings.EMAIL_TEST_USER]
            
            EmailService.send_email(subject, message, recipient_list)
            
        except Exception as e:
            raise EmailServiceException(f"Failed to send password email: {str(e)}")
    
    @staticmethod
    def send_batch_password_emails(students: List[Any]) -> Dict[str, Any]:
        """
        Send password emails to multiple students with concurrent processing.
        
        Args:
            students: List of student objects
            
        Returns:
            Dictionary with success message and failure details
            
        Raises:
            EmailServiceException: If batch email operation fails
        """
        try:
            import concurrent.futures
            from django.conf import settings
            
            count = len(students)
            if int(settings.EMAIL_TEST_MODE) == 1:
                count = int(settings.EMAIL_TEST_COUNT)
            
            failed_emails = []
            successful_count = 0
            
            for student in students[:count]:
                try:
                    plain_password, hashed_password = EmailService._create_password_from_user(student)
                    EmailService._save_password(student, hashed_password)
                    
                    student_data = {
                        'username': student.username,
                        'email': student.email
                    }
                    
                    EmailService.send_password_email_single(student_data, plain_password)
                    successful_count += 1
                    
                except Exception as e:
                    failed_email_info = {
                        'student_email': student.email,
                        'student_username': student.username,
                        'error': str(e)
                    }
                    failed_emails.append(failed_email_info)
                    EmailService._log_failed_email(student, plain_password if 'plain_password' in locals() else 'N/A', 
                                                 hashed_password if 'hashed_password' in locals() else 'N/A', str(e))
            
            return {
                'message': f'Email process completed. {successful_count} successful, {len(failed_emails)} failed.',
                'successful_count': successful_count,
                'failed_count': len(failed_emails),
                'failed_emails': failed_emails
            }
            
        except Exception as e:
            raise EmailServiceException(f"Failed to send batch emails: {str(e)}")
    
    @staticmethod
    def send_concurrent_emails(created_users: List[Dict[str, Any]], password: str = "user@123") -> None:
        """
        Send emails to multiple users concurrently.
        
        Args:
            created_users: List of user dictionaries
            password: Default password to send
            
        Raises:
            EmailServiceException: If concurrent email sending fails
        """
        try:
            import concurrent.futures
            from django.contrib.auth.hashers import make_password
            
            max_threads = min(10, len(created_users))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                future_to_user = [
                    executor.submit(EmailService.send_password_email_single, user, password) 
                    for user in created_users
                ]
                
                for future, user in zip(future_to_user, created_users):
                    try:
                        future.result()
                    except Exception as e:
                        EmailService._log_failed_email(user, password, make_password(password), str(e))
            
        except Exception as e:
            raise EmailServiceException(f"Failed to send concurrent emails: {str(e)}")
    
    @staticmethod
    def _create_password_from_user(student: Any) -> Tuple[str, str]:
        """
        Create password for a student based on their information.
        
        Args:
            student: Student object with email and first_name
            
        Returns:
            Tuple of (plain_password, hashed_password)
        """
        try:
            import string
            import random
            from django.contrib.auth.hashers import make_password
            
            special_characters = string.punctuation
            random_specials = "".join(random.choice(special_characters) for _ in range(2))
            roll_no = student.email[5:-14].upper()
            password = f"{student.first_name.lower().capitalize().split(' ')[0]}{roll_no}{random_specials}"
            hashed_password = make_password(password)
            
            return password, hashed_password
            
        except Exception as e:
            raise EmailServiceException(f"Failed to create password: {str(e)}")
    
    @staticmethod
    def _save_password(student: Any, hashed_password: str) -> None:
        """
        Save hashed password to student object.
        
        Args:
            student: Student object to update
            hashed_password: Hashed password to save
        """
        try:
            student.password = hashed_password
            student.save()
        except Exception as e:
            raise EmailServiceException(f"Failed to save password: {str(e)}")
    
    @staticmethod
    def _log_failed_email(student: Any, plain_password: str, hashed_password: str, error: str) -> None:
        """
        Log failed email attempt to file.
        
        Args:
            student: Student object or dictionary
            plain_password: Plain text password
            hashed_password: Hashed password
            error: Error message
        """
        try:
            import os
            
            log_dir = "failed_emails"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "failed_emails.txt")
            
            # Handle both object and dictionary formats
            if hasattr(student, 'email'):
                email = student.email
                username = student.username
            else:
                email = student.get('email', 'N/A')
                username = student.get('username', 'N/A')
            
            with open(log_file, "a") as f:
                f.write(f"Failed to send email to: {email}\\n")
                f.write(f"Username: {username}\\n")
                f.write(f"Plain Password: {plain_password}\\n")
                f.write(f"Hashed Password: {hashed_password}\\n")
                f.write(f"Error: {error}\\n")
                f.write("\\n")
                
        except Exception as e:
            # Don't raise exception for logging failures
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log email failure: {str(e)}")
    
    @staticmethod
    def create_password_from_data(data: Dict[str, Any]) -> str:
        """
        Create password from user data.
        
        Args:
            data: Dictionary containing username
            
        Returns:
            Generated password string
        """
        try:
            import string
            import random
            
            user_name = data.get('username', '').lower().capitalize()
            special_characters = string.punctuation
            random_specials = ''.join(random.choice(special_characters) for _ in range(3))
            return f"{user_name}{random_specials}"
            
        except Exception as e:
            raise EmailServiceException(f"Failed to create password from data: {str(e)}")
    
    @staticmethod
    def get_email_configuration() -> Dict[str, Any]:
        """
        Get current email configuration settings.
        
        Returns:
            Dictionary with email configuration
        """
        try:
            from django.conf import settings
            
            return {
                'host_user': getattr(settings, 'EMAIL_HOST_USER', None),
                'test_mode': int(getattr(settings, 'EMAIL_TEST_MODE', 0)),
                'test_user': getattr(settings, 'EMAIL_TEST_USER', None),
                'test_count': int(getattr(settings, 'EMAIL_TEST_COUNT', 1))
            }
            
        except Exception as e:
            raise EmailServiceException(f"Failed to get email configuration: {str(e)}")


class EmailServiceException(DomainException):
    """Email operation related errors"""
    pass    @
staticmethod
    def bulk_import_students_from_csv(csv_file) -> Dict[str, Any]:
        """
        Import students from CSV file.
        
        Args:
            csv_file: Uploaded CSV file
            
        Returns:
            Dictionary with import results
            
        Raises:
            UserServiceException: If import fails
        """
        try:
            import csv
            from io import StringIO
            from .helpers import add_user_extra_info, add_user_designation_info, add_student_info, mail_to_user
            
            file_data = csv_file.read().decode('utf-8')
            csv_data = csv.reader(StringIO(file_data))
            
            headers = next(csv_data)
            created_users = []
            failed_users = []
            
            for row in csv_data:
                if len(row) < 9:
                    failed_users.append(row)
                    continue
                    
                try:
                    # Create user data from CSV row
                    user_data = {
                        'username': row[0],
                        'first_name': row[1] if len(row[1]) > 0 else 'NA',
                        'last_name': row[2] if len(row[2]) > 0 else 'NA',
                        'sex': row[3],
                        'category': row[4],
                        'father_name': row[5],
                        'mother_name': row[6],
                        'batch': int(row[7]) if row[7] else None,
                        'programme': row[8],
                        'title': row[9] if len(row) > 9 else None,
                        'dob': row[10] if len(row) > 10 else None,
                        'address': row[11] if len(row) > 11 else None,
                        'phone': row[12] if len(row) > 12 else None,
                        'department': row[13] if len(row) > 13 else None
                    }
                    
                    # Use existing create_student method
                    result = UserService.create_student(user_data)
                    created_users.append(result)
                    
                except Exception as e:
                    print(f"Error creating user from row: {e}")
                    failed_users.append(row)
            
            # Send emails to created users
            if len(created_users) > 0:
                try:
                    mail_to_user(created_users)
                except Exception as e:
                    print(f"Error sending emails: {e}")
            
            response_data = {
                "message": f"{len(created_users)} users created successfully.",
                "created_users": created_users,
                "skipped_users_count": len(failed_users),
            }
            
            # Add failed users CSV if any
            if failed_users:
                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(headers)
                
                for failed_user in failed_users:
                    writer.writerow(failed_user)
                
                output.seek(0)
                response_data["skipped_users_csv"] = output.getvalue()
            
            return response_data
            
        except Exception as e:
            raise UserServiceException(f"Failed to import users from CSV: {str(e)}")
    
    @staticmethod
    def bulk_export_users_to_csv():
        """
        Export all users to CSV format.
        
        Returns:
            HttpResponse with CSV data
            
        Raises:
            UserServiceException: If export fails
        """
        try:
            import csv
            from django.http import HttpResponse
            from django.contrib.auth.models import User as AuthUser
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser'])
            
            users = AuthUser.objects.all()
            
            for user in users:
                writer.writerow([
                    user.username, 
                    user.first_name, 
                    user.last_name, 
                    user.email, 
                    user.is_staff, 
                    user.is_superuser
                ])
            
            return response
            
        except Exception as e:
            raise UserServiceException(f"Failed to export users to CSV: {str(e)}")   
 @staticmethod
    def send_batch_emails_to_batch(batch_id: int) -> Dict[str, Any]:
        """
        Send emails to all students in a specific batch.
        
        Args:
            batch_id: Batch ID to send emails to
            
        Returns:
            Dictionary with email sending results
            
        Raises:
            EmailServiceException: If batch email sending fails
        """
        try:
            from django.conf import settings
            from .models import Student
            from .helpers import configure_password_mail
            
            # Get email configuration
            emails = getattr(settings, 'EMAIL_TEST_ARRAY', '')
            email_list = emails.split(',') if emails else []
            
            # Filter students based on email configuration
            if len(email_list) > 1:
                students = Student.objects.filter(
                    batch=batch_id, 
                    id__user__email__in=email_list
                )
            else:
                students = Student.objects.filter(batch=batch_id)
            
            # Extract user data
            students_data = [student.id.user for student in students]
            
            if not students_data:
                raise EmailServiceException("No students found for the specified batch")
            
            # Use existing configure_password_mail function
            configure_password_mail(students_data)
            
            return {
                'message': f'Emails sent to {len(students_data)} students in batch {batch_id}',
                'student_count': len(students_data)
            }
            
        except Exception as e:
            raise EmailServiceException(f"Failed to send batch emails: {str(e)}")    @
staticmethod
    def update_schedule_run_time(schedule_id: str) -> None:
        """
        Update the last_run_at and next_run_at times for a backup schedule.
        
        Args:
            schedule_id: UUID of the backup schedule
            
        Raises:
            BackupServiceException: If update fails
        """
        try:
            from .models import BackupSchedule
            from . import scheduler as sched_module
            
            sched = BackupSchedule.objects.get(id=schedule_id)
            sched.last_run_at = timezone.now()
            
            # compute next_run_at from APScheduler job
            scheduler = sched_module.get_scheduler()
            job_id = sched_module._job_id(sched.db_name)
            job = scheduler.get_job(job_id)
            if job and job.next_run_time:
                sched.next_run_at = job.next_run_time
                
            sched.save(update_fields=["last_run_at", "next_run_at"])
            
        except Exception as e:
            raise BackupServiceException(f"Failed to update schedule run time: {str(e)}")
    
    @staticmethod
    def enforce_retention_policy(db_name: str, schedule_id: str) -> None:
        """
        Enforce retention policy by deleting old backups beyond retain_last_n.
        
        Args:
            db_name: Database name
            schedule_id: UUID of the backup schedule
            
        Raises:
            BackupServiceException: If retention enforcement fails
        """
        import os
        
        try:
            from .models import BackupRecord, BackupSchedule
            
            sched = BackupSchedule.objects.get(id=schedule_id)
            n = sched.retain_last_n
            if n <= 0:
                return
                
            # get all successful backups ordered newest first
            successful = BackupRecord.objects.filter(
                db_name=db_name, status="success"
            ).order_by("-created_at")
            
            to_delete = successful[n:]
            for b in to_delete:
                if b.file_path and os.path.exists(b.file_path):
                    try:
                        os.remove(b.file_path)
                    except OSError:
                        pass
                b.delete()
                
        except Exception as e:
            raise BackupServiceException(f"Failed to enforce retention policy: {str(e)}")
cl
ass DatabaseServiceException(DomainException):
    """Exception raised for database service errors."""
    pass


class DatabaseService:
    """Service for database operations and schema updates."""
    
    @staticmethod
    def update_globals_database() -> Dict[str, Any]:
        """
        Execute global database updates including schema changes and data updates.
        
        Returns:
            Dict with success status and message
            
        Raises:
            DatabaseServiceException: If database update fails
        """
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Add columns to globals_designation table
                cursor.execute("""
                    ALTER TABLE globals_designation
                    ADD COLUMN IF NOT EXISTS basic BOOLEAN NOT NULL DEFAULT FALSE;
                """)

                cursor.execute("""
                    ALTER TABLE globals_designation
                    ADD COLUMN IF NOT EXISTS category VARCHAR(20) NULL;
                """)

                cursor.execute("""
                    ALTER TABLE globals_designation
                    ADD COLUMN IF NOT EXISTS dept_if_not_basic VARCHAR(100) NULL;
                """)

                # Update auth_user sequence
                cursor.execute("""
                    DROP SEQUENCE IF EXISTS auth_user_id_seq CASCADE;
                """)
                    
                cursor.execute("""
                    CREATE SEQUENCE auth_user_id_seq;
                """)
                    
                cursor.execute("""
                    ALTER TABLE auth_user
                    ALTER COLUMN id SET DEFAULT NEXTVAL('auth_user_id_seq');
                """)
                    
                cursor.execute("""
                    SELECT SETVAL('auth_user_id_seq', COALESCE(MAX(id), 1))
                    FROM auth_user;
                """)

                # Update globals_moduleaccess sequence
                cursor.execute("""
                    DROP SEQUENCE IF EXISTS globals_moduleaccess_id_seq CASCADE;
                """)
                    
                cursor.execute("""
                    CREATE SEQUENCE globals_moduleaccess_id_seq;
                """)
                    
                cursor.execute("""
                    ALTER TABLE globals_moduleaccess
                    ALTER COLUMN id SET DEFAULT NEXTVAL('globals_moduleaccess_id_seq');
                """)
                    
                cursor.execute("""
                    SELECT SETVAL('globals_moduleaccess_id_seq', COALESCE(MAX(id), 1))
                    FROM globals_moduleaccess;
                """)

                # Update globals_holdsdesignation sequence
                cursor.execute("""
                    DROP SEQUENCE IF EXISTS globals_holdsdesignation_id_seq CASCADE;
                """)
                    
                cursor.execute("""
                    CREATE SEQUENCE globals_holdsdesignation_id_seq;
                """)
                    
                cursor.execute("""
                    ALTER TABLE globals_holdsdesignation
                    ALTER COLUMN id SET DEFAULT NEXTVAL('globals_holdsdesignation_id_seq');
                """)
                    
                cursor.execute("""
                    SELECT SETVAL('globals_holdsdesignation_id_seq', COALESCE(MAX(id), 1))
                    FROM globals_holdsdesignation;
                """)

                # Create trigger for basic designation enforcement
                cursor.execute("""
                    DROP TRIGGER IF EXISTS check_basic_designation ON globals_holdsdesignation;
                """)
                    
                cursor.execute("""
                    DROP FUNCTION IF EXISTS enforce_single_basic_designation();
                """)
                    
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION enforce_single_basic_designation()
                    RETURNS TRIGGER AS $
                        BEGIN
                            IF NEW.designation_id IS NOT NULL AND (
                            SELECT basic 
                            FROM globals_designation 
                            WHERE id = NEW.designation_id
                        ) = TRUE THEN
                            IF (
                                SELECT COUNT(*) 
                                FROM globals_holdsdesignation h 
                                JOIN globals_designation d 
                                ON h.designation_id = d.id
                                WHERE h.user_id = NEW.user_id AND d.basic = TRUE
                        ) > 0 THEN
                                RAISE EXCEPTION 'A user can only have one basic designation.';
                            END IF;
                        END IF;

                        RETURN NEW;
                    END;
                    $ LANGUAGE plpgsql;
                """)
                    
                cursor.execute("""
                    CREATE TRIGGER check_basic_designation
                    BEFORE INSERT OR UPDATE ON globals_holdsdesignation
                    FOR EACH ROW
                    EXECUTE FUNCTION enforce_single_basic_designation();
                """)

                # Update designation data
                cursor.execute("""
                    UPDATE globals_designation
                    SET basic = TRUE
                    WHERE name IN ('Professor', 'Associate Professor', 'Assistant Professor', 'student', 'Registrar');
                """)

                cursor.execute("""
                    UPDATE globals_designation
                    SET category = CASE
                        WHEN name IN ('Professor', 'Associate Professor', 'Assistant Professor', 
                                    'HOD (CSE)', 'HOD (ECE)', 'HOD (ME)', 'HOD (Design)', 
                                    'HOD (NS)', 'HOD (Liberal Arts)')
                        THEN 'faculty'
                        WHEN name IN ('student', 'co-ordinator', 'co co-ordinator')
                        THEN 'student'
                        WHEN name IN ('Registrar', 'Compounder')
                        THEN 'staff'
                        ELSE category
                    END
                    WHERE name IS NOT NULL;
                """)

            return {
                "success": True, 
                "message": "Database updates completed successfully."
            }
            
        except Exception as e:
            raise DatabaseServiceException(f"Failed to update globals database: {str(e)}")