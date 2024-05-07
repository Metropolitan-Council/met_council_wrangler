from setuptools import setup

classifiers = [
    "Development Status :: 1 - Planning",
    "License :: OSI Approved :: Apache Software License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.7",
]

with open("README.md") as f:
    long_description = f.read()

with open("requirements.docs.txt") as f:
    docs_requirements = f.readlines()
install_requires = [r.strip() for r in docs_requirements]

with open("requirements.txt") as f:
    requirements = f.readlines()
install_requires_dev = [r.strip() for r in requirements]

install_requires = install_requires + install_requires_dev

setup(
    name="met_council_wrangler",
    version="0.0.1",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Metropolitan-Council/met_council_wrangler",
    license="Apache 2",
    platforms="any",
    packages=["met_council_wrangler"],
    include_package_data=True,
    install_requires=install_requires,
)
