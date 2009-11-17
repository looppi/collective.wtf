from setuptools import setup, find_packages
import os

version = '1.0b8'

setup(name='collective.wtf',
      version=version,
      description="GenericSetup importer and exporter for workflow definitions that uses CSV instead of XML",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone workflow genericsetup',
      author='Martin Aspeli',
      author_email='optilude@gmail.com',
      url='http://plone.org',
      license='LGPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zope.interface',
          'zope.component',
          'Products.CMFCore',
          'Products.DCWorkflow',
          'Products.GenericSetup',
          'plone.memoize',
          
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
