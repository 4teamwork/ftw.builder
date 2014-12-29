from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.testing import TEMP_DIRECTORY_LAYER
from unittest2 import TestCase


class TestZCMLBuilder(TestCase):
    layer = TEMP_DIRECTORY_LAYER

    def setUp(self):
        self.temp_directory = self.layer['temp_directory']

    def test_build_zcml_file_at_path(self):
        path = self.temp_directory.joinpath('fancy.zcml')
        create(Builder('zcml').at_path(path))

        self.assertTrue(path.isfile(), 'ZCML file not created at {0}'.format(path))
        with open(path) as zcml_file:
            zcml = zcml_file.read()

        self.assertEqual('<configure xmlns="http://namespaces.zope.org/zope"/>\n', zcml)

    def test_add_node(self):
        builder = Builder('zcml').with_node('include', package='foo.bar')
        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope">',
             '  <include package="foo.bar"/>',
             '</configure>'),
            builder)

    def test_add_node_with_known_nondefault_namespace_by_default_prefix(self):
        builder = (Builder('zcml')
                   .with_node('include', package='foo.bar')
                   .with_node('genericsetup:registerProfile', name='default'))
        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope"'
             ' xmlns:genericsetup="http://namespaces.zope.org/genericsetup">',
             '  <include package="foo.bar"/>',
             '  <genericsetup:registerProfile name="default"/>',
             '</configure>'),
            builder)

    def test_add_node_with_unknown_namespace_by_url(self):
        builder = (Builder('zcml')
                   .with_node('{http://namespaces.zope.org/foobar}doit'))
        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope"'
             ' xmlns:foobar="http://namespaces.zope.org/foobar">',
             '  <foobar:doit/>',
             '</configure>'),
            builder)

    def test_include_package(self):
        builder = (Builder('zcml')
                   .include('Products.GenericSetup', file='meta.zcml')
                   .include('Products.CMFPlone')
                   .include(file='profiles.zcml'))

        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope">',
             '  <include file="meta.zcml" package="Products.GenericSetup"/>',
             '  <include package="Products.CMFPlone"/>',
             '  <include file="profiles.zcml"/>',
             '</configure>'),
            builder)

    def test_include_zcml_builder_in_same_directory(self):
        configure = (
            Builder('zcml')
            .at_path(self.temp_directory.joinpath('configure.zcml'))
            .include(Builder('zcml')
                     .at_path(self.temp_directory.joinpath('profiles.zcml'))))

        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope">',
             '  <include file="profiles.zcml"/>',
             '</configure>'),
            configure)

    def test_include_zcml_builder_in_sub_package(self):
        configure = (
            Builder('zcml')
            .at_path(self.temp_directory.joinpath('configure.zcml'))
            .include(Builder('zcml')
                     .at_path(self.temp_directory.joinpath('browser', 'configure.zcml')))
            .include(Builder('zcml')
                     .at_path(self.temp_directory.joinpath('zcml', 'meta.zcml'))))

        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope">',
             '  <include package=".browser"/>',
             '  <include file="meta.zcml" package=".zcml"/>',
             '</configure>'),
            configure)

    def test_inclusion_does_not_use_path_too_early(self):
        # The problem is that at_path may be set just before create() by a another builder.
        # Therefore "building" the ZCML should not depend on the path, but creating can.

        main_builder = Builder('zcml')
        sub_builder = Builder('zcml')
        main_builder.include(sub_builder)

        main_builder.at_path(self.temp_directory.joinpath('configure.zcml'))
        sub_builder.at_path(self.temp_directory.joinpath('browser', 'configure.zcml'))

        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope">',
             '  <include package=".browser"/>',
             '</configure>'),
            main_builder)

    def test_get_relative_dottedname(self):
        builder = Builder('zcml').at_path(self.temp_directory.joinpath('configure.zcml'))

        self.assertEqual(
            '.browser.views.EditView',

            builder.get_relative_dottedname(self.temp_directory.joinpath('browser', 'views.py'),
                                            'EditView'))

    def test_i18n_domain(self):
        builder = Builder('zcml').with_i18n_domain('my.package')

        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope"'
             ' xmlns:i18n="http://namespaces.zope.org/i18n"'
             ' i18n_domain="my.package"/>'),
            builder)

    def test_nested_structures(self):
        builder = Builder('zcml')
        condition = builder.create_node('configure', **{'condition': 'installed foobar'})
        builder.include('foobar', parent=condition)
        builder.create_node('something', condition)

        self.assert_zcml(
            ('<configure xmlns="http://namespaces.zope.org/zope">',
             '  <configure condition="installed foobar">',
             '    <include package="foobar"/>',
             '    <something/>',
             '  </configure>',
             '</configure>'),
            builder)

    def assert_zcml(self, expected, builder):
        if isinstance(expected, tuple):
            expected = '\n'.join(expected)

        self.assertMultiLineEqual(expected.strip() + '\n',
                                  builder.generate().strip() + '\n')
