from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from ftw.builder import registry
from ftw.builder import session
from zope.component.hooks import getSite
from zope.interface import alsoProvides
import transaction


def create(builder, **kwargs):
    return CREATOR_CHAIN[0](builder, **kwargs)


def ticking_creator(clock, **forward):
    """Returns a builder create()-callable, which "ticks" an
    ftw.testing clock forward after each created object.
    See https://github.com/4teamwork/ftw.testing#freezing-datetimenow

    It can be activated globally when used as context manager.
    """
    return TickingCreator(clock, **forward)


class TickingCreator(object):
    """The TickingCreator ticks an ftw.testing clock forward after each
    created object.
    See https://github.com/4teamwork/ftw.testing#freezing-datetimenow

    It can be activated globally when used as context manager.
    """

    def __init__(self, clock, **forward):
        self.clock = clock
        self.forward = forward
        self.parent_create = None

    def __call__(self, *args, **kwargs):
        try:
            if self.parent_create is not None:
                return self.parent_create(*args, **kwargs)
            else:
                return create(*args, **kwargs)
        finally:
            self.clock.forward(**self.forward)

    def __enter__(self):
        """When used as context manager, the ticking creator is installed
        globally.
        """
        self.parent_create = CREATOR_CHAIN[0]
        CREATOR_CHAIN.insert(0, self)

    def __exit__(self, exc_type, exc_value, traceback):
        self.parent_create = None
        CREATOR_CHAIN.remove(self)


def original_create(builder, **kwargs):
    return builder.create(**kwargs)


# The creator chain is a chain of creators, where always the creator
# at index 0 is called.
# When a new creator is registred which just wraps the original creator
# it should be inserted at index 0 and delegate calls to the creator
# at index 1. A wrapper must not access the chain when called but on setup.
CREATOR_CHAIN = [original_create]


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

    def set_modification_date(self, obj):
        obj.setModificationDate(
            modification_date=self.modification_date)
        obj.reindexObject(idxs=['modified'])

    def set_creation_date(self, obj):
        obj.setCreationDate(creation_date=self.creation_date)
        obj.reindexObject(idxs=['created'])
