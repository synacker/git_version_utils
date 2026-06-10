"""Setup script for git-version-utils.

The package version is determined dynamically from git tags.
Run `python tools/write_version.py` before building to generate
src/git_version/_version.py with the correct version.

The version in pyproject.toml is a fallback placeholder (0.0.0).
"""

import os
import re

from setuptools import setup


def get_version() -> str:
    """Get the package version from pyproject.toml."""
    pyproject = os.path.join(os.path.dirname(__file__), "pyproject.toml")
    if not os.path.exists(pyproject):
        return "0.0.0"
    with open(pyproject, "r") as f:
        content = f.read()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return match.group(1) if match else "0.0.0"


if __name__ == "__main__":
    setup(version=get_version())