from DateTime import DateTime
from datetime import datetime
from ftw.builder import Builder
from ftw.builder import create
from ftw.builder import registry
from ftw.builder.dexterity import DexterityBuilder
from ftw.builder.testing import BUILDER_INTEGRATION_TESTING
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.fti import DexterityFTI
from unittest2 import TestCase
from zope import schema
from zope.component import adapter
from zope.component.globalregistry import getGlobalSiteManager
from zope.component.hooks import getSite
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent


class IFoo(Interface):
    pass


class IBookSchema(Interface):
    title = schema.TextLine(
        title=u'Title',
        required=False)

    chapters = schema.Tuple(
        title=u'Chapters',
        value_type=schema.TextLine(),
        required=False,
        missing_value=())

    author = schema.TextLine(
        title=u'Author',
        required=False,
        default=u'hugo.boss')


alsoProvides(IBookSchema, IFormFieldProvider)


class BookBuilder(DexterityBuilder):
    portal_type = 'Book'


class DexterityBaseTestCase(TestCase):

    layer = BUILDER_INTEGRATION_TESTING

    def setUp(self):
        super(DexterityBaseTestCase, self).setUp()
        self.portal = self.layer['portal']

        # create test user
        pas = self.portal['acl_users']
        pas.source_users.addUser(u'hugo.boss', u'Hugo Boss', 'secret')
        setRoles(self.portal, u'hugo.boss', ['Manager'])
        login(self.portal, u'Hugo Boss')

        # add test fti
        self.fti = DexterityFTI('Book')
        self.fti.schema = 'ftw.builder.tests.test_dexterity.IBookSchema'
        self.fti.behaviors = (
            'plone.app.dexterity.behaviors.metadata.IPublication',
            'plone.app.dexterity.behaviors.metadata.IOwnership')

        self.portal.portal_types._setObject('Book', self.fti)

        # use our own builder registry and register our book builder
        self.old_registry = registry.builder_registry
        registry.builder_registry = registry.Registry()
        registry.builder_registry.register('book', BookBuilder)

    def tearDown(self):
        registry.builder_registry = self.old_registry


class TestDexterityBuilder(DexterityBaseTestCase):

    def test_check_constraints_when_activated(self):
        self.fti.global_allow = False

        with self.assertRaises(ValueError) as cm:
            create(Builder('book')
                         .with_constraints()
                         .having(title=u'Testtitle'))

        self.assertEquals(
            'Disallowed subobject type: Book', str(cm.exception))

    def test_ignore_constraints_by_default(self):
        self.fti.global_allow = False

        create(Builder('book').having(title=u'Testtitle'))

    def test_sets_value_on_schema_fields(self):
        book = create(Builder('book')
                         .having(title=u'Testtitle'))

        self.assertEquals('Testtitle', book.title)

    def test_sets_value_on_behavior_fields(self):
        book = create(Builder('book')
                     .having(title=u'Testtitle',
                             effective=datetime(2013, 1, 1)))

        self.assertEquals(DateTime(2013, 1, 1), book.effective())

    def test_initalizing_fields_with_missing_value(self):
        book = create(Builder('book')
                     .having(title=u'Testtitle'))

        self.assertEquals((), book.chapters)

    def test_sets_default_values_by_default(self):
        book = create(Builder('book')
                     .having(title=u'Testtitle'))

        self.assertEquals(u'hugo.boss', book.author)
        self.assertEquals((u'hugo.boss', ), book.listCreators())

    def test_object_providing_interface(self):
        book = create(Builder('book').providing(IFoo))
        self.assertTrue(IFoo.providedBy(book))


@adapter(IObjectCreatedEvent)
def fake_created_handler(event):
    getSite().fired_events.append(event)


@adapter(IObjectAddedEvent)
def fake_added_handler(event):
    getSite().fired_events.append(event)


class TestEventNotifying(DexterityBaseTestCase):

    def setUp(self):
        super(TestEventNotifying, self).setUp()

        self.portal.fired_events = []
        gsm = getGlobalSiteManager()
        gsm.registerHandler(fake_created_handler)
        gsm.registerHandler(fake_added_handler)

    def tearDown(self):
        super(TestEventNotifying, self).tearDown()
        gsm = getGlobalSiteManager()
        gsm.unregisterHandler(fake_created_handler)
        gsm.unregisterHandler(fake_added_handler)

    def test_notify_events_by_default(self):
        create(Builder('book').having(title=u'Testtitle'))

        events = self.portal.fired_events

        self.assertTrue(IObjectCreatedEvent.providedBy(events[0]))
        self.assertTrue(IObjectAddedEvent.providedBy(events[1]))
        self.assertEquals(
            2, len(events),
            'The expected events (ObjectAddedEvent and ObjectCreatedEvent)'
            'are fired not like expected (%s)' % str(events))
