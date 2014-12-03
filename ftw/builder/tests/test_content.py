from ftw.builder import Builder
from ftw.builder import create
from ftw.builder import HAS_DEXTERITY
from ftw.builder.tests import IntegrationTestCase
from operator import methodcaller
from Products.CMFCore.utils import getToolByName
from zope.interface import Interface

if HAS_DEXTERITY:
    from plone.dexterity.interfaces import IDexterityContent
    from plone.rfc822.interfaces import IPrimaryFieldInfo


class IFoo(Interface):
    pass


def get_file(obj):
    if HAS_DEXTERITY and IDexterityContent.providedBy(obj):
        return IPrimaryFieldInfo(obj).value
    else:
        return obj.getFile()


class TestContentBuilder(IntegrationTestCase):

    def test_object_id_is_chosen_from_title_automatically(self):
        folder1 = create(Builder('folder').titled(u'Foo'))
        self.assertEqual('foo', folder1.getId())

        folder2 = create(Builder('folder').titled(u'Foo'))
        self.assertEqual('foo-1', folder2.getId())

    def test_object_providing_interface(self):
        folder = create(Builder('folder').providing(IFoo))
        self.assertTrue(IFoo.providedBy(folder))

    def test_object_providing_interface_updates_catalog(self):
        folder = create(Builder('folder').providing(IFoo))

        catalog = getToolByName(folder, 'portal_catalog')
        rid = catalog.getrid('/'.join(folder.getPhysicalPath()))
        index_data = catalog.getIndexDataForRID(rid)

        self.assertIn('ftw.builder.tests.test_content.IFoo',
                      index_data['object_provides'])


class TestFolderBuilder(IntegrationTestCase):

    def test_creates_a_folder(self):
        folder = create(Builder('folder'))
        self.assertEquals('Folder', folder.portal_type)


class TestPageBuilder(IntegrationTestCase):

    def test_Page_builder_creates_a_Document(self):
        page = create(Builder('page'))
        self.assertEquals('Document', page.portal_type)

    def test_alias_Document_also_works_for_creating_documents(self):
        page = create(Builder('document'))
        self.assertEquals('Document', page.portal_type)


class TestFileBuilder(IntegrationTestCase):

    def test_creates_a_File_object(self):
        file_ = create(Builder('file'))
        self.assertEquals('File', file_.portal_type)

    def test_file_data_can_be_attached(self):
        obj = create(Builder('file')
                     .attach_file_containing(u'Data Data', u'data.txt'))

        file_ = get_file(obj)
        self.assertEquals(
            {'filename': u'data.txt',
             'data': u'Data Data'},

            {'filename': file_.filename,
             'data': file_.data})

    def test_dummy_content_can_be_attached(self):
        obj = create(Builder('file')
                     .with_dummy_content())

        file_ = get_file(obj)
        self.assertEquals(
            {'filename': u'test.doc',
             'data': u'Test data'},

            {'filename': file_.filename,
             'data': file_.data})


class TestImageBuilder(IntegrationTestCase):

    def test_creates_an_image_object(self):
        image = create(Builder('image'))
        self.assertEquals('Image', image.portal_type)

    def test_setting_image_data(self):
        image = create(Builder('image')
                       .attach_file_containing(u'IMG', u'foo.png'))
        file_ = get_file(image)

        self.assertEquals(
            {'filename': u'foo.png',
             'data': u'IMG'},

            {'filename': file_.filename,
             'data': file_.data})

    def test_dummy_content_can_be_attached(self):
        image = create(Builder('image')
                       .with_dummy_content())
        file_ = get_file(image)

        self.assertEquals(
            {'filename': u'image.gif',
             'data': 'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00'
             '\x00!\xf9\x04\x04\x00\x00\x00\x00,\x00\x00\x00\x00\x01'
             '\x00\x01\x00\x00\x02\x02D\x01\x00;'},

            {'filename': file_.filename,
             'data': file_.data})

    def test_dummy_content_is_a_real_image(self):
        image = create(Builder('image')
                       .with_dummy_content())

        scaling = image.restrictedTraverse('@@images')

        self.assertIsNotNone(scaling.scale(width=100,
                                           height=100,
                                           direction='down'),
                             'Could not scale the image.')


class TestCollectionBuilder(IntegrationTestCase):

    def test_creating_collection_with_query(self):
        create(Builder('page').titled(u'The Page'))

        collection = create(Builder('collection')
                            .titled(u'The Collection')
                            .having(query=[{'i': 'Type',
                                            'o': 'plone.app.querystring.operation.string.is',
                                            'v': 'Collection'}]))

        self.assertEquals(['The Collection'],
                          map(methodcaller('Title'),
                              collection.results()))

    def test_creating_colleciton_from_query_with_string(self):
        create(Builder('page').titled(u'The Page'))

        collection = create(Builder('collection')
                            .titled(u'The Collection')
                            .from_query({'portal_type': 'Collection'}))

        self.assertEquals(['The Collection'],
                          map(methodcaller('Title'),
                              collection.results()))

    def test_creating_colleciton_from_query_with_list(self):
        create(Builder('document').titled(u'The Page'))

        collection = create(Builder('collection')
                            .titled(u'The Collection')
                            .from_query({'portal_type': ['Collection',
                                                         'Document']}))

        self.assertEquals(
            sorted(['The Page', 'The Collection']),
            sorted(map(methodcaller('Title'),
                       collection.results())))
