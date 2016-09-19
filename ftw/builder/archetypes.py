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

        self.set_properties(obj)

        if processForm:
            obj.processForm()
        return obj

    def choose_name(self):
        if self._id is not None:
            return self._id

        title = self.arguments.get('title', self.portal_type)
        chooser = INameChooser(self.container)
        return chooser.chooseName(title, self.container)
