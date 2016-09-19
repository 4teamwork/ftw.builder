from Acquisition import aq_base
from ftw.builder import HAS_RELATION
from ftw.builder.builder import PloneObjectBuilder
from operator import methodcaller
from plone.app.dexterity.behaviors.metadata import IOwnership
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.dexterity.utils import getAdditionalSchemata
from plone.dexterity.utils import iterSchemata
from z3c.form.interfaces import IValue
from zope.component import createObject
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent
from zope.schema import getFieldsInOrder

if HAS_RELATION:
    from z3c.relationfield.interfaces import IRelationChoice
    from z3c.relationfield.interfaces import IRelationList
    from z3c.relationfield.interfaces import IRelationValue
    from z3c.relationfield.relation import RelationValue
    from zope.intid.interfaces import IIntIds

none_marker = object()


class DexterityBuilder(PloneObjectBuilder):

    basic_attributes = ('title', 'id',)

    def __init__(self, session):
        super(DexterityBuilder, self).__init__(session)
        self.checkConstraints = False
        self.set_default_values = True

    @property
    def creation_arguments(self):
        creation_arguments = {}
        for key in self.basic_attributes:
            if key in self.arguments:
                creation_arguments[key] = self.arguments[key]
        return creation_arguments

    def without_defaults(self):
        self.set_default_values = False
        return self

    def with_constraints(self):
        self.checkConstraints = True
        return self

    def create(self):
        self.before_create()
        obj = self.create_object()
        self.after_create(obj)
        return obj

    def _create_content(self):
        """Create object almost the same way as dexterity.utils.createContent
        but only set basic attributes and do not fire a created event yet.

        """
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        content = createObject(fti.factory, **self.creation_arguments)

        # Note: The factory may have done this already, but we want to be sure
        # that the created type has the right portal type. It is possible
        # to re-define a type through the web that uses the factory from an
        # existing type, but wants a unique portal_type!
        content.portal_type = fti.getId()
        return content

    def create_object(self):
        """Creates an instance of our dexterity content type.

        Performs the following actions in order:
        - Create the instance
        - Set field values and default values
        - Fire a created event
        - Add content to its container

        """
        self.insert_field_default_values()
        content = self._create_content()

        # Acquisition wrap content temporarily to make sure schema
        # interfaces can be adapted to `content`
        content = content.__of__(self.container)
        self.set_field_values(content)
        self.set_missing_values_for_empty_fields(content)
        self.set_properties(content)
        # Remove temporary acquisition wrapper
        content = aq_base(content)
        notify(ObjectCreatedEvent(content))

        obj = addContentToContainer(
            self.container,
            content,
            checkConstraints=self.checkConstraints)

        return obj

    def insert_field_default_values(self):
        for name, field in self.iter_fields():
            if name in self.arguments:
                continue

            default = self.get_default_value_for_field(field)
            if default:
                self.arguments[name] = default

    def set_field_values(self, obj):
        for name, field in self.iter_fields(obj):

            if name in self.arguments:
                value = self.arguments.get(name)

                if HAS_RELATION and IRelationChoice.providedBy(field):
                    value = self._as_relation_value(value)
                elif HAS_RELATION and IRelationList.providedBy(field):
                    value = [self._as_relation_value(item) for item in value]

                field.set(field.interface(obj), value)

    def _as_relation_value(self, value):
        if IRelationValue.providedBy(value):
            return value

        intids = getUtility(IIntIds)
        return RelationValue(intids.getId(value))

    def set_missing_values_for_empty_fields(self, obj):
        for name, field in self.iter_fields(obj):

            if field.required:
                continue

            try:
                value = field.get(field.interface(obj))
                if value:
                    # Field is present, nothing to do
                    continue
            except AttributeError:
                # Field is missing, go on and set default value
                pass

            if name in self.arguments:
                continue

            missing_value = self.get_missing_value_for_field(field)
            if missing_value != none_marker:
                field.set(field.interface(obj), missing_value)

    def get_default_value_for_field(self, field):
        default = queryMultiAdapter(
            (self.container, self.container.REQUEST, None, field, None),
            IValue, name='default')

        if default is not None:
            value = default.get()
        else:
            # Bind field so that for an IContextAwareDefaultFactory it
            # gets passed a context (i.e. the container)
            bound_field = field.bind(self.container)
            value = getattr(bound_field, 'default', None)

        # The default value of the 'creators' field returns a tuple
        # of strings instead of a tuple of unicodes.
        # -----
        # Because the field equality check is insufficient we need to check
        # the field interface additionally.
        if IOwnership['creators'] == field and field.interface == IOwnership:
            value = tuple(map(methodcaller('decode', 'utf8'), value))
        return value

    def get_missing_value_for_field(self, field):
        try:
            return field.missing_value
        except AttributeError:
            return none_marker

    def iter_fields(self, obj=None):
        if obj:
            schematas = iterSchemata(obj)
        else:
            schematas = self.iter_schemata_for_protal_type(self.portal_type)

        for schemata in schematas:
            for name, field in getFieldsInOrder(schemata):
                if hasattr(field, 'readonly') and field.readonly:
                    continue

                yield (name, field)

    def iter_schemata_for_protal_type(self, portal_type):
        fti = queryUtility(IDexterityFTI, name=portal_type)
        if fti is None:
            return

        yield fti.lookupSchema()
        for schema in getAdditionalSchemata(portal_type=portal_type):
            yield schema

    def set_creation_date(self, obj):
        obj.creation_date = self.creation_date
        obj.reindexObject(idxs=['created'])
