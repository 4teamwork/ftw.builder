from ftw.builder import builder_registry
from plone.app.portlets.portlets import navigation
from plone.portlet.static import static
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from zope.component import getUtility, getMultiAdapter
from zope.component.hooks import getSite
from zope.container.interfaces import INameChooser
import transaction


class PlonePortletBuilder(object):

    def __init__(self, session):
        self.session = session
        self.container = getSite()
        self.manager_name = u'plone.leftcolumn'
        self.arguments = {}

    def within(self, container):
        self.container = container
        return self

    def in_manager(self, manager_name):
        self.manager_name = manager_name
        return self

    def having(self, **kwargs):
        self.arguments.update(kwargs)
        return self

    def create(self):
        self.before_create()
        manager, assignments = self.get_manager_and_assignments()
        portlet = self.create_portlet(assignments)
        self.after_create(manager, assignments, portlet)
        return portlet

    def create_portlet(self, assignments):
        portlet = self.assignment_class(**self.arguments)
        name = self.choose_name(assignments, portlet)
        portlet.__name__ = name
        assignments[name] = portlet
        return portlet

    def get_manager_and_assignments(self):
        portal = getSite()
        manager = getUtility(
            IPortletManager,
            name=self.manager_name,
            context=portal
        )
        assignments = getMultiAdapter(
            (self.container, manager),
            IPortletAssignmentMapping,
            context=portal
        )
        return manager, assignments

    def choose_name(self, assignments, portlet):
        return INameChooser(assignments).chooseName(
            name=portlet.__class__.__name__, object=portlet)

    def before_create(self):
        pass

    def after_create(self, manager, assignments, portlet):
        if self.session.auto_commit:
            transaction.commit()


class StaticPortletBuilder(PlonePortletBuilder):
    assignment_class = static.Assignment

    def titled(self, title):
        self.arguments['header'] = title
        return self

builder_registry.register('static portlet', StaticPortletBuilder)


class NavigationPortletBuilder(PlonePortletBuilder):
    assignment_class = navigation.Assignment

    def titled(self, title):
        self.arguments['name'] = title
        return self

builder_registry.register('navigation portlet', NavigationPortletBuilder)
