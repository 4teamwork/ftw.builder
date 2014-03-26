from StringIO import StringIO
from ftw.builder import builder_registry
from ftw.builder.builder import PloneObjectBuilder
from zope.container.interfaces import INameChooser


class ArchetypesBuilder(PloneObjectBuilder):

    def __init__(self, *args, **kwargs):
        super(ArchetypesBuilder, self).__init__(*args, **kwargs)
        self._id = None

    def with_id(self, id_):
        self._id = id_
        return self

    def create_object(self, processForm=True):
        name = self.choose_name()
        self.container.invokeFactory(
            self.portal_type, name, **self.arguments)
        obj = self.container.get(name)

        if processForm:
            obj.processForm()
        return obj

    def choose_name(self):
        if self._id is not None:
            return self._id

        title = self.arguments.get('title', self.portal_type)
        chooser = INameChooser(self.container)
        return chooser.chooseName(title, self.container)


class FolderBuilder(ArchetypesBuilder):

    portal_type = 'Folder'

builder_registry.register('folder', FolderBuilder)


class PageBuilder(ArchetypesBuilder):

    portal_type = 'Document'

builder_registry.register('page', PageBuilder)
builder_registry.register('document', PageBuilder)


class FileBuilder(ArchetypesBuilder):

    portal_type = 'File'

    def attach_file_containing(self, content, name="test.doc"):
        data = StringIO(content)
        data.filename = name
        self.attach(data)
        return self

    def attach(self, file_):
        self.arguments['file'] = file_
        return self

    def with_dummy_content(self):
        self.attach_file_containing("Test data")
        return self

builder_registry.register('file', FileBuilder)


class ImageBuilder(FileBuilder):

    portal_type = 'Image'

    def attach_file_containing(self, content, name="image.gif"):
        return super(ImageBuilder, self) \
            .attach_file_containing(content, name)

    def with_dummy_content(self):
        data = (
            'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00'
            '\x00!\xf9\x04\x04\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00'
            '\x01\x00\x00\x02\x02D\x01\x00;')

        return self.attach_file_containing(data)

builder_registry.register('image', ImageBuilder)
