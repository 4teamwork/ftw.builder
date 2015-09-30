from ftw.builder import session
from path import Path
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import Layer
from plone.testing import zca
from Products.CMFPlone.utils import getFSVersionTuple
from zope.configuration import xmlconfig
import tempfile


class BuilderLayer(Layer):

    def testSetUp(self):
        session.current_session = session.factory()

    def testTearDown(self):
        session.current_session = None


BUILDER_LAYER = BuilderLayer()


class set_builder_session_factory(Layer):

    def __init__(self, factory):
        super(set_builder_session_factory, self).__init__()
        self.factory = factory

    def setUp(self):
        self.old_factory = session.factory
        session.factory = self.factory

    def tearDown(self):
        session.factory = self.old_factory


def functional_session_factory():
    sess = session.BuilderSession()
    sess.auto_commit = True
    return sess


class TempDirectoryLayer(Layer):

    defaultBases = (BUILDER_LAYER, )

    def testSetUp(self):
        self['temp_directory'] = Path(tempfile.mkdtemp('ftw.builder'))

    def testTearDown(self):
        self['temp_directory'].rmtree_p()


TEMP_DIRECTORY_LAYER = TempDirectoryLayer()


class BuilderTestingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, TEMP_DIRECTORY_LAYER, )

    def testSetUp(self):
        zca.pushGlobalRegistry()
        self['configurationContext'] = zca.stackConfigurationContext(
            self.get('configurationContext'),
            name='ftw.builder:PACKAGE_BUILDER_LAYER')

    def testTearDown(self):
        zca.popGlobalRegistry()

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

        # register behavior
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope"'
            '           xmlns:plone="http://namespaces.plone.org/plone">'
            '    <include package="zope.component" file="meta.zcml" />'
            '    <include package="plone.behavior" file="meta.zcml" />'
            '    <include package="zope.annotation" />'
            '    <plone:behavior'
            '        title="Annotation behavior"'
            '        provides="ftw.builder.tests.test_dexterity.IAnnotationStored"'
            '        factory="plone.behavior.AnnotationStorage"'
            '    />'
            '</configure>',
            context=configurationContext)

    def setUpPloneSite(self, portal):
        if getFSVersionTuple() > (5, ):
            applyProfile(portal, 'plone.app.contenttypes:default')
        else:
            applyProfile(portal, 'plone.app.dexterity:default')
            applyProfile(portal, 'plone.app.relationfield:default')


BUILDER_FIXTURE = BuilderTestingLayer()

BUILDER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(BUILDER_FIXTURE, ), name="Builder:Integration")

BUILDER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(BUILDER_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="Builder:Functional")
