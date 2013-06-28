
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


builder_registry = Registry()
