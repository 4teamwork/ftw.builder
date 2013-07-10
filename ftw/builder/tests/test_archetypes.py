from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase


class TestArchetypesBuilder(IntegrationTestCase):

    def test_unmarks_creation_flag_with_procjessForm_by_default(self):
        folder = create(Builder('folder'))
        self.assertFalse(folder.checkCreationFlag(),
                         'Creation flag should be False after creation by default.')

    def test_calling_processForm_can_be_disabled(self):
        folder = create(Builder('folder'), processForm=False)
        self.assertTrue(folder.checkCreationFlag(),
                        'Creation flag should be True when disabling processForm')

    def test_object_id_is_chosen_from_title_automatically(self):
        folder1 = create(Builder('folder').titled('Foo'))
        self.assertEqual('foo', folder1.getId())

        folder2 = create(Builder('folder').titled('Foo'))
        self.assertEqual('foo-1', folder2.getId())

    def test_object_id_can_be_set(self):
        folder = create(Builder('folder').with_id('bar'))
        self.assertEqual('bar', folder.getId())


class TestATFolderBuilder(IntegrationTestCase):

    def test_creates_a_folder(self):
        folder = create(Builder('folder'))
        self.assertEquals('Folder', folder.portal_type)


class TestATPageBuilder(IntegrationTestCase):

    def test_Page_builder_creates_a_Document(self):
        page = create(Builder('page'))
        self.assertEquals('Document', page.portal_type)

    def test_alias_Document_also_works_for_creating_documents(self):
        page = create(Builder('document'))
        self.assertEquals('Document', page.portal_type)


class TestATFileBuilder(IntegrationTestCase):

    def test_creates_a_File_object(self):
        file_ = create(Builder('file'))
        self.assertEquals('File', file_.portal_type)

    def test_file_data_can_be_attached(self):
        file_ = create(Builder('file')
                       .attach_file_containing('Data Data', 'data.txt'))

        self.assertEquals(
            {'filename': 'data.txt',
             'data': 'Data Data'},

            {'filename': file_.getFile().filename,
             'data': file_.getFile().data})

    def test_dummy_content_can_be_attached(self):
        file_ = create(Builder('file')
                       .with_dummy_content())

        self.assertEquals(
            {'filename': 'test.doc',
             'data': 'Test data'},

            {'filename': file_.getFile().filename,
             'data': file_.getFile().data})
