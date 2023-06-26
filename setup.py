import os

from setuptools import find_packages
from setuptools import setup

VERSION = "3.dev0"


setup(
    name="emrt.necd.content",
    version=VERSION,
    description="Content-types for EMRT-NECD Review Tool",
    long_description=(
        open("README.txt").read()
        + "\n"
        + open(os.path.join("docs", "HISTORY.txt")).read()
    ),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="",
    author="Mikel Larreategi",
    author_email="mlarreategi@codesyntax.com",
    url="https://github.com/eea/emrt.necd.content/",
    license="GPL",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=["emrt", "emrt.necd"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "collective.z3cform.datagridfield",
        "plone.formwidget.multifile",
        "pas.plugins.ldap",
        "cs.htmlmailer",
        "collective.deletepermission",
        "tablib",
        "python-docx",
        "collective.monkeypatcher",
        "openpyxl",
        # "eea.cache",
        "pylibmc",
    ],
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
