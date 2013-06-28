from ftw.builder.session import BuilderSession
from unittest2 import TestCase
from zope.testing.cleanup import CleanUp


class TestSession(TestCase):

    def test_session_instance_is_singleton(self):
        self.assertEquals(BuilderSession.instance(),
                          BuilderSession.instance())

    def test_session_is_reset_for_each_test(self):
        executed = {'test_executed': False}

        class Test(CleanUp, TestCase):
            def test_enable_auto_commit(self):
                session = BuilderSession.instance()
                session.auto_commit = True
                executed['test_executed'] = True

        Test(methodName='test_enable_auto_commit').run()

        self.assertEquals(False, BuilderSession.instance().auto_commit,
                          'builder session was not reset in cleanup')
        self.assertEquals({'test_executed': True}, executed,
                          'Nested test was not executed')
