from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.testing import BUILDER_INTEGRATION_TESTING
from unittest2 import TestCase


class TestPackageBuilderZCML(TestCase):
    layer = BUILDER_INTEGRATION_TESTING

    def test_loading_zcml_with_context_manager(self):
        package = create(
            Builder('python package')
            .named('the.package')
            .at_path(self.layer['temp_directory'])

            .with_subpackage(
                Builder('subpackage')
                .named('browser')

                .with_file('hello_world.pt', '"Hello World"')
                .with_zcml_node('browser:page',
                                **{'name': 'hello-world.json',
                                   'template': 'hello_world.pt',
                                   'permission': 'zope2.View',
                                   'for': '*'})))

        with package.zcml_loaded(self.layer['configurationContext']):
            self.assertEqual('"Hello World"',
                             self.layer['portal'].restrictedTraverse('hello-world.json')())

    def test_loading_zcml_with_load_zcml_method(self):
        package = create(
            Builder('python package')
            .named('the.package')
            .at_path(self.layer['temp_directory'])

            .with_file('good_morning.pt', '"Good Morning"')
            .with_zcml_node('browser:page',
                            **{'name': 'good_morning.json',
                               'template': 'good_morning.pt',
                               'permission': 'zope2.View',
                               'for': '*'}))

        with package:
            package.load_zcml(self.layer['configurationContext'])
            self.assertEqual('"Good Morning"',
                             self.layer['portal'].restrictedTraverse('good_morning.json')())
