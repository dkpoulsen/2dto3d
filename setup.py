"""
2Dto3D Video Converter

A Python application that leverages machine learning models to convert 2D videos
into 3D videos using depth estimation and stereoscopic video generation.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (
    (this_directory / "README.md").read_text(encoding="utf-8")
    if (this_directory / "README.md").exists()
    else ""
)

# Read requirements
requirements = []
requirements_path = this_directory / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-r"):
                requirements.append(line)

setup(
    name="video2d3d",
    version="0.1.0",
    author="Automaker",
    author_email="",
    description="Convert 2D videos to 3D using deep learning depth estimation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/automaker/2dto3d",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Typing :: Typed",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "ruff>=0.0.200",
            "mypy>=0.950",
        ],
        "gpu": [
            "torch>=1.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "video2d3d=video2d3d.cli:main",
            "v2d3d=video2d3d.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "video2d3d": ["py.typed"],
    },
    zip_safe=False,
)
