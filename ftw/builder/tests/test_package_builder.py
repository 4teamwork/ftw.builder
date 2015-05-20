from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.testing import TEMP_DIRECTORY_LAYER
from path import Path
from unittest2 import TestCase
import inspect
import pkg_resources


class TestPackageBuilder(TestCase):
    layer = TEMP_DIRECTORY_LAYER

    def setUp(self):
        self.temp_directory = self.layer['temp_directory']

    def test_build_package_at_path(self):
        path = self.temp_directory.joinpath('my.package')
        package = create(Builder('python package')
                         .at_path(path)
                         .named('my.fancy.package'))

        self.assertEqual('my.fancy.package', package.name,
                         'Wrong package name')

        self.assertEqual(path, package.root_path,
                         'The root path is not the path passed'
                         ' in with .at_path')

        self.assertEqual(path.joinpath('my', 'fancy', 'package'),
                         package.package_path,
                         'The package path is wrong.')

        self.assertTrue(package.package_path.isdir(),
                        'Package directory was not created.')

        self.assertTrue(package.root_path.joinpath('setup.py').isfile(),
                        'setup.py is missing')

        self.assertTrue(package.root_path.joinpath('my', '__init__.py').isfile(),
                        'namespace __init__.py is missing (my)')

        self.assertTrue(package.root_path.joinpath('my', 'fancy', '__init__.py').isfile(),
                        'namespace __init__.py is missing (my/fancy)')

        self.assertTrue(package.package_path.joinpath('__init__.py').isfile(),
                        'package __init__.py is missing')

    def test_with_egginfo(self):
        create(Builder('python package')
               .at_path(self.temp_directory)
               .named('the.package'))

        egginfo = self.temp_directory.joinpath('the.package.egg-info')
        self.assertTrue(egginfo.isdir(), 'egg-info directory was not created.')
        self.assertTrue(egginfo.joinpath('PKG-INFO').isfile(), 'egg-info is not complete')

        self.assertFalse(self.temp_directory.joinpath('setup.pyc').isfile(), 'WAAT COMPILE SHIT')

    def test_configure_zcml_has_i18n_domain_declared(self):
        package = (Builder('python package')
                   .at_path(self.temp_directory)
                   .named('the.package'))
        package.get_configure_zcml()
        create(package)

        self.assertIn(
            'i18n_domain="the.package"',
            self.temp_directory.joinpath('the', 'package', 'configure.zcml').text())

    def test_with_subpackage(self):
        path = self.temp_directory.joinpath('my.package')

        create(Builder('python package')
               .at_path(path)
               .named('my.package')
               .with_subpackage(Builder('subpackage')
                                .named('browser')
                                .with_zcml_file()))

        package_zcml = path.joinpath('my', 'package', 'configure.zcml')
        self.assertTrue(package_zcml.isfile(),
                        'Main configure.zcml was not created.')
        self.assertIn('<include package=".browser"/>',
                      package_zcml.text(),
                      'Main package ZCML does not include browser ZCML.')

        browser_zcml = path.joinpath('my', 'package', 'browser', 'configure.zcml')
        self.assertTrue(browser_zcml.isfile(),
                        'browser package configure.zcml was not created.')

    def test_detects_name_collision_with_package(self):
        with self.assertRaises(ValueError) as cm:
            Builder('python package').named('ftw.builder')

        self.assertEqual('Invalid package name "ftw.builder": '
                         'there is already a package or module with the same name.',
                         str(cm.exception))

    def test_detects_name_collision_with_module(self):
        with self.assertRaises(ValueError) as cm:
            Builder('python package').named('ftw.builder.testing')

            self.assertEqual('Invalid package name "ftw.builder.testing": '
                         'there is already a package or module with the same name.',
                         str(cm.exception))

    def test_package_can_be_imported(self):
        path = self.layer['temp_directory'].joinpath('the.package')
        package = create(Builder('python package').named('the.package').at_path(path))
        with package:
            module = package.import_package()
            self.assertTrue(inspect.ismodule(module))
            self.assertEqual(path.joinpath('the', 'package'), Path(module.__file__).dirname())

    # We run this test two times. If the first time is not cleaned up properly
    # we will end up with a wrong module file path since the temp_directory changes
    # for each test and the module will not be imported but taken from sys.modules.
    test_package_path_is_cleaned_up = test_package_can_be_imported

    def test_context_manager_returns_package_repr(self):
        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory']))

        with package as return_value:
            self.assertEqual(package, return_value,
                             'Context manager return value should be the package repr.')

    def test_import_package_context_manager(self):
        path = self.layer['temp_directory'].joinpath('the.package')
        package = create(Builder('python package').named('the.package').at_path(path))
        with package.imported() as module:
            self.assertTrue(inspect.ismodule(module))
            self.assertEqual(path.joinpath('the', 'package'), Path(module.__file__).dirname())

    def test_pkg_resources_working_set_is_updated(self):
        path = self.layer['temp_directory'].joinpath('the.package')
        package = create(Builder('python package').named('the.package').at_path(path))

        with self.assertRaises(pkg_resources.DistributionNotFound):
            pkg_resources.get_distribution('the.package')

        with package.imported():
            self.assertTrue(pkg_resources.get_distribution('the.package'))

        with self.assertRaises(pkg_resources.DistributionNotFound):
            pkg_resources.get_distribution('the.package')

    def test_create_a_directory_in_the_root(self):
        path = self.layer['temp_directory'].joinpath('the.package')
        create(Builder('python package')
               .named('the.package')
               .at_path(path)
               .with_root_directory('docs'))
        self.assertTrue(path.joinpath('docs').isdir(),
                        'Directory "docs" was not created.')

    def test_create_a_file_in_the_root_directory(self):
        path = self.layer['temp_directory'].joinpath('the.package')
        create(Builder('python package')
               .named('the.package')
               .at_path(path)
               .with_root_file('docs/HISTORY.txt', 'CHANGELOG',
                               makedirs=True))

        history_path = path.joinpath('docs', 'HISTORY.txt')
        self.assertTrue(history_path.isfile(),
                        'File "docs/HISTORY.txt" was not created.')
        self.assertEquals('CHANGELOG', history_path.text())

    def test_create_a_directory_in_the_package(self):
        path = self.layer['temp_directory'].joinpath('the.package')
        create(Builder('python package')
               .named('the.package')
               .at_path(path)
               .with_directory('resources'))
        self.assertTrue(path.joinpath('the', 'package', 'resources').isdir(),
                        'Directory "resources" was not created.')

    def test_create_a_file_in_the_package_directory(self):
        path = self.layer['temp_directory'].joinpath('the.package')
        create(Builder('python package')
               .named('the.package')
               .at_path(path)
               .with_file('resources/print.css', 'body {}',
                          makedirs=True))

        print_path = path.joinpath('the', 'package', 'resources', 'print.css')
        self.assertTrue(print_path.isfile(),
                        'File "README.txt" was not created.')
        self.assertEquals('body {}', print_path.text())

    def test_delegates_zcml_include_to_zcml_builder(self):
        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])
                         .with_zcml_include('Products.GenericSetup'))

        self.assertIn('<include package="Products.GenericSetup"/>',
                      package.package_path.joinpath('configure.zcml').text())

    def test_delegates_zcml_node_to_zcml_builder(self):
        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])
                         .with_zcml_node('browser:page', name='hello-world'))

        self.assertIn('<browser:page name="hello-world"/>',
                      package.package_path.joinpath('configure.zcml').text())

    def test_package_version(self):
        with create(Builder('python package')
                    .named('the.package')
                    .at_path(self.layer['temp_directory'])).imported():
            self.assertEquals('1.0.0.dev0',
                              pkg_resources.get_distribution('the.package').version)

        with create(Builder('python package')
                    .named('the.package')
                    .with_version('1.2.3')
                    .at_path(self.layer['temp_directory'])).imported():
            self.assertEquals('1.2.3',
                              pkg_resources.get_distribution('the.package').version)


class TestNamespacePackage(TestCase):
    layer = TEMP_DIRECTORY_LAYER

    def setUp(self):
        self.temp_directory = self.layer['temp_directory']

    def test_creates_namespace_package(self):
        path = self.temp_directory.joinpath('ftw')
        create(Builder('namespace package').at_path(path))

        self.assertTrue(path.isdir(),
                        'Package directory was not created.')

        self.assertTrue(path.joinpath('__init__.py').isfile(),
                        'Package __init__.py file was not created.')


class TestSubPackageBuilder(TestCase):
    layer = TEMP_DIRECTORY_LAYER

    def setUp(self):
        self.temp_directory = self.layer['temp_directory']

    def test_creating_subpackage_creates_init_file(self):
        path = self.temp_directory.joinpath('browser')
        create(Builder('subpackage').at_path(path))

        self.assertTrue(path.isdir(),
                        'Package directory was not created.')

        self.assertTrue(path.joinpath('__init__.py').isfile(),
                        'Package __init__.py file was not created.')

    def test_creates_configure_zcml_on_demand(self):
        path = self.temp_directory.joinpath('browser')
        builder = (Builder('subpackage').at_path(path))

        zcml = builder.get_configure_zcml()
        self.assertEqual(zcml, builder.get_configure_zcml())
        create(builder)

        self.assertTrue(zcml.path.isfile(), 'configure.zcml file was not written')

    def test_getting_subpackage_builder(self):
        builder = Builder('subpackage')
        self.assertEquals(builder.get_subpackage('browser'),
                          builder.get_subpackage('browser'),
                          '.get_subpackage() does not always return the same builder'
                          ' for the same name.')
