from ftw.builder.utils import parent_namespaces
from ftw.builder.utils import serialize_callable
from unittest2 import TestCase


class TestParentNamespaces(TestCase):

    def test_returns_a_list_of_parent_namespaces_in_order(self):
        self.assertEqual(
            ['one', 'one.two', 'one.two.three'],
            parent_namespaces('one.two.three.four'))

    def test_returns_empty_list_for_first_level_dottednames(self):
        self.assertEqual(
            [],
            parent_namespaces('one'))


class TestCallableSerializer(TestCase):

    def test_serializing_function(self):
        def foo(bar):
            """Prints the argument
            """
            print 'bar is:', bar
            return bar

        self.assertMultiLineEqual('''
def foo(bar):
    """Prints the argument
    """
    print 'bar is:', bar
    return bar
'''.lstrip(), serialize_callable(foo))

    def test_serializing_class_imports_superclasses(self):
        class TestSomething(TestCase):
            def test(self):
                assert 'something'

        self.assertMultiLineEqual('''
from unittest2.case import TestCase


class TestSomething(TestCase):
    def test(self):
        assert 'something'
'''.lstrip(), serialize_callable(TestSomething))

    def test_builtins_are_not_imported(self):
        class Foo(tuple):
            pass

        self.assertMultiLineEqual('''
class Foo(tuple):
    pass
'''.lstrip(), serialize_callable(Foo))

    def test_globals_to_import_can_be_passed_as_positional_arguments(self):
        def print_docs():
            print parent_namespaces.__docs__
            print serialize_callable.__docs__

        self.assertMultiLineEqual('''
from ftw.builder.utils import parent_namespaces
from ftw.builder.utils import serialize_callable


def print_docs():
    print parent_namespaces.__docs__
    print serialize_callable.__docs__
'''.lstrip(), serialize_callable(print_docs, parent_namespaces, serialize_callable))

    def test_callable_is_required(self):
        with self.assertRaises(ValueError) as cm:
            serialize_callable(1)

        self.assertEquals('A callable is required.',
                          str(cm.exception))
