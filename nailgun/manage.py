#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # sys.path.insert(0, os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailgun.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
