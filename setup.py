import os.path

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
about = {}  # type: dict
with open(os.path.join(here, "appconfig_helper", "version.py"), "r") as f:
    exec(f.read(), about)

with open(os.path.join(here, "README.md"), "r") as f:
    long_description = f.read()

setup(
    name="sample-helper-aws-appconfig",
    version=about["VERSION"],
    description="Sample helper library for AWS AppConfig",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Amazon Web Services",
    maintainer="James Seward",
    maintainer_email="sewardjm@amazon.co.uk",
    url="https://github.com/aws-samples/sample-python-helper-aws-appconfig",
    keywords=["aws", "appconfig"],
    packages=find_packages(),
    install_requires=["boto3 >= 1.10.27", "pyyaml"],
    python_requires=">=3.6",
    license="OSI Approved (Apache-2.0)",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Typing :: Typed",
    ],
)
