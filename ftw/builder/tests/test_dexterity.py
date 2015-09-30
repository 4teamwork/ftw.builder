from datetime import datetime
from DateTime import DateTime
from ftw.builder import Builder
from ftw.builder import create
from ftw.builder import registry
from ftw.builder.dexterity import DexterityBuilder
from ftw.builder.testing import BUILDER_FUNCTIONAL_TESTING
from ftw.builder.tests.test_builder import obj2brain
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.fti import DexterityFTI
from plone.formwidget.contenttree import ObjPathSourceBinder
from Products.CMFPlone.utils import getFSVersionTuple
from unittest2 import skipIf
from unittest2 import TestCase
from z3c.relationfield.relation import RelationValue
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.component import adapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.intid.interfaces import IIntIds
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
        default=u'test_user_1_')

    relation_choice = RelationChoice(
        title=u'Relation-Choice',
        source=ObjPathSourceBinder(),
        required=False,
    )

    relation_list = RelationList(
        title=u'Relation-List',
        default=[],
        value_type=RelationChoice(
            title=u"Relation-List",
            source=ObjPathSourceBinder(),
            ),
        required=False,
        )

alsoProvides(IBookSchema, IFormFieldProvider)


class IAnnotationStored(Interface):
    some_field = schema.TextLine(title=u"Some field", default=u"default value")

alsoProvides(IAnnotationStored, IFormFieldProvider)


class BookBuilder(DexterityBuilder):
    portal_type = 'Book'


class DexterityBaseTestCase(TestCase):

    layer = BUILDER_FUNCTIONAL_TESTING

    def setUp(self):
        super(DexterityBaseTestCase, self).setUp()
        self.portal = self.layer['portal']

        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        login(self.portal, TEST_USER_NAME)

        # add test fti
        self.fti = DexterityFTI('Book')
        self.fti.schema = 'ftw.builder.tests.test_dexterity.IBookSchema'
        self.fti.behaviors = (
            'plone.app.dexterity.behaviors.metadata.IPublication',
            'plone.app.dexterity.behaviors.metadata.IOwnership',
            'ftw.builder.tests.test_dexterity.IAnnotationStored',)

        self.portal.portal_types._setObject('Book', self.fti)

        # use our own builder registry and register our book builder
        self.old_registry = registry.builder_registry
        registry.builder_registry = registry.Registry()
        registry.builder_registry.register('book', BookBuilder)

        self.intids = getUtility(IIntIds)

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

        self.assertEquals(DateTime('2013-01-01T00:00:00+01:00'),
                          DateTime(book.EffectiveDate()).toZone('GMT+1'))

    def test_initalizing_fields_with_missing_value(self):
        book = create(Builder('book')
                     .having(title=u'Testtitle'))

        self.assertEquals((), book.chapters)

    def test_sets_default_values_by_default(self):
        book = create(Builder('book')
                     .having(title=u'Testtitle'))

        self.assertEquals(u'test_user_1_', book.author)
        self.assertEquals((u'test_user_1_', ), book.listCreators())

    def test_object_providing_interface(self):
        book = create(Builder('book').providing(IFoo))
        self.assertTrue(IFoo.providedBy(book))

    def test_with_creation_date_updates_obj_and_brain(self):
        creation_date = DateTime(2011, 2, 3, 5, 7, 11)

        book = create(Builder('book').with_creation_date(creation_date))

        self.assertEquals(creation_date, book.created())
        self.assertEquals(creation_date, obj2brain(book).created)

    def test_initializes_relation_choice_relation_value_from_object(self):
        related = create(Builder('book'))

        book = create(Builder('book').having(relation_choice=related))
        self.assertTrue(isinstance(book.relation_choice, RelationValue))
        self.assertEqual(related, book.relation_choice.to_object)

    def test_preserves_relation_choice_relation_value_instance(self):
        related = create(Builder('book'))

        book = create(Builder('book').having(
            relation_choice=RelationValue(self.intids.getId(related))))
        self.assertTrue(isinstance(book.relation_choice, RelationValue))
        self.assertEqual(related, book.relation_choice.to_object)

    def test_initializes_relation_list_relation_values_from_object_list(self):
        related = create(Builder('book'))

        book = create(Builder('book').having(relation_list=[related]))
        self.assertTrue(isinstance(book.relation_list[0], RelationValue))
        self.assertEqual(related, book.relation_list[0].to_object)

    def test_preserves_relation_list_relation_value_instances(self):
        related = create(Builder('book'))

        book = create(Builder('book').having(
            relation_list=[RelationValue(self.intids.getId(related))]))
        self.assertTrue(isinstance(book.relation_list[0], RelationValue))
        self.assertEqual(related, book.relation_list[0].to_object)

    @skipIf(getFSVersionTuple() >= (5,),
            'default value lookup is broken in plone5 and ignores annotation '
            'storage')
    def test_stores_annotation_storage_fields_correctly(self):
        book = create(Builder('book').having(some_field=u'foo'))

        self.assertFalse(hasattr(book, 'some_field'))
        self.assertEqual(u'foo', IAnnotationStored(book).some_field)

    @skipIf(getFSVersionTuple() >= (5,),
            'default value lookup is broken in plone5 and ignores annotation '
            'storage')
    def test_initializes_annotation_storage_defaults(self):
        book = create(Builder('book'))

        self.assertFalse(hasattr(book, 'some_field'))
        self.assertEqual(u"default value", IAnnotationStored(book).some_field)


@adapter(IObjectCreatedEvent)
def track_created_events(event):
    getSite().fired_events.append(event)


@adapter(IObjectAddedEvent)
def track_added_events(event):
    getSite().fired_events.append(event)


class TestEventNotifying(DexterityBaseTestCase):

    def setUp(self):
        super(TestEventNotifying, self).setUp()
        self.portal.fired_events = []
        self.portal.getSiteManager().registerHandler(track_created_events)
        self.portal.getSiteManager().registerHandler(track_added_events)

    def test_notify_events_by_default(self):
        create(Builder('book').having(title=u'Testtitle'))
        created_event, added_event = self.portal.fired_events
        self.assertTrue(IObjectCreatedEvent.providedBy(created_event))
        self.assertTrue(IObjectAddedEvent.providedBy(added_event))
