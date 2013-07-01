
class BuilderSession(object):

    def __init__(self):
        self.auto_commit = False

factory = BuilderSession
current_session = None
