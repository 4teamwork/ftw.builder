import os
from setuptools import setup, find_packages


version = '1.12.1.dev0'

tests_require = [
    'Acquisition',
    'ftw.testbrowser',
    'ftw.testing',
    'plone.api',
    'plone.app.dexterity[relations]',
    'plone.app.testing',
    'plone.formwidget.contenttree',
    'zope.configuration',
    ]


setup(name='ftw.builder',
      version=version,
      description='Builder pattern for creating Plone objects in tests',

      long_description=open('README.rst').read() + '\n' + \
          open(os.path.join('docs', 'HISTORY.txt')).read(),

      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Framework :: Plone :: 5.1',
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
          'Acquisition',
          'Plone',
          'Products.CMFCore',
          'Products.CMFPlone',
          'lxml',
          'path.py',
          'plone.app.dexterity',
          'setuptools',
          'transaction',
          'z3c.form',
          'z3c.relationfield',
          'zope.component',
          'zope.configuration',
          'zope.container',
          'zope.event',
          'zope.interface',
          'zope.intid',
          'zope.lifecycleevent',
          'zope.schema',
      ],

      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      )
