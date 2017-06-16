from Acquisition import aq_inner
from Acquisition import aq_parent
from datetime import datetime
from DateTime import DateTime
from ftw.builder import Builder
from ftw.builder import ticking_creator
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase
from ftw.testing import freeze
from plone import api
from Products.CMFCore.utils import getToolByName


def obj2brain(obj):
    catalog = getToolByName(obj, 'portal_catalog')
    query = {'path':
             {'query': '/'.join(obj.getPhysicalPath()),
              'depth': 0}}
    brains = catalog(query)
    if len(brains) == 0:
        raise Exception('Not in catalog: %s' % obj)
    else:
        return brains[0]


class TestCreatingObjects(IntegrationTestCase):

    def test_default_container_is_plone_site(self):
        folder = create(Builder('folder'))
        self.assertEqual(self.portal, aq_parent(aq_inner(folder)))

    def test_default_id_is_portal_type(self):
        folder = create(Builder('folder'))
        self.assertEqual('folder', folder.getId())

    def test_create_folder_with_title(self):
        folder = create(Builder('folder').titled(u'The Folder'))
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

    def test_changing_workflow_state_reindexes_object_security(self):
        self.set_workflow_chain('Folder', 'simple_publication_workflow')

        normal_folder = create(Builder('folder'))
        self.assertNotIn(
            'Anonymous',
            self.get_allowed_roles_and_users_for(normal_folder))

        published_folder = create(Builder('folder')
                                  .in_state('published'))
        self.assertEquals(
            ['Anonymous'],
            self.get_allowed_roles_and_users_for(published_folder))

    def test_changing_workflow_state_updates_also_the_brain(self):
        self.set_workflow_chain('Folder', 'simple_publication_workflow')

        normal_folder = create(Builder('folder'))
        self.assertNotIn(
            'Anonymous',
            self.get_allowed_roles_and_users_for(normal_folder))

        published_folder = create(Builder('folder')
                                  .in_state('published'))

        self.assertEquals('published',
                          obj2brain(published_folder).review_state)

    def test_with_modification_date_updates_obj_and_brain(self):
        modified = DateTime(2013, 1, 1)

        folder = create(Builder('folder')
                        .with_modification_date(modified))

        self.assertEquals(modified, folder.modified())
        self.assertEquals(modified, obj2brain(folder).modified)

    def test_with_creation_date_updates_obj_and_brain(self):
        created = DateTime(2011, 2, 3, 5, 7, 11)

        folder = create(Builder('folder')
                        .with_creation_date(created))

        self.assertEquals(created, folder.created())
        self.assertEquals(created, obj2brain(folder).created)

    def set_workflow_chain(self, for_type, to_workflow):
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes((for_type,),
                                      (to_workflow,))

    def get_allowed_roles_and_users_for(self, obj):
        catalog = getToolByName(self.portal, 'portal_catalog')
        path = '/'.join(obj.getPhysicalPath())
        rid = catalog.getrid(path)
        index_data = catalog.getIndexDataForRID(rid)
        return index_data.get('allowedRolesAndUsers')


class TestTickingCreator(IntegrationTestCase):

    def test_ticking_creator_function(self):
        with freeze(datetime(2010, 1, 1)) as clock:
            create = ticking_creator(clock, days=1)
            self.assertEquals(DateTime(2010, 1, 1),
                              create(Builder('folder')).created())
            self.assertEquals(DateTime(2010, 1, 2),
                              create(Builder('folder')).created())
            self.assertEquals(DateTime(2010, 1, 3),
                              create(Builder('folder')).created())

    def test_activating_ticking_creator_in_context_manager(self):
        with freeze(datetime(2010, 1, 1)) as clock:
            with ticking_creator(clock, days=1):
                self.assertEquals(DateTime(2010, 1, 1),
                                  create(Builder('folder')).created())
                self.assertEquals(DateTime(2010, 1, 2),
                                  create(Builder('folder')).created())
                self.assertEquals(DateTime(2010, 1, 3),
                                  create(Builder('folder')).created())
