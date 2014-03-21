from Products.CMFCore.utils import getToolByName
from ftw.builder import builder_registry
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.component import getUtility
from zope.component.hooks import getSite
import transaction


class GroupBuilder(object):

    def __init__(self, session):
        self.session = session
        self.portal = getSite()
        self.properties = {}
        self.groupid = None
        self.roles = ()
        self.members = []
        self.local_roles = {}

    def titled(self, title):
        return self.having(title=title)

    def with_groupid(self, groupid):
        self.groupid = groupid
        return self

    def with_roles(self, *roles, **kwargs):
        context = kwargs.get('on', None)
        if context is None:
            self.roles = tuple(roles)
        else:
            self.local_roles[context] = roles
        return self

    def with_members(self, *members):
        self.members.extend(members)
        return self

    def having(self, **kwargs):
        self.properties.update(kwargs)
        return self

    def create(self):
        self.before_create()
        group = self.create_group(self.groupid, self.roles, self.properties)
        self.add_members(group)
        self.after_create(group)
        return group

    def create_group(self, groupid, roles, properties):
        portal_groups = getToolByName(self.portal, 'portal_groups')
        portal_groups.addGroup(groupid, roles=roles, properties=properties)
        self.set_roles(groupid)
        return portal_groups.getGroupById(self.groupid)

    def add_members(self, group):
        portal_groups = getToolByName(self.portal, 'portal_groups')
        for member in self.members:
            portal_groups.addPrincipalToGroup(member.getId(), group.getId())

    def before_create(self):
        self.validate()
        self.update_group_id()

    def after_create(self, group):
        if self.session.auto_commit:
            transaction.commit()

    def validate(self):
        assert self.groupid or self.properties.get('title', None), \
            'Cannot create group: no group title (or id) defined.'

    def update_group_id(self):
        if self.groupid:
            return

        title = self.properties.get('title')
        normalizer = getUtility(IIDNormalizer)
        self.groupid = normalizer.normalize(title)

    def set_roles(self, groupid):
        for context, roles in self.local_roles.items():
            context.manage_setLocalRoles(groupid, tuple(roles))
            context.reindexObjectSecurity()


builder_registry.register('group', GroupBuilder)
