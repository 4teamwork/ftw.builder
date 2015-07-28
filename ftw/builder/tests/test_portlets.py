from ftw.builder import Builder
from ftw.builder import create
from ftw.builder.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from Products.CMFPlone.utils import getFSVersionTuple


class TestStaticPortletBuilder(FunctionalTestCase):

    def setUp(self):
        super(TestStaticPortletBuilder, self).setUp()

    @browsing
    def test_static_portlet_found_in_leftcolumn(self, browser):
        portlet_text = 'Hello Left Column'
        create(Builder('static portlet')
               .titled('My Static Portlet')
               .having(text='<p>{0}</p>'.format(portlet_text)))

        browser.login().open(self.portal)
        column_one = browser.css('#portal-column-one')

        # Test the portlet header.
        self.assertEqual(
            'My Static Portlet',
            column_one.css('.portletHeader').first.text
        )

        # Test the portlet content.
        css_selector = '.portletItem'
        if getFSVersionTuple() >= (5,):
            css_selector = '.portletContent'

        self.assertEqual(
            portlet_text,
            column_one.css(css_selector).first.text
        )

    @browsing
    def test_static_portlet_found_in_rightcolumn(self, browser):
        portlet_text = 'Hello Right Column'
        create(Builder('static portlet')
               .titled('My Static Portlet')
               .having(text='<p>{0}</p>'.format(portlet_text))
               .in_manager(u'plone.rightcolumn'))

        browser.login().open(self.portal)
        column_two = browser.css('#portal-column-two')

        # Test the portlet header.
        self.assertEqual(
            'My Static Portlet',
            column_two.css('.portletHeader').first.text
        )

        # Test the portlet content.
        css_selector = '.portletItem'
        if getFSVersionTuple() >= (5,):
            css_selector = '.portletContent'

        self.assertEqual(
            portlet_text,
            column_two.css(css_selector).first.text
        )


class TestNavigationPortletBuilder(FunctionalTestCase):

    def setUp(self):
        super(TestNavigationPortletBuilder, self).setUp()

    @browsing
    def test_navi_portlet_found_in_leftcolumn(self, browser):
        self.grant('Manager')
        create(Builder('folder').titled(u'My Folder'))

        create(Builder('navigation portlet')
               .titled('My Navigation Portlet')
               .having(includeTop=True, topLevel=0))

        browser.login().open(self.portal)
        column_one = browser.css('#portal-column-one')

        # Test the portlet header.
        self.assertEqual(
            'My Navigation Portlet',
            column_one.css('.portletHeader').first.text
        )

        # Test the portlet content.
        css_selector = '.portletItem  ul li'
        if getFSVersionTuple() >= (5,):
            css_selector = '.portletContent ul li'

        self.assertEqual(
            ['Home', 'My Folder'],
            column_one.css(css_selector).text
        )
