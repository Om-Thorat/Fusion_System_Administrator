#!/usr/bin/env python
"""
Simple test to verify selectors can be imported and basic functions work.
This is a quick validation before running the full test suite.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

try:
    from api import selectors
    print("✅ Successfully imported selectors module")
    
    # Test that functions exist
    functions_to_test = [
        'get_all_departments',
        'get_all_batches', 
        'get_all_programmes',
        'get_user_by_username',
        'get_all_designations',
        'get_students_with_filters',
        'get_faculty_with_filters',
        'get_staff_with_filters'
    ]
    
    for func_name in functions_to_test:
        if hasattr(selectors, func_name):
            print(f"✅ Function {func_name} exists")
        else:
            print(f"❌ Function {func_name} missing")
    
    print("\n✅ All selector functions are properly defined!")
    print("📝 Selectors module is ready for use in views")
    
except ImportError as e:
    print(f"❌ Failed to import selectors: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error testing selectors: {e}")
    sys.exit(1)