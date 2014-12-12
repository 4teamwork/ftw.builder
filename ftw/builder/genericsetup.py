from ftw.builder import builder_registry
from lxml import etree
from path import Path


class GenericSetupBuilder(object):
    """Creates a Generic Setup profile within a python package.
    """

    def __init__(self, session):
        self.session = session
        self.name = 'default'
        self.title = None
        self.fs_version = None
        self.dependencies = []
        self.package = None
        self.path = None
        self.directories = []
        self.files = []

    def named(self, name):
        """Change the name of the profile.
        The name is "default" by default.
        """
        self.name = name
        return self

    def titled(self, title):
        """Set the title of the profile.
        By default the name of the profile is used as title.
        """
        self.title = title
        return self

    def with_fs_version(self, fs_version):
        """Set the filesystem version of the profile (metadata.xml).
        """
        self.fs_version = fs_version
        return self

    def with_directory(self, relative_path):
        """Create a directory in the profile.
        """
        self.directories.append(relative_path)
        return self

    def with_file(self, relative_path, contents, makedirs=False):
        """Create a file within this package.
        """
        if makedirs and Path(relative_path).parent:
            self.with_directory(Path(relative_path).parent)

        self.files.append((relative_path, contents))
        return self

    def with_dependencies(self, *profile_ids):
        """Add Generic Setup dependencies to the profile.
        Provide one or many profile ids as positional arguments.
        """
        for profile_id in profile_ids:
            if not profile_id.startswith('profile-'):
                profile_id = 'profile-{0}'.format(profile_id)
            if profile_id not in self.dependencies:
                self.dependencies.append(profile_id)
        return self

    def within(self, package):
        """Declare the package (subpackage builder) where the profile
        should be created.
        """
        self.package = package
        return self

    def create(self):
        if self.package is None:
            raise ValueError(
                'GS profile builder requires a package,'
                ' register it with PythonPackageBuilder.with_profile(..)'
                ' or use .within(package).')

        self.path = self.package.path.joinpath('profiles', self.name)
        self.path.makedirs()
        self._prepare_metadata_xml()
        self._register_zcml()

        for relative_path in self.directories:
            self.path.joinpath(relative_path).makedirs()

        for path, contents in self.files:
            self.path.joinpath(path).write_text(contents)

        return self.path

    def _prepare_metadata_xml(self):
        root = etree.Element('metadata')
        if self.fs_version:
            etree.SubElement(root, 'version').text = self.fs_version

        if self.dependencies:
            dependencies_node = etree.SubElement(root, 'dependencies')
            for profile_id in self.dependencies:
                node = etree.SubElement(dependencies_node, 'dependency')
                node.text = profile_id

        document = etree.tostring(root, pretty_print=True,
                                  xml_declaration=True, encoding='utf-8')
        self.with_file('metadata.xml', document)

    def _register_zcml(self):
        self.package.with_zcml_include('Products.GenericSetup')
        self.package.with_zcml_node(
            'genericsetup:registerProfile',
            name=self.name,
            title=self.title or self.name,
            directory=self.path.relpath(self.package.path),
            provides='Products.GenericSetup.interfaces.EXTENSION')


builder_registry.register('genericsetup profile', GenericSetupBuilder)
