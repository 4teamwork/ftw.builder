from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase
from plone import api


class TestCreatingObjects(IntegrationTestCase):

    def test_default_container_is_plone_site(self):
        folder = create(Builder('folder'))
        self.assertEqual(self.portal, aq_parent(aq_inner(folder)))

    def test_default_id_is_portal_type(self):
        folder = create(Builder('folder'))
        self.assertEqual('folder', folder.getId())

    def test_create_folder_with_title(self):
        folder = create(Builder('folder').titled('The Folder'))
        self.assertEqual('The Folder', folder.Title())
        self.assertEqual('the-folder', folder.getId())

    def test_changing_workflow_state(self):
        self.set_workflow_chain('Folder', 'simple_publication_workflow')

        normal_folder = create(Builder('folder'))
        self.assertEquals('private',
                          api.content.get_state(normal_folder))

        published_folder = create(Builder('folder').in_state('published'))
        self.assertEquals('published',
                          api.content.get_state(published_folder))

    def set_workflow_chain(self, for_type, to_workflow):
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes((for_type,),
                                      (to_workflow,))
