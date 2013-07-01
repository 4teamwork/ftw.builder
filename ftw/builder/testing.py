from ftw.builder import session
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import Layer
from zope.configuration import xmlconfig


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


class BuilderLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)


BUILDER_FIXTURE = BuilderLayer()

BUILDER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(BUILDER_FIXTURE, ), name="Builder:Integration")

BUILDER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(BUILDER_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="Builder:Functional")
