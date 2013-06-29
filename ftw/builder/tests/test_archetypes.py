from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase


class TestArchetypesBuilder(IntegrationTestCase):

    def test_unmarks_creation_flag_with_procjessForm_by_default(self):
        folder = create(Builder('Folder'))
        self.assertFalse(folder.checkCreationFlag(),
                         'Creation flag should be False after creation by default.')

    def test_calling_processForm_can_be_disabled(self):
        folder = create(Builder('Folder'), processForm=False)
        self.assertTrue(folder.checkCreationFlag(),
                        'Creation flag should be True when disabling processForm')

    def test_object_id_is_chosen_from_title_automatically(self):
        folder1 = create(Builder('Folder').titled('Foo'))
        self.assertEqual('foo', folder1.getId())

        folder2 = create(Builder('Folder').titled('Foo'))
        self.assertEqual('foo-1', folder2.getId())

    def test_object_id_can_be_set(self):
        folder = create(Builder('Folder').with_id('bar'))
        self.assertEqual('bar', folder.getId())


class TestATFolderBuilder(IntegrationTestCase):

    def test_creates_a_folder(self):
        folder = create(Builder('Folder'))
        self.assertEquals('Folder', folder.portal_type)
