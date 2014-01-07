from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import IntegrationTestCase


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
