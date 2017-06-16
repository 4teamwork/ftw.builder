ftw.builder
===========

Create Plone objects in tests with the
`Builder Pattern <http://www.oodesign.com/builder-pattern.html>`_.

The builder pattern simplifies constructing objects.
In tests we often need to create Plone objects, sometimes a single object,
sometimes a whole graph of objects.
Using the builder pattern allows us to do this in a DRY way, so that we do not
repeat this over and over.

.. code:: python

    from ftw.builder import create
    from ftw.builder import Builder

    def test_foo(self):
        folder = create(Builder('folder')
                        .titled('My Folder')
                        .in_state('published'))


.. contents:: Table of Contents

Installation
------------

Add ``ftw.builder`` as (test-) dependency to your package in ``setup.py``:

.. code:: python

    tests_require = [
        'ftw.builder',
        ]

    setup(name='my.package',
          tests_require=tests_require,
          extras_require={'tests': tests_require})


Usage
-----

Setup builder session in your testcase

.. code:: python

    from ftw.builder import session

    class TestPerson(unittest2.TestCase):

        def setUp(self):
            session.current_session = session.factory()

        def tearDown(self):
            session.current_session = None

In plone projects you can use the ``BUILDER_LAYER`` which your testing layer should base on. So the the session management is handled by the ``BUILDER_LAYER``:

.. code:: python

    from ftw.builder.testing import BUILDER_LAYER

    class MyPackageLayer(PloneSandboxLayer):

        defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

Use the builder for creating objects in your tests:

.. code:: python


    from ftw.builder import Builder
    from ftw.builder import create
    from my.package.testing import MY_PACKAGE_INTEGRATION_TESTING
    from unittest2 import TestCase

    class TestMyFeature(TestCase)

        layer = MY_PACKAGE_INTEGRATION_TESTING

        def test_folder_is_well_titled(self):
            folder = create(Builder('folder')
                            .titled('My Folder')
                            .in_state('published'))

            self.assertEquals('My Folder', folder.Title())


Session
~~~~~~~

The ``BuilderSession`` keeps configuration for multiple builders. It is set up
and destroyed by the ``BUILDER_LAYER`` and can be configured or replaced by a
custom session with ``set_builder_session_factory``.

Auto commit
+++++++++++

When having a functional testing layer (``plone.app.testing.FunctionalTesting``)
and doing browser tests it is necessary that the new objects are committed in
the ZODB. When using a ``IntegrationTesting`` on the other hand it is essential
that nothing is comitted, since this would break test isolation.

The session provides the ``auto_commit`` option (dislabed by default), which
commits to the ZODB after creating an object. Since it is disabled by default
you need to enable it in functional test cases.

A default session factory ``functional_session_factory`` that enables the
auto-commit feature is provided:

.. code:: python

    def functional_session_factory():
        sess = BuilderSession()
        sess.auto_commit = True
        return sess


You can use ``set_builder_session_factory`` to replace the default session
factory in functional tests. Make sure to also base your fixture on the
``BUILDER_LAYER`` fixture:

.. code:: python

    from ftw.builder.session import BuilderSession
    from ftw.builder.testing import BUILDER_LAYER
    from ftw.builder.testing import functional_session_factory
    from ftw.builder.testing import set_builder_session_factory
    from plone.app.testing import FunctionalTesting
    from plone.app.testing import IntegrationTesting
    from plone.app.testing import PLONE_FIXTURE
    from plone.app.testing import PloneSandboxLayer


    class MyPackageLayer(PloneSandboxLayer):
        defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    MY_PACKAGE_FIXTURE = MyPackageLayer()

    MY_PACKAGE_INTEGRATION_TESTING = IntegrationTesting(
        bases=(MY_PACKAGE_FIXTURE, ),
        name="MyPackage:Integration")

    MY_PACKAGE_FUNCTIONAL_TESTING = FunctionalTesting(
        bases=(MY_PACKAGE_FIXTURE,
               set_builder_session_factory(functional_session_factory)),
        name="MyPackage:Integration")



Plone object builders
~~~~~~~~~~~~~~~~~~~~~

For creating Plone objects (Archetypes or Dexterity) there are some methods for
setting basic options:

- ``within(container)`` - tell the builder where to create the object
- ``titled(title)`` - name the object
- ``having(field=value)`` - set the value of any field on the object
- ``in_state(review_state)`` - set the object into any review state of the workflow
  configured for this type
- ``providing(interface1, interface2, ...)`` - let the object provide interfaces
- ``with_property(name, value, value_type='string')`` - set a property



Default builders
~~~~~~~~~~~~~~~~

The ``ftw.builder`` ships with some builders for some default Plone
content types, but the idea is that you can easily craft your own builders for
your types or extend existing builders.

The built-in builders are:

- ``folder`` - creates an folder
- ``page`` (or ``document``) - creates an page (alias Document)
- ``file`` - creates a File
- ``image`` - creates an Image
- ``collection`` (or ``topic``) - creates a collection

There are two builder implementations, an Archetypes (Plone < 5) and a
Dexterity (Plone >= 5) implementation.
When using ``plone.app.contenttypes`` with Plone 4, you may want to switch
the builders to dexterity:

.. code:: python

    from ftw.builder.content import at_content_builders_registered
    from ftw.builder.content import dx_content_builders_registered
    from ftw.builder.content import register_at_content_builders
    from ftw.builder.content import register_dx_content_builders


    # permanently
    register_dx_content_builders(force=True)

    # temporary
    with dx_content_builders_registered():
        # do stuff


Attaching files
+++++++++++++++

The default Archetypes file builder let's you attach a file or create the file
with dummy content. The archetypes image builder provides a real image (1x1 px GIF):

.. code:: python

    file1 = create(Builder('file')
                   .with_dummy_content())

    file2 = create(Builder('file')
                   .attach_file_containing('File content', name='filename.pdf')

    image1 = create(Builder('image')
                   .with_dummy_content())


Users builder
+++++++++++++

There is a "user" builder registered by default.

By default the user is named John Doe:

.. code:: python

    john = create(Builder('user'))
    john.getId() == "john.doe"
    john.getProperty('fullname') == "Doe John"
    john.getProperty('email') == "john@doe.com"
    john.getRoles() == ['Member', 'Authenticated']

Changing the name of the user changes also the userid and the email address.
You can also configure all the other necessary things:

.. code:: python

    folder = create(Builder('folder'))
    hugo = create(Builder('user')
                  .named('Hugo', 'Boss')
                  .with_roles('Contributor')
                  .with_roles('Editor', on=folder))

    hugo.getId() == 'hugo.boss'
    hugo.getProperty('fullname') == 'Boss Hugo'
    hugo.getProperty('email') == 'hugo@boss.com'
    hugo.getRoles() == ['Contributor', 'Authenticated']
    hugo.getRolesInContext(folder) == ['Contributor', 'Authenticated', 'Editor']


Groups builder
++++++++++++++

The "group" bilder helps you create groups:

.. code:: python

    folder = create(Builder('folder'))
    user = create(Builder('user'))
    group = create(Builder('group')
                   .titled('Administrators')
                   .with_roles('Site Administrator')
                   .with_roles('Editor', on=folder)
                   .with_members(user))



Creating new builders
~~~~~~~~~~~~~~~~~~~~~

The idea is that you create your own builders for your application.
This might be builders creating a single Plone object (Archetypes or Dexterity)
or builders creating a set of objects using other builders.


Creating python builders
++++++++++++++++++++++++

Define a simpe builder class for your python object and register them in the builder registry

.. code:: python

    class PersonBuilder(object):

        def __init__(self, session):
            self.session = session
            self.children_names = []
            self.arguments = {}

        def of_age(self):
            self.arguments['age'] = 18
            return self

        def with_children(self, children_names):
            self.children_names = children_names
            return self

        def having(self, **kwargs):
            self.arguments.update(kwargs)
            return self

        def create(self, **kwargs):
            person = Person(
                self.arguments.get('name'),
                self.arguments.get('age'))

            for name in self.children_names:
                person.add_child(
                    create(Builder('person').having(name=name, age=5))
                )

            return person

    builder_registry.register('person', PersonBuilder)


Creating Archetypes builders
++++++++++++++++++++++++++++

Use the ``ArchetypesBuilder`` base class for creating new Archetypes builders.
Set the ``portal_type`` and your own methods.

.. code:: python

    from ftw.builder.archetypes import ArchetypesBuilder
    from ftw.builder import builder_registry

    class NewsBuilder(ArchetypesBuilder):
        portal_type = 'News Item'

        def containing(self, text):
            self.arguments['text'] = text
            return self

    builder_registry.register('news', NewsBuilder)


Creating Dexterity builders
+++++++++++++++++++++++++++

Use the ``DexterityBuilder`` base class for creating new Dexterity builders.
Set the ``portal_type`` and your own methods.

.. code:: python

    from ftw.builder.dexterity import DexterityBuilder
    from ftw.builder import builder_registry

    class DocumentBuilder(DexterityBuilder):
        portal_type = 'dexterity.document'

        def with_dummy_content(self):
            self.arguments["file"] = NamedBlobFile(data='Test data', filename='test.doc')
            return self


Events
++++++

You can do things before and after creating the object:

.. code:: python

    class MyBuilder(ArchetypesBuilder):

        def before_create(self):
            super(NewsBuilder, self).before_create()
            do_something()

        def after_create(self):
            do_something()
            super(NewsBuilder, self).after_create()


Overriding existing builders
++++++++++++++++++++++++++++

Sometimes it is necessary to override an existing builder.
For re-registering an existing builder you can use
the ``force`` flag:

.. code:: python

    builder_registry.register('file', CustomFileBuilder, force=True)


Ticking frozen clock forward on create
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With ``ftw.testing`` it is possible to
`freeze the time <https://github.com/4teamwork/ftw.testing#freezing-datetime-now>`_.

When freezing the time and creating multiple objects, they will all end up with
the same creation date. This can cause an inconsistent sorting order.

In order to solve this problem, ``ftw.builder`` provides a ``ticking_creator``,
which moves the clock forward every time an object is created.
This means we have distinct, consistent creation dates.

Usage example:

.. code:: python

    from datetime import datetime
    from ftw.builder import Builder
    from ftw.builder import ticking_creator
    from ftw.testing import freeze

    with freeze(datetime(2010, 1, 1)) as clock:
        create = ticking_creator(clock, days=1)
        self.assertEquals(DateTime(2010, 1, 1),
                          create(Builder('folder')).created())
        self.assertEquals(DateTime(2010, 1, 2),
                          create(Builder('folder')).created())
        self.assertEquals(DateTime(2010, 1, 3),
                          create(Builder('folder')).created())


It is convenient to install the ticking creator globally, so if builder
creates objects with another builder, it also ticks the clock for the
nested builder call.
This can be achieved by using the ticking creator as context manager:

.. code:: python

    from datetime import datetime
    from ftw.builder import Builder
    from ftw.builder import create
    from ftw.builder import ticking_creator
    from ftw.testing import freeze

    with freeze(datetime(2010, 1, 1)) as clock:
        with ticking_creator(clock, days=1):
            self.assertEquals(DateTime(2010, 1, 1),
                              create(Builder('folder')).created())
            self.assertEquals(DateTime(2010, 1, 2),
                              create(Builder('folder')).created())
            self.assertEquals(DateTime(2010, 1, 3),
                              create(Builder('folder')).created())



Other builders
--------------

Python package builder
~~~~~~~~~~~~~~~~~~~~~~

The Python package builder builds a python package on the file system.

- creates a setup.py
- namespace packages are supported
- builds the egg-info
- creates a configure.zcml on demand

Example:

.. code:: python

    >>> import tempfile
    >>> tempdir = tempfile.mkdtemp()

    >>> package = create(Builder('python package')
    ...                  .at_path(tempdir)
    ...                  .named('my.package')
    ...
    ...                  .with_root_directory('docs')
    ...                  .with_root_file('docs/HISTORY.txt', 'CHANGELOG...')
    ...                  .with_file('resources/print.css', 'body {}', makedirs=True)
    ...
    ...                  .with_subpackage(Builder('subpackage')
    ...                                   .named('browser')))
    >>>
    >>> with package.imported() as module:
    ...     print module
    ...
    <module 'my.package' from '...../tmpcAZhM2/my/package/__init__.py'>

It is also possible to create / load ZCML, all you need is a stacked configuration context.
Plone's testing layers provide a configuration context, but be aware that the component
registry is not isolated.
You may want to isolate the component registry with
`plone.testing.zca.pushGlobalRegistry <https://github.com/plone/plone.testing/blob/master/src/plone/testing/zca.py#L54>`_.

.. code:: python

      package = create(
          Builder('python package')
          .named('the.package')
          .at_path(self.layer['temp_directory'])

          .with_subpackage(
              Builder('subpackage')
              .named('browser')

              .with_file('hello_world.pt', '"Hello World"')
              .with_zcml_node('browser:page',
                              **{'name': 'hello-world.json',
                                 'template': 'hello_world.pt',
                                 'permission': 'zope2.View',
                                 'for': '*'})))

      with package.zcml_loaded(self.layer['configurationContext']):
          self.assertEqual('"Hello World"',
                           self.layer['portal'].restrictedTraverse('hello-world.json')())


Generic Setup profile builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "genericsetup profile" builder helps building a profile within a python package:

.. code:: python

    create(Builder('python package')
           .named('the.package')
           .at_path(self.layer['temp_directory'])

           .with_profile(Builder('genericsetup profile')
                         .with_fs_version('3109')
                         .with_dependencies('collective.foo:default')
                         .with_file('types/MyType.xml', '<object></object>',
                                    makedirs=True)))


Plone upgrade step builder
~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds a Generic Setup upgrade step for a package:

.. code:: python

    create(Builder('python package')
           .named('the.package')
           .at_path(self.layer['temp_directory'])

           .with_profile(Builder('genericsetup profile')
                         .with_upgrade(Builder('plone upgrade step')
                                       .upgrading('1000', '1001')
                                       .titled('Add some actions...')
                                       .with_description('Some details...'))))



ZCML file builder
~~~~~~~~~~~~~~~~~

The ZCML builder builds a ZCML file:

.. code:: python

    create(Builder('zcml')
           .at_path('/path/to/my/package/configure.zcml')
           .with_i18n_domain('my.package')

           .include('.browser')
           .include('Products.GenericSetup', file='meta.zcml')
           .include(file='profiles.zcml')

           .with_node('i18n:registerTranslations', directory='locales'))


Portlet builder
~~~~~~~~~~~~~~~

The ``ftw.builder`` ships with a few builders for Plone portlets, but the
idea is that you can easily craft your own builders for your portlets or
extend existing builders.

Example:

.. code:: python

    from ftw.builder import builder_registry
    from ftw.builder.portlets import PlonePortletBuilder
    from my.package.portlets import my_portlet

    class MyPortletBuilder(PlonePortletBuilder):
        assignment_class = my_portlet.Assignment

    builder_registry.register('my portlet', MyPortletBuilder)


The built-in builders are:

- ``static portlet`` - creates a static portlet
- ``navigation portlet`` - creates a navigation portlet


Development / Tests
-------------------

.. code:: bash

    $ git clone https://github.com/4teamwork/ftw.builder.git
    $ cd ftw.builder
    $ ln -s development.cfg buildout.cfg
    $ python2.7 bootstrap.py
    $ ./bin/buildout
    $ ./bin/test


Links
-----

- Github: https://github.com/4teamwork/ftw.builder
- Issues: https://github.com/4teamwork/ftw.builder/issues
- Pypi: http://pypi.python.org/pypi/ftw.builder
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.builder


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.builder`` is licensed under GNU General Public License, version 2.
