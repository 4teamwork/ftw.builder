from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase
from zope.interface import Interface


class IFoo(Interface):
    pass


class TestArchetypesBuilder(IntegrationTestCase):

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

    def test_object_id_is_chosen_from_title_automatically(self):
        folder1 = create(Builder('folder').titled('Foo'))
        self.assertEqual('foo', folder1.getId())

        folder2 = create(Builder('folder').titled('Foo'))
        self.assertEqual('foo-1', folder2.getId())

    def test_object_id_can_be_set(self):
        folder = create(Builder('folder').with_id('bar'))
        self.assertEqual('bar', folder.getId())

    def test_object_providing_interface(self):
        folder = create(Builder('folder').providing(IFoo))
        self.assertTrue(IFoo.providedBy(folder))

    def test_object_providing_interface_updates_catalog(self):
        folder = create(Builder('folder').providing(IFoo))

        catalog = getToolByName(folder, 'portal_catalog')
        rid = catalog.getrid('/'.join(folder.getPhysicalPath()))
        index_data = catalog.getIndexDataForRID(rid)

        self.assertIn('ftw.builder.tests.test_archetypes.IFoo',
                      index_data['object_provides'])


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


class TestATImageBuilder(IntegrationTestCase):

    def test_creates_an_image_object(self):
        image = create(Builder('image'))
        self.assertEquals('Image', image.portal_type)

    def test_setting_image_data(self):
        image = create(Builder('image')
                       .attach_file_containing('IMG', 'foo.png'))

        self.assertEquals(
            {'filename': 'foo.png',
             'data': 'IMG'},

            {'filename': image.getFile().filename,
             'data': image.getFile().data})

    def test_dummy_content_can_be_attached(self):
        image = create(Builder('image')
                       .with_dummy_content())

        self.assertEquals(
            {'filename': 'image.gif',
             'data': 'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00'
                     '\x00!\xf9\x04\x04\x00\x00\x00\x00,\x00\x00\x00\x00\x01'
                     '\x00\x01\x00\x00\x02\x02D\x01\x00;'},

            {'filename': image.getFile().filename,
             'data': image.getFile().data})

    def test_dummy_content_is_a_real_image(self):
        image = create(Builder('image')
                       .with_dummy_content())

        scale = image.restrictedTraverse('@@images')

        self.assertIsNotNone(scale.scale('image',
                                         width=100,
                                         height=100,
                                         direction='down'),
                             'Could no scale the image.')
