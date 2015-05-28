from ftw.builder import builder_registry
from ftw.builder import create
from ftw.builder.utils import serialize_callable
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
        self.package_name = None
        self.directories = []
        self.files = []
        self.upgrades = []

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

    def with_upgrade(self, upgrade_builder):
        """Adds an upgrade builder for this profile.
        """
        self.upgrades.append(upgrade_builder.for_profile(self))
        return self

    def with_package_name(self, package_name):
        """Sets the package name.
        """
        self.package_name = package_name
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

        self.profile_name = ':'.join((self.package_name, self.name))
        self.path = self.package.path.joinpath('profiles', self.name)
        self.path.makedirs()
        self._prepare_metadata_xml()
        self._register_zcml()
        map(create, self.upgrades)

        for relative_path in self.directories:
            self.path.joinpath(relative_path).makedirs_p()

        for path, contents in self.files:
            self.path.joinpath(path).write_text(contents)

        return self.path

    def _autopick_version_by_upgrades(self):
        if self.fs_version is not None:
            return

        for upgrade in self.upgrades:
            if not self.fs_version or upgrade.destination_version > self.fs_version:
                self.fs_version = upgrade.destination_version

    def _prepare_metadata_xml(self):
        self._autopick_version_by_upgrades()
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
            title=self.title or self.package_name,
            directory=self.path.relpath(self.package.path),
            provides='Products.GenericSetup.interfaces.EXTENSION')

builder_registry.register('genericsetup profile', GenericSetupBuilder)


def noop_upgrade(setup_context):
    """Default noop upgrade step.
    """
    return


class PloneUpgradeStepBuilder(object):

    def __init__(self, session):
        self.session = session
        self.source_version = None
        self.destination_version = None
        self.title = None
        self.description = None
        self.profile_builder = None
        self.code = None
        self.funcname = None
        self.calling(noop_upgrade)

    def upgrading(self, from_, to):
        """Set the source and destionation version for this upgrade step.
        """
        self.source_version = from_
        self.destination_version = to
        return self

    def titled(self, title):
        """Sets the title of the upgrade step.
        """
        self.title = title
        return self

    def with_description(self, description):
        """Sets the description of the upgrade step.
        """
        self.description = description
        return self

    def with_code(self, python_code_as_string, function_or_classname):
        """Sets the python code of the upgrade.
        The python code is passed as string ``python_code_as_string``
        and will be written directly to the python file.
        For registering it properly in the ZCML, the name of the callable
        must be set with the ``function_or_classname`` argument.
        """
        self.code = python_code_as_string
        self.funcname = function_or_classname
        return self

    def calling(self, callable_, *to_import):
        """Make the upgrade step execute the callable passed as argument.
        The callable will be serialized to a string.

        If the callable is a class, superclasses are automatically imported.
        Other globals are not imported and need to be passed to ``calling``
        as additional positional arguments.
        """

        source = serialize_callable(callable_, *to_import)
        return self.with_code(source, callable_.__name__)

    def for_profile(self, profile_builder):
        """Set the profile builder for this up
        """
        self.profile_builder = profile_builder
        return self

    def create(self):
        if not self.source_version or not self.destination_version:
            raise ValueError('Source and destination versions are required.'
                             ' Use .upgrade(from, to).')
        if not self.profile_builder:
            raise ValueError('Unkown profile for the upgrade step:'
                             ' Use GenericSetupBuilder.with_upgrade(this)')

        basename = 'to{0}'.format(self.destination_version.replace('.', '_'))
        package = self.profile_builder.package.get_subpackage('upgrades')
        if self.profile_builder.name != 'default':
            package = package.get_subpackage(self.profile_builder.name)

        package.with_file('{0}.py'.format(basename), self.code)
        package.with_zcml_node(
            'genericsetup:upgradeStep',
            title=self.title or '',
            description=self.description or '',
            source=self.source_version,
            destination=self.destination_version,
            handler='.'.join(('', basename, self.funcname)),
            profile=self.profile_builder.profile_name)


builder_registry.register('plone upgrade step', PloneUpgradeStepBuilder)
