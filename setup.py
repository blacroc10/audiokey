"""
Setup configuration for AudioKey project
"""

from setuptools import setup, find_packages

with open("docs/GETTING_STARTED.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="audiokey",
    version="1.0.0",
    author="AudioKey Team",
    description="Security-Based AI System for Audio-Derived Encryption Keys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/audiokey",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "librosa>=0.10.0",
        "scipy>=1.11.0",
        "pydub>=0.25.0",
        "pycryptodome>=3.19.0",
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "soundfile>=0.12.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "audiokey=app.cli:main",
        ],
    },
)
