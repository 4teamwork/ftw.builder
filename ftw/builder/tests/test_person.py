from ftw.builder import Builder
from ftw.builder import create
from ftw.builder import session
from ftw.builder.tests import person
import unittest2


class TestPerson(unittest2.TestCase):

    def setUp(self):
        session.current_session = session.factory()

    def tearDown(self):
        session.current_session = None

    def test_18_is_adult(self):
        hugo = create(Builder('person')
                      .having(name='Hugo Boss', age=18))

        self.assertTrue(hugo.is_adult())

    def test_under_18_is_not_adult(self):
        peter = create(Builder('person')
                       .having(name='Peter Muster', age=17))

        self.assertFalse(peter.is_adult())

    def test_adult_is_allowed_to_drink(self):
        adult = create(Builder('person')
                       .of_age())

        self.assertTrue(adult.allowed_to_drink_alcohol())

    def test_parents_have_children(self):
        parent = create(Builder('person')
                        .with_children(['peter', 'sophie', 'james']))

        self.assertEquals(['peter', 'sophie', 'james'],
                          [child.name for child in parent.children])

if __name__ == "__main__":
    unittest2.main()
