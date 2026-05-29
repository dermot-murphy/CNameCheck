#!/usr/bin/env python3
"""
cstylecheck.py — CLI entry-point wrapper.

This thin wrapper exists so that the tool can still be invoked directly as a
script (``python src/cstylecheck.py [options] files...``) without installing
the package.  The actual implementation lives in the ``cstylecheck`` package
directory (``src/cstylecheck/__init__.py`` and sub-modules).

When imported as a module, Python prefers the package directory
(``src/cstylecheck/``) over this file, so ``import cstylecheck`` always loads
the package.  This file is only executed when run as ``__main__``.
"""
import sys
import os

# Ensure the package directory (src/) is on the path so the package is found
# even when this script is invoked directly from a checkout.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cstylecheck.cli import main  # noqa: E402

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as _e:
        if isinstance(_e.code, str):
            print(_e.code, file=sys.stderr)
            sys.exit(2)
        raise
