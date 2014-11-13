from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase
from Products.CMFPlone.utils import getFSVersionTuple
from unittest2 import skipIf


@skipIf(getFSVersionTuple() >= (5,),
        'archetypes is no longer installed in Plone >= 5')
class TestArchetypesBuilder(IntegrationTestCase):

    def test_object_id_can_be_set(self):
        folder = create(Builder('folder').with_id('bar'))
        self.assertEqual('bar', folder.getId())

    def test_unmarks_creation_flag_with_procjessForm_by_default(self):
        folder = create(Builder('folder'))
        self.assertFalse(
            folder.checkCreationFlag(),
            'Creation flag should be False after creation by default.')

    def test_calling_processForm_can_be_disabled(self):
        folder = create(Builder('folder'), processForm=False)
        self.assertTrue(
            folder.checkCreationFlag(),
            'Creation flag should be True when disabling processForm')
