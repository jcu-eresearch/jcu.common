from setuptools import setup, find_packages
import os

version = '0.1'

long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.txt').read()
    + '\n' +
    open('CHANGES.txt').read()
    + '\n')

setup(name='jcu.common',
      version=version,
      description="Common utilities for Pyramid applications at JCU",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='pyramid wsgi who auth',
      author='David Beitey',
      author_email='eresearch@jcu.edu.au',
      url='http://eresearch.jcu.edu.au/',
      license='gpl',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      extras_require={
          'auth': ['pyramid',
                   'pyramid_who',
                   'repoze.who.plugins.cas'],
          'forms': ['deform'],
          'static': ['fanstatic'],
      },
      setup_requires=[
          'setuptools-git',
      ],
      entry_points="""
      [fanstatic.libraries]
      jcu_common = jcu.common.resources:library

      # -*- Entry points: -*-
      """,
      )
