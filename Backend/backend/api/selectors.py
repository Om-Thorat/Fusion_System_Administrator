"""
Selectors module for read-only database operations.

This module contains all database query functions that retrieve data without
side effects. These functions are used by views to separate query logic from
presentation logic.

Design Principles:
- Pure functions with no side effects
- Return Django QuerySets or model instances
- Accept filtering parameters as function arguments
- No business logic, only data retrieval
"""

from django.db.models import QuerySet, Max
from django.db.models.functions import Upper
from typing import Optional, Dict, Any, List

from .models import (
    GlobalsDepartmentinfo, Batch, Programme, AuthUser, GlobalsDesignation,
    GlobalsHoldsdesignation, GlobalsModuleaccess, Student, GlobalsFaculty, Staff
)


# Academic Data Selectors
def get_all_departments() -> QuerySet[GlobalsDepartmentinfo]:
    """
    Get all departments ordered by ID.
    
    Returns:
        QuerySet of GlobalsDepartmentinfo objects ordered by id
    """
    return GlobalsDepartmentinfo.objects.all().order_by('id')


def get_all_batches() -> QuerySet[Batch]:
    """
    Get all distinct batches by year.
    
    Returns:
        QuerySet of Batch objects with distinct years
    """
    return Batch.objects.distinct('year')


def get_all_programmes() -> QuerySet[Programme]:
    """
    Get all programmes ordered by ID.
    
    Returns:
        QuerySet of Programme objects ordered by id
    """
    return Programme.objects.all().order_by('id')


def get_department_by_name(name: str) -> GlobalsDepartmentinfo:
    """
    Get department by name.
    
    Args:
        name: Department name to search for
        
    Returns:
        GlobalsDepartmentinfo object
        
    Raises:
        GlobalsDepartmentinfo.DoesNotExist: If department not found
    """
    return GlobalsDepartmentinfo.objects.get(name=name)


def get_batch_by_filters(name: Optional[str] = None, 
                        discipline_acronym: Optional[str] = None, 
                        year: Optional[int] = None) -> Optional[Batch]:
    """
    Get batch by multiple filter criteria.
    
    Args:
        name: Batch name to filter by
        discipline_acronym: Discipline acronym to filter by
        year: Year to filter by
        
    Returns:
        First matching Batch object or None if not found
    """
    queryset = Batch.objects.all()
    
    if name:
        queryset = queryset.filter(name=name)
    if discipline_acronym:
        queryset = queryset.filter(discipline__acronym=discipline_acronym)
    if year:
        queryset = queryset.filter(year=year)
        
    return queryset.first()


# User and Role Selectors
def get_user_by_username(username: str) -> AuthUser:
    """
    Get user by username (case-insensitive).
    
    Args:
        username: Username to search for
        
    Returns:
        AuthUser object
        
    Raises:
        AuthUser.DoesNotExist: If user not found
    """
    return AuthUser.objects.get(username__iexact=username)


def get_user_by_username_upper(username: str) -> AuthUser:
    """
    Get user by username with uppercase annotation.
    
    Args:
        username: Username to search for (will be converted to uppercase)
        
    Returns:
        AuthUser object with username_upper annotation
        
    Raises:
        AuthUser.DoesNotExist: If user not found
    """
    return AuthUser.objects.annotate(
        username_upper=Upper('username')
    ).get(username_upper=username.upper())


def get_all_users() -> QuerySet[AuthUser]:
    """
    Get all users.
    
    Returns:
        QuerySet of all AuthUser objects
    """
    return AuthUser.objects.all()


def get_user_roles(user: AuthUser) -> QuerySet[GlobalsHoldsdesignation]:
    """
    Get all role assignments for a user.
    
    Args:
        user: AuthUser instance
        
    Returns:
        QuerySet of GlobalsHoldsdesignation objects for the user
    """
    return GlobalsHoldsdesignation.objects.filter(user=user)


def get_designations_by_ids(designation_ids: list) -> QuerySet[GlobalsDesignation]:
    """
    Get designations by list of IDs.
    
    Args:
        designation_ids: List of designation IDs
        
    Returns:
        QuerySet of GlobalsDesignation objects matching the IDs
    """
    return GlobalsDesignation.objects.filter(id__in=designation_ids)


def get_all_designations() -> QuerySet[GlobalsDesignation]:
    """
    Get all designations.
    
    Returns:
        QuerySet of all GlobalsDesignation objects
    """
    return GlobalsDesignation.objects.all()


def get_designations_by_category(category: str, basic: Optional[bool] = None) -> QuerySet[GlobalsDesignation]:
    """
    Get designations filtered by category and optionally by basic flag.
    
    Args:
        category: Category to filter by
        basic: Optional basic flag to filter by
        
    Returns:
        QuerySet of filtered GlobalsDesignation objects
    """
    queryset = GlobalsDesignation.objects.filter(category=category)
    
    if basic is not None:
        queryset = queryset.filter(basic=basic)
        
    return queryset


def get_designation_by_name(name: str) -> GlobalsDesignation:
    """
    Get designation by name.
    
    Args:
        name: Designation name to search for
        
    Returns:
        GlobalsDesignation object
        
    Raises:
        GlobalsDesignation.DoesNotExist: If designation not found
    """
    return GlobalsDesignation.objects.get(name=name)


def get_module_access_by_designation(designation: str) -> GlobalsModuleaccess:
    """
    Get module access by designation name.
    
    Args:
        designation: Designation name to search for
        
    Returns:
        GlobalsModuleaccess object
        
    Raises:
        GlobalsModuleaccess.DoesNotExist: If module access not found
    """
    return GlobalsModuleaccess.objects.get(designation=designation)


def get_max_module_access_id() -> int:
    """
    Get the maximum ID from GlobalsModuleaccess table.
    
    Returns:
        Maximum ID value or 0 if no records exist
    """
    max_id = GlobalsModuleaccess.objects.aggregate(Max('id'))['id__max']
    return max_id or 0


# User List Selectors with Filters
def get_students_with_filters(programme: Optional[str] = None,
                             batch: Optional[int] = None,
                             discipline: Optional[str] = None,
                             category: Optional[str] = None,
                             gender: Optional[str] = None) -> QuerySet[Student]:
    """
    Get students with optional filters.
    
    Args:
        programme: Programme name to filter by (case-insensitive)
        batch: Batch ID to filter by
        discipline: Discipline name to filter by (case-insensitive)
        category: Category to filter by (case-insensitive)
        gender: Gender to filter by (case-insensitive)
        
    Returns:
        QuerySet of Student objects with applied filters
    """
    students = Student.objects.select_related('id__user', 'id__department', 'batch_id')
    
    if programme:
        students = students.filter(programme__iexact=programme)
    if batch:
        students = students.filter(batch=batch)
    if discipline:
        students = students.filter(batch_id__discipline__name__iexact=discipline)
    if category:
        students = students.filter(category__iexact=category)
    if gender:
        students = students.filter(id__sex__iexact=gender)
        
    return students


def get_faculty_with_filters(designation: Optional[str] = None,
                            gender: Optional[str] = None) -> QuerySet[GlobalsFaculty]:
    """
    Get faculty with optional filters.
    
    Args:
        designation: Designation name to filter by (case-insensitive)
        gender: Gender to filter by (case-insensitive)
        
    Returns:
        QuerySet of GlobalsFaculty objects with applied filters
    """
    faculty = GlobalsFaculty.objects.select_related(
        'id__user', 'id__department'
    ).prefetch_related('id__user__holds_designations__designation')
    
    if designation:
        faculty = faculty.filter(
            id__user__holds_designations__designation__name__iexact=designation
        ).distinct()
    if gender:
        faculty = faculty.filter(id__sex__iexact=gender)
        
    return faculty


def get_staff_with_filters(designation: Optional[str] = None,
                          gender: Optional[str] = None) -> QuerySet[Staff]:
    """
    Get staff with optional filters.
    
    Args:
        designation: Designation name to filter by (case-insensitive)
        gender: Gender to filter by (case-insensitive)
        
    Returns:
        QuerySet of Staff objects with applied filters
    """
    staff = Staff.objects.select_related(
        "id__user", "id__department"
    ).prefetch_related('id__user__holds_designations__designation')
    
    if designation:
        staff = staff.filter(
            id__user__holds_designations__designation__name__iexact=designation
        ).distinct()
    if gender:
        staff = staff.filter(id__sex__iexact=gender)
        
    return staff


def get_students_by_batch_and_emails(batch: int, email_list: Optional[list] = None) -> QuerySet[Student]:
    """
    Get students by batch and optionally filter by email list.
    
    Args:
        batch: Batch ID to filter by
        email_list: Optional list of emails to filter by
        
    Returns:
        QuerySet of Student objects matching criteria
    """
    if email_list and len(email_list) > 1:
        return Student.objects.filter(
            batch=batch, 
            id__user__email__in=email_list
        )
    else:
        return Student.objects.filter(batch=batch)


# Additional User and Role Selectors for Complete Coverage
def get_user_role_names(user: AuthUser) -> set:
    """
    Get set of role names for a user.
    
    Args:
        user: AuthUser instance
        
    Returns:
        Set of role names (strings) assigned to the user
    """
    return set(
        GlobalsHoldsdesignation.objects.filter(user=user)
        .values_list('designation__name', flat=True)
    )


def delete_user_roles_by_names(user: AuthUser, role_names: list) -> int:
    """
    Delete user role assignments by role names.
    
    Args:
        user: AuthUser instance
        role_names: List of role names to remove
        
    Returns:
        Number of role assignments deleted
    """
    deleted_count, _ = GlobalsHoldsdesignation.objects.filter(
        user=user, 
        designation__name__in=role_names
    ).delete()
    return deleted_count


def user_has_role(user: AuthUser, role_name: str) -> bool:
    """
    Check if user has a specific role.
    
    Args:
        user: AuthUser instance
        role_name: Role name to check for
        
    Returns:
        True if user has the role, False otherwise
    """
    return GlobalsHoldsdesignation.objects.filter(
        user=user,
        designation__name=role_name
    ).exists()


def get_users_by_role(role_name: str) -> QuerySet[AuthUser]:
    """
    Get all users with a specific role.
    
    Args:
        role_name: Role name to filter by
        
    Returns:
        QuerySet of AuthUser objects with the specified role
    """
    return AuthUser.objects.filter(
        holds_designations__designation__name=role_name
    ).distinct()


def get_designation_with_module_access(designation_name: str) -> tuple:
    """
    Get designation and its module access in one query.
    
    Args:
        designation_name: Name of the designation
        
    Returns:
        Tuple of (GlobalsDesignation, GlobalsModuleaccess) objects
        
    Raises:
        GlobalsDesignation.DoesNotExist: If designation not found
        GlobalsModuleaccess.DoesNotExist: If module access not found
    """
    designation = GlobalsDesignation.objects.get(name=designation_name)
    module_access = GlobalsModuleaccess.objects.get(designation=designation_name)
    return designation, module_access


def get_user_with_roles(username: str) -> tuple:
    """
    Get user and their roles in optimized queries.
    
    Args:
        username: Username to search for (case-insensitive)
        
    Returns:
        Tuple of (AuthUser, QuerySet[GlobalsDesignation]) 
        
    Raises:
        AuthUser.DoesNotExist: If user not found
    """
    user = AuthUser.objects.get(username__iexact=username)
    
    # Get role assignments for this user
    role_assignments = GlobalsHoldsdesignation.objects.filter(user=user)
    
    if not role_assignments.exists():
        return user, GlobalsDesignation.objects.none()
    
    # Get the actual designation objects
    designation_ids = [assignment.designation_id for assignment in role_assignments]
    roles = GlobalsDesignation.objects.filter(id__in=designation_ids)
    
    return user, roles


def check_user_exists_by_username(username: str) -> bool:
    """
    Check if user exists by username (case-insensitive).
    
    Args:
        username: Username to check
        
    Returns:
        True if user exists, False otherwise
    """
    return AuthUser.objects.filter(username__iexact=username).exists()


def get_filtered_designations(category: Optional[str] = None, 
                             basic: Optional[bool] = None,
                             designation_type: Optional[str] = None) -> QuerySet[GlobalsDesignation]:
    """
    Get designations with multiple optional filters.
    
    Args:
        category: Category to filter by
        basic: Basic flag to filter by
        designation_type: Type to filter by
        
    Returns:
        QuerySet of filtered GlobalsDesignation objects
    """
    queryset = GlobalsDesignation.objects.all()
    
    if category:
        queryset = queryset.filter(category=category)
    if basic is not None:
        queryset = queryset.filter(basic=basic)
    if designation_type:
        queryset = queryset.filter(type=designation_type)
        
    return queryset

# Backup and System Selectors
def get_all_backup_records(db_name: Optional[str] = None) -> QuerySet:
    """
    Get all backup records, optionally filtered by database name.
    
    Args:
        db_name: Optional database name to filter by
        
    Returns:
        QuerySet of BackupRecord objects
    """
    from .models import BackupRecord
    
    queryset = BackupRecord.objects.all()
    
    if db_name:
        queryset = queryset.filter(db_name=db_name)
        
    return queryset


def get_backup_by_id(backup_id) -> 'BackupRecord':
    """
    Get backup record by ID.
    
    Args:
        backup_id: UUID of the backup record
        
    Returns:
        BackupRecord object
        
    Raises:
        BackupRecord.DoesNotExist: If backup not found
    """
    from .models import BackupRecord
    return BackupRecord.objects.get(id=backup_id)


def get_all_restore_records(db_name: Optional[str] = None) -> QuerySet:
    """
    Get all restore records, optionally filtered by database name.
    
    Args:
        db_name: Optional database name to filter by
        
    Returns:
        QuerySet of RestoreRecord objects
    """
    from .models import RestoreRecord
    
    queryset = RestoreRecord.objects.all()
    
    if db_name:
        queryset = queryset.filter(db_name=db_name)
        
    return queryset


def get_restore_record_by_id(restore_id) -> 'RestoreRecord':
    """
    Get restore record by ID.
    
    Args:
        restore_id: UUID of the restore record
        
    Returns:
        RestoreRecord object
        
    Raises:
        RestoreRecord.DoesNotExist: If restore not found
    """
    from .models import RestoreRecord
    return RestoreRecord.objects.get(id=restore_id)


def get_restore_records_by_db_name(db_name: str) -> QuerySet:
    """
    Get restore records filtered by database name.
    
    Args:
        db_name: Database name to filter by
        
    Returns:
        QuerySet of RestoreRecord objects
    """
    from .models import RestoreRecord
    return RestoreRecord.objects.filter(db_name=db_name)


def get_all_backup_schedules() -> QuerySet:
    """
    Get all backup schedules.
    
    Returns:
        QuerySet of BackupSchedule objects
    """
    from .models import BackupSchedule
    return BackupSchedule.objects.all()


def get_backup_schedule_by_id(schedule_id) -> 'BackupSchedule':
    """
    Get backup schedule by ID.
    
    Args:
        schedule_id: UUID of the backup schedule
        
    Returns:
        BackupSchedule object
        
    Raises:
        BackupSchedule.DoesNotExist: If schedule not found
    """
    from .models import BackupSchedule
    return BackupSchedule.objects.get(id=schedule_id)


def get_health_checks(db_name: str, days_back: int = 90) -> QuerySet:
    """
    Get health check records for a database within specified time period.
    
    Args:
        db_name: Database name to filter by
        days_back: Number of days to look back (default: 90)
        
    Returns:
        QuerySet of HealthCheck objects within the time period
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import HealthCheck
    
    since = timezone.now() - timedelta(days=days_back)
    return HealthCheck.objects.filter(
        db_name=db_name, 
        checked_at__gte=since
    )


def get_backup_count_by_db(db_name: str) -> int:
    """
    Get count of backup records for a specific database.
    
    Args:
        db_name: Database name to count backups for
        
    Returns:
        Number of backup records for the database
    """
    from .models import BackupRecord
    return BackupRecord.objects.filter(db_name=db_name).count()


def get_last_successful_backup(db_name: str) -> Optional['BackupRecord']:
    """
    Get the most recent successful backup for a database.
    
    Args:
        db_name: Database name to search for
        
    Returns:
        Most recent successful BackupRecord or None if not found
    """
    from .models import BackupRecord
    return BackupRecord.objects.filter(
        db_name=db_name, 
        status="success"
    ).first()


def backup_exists(backup_id) -> bool:
    """
    Check if backup record exists by ID.
    
    Args:
        backup_id: UUID of the backup record
        
    Returns:
        True if backup exists, False otherwise
    """
    from .models import BackupRecord
    return BackupRecord.objects.filter(id=backup_id).exists()


def restore_exists(restore_id) -> bool:
    """
    Check if restore record exists by ID.
    
    Args:
        restore_id: UUID of the restore record
        
    Returns:
        True if restore exists, False otherwise
    """
    from .models import RestoreRecord
    return RestoreRecord.objects.filter(id=restore_id).exists()


def schedule_exists(schedule_id) -> bool:
    """
    Check if backup schedule exists by ID.
    
    Args:
        schedule_id: UUID of the backup schedule
        
    Returns:
        True if schedule exists, False otherwise
    """
    from .models import BackupSchedule
    return BackupSchedule.objects.filter(id=schedule_id).exists()


def get_backup_schedule_by_db_name(db_name: str) -> Optional['BackupSchedule']:
    """
    Get backup schedule by database name.
    
    Args:
        db_name: Database name to search for
        
    Returns:
        BackupSchedule object or None if not found
    """
    from .models import BackupSchedule
    return BackupSchedule.objects.filter(db_name=db_name).first()


def get_enabled_backup_schedules() -> QuerySet:
    """
    Get all enabled backup schedules.
    
    Returns:
        QuerySet of enabled BackupSchedule objects
    """
    from .models import BackupSchedule
    return BackupSchedule.objects.filter(enabled=True)
# Academic Data Selectors
def get_all_departments():
    """
    Get all departments ordered by ID.
    
    Returns:
        QuerySet of GlobalsDepartmentinfo objects
    """
    from .models import GlobalsDepartmentinfo
    return GlobalsDepartmentinfo.objects.all().order_by('id')


def get_all_batches():
    """
    Get all distinct batches by year.
    
    Returns:
        QuerySet of Batch objects with distinct years
    """
    from .models import Batch
    return Batch.objects.distinct('year')


def get_all_programmes():
    """
    Get all programmes ordered by ID.
    
    Returns:
        QuerySet of Programme objects
    """
    from .models import Programme
    return Programme.objects.all().order_by('id')


def get_department_by_name(name: str):
    """
    Get department by name.
    
    Args:
        name: Department name
        
    Returns:
        GlobalsDepartmentinfo object
        
    Raises:
        DoesNotExist: If department not found
    """
    from .models import GlobalsDepartmentinfo
    return GlobalsDepartmentinfo.objects.get(name=name)


def get_department_by_id(department_id: int):
    """
    Get department by ID.
    
    Args:
        department_id: Department ID
        
    Returns:
        GlobalsDepartmentinfo object
        
    Raises:
        DoesNotExist: If department not found
    """
    from .models import GlobalsDepartmentinfo
    return GlobalsDepartmentinfo.objects.get(id=department_id)


def get_batch_by_criteria(name: str = None, discipline_acronym: str = None, year: int = None):
    """
    Get batch by various criteria.
    
    Args:
        name: Batch name
        discipline_acronym: Discipline acronym
        year: Batch year
        
    Returns:
        QuerySet of Batch objects matching criteria
    """
    from .models import Batch
    
    queryset = Batch.objects.all()
    
    if name:
        queryset = queryset.filter(name=name)
    if discipline_acronym:
        queryset = queryset.filter(discipline__acronym=discipline_acronym)
    if year:
        queryset = queryset.filter(year=year)
    
    return queryset


def get_programme_by_name(name: str):
    """
    Get programme by name.
    
    Args:
        name: Programme name
        
    Returns:
        Programme object
        
    Raises:
        DoesNotExist: If programme not found
    """
    from .models import Programme
    return Programme.objects.get(name=name)

# User filtering selectors
def get_students_with_filters(programme: Optional[str] = None, batch: Optional[str] = None, 
                             discipline: Optional[str] = None, category: Optional[str] = None, 
                             gender: Optional[str] = None) -> QuerySet:
    """
    Get students with optional filters.
    
    Args:
        programme: Programme name to filter by
        batch: Batch to filter by
        discipline: Discipline name to filter by
        category: Category to filter by
        gender: Gender to filter by
        
    Returns:
        QuerySet of Student objects with related data
    """
    from .models import Student
    
    students = Student.objects.select_related('id__user', 'id__department', 'batch_id')
    
    if programme:
        students = students.filter(programme__iexact=programme)
    if batch:
        students = students.filter(batch=batch)
    if discipline:
        students = students.filter(batch_id__discipline__name__iexact=discipline)
    if category:
        students = students.filter(category__iexact=category)
    if gender:
        students = students.filter(id__sex__iexact=gender)
        
    return students


def get_faculty_with_filters(designation: Optional[str] = None, gender: Optional[str] = None) -> QuerySet:
    """
    Get faculty with optional filters.
    
    Args:
        designation: Designation name to filter by
        gender: Gender to filter by
        
    Returns:
        QuerySet of GlobalsFaculty objects with related data
    """
    from .models import GlobalsFaculty
    
    faculty = GlobalsFaculty.objects.select_related('id__user', 'id__department').prefetch_related('id__user__holds_designations__designation')
    
    if designation:
        faculty = faculty.filter(id__user__holds_designations__designation__name__iexact=designation).distinct()
    if gender:
        faculty = faculty.filter(id__sex__iexact=gender)
        
    return faculty


def get_staff_with_filters(designation: Optional[str] = None, gender: Optional[str] = None) -> QuerySet:
    """
    Get staff with optional filters.
    
    Args:
        designation: Designation name to filter by
        gender: Gender to filter by
        
    Returns:
        QuerySet of Staff objects with related data
    """
    from .models import Staff
    
    staff = Staff.objects.select_related("id__user", "id__department").prefetch_related('id__user__holds_designations__designation')
    
    if designation:
        staff = staff.filter(id__user__holds_designations__designation__name__iexact=designation).distinct()
    if gender:
        staff = staff.filter(id__sex__iexact=gender)
        
    return staff


def get_designations_by_category(category: str = 'student', basic: bool = True) -> QuerySet:
    """
    Get designations filtered by category and basic flag.
    
    Args:
        category: Category to filter by (default: 'student')
        basic: Basic flag to filter by (default: True)
        
    Returns:
        QuerySet of GlobalsDesignation objects
    """
    from .models import GlobalsDesignation
    
    return GlobalsDesignation.objects.all().filter(category=category, basic=basic)


def get_designations_by_ids(designation_ids: List[int]) -> QuerySet:
    """
    Get designations by a list of IDs.
    
    Args:
        designation_ids: List of designation IDs
        
    Returns:
        QuerySet of GlobalsDesignation objects
    """
    from .models import GlobalsDesignation
    
    return GlobalsDesignation.objects.filter(id__in=designation_ids)


def get_enabled_backup_schedules() -> QuerySet:
    """
    Get all enabled backup schedules.
    
    Returns:
        QuerySet of BackupSchedule objects that are enabled
    """
    from .models import BackupSchedule
    
    return BackupSchedule.objects.filter(enabled=True)