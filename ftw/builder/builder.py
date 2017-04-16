from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from ftw.builder import registry
from ftw.builder import session
from zope.component.hooks import getSite
from zope.interface import alsoProvides
import transaction


def create(builder, **kwargs):
    return builder.create(**kwargs)


def ticking_creator(clock, **forward):
    """Returns a builder create()-function, which "ticks" an
    ftw.testing clock forward after each created object.
    See https://github.com/4teamwork/ftw.testing#freezing-datetimenow
    """
    def ticking_create(*args, **kwargs):
        try:
            return create(*args, **kwargs)
        finally:
            clock.forward(**forward)
    return ticking_create


def Builder(name):
    if not session.current_session:
        raise Exception('There is no builder session - you need to use the '
                        'BUILDER_LAYER as bases of your layer.')

    builder_klass = registry.builder_registry.get(name)
    return builder_klass(session.current_session)


class PloneObjectBuilder(object):

    def __init__(self, session):
        self.session = session
        self.container = getSite()
        self.arguments = {}
        self.review_state = None
        self.effective_date = None
        self.expiration_date = None
        self.modification_date = None
        self.creation_date = None
        self.interfaces = []
        self.properties = []

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

    def with_effective_date(self, effective_date):
        self.effective_date = effective_date
        return self

    def with_expiration_date(self, epiration_date):
        self.expiration_date = epiration_date
        return self

    def with_modification_date(self, modification_date):
        self.modification_date = modification_date
        return self

    def with_creation_date(self, creation_date):
        self.creation_date = creation_date
        return self

    def with_property(self, name, value, value_type='string'):
        self.properties.append((name, value, value_type))
        return self

    def providing(self, *interfaces):
        self.interfaces.extend(interfaces)
        return self

    def create(self, **kwargs):
        self.before_create()
        obj = self.create_object(**kwargs)
        self.after_create(obj)
        return obj

    def before_create(self):
        pass

    def after_create(self, obj):
        if self.interfaces:
            alsoProvides(obj, *self.interfaces)
            obj.reindexObject(idxs=['object_provides'])

        self.change_workflow_state(obj)

        if self.effective_date:
            self.set_effective_date(obj)

        if self.expiration_date:
            self.set_expiration_date(obj)

        if self.modification_date:
            self.set_modification_date(obj)

        if self.creation_date:
            self.set_creation_date(obj)

        if self.session.auto_commit:
            transaction.commit()

    def set_properties(self, obj):
        for property_args in self.properties:
            obj._setProperty(*property_args)

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
            'review_state': self.review_state,
            'action': '',
            'actor': ''})

        for workflow_id in chain:
            workflow = wftool.get(workflow_id)
            if hasattr(aq_base(workflow), 'updateRoleMappingsFor'):
                workflow.updateRoleMappingsFor(obj)

        obj.reindexObjectSecurity()
        obj.reindexObject(idxs=['review_state'])

    def set_effective_date(self, obj):
        obj.setEffectiveDate(self.effective_date)
        obj.reindexObject(idxs=['effective'])

    def set_expiration_date(self, obj):
        obj.setExpirationDate(self.expiration_date)
        obj.reindexObject(idxs=['expires'])

    def set_modification_date(self, obj):
        obj.setModificationDate(
            modification_date=self.modification_date)
        obj.reindexObject(idxs=['modified'])

    def set_creation_date(self, obj):
        obj.setCreationDate(creation_date=self.creation_date)
        obj.reindexObject(idxs=['created'])
