from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from ftw.builder import builder_registry
from ftw.builder.session import BuilderSession
from zope.component.hooks import getSite
import transaction


def create(builder, **kwargs):
    return builder.create(**kwargs)


def Builder(name):
    builder_klass = builder_registry.get(name)
    return builder_klass(BuilderSession.instance())


class PloneObjectBuilder(object):

    def __init__(self, session):
        self.session = session
        self.container = getSite()
        self.arguments = {}
        self.review_state = None

    def within(self, container):
        self.container = container
        return self

    def having(self, **kwargs):
        self.arguments.update(kwargs)
        return self

    def titled(self, title):
        self.arguments["title"] = title
        return self

    def in_state(self, review_state):
        self.review_state = review_state
        return self

    def create(self, **kwargs):
        self.before_create()
        obj = self.create_object(**kwargs)
        self.after_create(obj)
        return obj

    def before_create(self):
        pass

    def after_create(self, obj):
        self.change_workflow_state(obj)
        if self.session.auto_commit:
            transaction.commit()

    def change_workflow_state(self, obj):
        if not self.review_state:
            return

        wftool = getToolByName(self.container, 'portal_workflow')
        chain = wftool.getChainFor(obj)
        if len(chain) != 1:
            raise ValueError(
                'Cannot change state of "%s" object - seems to have no'
                ' or too many workflows: %s' % (
                    self.portal_type, chain))

        wftool.setStatusOf(chain[0], obj, {
                'review_state': self.review_state})

        for workflow_id in chain:
            workflow = wftool.get(workflow_id)
            if hasattr(aq_base(workflow), 'updateRoleMappingsFor'):
                workflow.updateRoleMappingsFor(obj)
