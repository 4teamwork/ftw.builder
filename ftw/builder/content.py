from ftw.builder import builder_registry
from ftw.builder import HAS_DEXTERITY
from ftw.builder.archetypes import ArchetypesBuilder
from Products.CMFPlone.utils import getFSVersionTuple
from StringIO import StringIO

if HAS_DEXTERITY:
    from ftw.builder.dexterity import DexterityBuilder

    from plone.namedfile.interfaces import HAVE_BLOBS
    if HAVE_BLOBS:
        from plone.namedfile.file import NamedBlobFile as NamedFile
    else:
        from plone.namedfile.file import NamedFile


if getFSVersionTuple() > (5, ):
    DefaultContentBuilder = DexterityBuilder
else:
    DefaultContentBuilder = ArchetypesBuilder


class FolderBuilder(DefaultContentBuilder):

    portal_type = 'Folder'

builder_registry.register('folder', FolderBuilder)


class PageBuilder(DefaultContentBuilder):

    portal_type = 'Document'

builder_registry.register('page', PageBuilder)
builder_registry.register('document', PageBuilder)


class FileBuilder(DefaultContentBuilder):

    portal_type = 'File'

    def attach_file_containing(self, content, name=u"test.doc"):
        if HAS_DEXTERITY and issubclass(self.__class__, DexterityBuilder):
            return self._attach_dx_file(content, name)
        else:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            return self._attach_at_file(content, name)

    def attach(self, file_):
        self.arguments['file'] = file_
        return self

    def with_dummy_content(self):
        self.attach_file_containing("Test data")
        return self

    def _attach_at_file(self, content, name):
        data = StringIO(content)
        data.filename = name
        self.attach(data)
        return self

    def _attach_dx_file(self, content, name):
        self.attach(NamedFile(data=content, filename=name))
        return self

builder_registry.register('file', FileBuilder)


class ImageBuilder(FileBuilder):

    portal_type = 'Image'

    def attach_file_containing(self, content, name=u"image.gif"):
        return super(ImageBuilder, self) \
            .attach_file_containing(content, name)

    def with_dummy_content(self):
        data = (
            'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00'
            '\x00!\xf9\x04\x04\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00'
            '\x01\x00\x00\x02\x02D\x01\x00;')

        return self.attach_file_containing(data)

    def attach(self, file_):
        if issubclass(self.__class__, DexterityBuilder):
            self.arguments['image'] = file_
        else:
            self.arguments['file'] = file_
        return self

builder_registry.register('image', ImageBuilder)


class CollectionBuilder(DefaultContentBuilder):
    portal_type = 'Collection'

    def from_query(self, query):
        """plone.app.collection collections use
        plone.app.querystring, making it really hard to just set
        a query.
        This method tries to convert a catalog query into a
        querystring-list so that it can be stored on the
        collection.

        However, it is very limited.
        For complicated queries you'll need to create your own
        querystring-list and set it with ``having``, e.g.:


        >>> create(Builder('collection')
        ...    .having(query=[{'i': 'Type',
        ...                    'o': 'plone.app.querystring.operation.string.is',
        ...                    'v': 'Collection'}]))
        """

        querystringthing = []

        for name, value in query.items():
            if isinstance(value, unicode):
                value = value.encode('utf-8')

            if isinstance(value, str):
                querystringthing.append(
                    {'i': name,
                     'o': 'plone.app.querystring.operation.string.is',
                     'v': value})

            elif isinstance(value, list):
                querystringthing.append(
                    {'i': name,
                     'o': 'plone.app.querystring.operation.selection.is',
                     'v': value})

            else:
                raise ValueError(
                    'This query is too complicated, since we need'
                    ' to generate a fancy querystring.'
                    ' Currently only string and list values are '
                    ' accepted. Please build your own querystring'
                    ' object (see plone.app.querystring).')

        return self.having(query=querystringthing)


builder_registry.register('collection', CollectionBuilder)
builder_registry.register('topic', CollectionBuilder)
