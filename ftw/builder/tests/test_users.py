from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase
from Products.CMFCore.utils import getToolByName


class TestUserBuilder(IntegrationTestCase):

    def test_defaults(self):
        user = create(Builder('user'))
        self.assertEquals(
            {'id': 'john.doe',
             'fullname': 'Doe John',
             'email': 'john@doe.com'},

            {'id': user.getId(),
             'fullname': user.getProperty('fullname'),
             'email': user.getProperty('email')})

    def test_defaults_are_chosen_by_first_and_lastname(self):
        user = create(Builder('user').named('Hugo', 'Boss'))
        self.assertEquals(
            {'id': 'hugo.boss',
             'fullname': 'Boss Hugo',
             'email': 'hugo@boss.com'},

            {'id': user.getId(),
             'fullname': user.getProperty('fullname'),
             'email': user.getProperty('email')})

    def test_user_can_be_created_in_groups(self):
        create(Builder('group').with_groupid('foo'))
        create(Builder('group').with_groupid('bar'))
        create(Builder('user').named('Hans', 'Peter').in_groups('foo', 'bar'))

        portal_groups = getToolByName(self.portal, 'portal_groups')
        self.assertEqual(['hans.peter'], portal_groups.getGroupMembers('foo'))
        self.assertEqual(['hans.peter'], portal_groups.getGroupMembers('bar'))

    def test_first_and_lastname_are_capitalized(self):
        user = create(Builder('user').named('hans-peter', 'linder'))
        self.assertEquals('Linder Hans-Peter', user.getProperty('fullname'))

    def test_user_is_registered_in_portal_membership(self):
        mtool = getToolByName(self.portal, 'portal_membership')
        self.assertFalse(mtool.getMemberById('hugo.boss'))
        create(Builder('user').with_userid('hugo.boss'))
        self.assertTrue(mtool.getMemberById('hugo.boss'))

    def test_generated_mail_address_is_normalized(self):
        user = create(Builder('user').named('H\xc3\xa4ns Peter', 'Linder'))
        self.assertEquals('hans-peter@linder.com', user.getProperty('email'))

    def test_changing_userid(self):
        user = create(Builder('user').with_userid('foo'))
        self.assertEquals('foo', user.getId())

    def test_changing_email_address(self):
        user = create(Builder('user').with_email('foo@bar.ch'))
        self.assertEquals('foo@bar.ch', user.getProperty('email'))

    def test_setting_roles_of_a_user(self):
        user = create(Builder('user').with_roles('Member', 'Contributor'))
        self.assertEquals(set(['Authenticated', 'Member', 'Contributor']),
                          set(user.getRoles()))

    def test_setting_roles_on_a_context(self):
        folder = create(Builder('folder'))

        user = create(Builder('user')
                      .with_roles('Contributor')
                      .with_roles('Editor', on=folder))

        self.assertEquals(
            {'portal': set(['Authenticated', 'Contributor']),
             'folder': set(['Authenticated', 'Contributor', 'Editor'])},

            {'portal': set(user.getRoles()),
             'folder': set(user.getRolesInContext(folder))})

    def test_security_indexes_are_up_to_date(self):
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Folder'],
                                      'simple_publication_workflow')
        folder = create(Builder('folder'))
        user = create(Builder('user')
                      .with_roles('Reader', on=folder))

        catalog = getToolByName(self.portal, 'portal_catalog')
        rid = catalog(path='/'.join(folder.getPhysicalPath()))[0].getRID()
        self.assertIn('user:{0}'.format(user.getId()),
                      catalog.getIndexDataForRID(rid)['allowedRolesAndUsers'])
