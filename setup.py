#!/usr/bin/env python3
"""
Setup script for Drevoid Chat Client.

Installs Drevoid as a Python package with CLI integration.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="drevoid",
    version="1.0.1",
    author="Pawan Kumar",
    author_email="aegis.invincible@gmail.com",
    description="Terminal-based LAN chat client with rooms, private messaging, and CTF flag detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/axiomchronicles/drevoid_client",
    project_urls={
        "Bug Tracker": "https://github.com/axiomchronicles/drevoid_client/issues",
        "Documentation": "https://github.com/axiomchronicles/drevoid_client/blob/main/docs",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "dre=drevoid.cli:main",
        ],
    },
    keywords="chat networking lan messaging ctf terminal",
    include_package_data=True,
)
