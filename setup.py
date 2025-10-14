"""
Setup script for VoiceGuard
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    return "VoiceGuard - Advanced Voice Authentication System Powered by AI"

# Read requirements
def read_requirements():
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
    return []

setup(
    name="voiceguard",
    version="1.0.0",
    author="VoiceGuard",
    author_email="",
    description="Advanced Voice Authentication System Powered by AI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "voiceguard=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)