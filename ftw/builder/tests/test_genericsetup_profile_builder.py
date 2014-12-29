from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.testing import BUILDER_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase


class TestGenericSetupProfileBuilder(TestCase):
    layer = BUILDER_INTEGRATION_TESTING

    def setUp(self):
        self.genericsetup = getToolByName(self.layer['portal'], 'portal_setup')
        self.package_builder = (Builder('python package')
                                .named('the.package')
                                .at_path(self.layer['temp_directory']))

    def test_loading_generic_setup_profile(self):
        package = create(self.package_builder
                         .with_profile(Builder('genericsetup profile')
                                       .named('default')))

        self.assertFalse(self.get_profile_info('the.package:default'))
        with package.zcml_loaded(self.layer['configurationContext']):
            self.assertTrue(self.get_profile_info('the.package:default'),
                            'Generic setup profile was not loaded.')

    def test_package_infos(self):
        package = create(self.package_builder
                         .with_profile(Builder('genericsetup profile')
                                       .titled('The Package')
                                       .with_fs_version('2003')))

        with package.zcml_loaded(self.layer['configurationContext']):
            self.assertDictContainsSubset(
                {'id': u'the.package:default',
                 'title': u'The Package',
                 'version': u'2003'},
                self.get_profile_info('the.package:default'))

    def test_default_title_is_package_name(self):
        package = create(self.package_builder
                         .with_profile(Builder('genericsetup profile')))

        with package.zcml_loaded(self.layer['configurationContext']):
            self.assertDictContainsSubset(
                {'id': u'the.package:default',
                 'title': u'the.package'},
                self.get_profile_info('the.package:default'))

    def test_creating_files_in_the_profile(self):
        package = create(self.package_builder
                         .with_profile(Builder('genericsetup profile')
                                       .with_file('catalog.xml', '<object></object>')))

        catalog = package.profiles['default'].joinpath('catalog.xml')
        self.assertTrue(catalog.isfile(),
                        'catalog.xml was not created.')
        self.assertEqual('<object></object>', catalog.text())

    def test_creating_directories_in_the_profile(self):
        package = create(self.package_builder
                         .with_profile(Builder('genericsetup profile')
                                       .with_directory('workflows')
                                       .with_file('types/thing.xml', '<object></object>',
                                                  makedirs=True)))

        profile_path = package.profiles['default']
        self.assertTrue(profile_path.joinpath('workflows').isdir(),
                        'Directory "workflows" was not created.')

        type_path = profile_path.joinpath('types', 'thing.xml')
        self.assertTrue(type_path.isfile(),
                        'types/thing.xml was not created.')
        self.assertEqual('<object></object>', type_path.text())

    def test_dependencies(self):
        package = create(self.package_builder
                         .with_profile(Builder('genericsetup profile')
                                       .with_dependencies('collective.foo:default',
                                                          'profile-collective.bar:default')))

        with package.zcml_loaded(self.layer['configurationContext']):
            self.assertEquals(
                (u'profile-collective.foo:default',
                 u'profile-collective.bar:default'),
                self.genericsetup.getDependenciesForProfile('the.package:default'))

    def get_profile_info(self, profile_id):
        try:
            return self.genericsetup.getProfileInfo(profile_id)
        except KeyError:
            return None
