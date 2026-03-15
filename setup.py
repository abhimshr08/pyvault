from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyvault",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A secure command-line password manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pyvault",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "cryptography>=3.4.0",
        "SQLAlchemy>=1.4.0",
    ],
    entry_points={
        "console_scripts": [
            "pyvault=pyvault.cli:cli",
        ],
    },
    extras_require={
        "dev": ["pytest>=6.2.0"],
    },
)