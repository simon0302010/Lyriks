from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lyriks",
    version="0.2.0",
    author="simon0302010",
    author_email="simon0302010@gmail.com",
    description="Automated lyrics video generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/simon0302010/Lyriks",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11,<3.12",
    install_requires=[
        "click",
        "demucs",
        "langdetect",
        "onnxruntime",
        "openai-whisper",
        "soundfile",
        "torch",
        "torchaudio",
        "whisper-timestamped",
        "moviepy",
        "iso639-lang",
        "matplotlib",
    ],
    license="GPL-3.0",
)