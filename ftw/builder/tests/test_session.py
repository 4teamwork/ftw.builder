from ftw.builder.session import BuilderSession
from unittest2 import TestCase


class TestSession(TestCase):

    def test_session_instance_is_singleton(self):
        self.assertEquals(BuilderSession.instance(),
                          BuilderSession.instance())
