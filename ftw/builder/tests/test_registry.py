from unittest2 import TestCase
from ftw.builder.registry import Registry


class FooBuilder(object):
    pass


class BarBuilder(object):
    pass


class TestRegistry(TestCase):

    def test_registered_and_getting_builders(self):
        registry = Registry()

        registry.register('Foo', FooBuilder)
        registry.register('Bar', BarBuilder)

        self.assertEquals(FooBuilder, registry.get('Foo'))
        self.assertEquals(BarBuilder, registry.get('Bar'))

    def test_overriding_registered_builders_raises_ValueError(self):
        registry = Registry()
        registry.register('Foo', FooBuilder)

        with self.assertRaises(ValueError) as cm:
            registry.register('Foo', BarBuilder)

        self.assertEqual(
            'Builder "Foo" is already registered (FooBuilder)',
            str(cm.exception))

    def test_overriding_registered_builders_is_possible_with_force(self):
        registry = Registry()
        registry.register('Foo', FooBuilder)
        registry.register('Foo', BarBuilder, force=True)

        self.assertEqual(BarBuilder, registry.get('Foo'))

    def test_getting_unknown_builder_raises_KeyError(self):
        registry = Registry()

        with self.assertRaises(KeyError) as cm:
            registry.get('My Type')

        self.assertEquals(
            "'Unknown builder \"My Type\"'",
            str(cm.exception))
