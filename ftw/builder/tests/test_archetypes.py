from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.testing import BUILDER_INTEGRATION_TESTING
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from unittest2 import TestCase


class TestArchetypesBuilder(TestCase):

    layer = BUILDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

    def test_object_id_is_chosen_from_title_automatically(self):
        folder1 = create(Builder('Folder').titled('Foo'))
        self.assertEqual('foo', folder1.getId())

        folder2 = create(Builder('Folder').titled('Foo'))
        self.assertEqual('foo-1', folder2.getId())
