from ftw.builder import session
from ftw.builder.testing import BUILDER_FUNCTIONAL_TESTING
from unittest2 import TestCase


class TestSessionAutoCommit(TestCase):

    layer = BUILDER_FUNCTIONAL_TESTING

    def test_auto_commit_is_enabled_by_auto_commit_layer(self):
        # The BUILDER_FUNCTIONAL_TESTING bases on the BUILDER_AUTO_COMMIT
        # testing layer, which should set the `auto_commit` option to
        # `True` in for the current session.
        self.assertTrue(
            session.current_session.auto_commit,
            'Auto commit should be set to True')
