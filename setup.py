import setuptools
import os

if "VERSION" in os.environ:
    version = os.environ["VERSION"]
else:
    version = "1.0.0.PRE"

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="clixon-pyapi",
    version=version,
    author="Kristofer Hallin, Olof Hagsand",
    author_email="clixon-pyapi@8n1.se",
    description="Clixon Python API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clicon/clixon-pyapi",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License"
        "Operating System :: OS Independent",
    ],
    license="Apache-2.0",
    python_requires='>=3.11',
    scripts=["clixon_server.py"],
)
