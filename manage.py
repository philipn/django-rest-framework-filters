#!/usr/bin/env python
import os
import sys

# Remove the package root directory from `sys.path`, ensuring that rest_framework_filters
# is imported from the installed site packages. Used for testing the distribution.
if '--no-pkgroot' in sys.argv:
    sys.argv.remove('--no-pkgroot')
    package_root = sys.path.pop(0)

    import rest_framework_filters
    package_dir = os.path.join(os.getcwd(), 'rest_framework_filters')
    assert not rest_framework_filters.__file__.startswith(package_dir)

    sys.path.insert(0, package_root)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
