import csv
import datetime
from django.http import HttpResponse
from django.db.models import Max, Q
from django.db.models.functions import Upper
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.views import APIView
from .models import GlobalsDesignation, GlobalsHoldsdesignation, GlobalsModuleaccess, AuthUser, Batch, Student, GlobalsDepartmentinfo, Programme, GlobalsFaculty, Staff
from .serializers import GlobalExtraInfoSerializer, GlobalsDesignationSerializer, GlobalsModuleaccessSerializer, AuthUserSerializer, GlobalsHoldsDesignationSerializer, StudentSerializer, GlobalsFacultySerializer, GlobalsDepartmentinfoSerializer, BatchSerializer, ProgrammeSerializer, StaffSerializer, ViewStudentsWithFiltersSerializer, ViewStaffWithFiltersSerializer, ViewFacultyWithFiltersSerializer
from io import StringIO
from .helpers import create_password, send_email, mail_to_user, configure_password_mail, add_user_extra_info, add_user_designation_info, add_student_info
from django.contrib.auth.hashers import make_password
from backend.settings import EMAIL_TEST_ARRAY
from django.conf import settings


@api_view(['GET'])
def get_all_departments(request):
    from . import selectors
    records = selectors.get_all_departments()
    serializer = GlobalsDepartmentinfoSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_batches(request):
    from . import selectors
    records = selectors.get_all_batches()
    serializer = BatchSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_programmes(request):
    from . import selectors
    records = selectors.get_all_programmes()
    serializer = ProgrammeSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_user_role_by_username(request):
    username = request.query_params.get('username')
    
    if not username:
        return Response({"error": "Username parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from . import selectors
        
        user = selectors.get_user_by_username(username)
        holds_designation_entries = selectors.get_user_roles(user)
        
        if not holds_designation_entries.exists():
            return Response({"error": "User has no designations."}, status=status.HTTP_404_NOT_FOUND)
        
        designation_ids = [entry.designation_id for entry in holds_designation_entries]
        roles = selectors.get_designations_by_ids(designation_ids)
        
        roles_serializer = GlobalsDesignationSerializer(roles, many=True)
        
        return Response({
            "user": AuthUserSerializer(user).data,
            "roles": roles_serializer.data,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        if "DoesNotExist" in str(type(e)):
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
def update_user_roles(request):
    try:
        from . import services
        
        username = request.data.get('username')
        roles_to_add = request.data.get('roles')

        if not username or not roles_to_add:
            return Response({"error": "Username and roles are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Use RoleService to update user roles
        services.RoleService.update_user_roles(username, roles_to_add)
        
        return Response({"message": "User roles updated successfully."}, status=status.HTTP_200_OK)
        
    except services.ValidationException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except services.UserServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            "error": f"Unexpected error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET'])
def global_designation_list(request):
    records = GlobalsDesignation.objects.all()
    serializer = GlobalsDesignationSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def get_category_designations(request):
    try:
        from . import selectors
        
        category = request.data.get('category', 'student')
        basic = request.data.get('basic', True)
        
        records = selectors.get_designations_by_category(category, basic)
        serializer = GlobalsDesignationSerializer(records, many=True)
        
        return Response(serializer.data)
        
    except Exception as e:
        return Response({
            "error": f"Failed to get designations: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def add_designation(request):
    serializer = GlobalsDesignationSerializer(data=request.data)
    if serializer.is_valid():
        role = serializer.save()
        max_id = GlobalsModuleaccess.objects.aggregate(Max('id'))['id__max']
        new_id = (max_id or 0) + 1
        data = {
            'id': new_id,
            'designation' : role.name,
            'program_and_curriculum' : False,
            'course_registration' : False,
            'course_management' : False,
            'other_academics' : False,
            'spacs' : False,
            'department' : False,
            'examinations' : False,
            'hr' : False,
            'iwd' : False,
            'complaint_management' : False,
            'fts' : False,
            'purchase_and_store' : False,
            'rspc' : False,
            'hostel_management' : False,
            'mess_management' : False,
            'gymkhana' : False,
            'placement_cell' : False,
            'visitor_hostel' : False,
            'phc' : False,
            'inventory_management': False,
        }
        module_serializer = GlobalsModuleaccessSerializer(data=data)
        if module_serializer.is_valid():
            module_serializer.save()
        return Response({'role': serializer.data, 'modules': module_serializer.data}, status.HTTP_201_CREATED)
    else :
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT', 'PATCH'])
def update_designation(request):
    name = request.data.get('name')
    
    if not name:
        return Response({"error": "No name provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        designation = GlobalsDesignation.objects.get(name=name)
    except GlobalsDesignation.DoesNotExist:
        return Response({"error": f"Designation with name '{name}' not found."}, status=status.HTTP_404_NOT_FOUND)
    
    partial = request.method == 'PATCH'
    serializer = GlobalsDesignationSerializer(designation, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def reset_password(request):
    user_name = request.data.get('username')
    try:
        user = AuthUser.objects.annotate(username_upper=Upper('username')).get(username_upper=user_name.upper())
        new_password = create_password(request.data)
        while new_password == user.password:
            new_password = create_password(request.data)
        
        user.password = new_password
        user.save()
        
        try:
            subject = 'Your Password has been reset!!'
            message = f"This Mail is to notify you that your password has been reset by the System Administrator.\n\nPlease check out the new password below:  {new_password}\n\nRegards,\nSystem Administrator,\nIIITDM Jabalpur."
            recipient_list = [f"{user.email}" if settings.EMAIL_TEST_MODE == 0 else settings.EMAIL_TEST_USER]
            send_email(subject=subject, message=message, recipient_list=recipient_list)
        except:
            print(e)
        finally:
            return Response({"password": new_password,"message": "Password reset successfully."}, status=status.HTTP_200_OK)
    except AuthUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_module_access(request):
    role_name = request.query_params.get('designation')
    
    if not role_name:
        return Response({"error": "No role provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        module_access = GlobalsModuleaccess.objects.get(designation=role_name)
    except GlobalsModuleaccess.DoesNotExist:
        return Response({"error": f"Module access for designation '{role_name}' not found."}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = GlobalsModuleaccessSerializer(module_access)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['PUT'])
def modify_moduleaccess(request):
    role_name = request.data.get('designation')
    
    if not role_name:
        return Response({"error": "No role provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        designation = GlobalsModuleaccess.objects.get(designation=role_name)
    except GlobalsModuleaccess.DoesNotExist:
        return Response({"error": f"Designation with name '{role_name}' not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = GlobalsModuleaccessSerializer(designation, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def add_individual_student(request):
    try:
        from . import services
        
        required_fields = ["username", "first_name", "last_name", "sex", "category", "father_name", "mother_name", "batch", "programme"]
        data = request.data
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return Response({
                "error": "Missing required fields.",
                "missing_fields": missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use UserService to create student
        result = services.UserService.create_student(data)
        
        response_data = {
            "message": f"1 user created successfully.",
            "created_users": [result],
            "skipped_users_count": 0,
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except services.ValidationException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except services.UserServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            "error": f"Unexpected error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def add_individual_staff(request):
    try:
        from . import services
        
        required_fields = ["username", "first_name", "last_name", "sex", "designation"]
        data = request.data
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return Response({
                "error": "Missing required fields.",
                "missing_fields": missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use UserService to create staff
        result = services.UserService.create_staff(data)
        
        return Response({
            "message": "Staff added successfully",
            "user_data": result,
        }, status=status.HTTP_201_CREATED)
        
    except services.ValidationException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except services.UserServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            "error": f"Unexpected error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def add_individual_faculty(request):
    required_fields = ["username", "first_name", "last_name", "sex", "designation"]
    data = request.data
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return Response({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }, status=status.HTTP_400_BAD_REQUEST)
    user_password = create_password(data)
    auth_user_data = {
        "password": make_password(user_password),
        "username": data['username'].lower(),
        "first_name": data['first_name'].lower().capitalize(),
        "last_name": data.get('last_name').lower().capitalize(),
        "email": f"{data['username'].lower()}@iiitdmj.ac.in",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
        "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    auth_serializer = AuthUserSerializer(data=auth_user_data)
    user = None
    if auth_serializer.is_valid():
        user = auth_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to auth user table",
            "data": auth_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    default_department = GlobalsDepartmentinfo.objects.get(name='CSE').id
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
        'department': data.get("department") if data.get("department") else default_department,
        'user': user.id,
    }
    extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
    extra_info = None
    if extra_info_serializer.is_valid():
        extra_info = extra_info_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to globals extra info table",
            "data": extra_info_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    holds_designation_data = {
        'designation' : data.get('designation'),
        'user' : user.id,
        'working' : user.id,
    }
    holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
    if holds_designation_serializer.is_valid():
        holds_designation_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to globals holds designation table",
            "data": holds_designation_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    faculty_id = extra_info.id
    faculty_data = {
        'id' : faculty_id,
    }

    faculty_serializer = GlobalsFacultySerializer(data=faculty_data)
    if faculty_serializer.is_valid():
        faculty_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to globals faculty table",
            "data": faculty_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "message": "Faculty added successfully",
        "auth_user_data": auth_user_data,
        "extra_info_user_data": extra_info_data,
        "holds_designation_user_data": holds_designation_data,
        "globals_faculty_data": faculty_data,
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def bulk_import_users(request):
    try:
        from . import services
        
        if 'file' not in request.FILES:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return Response({"error": "Please upload a valid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        # Use UserService to handle bulk import
        result = services.UserService.bulk_import_students_from_csv(file)
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except services.ValidationException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except services.UserServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            "error": f"Unexpected error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def bulk_export_users(request):
    try:
        from . import services
        
        # Use UserService to handle bulk export
        response = services.UserService.bulk_export_users_to_csv()
        
        return response
        
    except services.UserServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            "error": f"Unexpected error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response

@api_view(['POST'])
def mail_to_whole_batch(request):
    try:
        from . import services
        
        batch = request.data.get('batch')
        if not batch:
            return Response({"error": "Batch is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use EmailService to send batch emails
        result = services.EmailService.send_batch_emails_to_batch(batch)
        
        return Response({"message": "Mail sent to whole batch successfully."}, status=status.HTTP_200_OK)
        
    except services.ValidationException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except services.EmailServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            "error": f"Unexpected error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "username", "first_name", "last_name", "sex", "category",
        "father_name", "mother_name", "batch", "programme", "title",
        "dob", "address", "phone_no", "department"
    ])
    return response

class UserListView(APIView):
    def get(self, request):
        try:
            from . import selectors
            
            user_type = request.GET.get('type')
            
            if user_type == "student":
                students = selectors.get_students_with_filters(
                    programme=request.GET.get("programme"),
                    batch=request.GET.get("batch"),
                    discipline=request.GET.get("discipline"),
                    category=request.GET.get("category"),
                    gender=request.GET.get("gender")
                )
                serializer = ViewStudentsWithFiltersSerializer(students, many=True)

            elif user_type == "faculty":
                faculty = selectors.get_faculty_with_filters(
                    designation=request.GET.get("designation"),
                    gender=request.GET.get("gender")
                )
                serializer = ViewFacultyWithFiltersSerializer(faculty, many=True)

            elif user_type == "staff":
                staff = selectors.get_staff_with_filters(
                    designation=request.GET.get("designation"),
                    gender=request.GET.get("gender")
                )
                serializer = ViewStaffWithFiltersSerializer(staff, many=True)

            else:
                return Response({"error": "Invalid or missing user type."}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                "error": f"Failed to retrieve users: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
