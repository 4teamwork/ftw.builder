from ftw.builder import Builder
from ftw.builder import builder_registry
from ftw.builder import create


class Person(object):

    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.children = []

    def is_adult(self):
        return self.age >= 18

    def allowed_to_drink_alcohol(self):
        return self.is_adult()

    def add_child(self, child):
        self.children.append(child)


class PersonBuilder(object):

    def __init__(self, session):
        self.session = session
        self.children_names = []
        self.arguments = {}

    def of_age(self):
        self.arguments['age'] = 18
        return self

    def with_children(self, children_names):
        self.children_names = children_names
        return self

    def having(self, **kwargs):
        self.arguments.update(kwargs)
        return self

    def create(self, **kwargs):
        person = Person(
            self.arguments.get('name'),
            self.arguments.get('age'))

        for name in self.children_names:
            person.add_child(
                create(Builder('person').having(name=name, age=5))
            )

        return person

builder_registry.register('person', PersonBuilder)
