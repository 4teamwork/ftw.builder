from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.testing import BUILDER_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase


class TestPloneUpgradeBuilder(TestCase):
    layer = BUILDER_INTEGRATION_TESTING

    def setUp(self):
        self.genericsetup = getToolByName(self.layer['portal'], 'portal_setup')

    def test_registers_upgrade_for_profile_in_ZCML(self):
        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])

                         .with_profile(Builder('genericsetup profile')
                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('1000', '1001')
                                                     .titled('Add some actions...')
                                                     .with_description('Some details...'))))

        self.assertTrue(
            package.package_path.joinpath('upgrades', 'to1001.py').isfile(),
            'Upgrade step code file was not generated in expected location.')

        with package.zcml_loaded(self.layer['configurationContext']):
            upgrades = self.genericsetup.listUpgrades('the.package:default')
            self.assertEqual(1, len(upgrades), 'Expected exactly one upgrade.')
            self.assertDictContainsSubset({
                    'ssource': u'1000',
                    'sdest': u'1001',
                    'title': u'Add some actions...',
                    'description': u'Some details...',
                    }, upgrades[0])

    def test_upgrades_for_non_default_profiles_are_put_in_subpackage(self):
        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])

                         .with_profile(Builder('genericsetup profile')
                                       .named('foo')

                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('2002', '3000'))))

        self.assertTrue(
            package.package_path.joinpath('upgrades', 'foo', 'to3000.py').isfile(),
            'Upgrade step code file was not generated in expected location.')

    def test_profile_fs_version_is_automatically_set_to_last_upgrade(self):
        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])
                         .with_profile(Builder('genericsetup profile')
                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('1001', '1002'))
                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('1002', '1003'))
                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('1000', '1001'))))

        self.assertIn('<version>1003</version>',
                      package.profiles['default'].joinpath('metadata.xml').text(),
                      'Version was not automatically picked.')

    def test_disabling_version_autopick_by_setting_version_to_False(self):
        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])
                         .with_profile(Builder('genericsetup profile')
                                       .with_fs_version(False)
                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('1000', '1001'))))

        self.assertNotIn('<version',
                      package.profiles['default'].joinpath('metadata.xml').text(),
                      'Version was set even though it was disabled explicitly.')

    def test_with_calling_a_function(self):
        def the_upgrade(setup_context):
            print 'YAY, we are up to date'

        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])
                         .with_profile(Builder('genericsetup profile')
                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('1000', to='1001')
                                                     .calling(the_upgrade))))

        self.assertMultiLineEqual(
            '\n'.join(("def the_upgrade(setup_context):",
                       "    print 'YAY, we are up to date'",
                       "")),
            package.package_path.joinpath('upgrades', 'to1001.py').text())

    def test_with_calling_a_class(self):
        class TheUpgrade(TestCase, tuple):
            def __init__(self, setup_context):
                print 'This is not an upgrade and does not work...'

        package = create(Builder('python package')
                         .named('the.package')
                         .at_path(self.layer['temp_directory'])
                         .with_profile(Builder('genericsetup profile')
                                       .with_upgrade(Builder('plone upgrade step')
                                                     .upgrading('1000', to='1001')
                                                     .calling(TheUpgrade))))

        self.assertMultiLineEqual(
            '\n'.join((
                    "from unittest2.case import TestCase",
                    "",
                    "",
                    "class TheUpgrade(TestCase, tuple):",
                    "    def __init__(self, setup_context):",
                    "        print 'This is not an upgrade and does not work...'",
                    "")),
            package.package_path.joinpath('upgrades', 'to1001.py').text())
