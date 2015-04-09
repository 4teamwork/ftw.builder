from Acquisition import aq_base
from ftw.builder.builder import PloneObjectBuilder
from operator import methodcaller
from plone.app.dexterity.behaviors.metadata import IOwnership
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.dexterity.utils import createContent
from plone.dexterity.utils import getAdditionalSchemata
from plone.dexterity.utils import iterSchemata
from z3c.form.interfaces import IValue
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.schema import getFieldsInOrder


none_marker = object()


class DexterityBuilder(PloneObjectBuilder):

    def __init__(self, session):
        super(DexterityBuilder, self).__init__(session)
        self.checkConstraints = False
        self.set_default_values = True

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

    def create_object(self):
        self.insert_field_default_values()
        content = createContent(self.portal_type, **self.arguments)

        # Acquisition wrap content temporarily to make sure schema
        # interfaces can be adapted to `content`
        content = content.__of__(self.container)
        self.set_field_values(content)
        self.set_missing_values_for_empty_fields(content)
        # Remove temporary acquisition wrapper
        content = aq_base(content)

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
                field.set(field.interface(obj), self.arguments.get(name))

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
            value = getattr(field, 'default', None)

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
