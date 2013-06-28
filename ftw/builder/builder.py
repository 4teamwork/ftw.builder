from ftw.builder import builder_registry
from ftw.builder.session import BuilderSession
from zope.component.hooks import getSite


def create(builder, **kwargs):
    return builder.create(**kwargs)


def Builder(name):
    builder_klass = builder_registry.get(name)
    return builder_klass(BuilderSession.instance())


class PloneObjectBuilder(object):

    def __init__(self, session):
        self.session = session
        self.container = getSite()
        self.arguments = {}

    def within(self, container):
        self.container = container
        return self

    def having(self, **kwargs):
        self.arguments.update(kwargs)
        return self

    def titled(self, title):
        self.arguments["title"] = title
        return self

    def create(self, **kwargs):
        self.before_create()
        obj = self.create_object(**kwargs)
        self.after_create(obj)
        return obj

    def before_create(self):
        pass

    def after_create(self, obj):
        pass
