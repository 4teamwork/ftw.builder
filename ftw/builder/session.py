from zope.testing.cleanup import addCleanUp


class BuilderSession(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.auto_commit = False

    @classmethod
    def instance(cls, *args, **kwgs):
        if not hasattr(cls, "_instance"):
            cls._instance = cls(*args, **kwgs)
        return cls._instance


@addCleanUp
def cleanup_builder_session():
    BuilderSession.instance().reset()
