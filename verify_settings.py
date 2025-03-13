#!/usr/bin/env python
"""
Simple script to verify that the settings module can be imported.
This is useful for debugging deployment issues.
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the settings module
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rs_systems.settings')
    from rs_systems import settings
    print("Successfully imported rs_systems.settings")
    print(f"INSTALLED_APPS: {settings.INSTALLED_APPS}")
except ImportError as e:
    print(f"Error importing rs_systems.settings: {e}")
    print("Python path:")
    for path in sys.path:
        print(f"  - {path}")
    
    # Check if the rs_systems directory exists and is a Python package
    rs_systems_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rs_systems')
    print(f"\nChecking rs_systems directory: {rs_systems_dir}")
    if os.path.isdir(rs_systems_dir):
        print("  - Directory exists")
        init_file = os.path.join(rs_systems_dir, '__init__.py')
        if os.path.isfile(init_file):
            print("  - __init__.py exists")
        else:
            print("  - __init__.py does not exist")
        
        settings_file = os.path.join(rs_systems_dir, 'settings.py')
        if os.path.isfile(settings_file):
            print("  - settings.py exists")
        else:
            print("  - settings.py does not exist")
    else:
        print("  - Directory does not exist") 