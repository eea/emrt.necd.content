from setuptools import setup, find_packages, Extension

from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError
from distutils.errors import DistutilsExecError
from distutils.errors import DistutilsPlatformError
import os

VERSION = '2.3.7'


class BuildFailed(Exception):
    pass


# copied from https://github.com/simplejson/simplejson/blob/master/setup.py
class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError, DistutilsPlatformError):
            raise BuildFailed()


def run_setup(build_ext=True):
    if build_ext:
        kw = dict(
            ext_modules=[
                Extension(
                    'emrt.necd.content.browser.flatten_json',
                    sources=[os.path.join(
                        'emrt', 'necd', 'content', 'browser',
                        'flatten_json.c'
                    )]
                ),
            ],
            cmdclass=dict(build_ext=ve_build_ext),
        )
    else:
        kw = {}

    setup(
        name='emrt.necd.content',
        version=VERSION,
        description="Content-types for EMRT-NECD Review Tool",
        long_description=(
            open("README.txt").read() + "\n" +
            open(os.path.join("docs", "HISTORY.txt")).read()
        ),
        # Get more strings from
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            "Framework :: Plone",
            "Programming Language :: Python",
            "Topic :: Software Development :: Libraries :: Python Modules",
            ],
        keywords='',
        author='Mikel Larreategi',
        author_email='mlarreategi@codesyntax.com',
        url='https://github.com/eea/emrt.necd.content/',
        license='GPL',
        packages=find_packages(exclude=['ez_setup']),
        namespace_packages=['emrt', 'emrt.necd'],
        include_package_data=True,
        zip_safe=False,
        install_requires=[
            'setuptools',
            'futures',
            'plone.app.dexterity [relations]',
            'plone.namedfile [blobs]',
            'collective.z3cform.datagridfield',
            'plone.api',
            'Products.ATVocabularyManager',
            'plone.app.versioningbehavior',
            'plone.app.workflowmanager',
            'plone.app.ldap',
            'cs.htmlmailer',
            'collective.deletepermission',
            'tablib',
            'python-docx==0.8.5',
            'zc.dict',
            'collective.monkeypatcher',
            'openpyxl',
            'five.pt',
            'simplejson',
        ],
        entry_points="""
        # -*- Entry points: -*-
        [z3c.autoinclude.plugin]
        target = plone
        """,
        **kw
        )


try:
    run_setup()
except BuildFailed:
    print('*' * 75)
    print('WARNING: Failed to build C extensions! Check GCC!')
    print('*' * 75)
    run_setup(False)
