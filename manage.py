#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import dotenv
from dotenv import load_dotenv
load_dotenv()

def main():
    
    try:
        from oracle11g_patch import apply_oracle11g_patches
        apply_oracle11g_patches()
    except ImportError:
        pass  # Patches not available, continue normally
    except Exception as e:
        print(f"Warning: Could not apply Oracle 11g patches: {e}")
        
        
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
        
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
