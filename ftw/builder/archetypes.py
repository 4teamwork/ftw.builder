from ftw.builder import builder_registry
from ftw.builder.builder import PloneObjectBuilder
from zope.container.interfaces import INameChooser


class ArchetypesBuilder(PloneObjectBuilder):

    def create_object(self, processForm=True):
        name = self.choose_name()
        self.container.invokeFactory(
            self.portal_type, name, **self.arguments)
        obj = self.container.get(name)

        if processForm:
            obj.processForm()
        return obj

    def choose_name(self):
        title = self.arguments.get('title', self.portal_type)
        chooser = INameChooser(self.container)
        return chooser.chooseName(title, self.container)


class FolderBuilder(ArchetypesBuilder):

    portal_type = 'Folder'

builder_registry.register('Folder', FolderBuilder)
