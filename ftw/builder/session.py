
class BuilderSession(object):

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    @classmethod
    def instance(cls, *args, **kwgs):
        if not hasattr(cls, "_instance"):
            cls._instance = cls(*args, **kwgs)
        return cls._instance
