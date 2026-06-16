#!/usr/bin/env python
import os
import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        os.environ.setdefault("TCB_USE_SQLITE", "True")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
