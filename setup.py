import os
from setuptools import setup, find_packages


version = '1.6.2'

tests_require = [
    'Acquisition',
    'plone.app.testing',
    'unittest2',
    'zope.configuration',
    'plone.api',
    ]


setup(name='ftw.builder',
      version=version,
      description='Builder pattern for creating Plone objects in tests',

      long_description=open('README.rst').read() + '\n' + \
          open(os.path.join('docs', 'HISTORY.txt')).read(),

      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Framework :: Plone :: 5.0',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

      keywords='ftw builder plone',
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.builder',

      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw', ],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
        'Products.CMFPlone',
        'lxml',
        'path.py',
        'setuptools',
        'zope.component',
        'zope.container',
        ],

      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      )
