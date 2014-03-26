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



Default builders
~~~~~~~~~~~~~~~~

The ``ftw.builder`` ships with some builders for some default Plone (Archetypes)
content types, but the idea is that you can easily craft your own builders for
your types or extend existing builders.

The built-in builders are:

- ``folder`` - creates an Archetypes folder
- ``page`` (or ``Document``) - creates an Archetypes page (alias Document)
- ``file`` - creates a File
- ``image`` - creates an Archetypes Image



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

- Main github project repository: https://github.com/4teamwork/ftw.builder
- Issue tracker: https://github.com/4teamwork/ftw.builder/issues
- Package on pypi: http://pypi.python.org/pypi/ftw.builder
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.builder


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.builder`` is licensed under GNU General Public License, version 2.

.. image:: https://cruel-carlota.pagodabox.com/0fd497302fbfecd53b8e5d608e3b7900
   :alt: githalytics.com
   :target: http://githalytics.com/4teamwork/ftw.builder
