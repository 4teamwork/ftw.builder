from ftw.builder import builder_registry
from ftw.builder.utils import strip_diacricits
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from zope.component.hooks import getSite
import transaction

import pkg_resources
try:
    pkg_resources.get_distribution('plone.app.testing')
except pkg_resources.DistributionNotFound:
    DEFAULT_PASSWORD = 'secret'
else:
    from plone.app.testing import TEST_USER_PASSWORD as DEFAULT_PASSWORD


class UserBuilder(object):

    def __init__(self, session):
        self.session = session
        self.portal = getSite()
        self.properties = {'firstname': 'John',
                           'lastname': 'Doe'}
        self.userid = None
        self.password = DEFAULT_PASSWORD
        self.roles = ['Member']
        self.local_roles = {}
        self.groupids = set()

    def with_userid(self, userid):
        self.userid = userid
        return self

    def with_email(self, email):
        return self.having(email=email)

    def with_password(self, password):
        self.password = password
        return self

    def with_roles(self, *roles, **kwargs):
        context = kwargs.get('on', None)
        if context is None:
            self.roles = roles
        else:
            self.local_roles[context] = roles
        return self

    def in_groups(self, *groupids):
        self.groupids.update(groupids)
        return self

    def named(self, firstname, lastname):
        self.having(firstname=firstname, lastname=lastname)
        return self

    def having(self, **kwargs):
        self.properties.update(kwargs)
        return self

    def create(self):
        self.before_create()
        user = self.create_user(self.userid,
                                self.password,
                                self.roles,
                                self.properties)
        self.after_create(user)
        return user

    def create_user(self, userid, password, roles, properties):
        regtool = getToolByName(self.portal, 'portal_registration')
        mtool = getToolByName(self.portal, 'portal_membership')
        user = regtool.addMember(userid, password, (), properties=properties)
        self.set_roles(user.getId(), roles)
        self.set_groups(user.getId())
        return mtool.getMemberById(userid)

    def set_roles(self, userid, roles):
        acl_users = getToolByName(self.portal, 'acl_users')
        acl_users.userFolderEditUser(userid, None, list(roles), [])

        for context, roles in self.local_roles.items():
            context.manage_setLocalRoles(userid, tuple(roles))
            context.reindexObjectSecurity()

    def set_groups(self, userid):
        if not self.groupids:
            return

        portal_groups = getToolByName(self.portal, 'portal_groups')
        for groupid in self.groupids:
            portal_groups.addPrincipalToGroup(userid, groupid)

    def before_create(self):
        self.update_properties()

    def after_create(self, user):
        if self.session.auto_commit:
            transaction.commit()

    def update_properties(self):
        lastname = self.properties.get('lastname').title()
        firstname = self.properties.get('firstname').title()
        self.update_userid_and_username(firstname, lastname)
        self.update_fullname(firstname, lastname)
        self.update_email(firstname, lastname)

    def update_fullname(self, firstname, lastname):
        if not self.properties.get('fullname', None):
            self.properties['fullname'] = ' '.join((lastname, firstname))

    def update_email(self, firstname, lastname):
        if not self.properties.get('email', None):
            firstname = self.normalize_name_for_email(firstname)
            lastname = self.normalize_name_for_email(lastname)
            email = '%s@%s.com' % (firstname, lastname)
            self.properties['email'] = email

    def update_userid_and_username(self, firstname, lastname):
        if self.userid is None:
            normalizer = getUtility(IIDNormalizer)
            first = normalizer.normalize(firstname)
            last = normalizer.normalize(lastname)
            self.userid = '.'.join((first, last))

        if not self.properties.get('username', None):
            self.properties['username'] = self.userid

    def normalize_name_for_email(self, name):
        name = name.lower()
        name = name.replace(' ', '-')
        return strip_diacricits(name)

builder_registry.register('user', UserBuilder)
