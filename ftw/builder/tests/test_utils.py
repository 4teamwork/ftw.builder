from unittest2 import TestCase
from ftw.builder.utils import parent_namespaces


class TestParentNamespaces(TestCase):

    def test_returns_a_list_of_parent_namespaces_in_order(self):
        self.assertEqual(
            ['one', 'one.two', 'one.two.three'],
            parent_namespaces('one.two.three.four'))

    def test_returns_empty_list_for_first_level_dottednames(self):
        self.assertEqual(
            [],
            parent_namespaces('one'))
