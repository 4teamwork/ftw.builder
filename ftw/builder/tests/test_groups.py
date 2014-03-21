from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase
from Products.CMFCore.utils import getToolByName


class TestUserBuilder(IntegrationTestCase):

    def test_group_name_is_normalized_by_title(self):
        group = create(Builder('group').titled('Masters of Disaster'))
        self.assertEquals('masters-of-disaster', group.getId())

    def test_title_is_set(self):
        group = create(Builder('group').titled('Masters of Disaster'))
        self.assertEquals('Masters of Disaster', group.getProperty('title'))

    def test_group_id_can_be_set(self):
        group = create(Builder('group').with_groupid('foo'))
        self.assertEquals('foo', group.getId())

    def test_either_userid_or_title_needs_to_be_defined(self):
        with self.assertRaises(AssertionError) as cm:
            create(Builder('group'))
        self.assertEquals(
            'Cannot create group: no group title (or id) defined.',
            str(cm.exception))

        self.assertTrue(create(Builder('group').with_groupid('foo')))
        self.assertTrue(create(Builder('group').titled('Bar')))

    def test_create_group_with_roles(self):
        group = create(Builder('group')
                       .titled('Something')
                       .with_roles('Editor', 'Contributor'))
        self.assertEquals(set(['Authenticated', 'Editor', 'Contributor']),
                          set(group.getRoles()))

    def test_create_group_with_local_roles(self):
        folder = create(Builder('folder'))
        group = create(Builder('group')
                       .titled('Something')
                       .with_roles('Editor', 'Contributor', on=folder))
        self.assertIn((group.getId(), ('Editor', 'Contributor')),
                      folder.get_local_roles())

    def test_create_group_with_participants(self):
        user = create(Builder('user'))
        group = create(Builder('group').titled('Administrators')
                       .with_members(user.getUser()))
        self.assertEquals([user], group.getAllGroupMembers())

    def test_security_indexes_are_up_to_date(self):
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Folder'],
                                      'simple_publication_workflow')
        folder = create(Builder('folder'))
        group = create(Builder('group')
                       .titled('group')
                       .with_roles('Reader', on=folder))

        catalog = getToolByName(self.portal, 'portal_catalog')
        rid = catalog(path='/'.join(folder.getPhysicalPath()))[0].getRID()
        self.assertIn('user:{0}'.format(group.getId()),
                      catalog.getIndexDataForRID(rid)['allowedRolesAndUsers'])
