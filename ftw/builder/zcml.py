from ftw.builder import builder_registry
from lxml import etree
from path import Path
from StringIO import StringIO


NAMESPACES = {
    'browser': 'http://namespaces.zope.org/browser',
    'five': 'http://namespaces.zope.org/five',
    'genericsetup': 'http://namespaces.zope.org/genericsetup',
    'grok': 'http://namespaces.zope.org/grok',
    'i18n': 'http://namespaces.zope.org/i18n',
    'inflator': 'http://namespaces.zope.org/inflator',
    'lawgiver': 'http://namespaces.zope.org/lawgiver',
    'meta': 'http://namespaces.zope.org/meta',
    'monkey': 'http://namespaces.plone.org/monkey',
    'plone': 'http://namespaces.plone.org/plone',
    'profilehook': 'http://namespaces.zope.org/profilehook',
    'transmogrifier': 'http://namespaces.plone.org/transmogrifier',
    'upgrade-step': 'http://namespaces.zope.org/ftw.upgrade',
    'zcml': 'http://namespaces.zope.org/zcml',
    }
NAMESPACE_PREFIXES = dict((value, key) for (key, value) in NAMESPACES.items())


class ZCMLBuilder(object):

    def __init__(self, session):
        self.session = session
        self.path = None
        self.root = etree.Element("configure", nsmap={
                None: 'http://namespaces.zope.org/zope'})
        self.lazy_nodes = []

    def at_path(self, path):
        self.path = Path(path)
        return self

    def with_i18n_domain(self, domain):
        self.load_namespace('i18n')
        self.root.attrib['i18n_domain'] = domain
        return self

    def with_node(self, tagname, parent=None, **attributes):
        self.create_node(tagname, parent, **attributes)
        return self

    def create_node(self, tagname, parent=None, **attributes):
        tagname = self._prepare_and_convert_namespace_in_tagname(tagname)
        if parent is None:
            parent = self.root
        return etree.SubElement(parent, tagname, **attributes)

    def with_lazy_node(self, callback, parent=None):
        """Creates a placeholder in the document.
        The placeholder will be updated on creation time by calling the
        callback and using its return value to update the node.
        The callback must return a tuple of tagname and attributes (dict).
        """
        if parent is None:
            parent = self.root
        node = etree.SubElement(parent, 'lazy_node')
        self.lazy_nodes.append((node, callback))
        return self

    def include(self, package_or_builder='.', parent=None, **attributes):
        # Inclusion must be done with a lazy node since we rely on the path,
        # but the path may not yet be set.
        def callback():
            if isinstance(package_or_builder, ZCMLBuilder):
                if attributes:
                    raise ValueError('Cannot set additional attributes'
                                     ' when including builder.')

                dirname, filename = package_or_builder.path.splitpath()
                package = self.get_relative_dottedname(dirname)
                if package != '.':
                    attributes['package'] = package
                if filename != 'configure.zcml':
                    attributes['file'] = filename

            elif package_or_builder != '.':
                attributes['package'] = package_or_builder

            return ('include', attributes)
        return self.with_lazy_node(callback, parent=parent)

    def get_relative_dottedname(self, path, *postfix):
        path = Path(path).relpath(self.path.dirname())
        if path.name.endswith('.py'):
            path = path.splitext()[0]
        if path.name != '.' and '.' in path.name:
            raise ValueError('Unsupported filename extension: {0}'.format(
                    path.name))
        return '.'.join(path.splitall() + list(postfix))

    def load_namespace(self, prefix, url=None):
        if url is None:
            url = NAMESPACES[prefix]

        if prefix in self.root.nsmap:
            assert self.root.nsmap[prefix] == url, \
                'Invalid prefix "{0}" for url "{1}", there is already an' + \
                ' url "{2}" for the same prefix'.format(
                prefix, url, self.root.nsmap[prefix])
            return

        new_nsmap = self.root.nsmap.copy()
        new_nsmap[prefix] = url
        new_root = etree.Element(self.root.tag, nsmap=new_nsmap)
        for child in self.root.getchildren():
            new_root.append(child)
        self.root = new_root

    def create(self):
        with self.path.open('w+') as zcml_file:
            zcml_file.write(self.generate())
        return self.path

    def generate(self):
        self._update_lazy_nodes()

        normalized = StringIO()
        self.root.getroottree().write_c14n(normalized)
        xml = etree.fromstring(normalized.getvalue())
        return etree.tostring(xml, pretty_print=True,
                              encoding='utf8').decode('utf-8')

    def _update_lazy_nodes(self):
        for node, callback in self.lazy_nodes:
            tagname, attributes = callback()
            tagname = self._prepare_and_convert_namespace_in_tagname(tagname)
            node.tag = tagname
            node.attrib.update(attributes)

    def _prepare_and_convert_namespace_in_tagname(self, tagname):
        if not tagname.startswith('{') and ':' in tagname:
            prefix, tagname = tagname.split(':', 1)
            tagname = '{%s}%s' % (NAMESPACES[prefix], tagname)

        if tagname.startswith('{'):
            url = tagname[1:].split('}', 1)[0]
            if url in NAMESPACE_PREFIXES:
                prefix = NAMESPACE_PREFIXES[url]
            else:
                prefix = url.split('/')[-1]
            self.load_namespace(prefix, url)

        return tagname


builder_registry.register('zcml', ZCMLBuilder)
