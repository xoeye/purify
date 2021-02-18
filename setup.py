"""Setup for purify"""
# type: ignore
from setuptools import setup, find_packages

PKG_NAME = "purify"
about = {}  # type: ignore
exec(open(f"{PKG_NAME}/__about__.py").read(), about)  # pylint: disable=exec-used

with open("README.md") as fh:
    long_description = fh.read()

setup(
    name=PKG_NAME,
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__author_email__"],
    url="https://github.com/xoeye/purify",
    description="Pythonic object-mutator transforms as pure functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={"": ["py.typed"]},
    python_requires=">=3.7",
    # it is important to keep these install_requires basically in sync with the Pipfile as well.
)
