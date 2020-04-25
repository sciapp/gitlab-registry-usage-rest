import os
import runpy
from setuptools import setup, find_packages


def get_version_from_pyfile(version_file="gitlab_registry_usage_rest/_version.py"):
    file_globals = runpy.run_path(version_file)
    return file_globals["__version__"]


def get_install_requires_from_requirements(requirements_filename="requirements.txt"):
    try:
        with open(requirements_filename, "r", encoding="utf-8") as requirements_file:
            requirements = requirements_file.readlines()
    except OSError:
        import logging

        logging.warning("Could not read the requirements file.")
    return requirements


def get_long_description_from_readme(readme_filename="README.md"):
    long_description = None
    if os.path.isfile(readme_filename):
        with open(readme_filename, "r", encoding="utf-8") as readme_file:
            long_description = readme_file.read()
    return long_description


version = get_version_from_pyfile()
long_description = get_long_description_from_readme()
install_requires = get_install_requires_from_requirements()

setup(
    name="gitlab-registry-usage-rest",
    version=version,
    packages=find_packages(),
    python_requires="~=3.3",
    install_requires=install_requires,
    entry_points={"console_scripts": ["gitlab-registry-usage-rest = gitlab_registry_usage_rest.app:main"]},
    author="Ingo Heimbach",
    author_email="i.heimbach@fz-juelich.de",
    description="A restful web service for querying the repository sizes of a GitLab registry.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/sciapp/gitlab-registry-usage-rest",
    keywords=["Git", "GitLab", "Docker", "Registry", "disk capacity", "RESTful"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP",
    ],
)
