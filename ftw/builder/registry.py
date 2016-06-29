from contextlib import contextmanager


class Registry(object):

    def __init__(self):
        self.builders = {}

    def register(self, name, builder, force=False):
        if name in self.builders and not force:
            raise ValueError('Builder "%s" is already registered (%s)' % (
                    name, self.builders[name].__name__))

        self.builders[name] = builder

    def get(self, name):
        if name not in self.builders:
            raise KeyError('Unkown builder "%s"' % name)

        return self.builders[name]

    @contextmanager
    def temporary_builder_config(self):
        builders = self.builders.copy()
        yield
        self.builders = builders


builder_registry = Registry()
