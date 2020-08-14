import os.path

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
about = {}  # type: dict
with open(os.path.join(here, "appconfig_helper", "version.py"), "r") as f:
    exec(f.read(), about)

with open(os.path.join(here, "README.md"), "r") as f:
    long_description = f.read()

setup(
    name="aws_appconfig_helper",
    version=about["VERSION"],
    description="AWS AppConfig Helper",
    author="Amazon Web Services",
    packages=find_packages(),
    install_requires=["boto3 >= 1.10.27", "pyyaml"],
    python_requires=">=3.6",
    license="OSI Approved (Apache-2.0)",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Typing :: Typed",
    ],
)
