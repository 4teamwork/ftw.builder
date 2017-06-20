from contextlib import contextmanager
from ftw.builder import Builder
from ftw.builder import builder_registry
from ftw.builder import create
from ftw.builder.utils import parent_namespaces
from path import Path
from zope.configuration import xmlconfig
import imp
import pkg_resources
import stat
import subprocess
import sys


SETUP_PY_TEMPLATE = """
from setuptools import setup, find_packages

setup(name='{name}',
      version='{version}',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages={namespaces},
      include_package_data=True,
      zip_safe=False,

      install_requires=[
        'setuptools',
      ])
"""


NAMESPACE_INIT_TEMPLATE = """
# See http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
"""


EGGINFO_BUILDER = """#!{executable}

import runpy
import sys

sys.dont_write_bytecode = True
sys.path[0:0] = ['{setuptools_path}']
sys.argv.append('egg_info')
runpy.run_module('setup')
"""


class Package(object):
    """A ``Package`` object is created when creating a python package
    using the "python package" builder.
    It contains infos about the package, such as useful paths and can
    be used for importing the package and doing things such as loading
    the ZCML.

    The object can be used as context manager to add the package temporarily to
    the python package so that it can be imported.
    When the context manager is exited, the package is removed from the python
    path and the currently loaded modules (sys.modules) is cleaned up.
    """

    def __init__(self, name, root_path, package_path, profiles=None):
        self.name = name
        self.root_path = root_path
        self.package_path = package_path
        self.profiles = profiles or {}

    def __enter__(self):
        sys.path.insert(0, self.root_path)
        self._original_working_set = pkg_resources.working_set
        pkg_resources.working_set = pkg_resources.WorkingSet._build_master()
        return self

    def __exit__(self, type, value, tb):
        pkg_resources.working_set = self._original_working_set
        sys.path.remove(self.root_path)
        modules_to_remove = filter(lambda name: name.startswith(self.name),
                                   sys.modules)
        modules_to_remove += (set(sys.modules.keys())
                              & set(parent_namespaces(self.name)))
        for name in modules_to_remove:
            del sys.modules[name]

    def import_package(self):
        """Imports the package and returns its module.
        This is only possible within a block where the package is used as a
        context manager (with statement), otherwise it may raise
        an ``ImportError``.
        """
        return __import__(self.name, fromlist=self.name)

    @contextmanager
    def imported(self):
        """A context manager which returns the imported module object.
        It extends the default context manager for extending the python path to
        make the module importable.
        On exit, the python path and sys.modules is cleaned up.
        """
        with self:
            yield self.import_package()

    def load_zcml(self, configuration_context):
        """Loads the configure.zcml of the package.
        """
        module = self.import_package()
        xmlconfig.file('configure.zcml', module, context=configuration_context)

    @contextmanager
    def zcml_loaded(self, configuration_context):
        """A context manager which loads the configure.zcml of the package.
        For doing that, the module of the package is imported.
        The context manager returns the module.
        On exit, the python path and sys.modules is cleaned up.
        """
        with self:
            self.load_zcml(configuration_context)
            yield self


class PythonPackageBuilder(object):
    """The python package builder builds a fully functional python package
    with setup.py, namespace packages and egg-info.
    """

    def __init__(self, session):
        self.session = session
        self.path = None
        self.name = None
        self.version = '1.0.0.dev0'
        self.namespaces = None
        self.package = Builder('subpackage')
        self.directories = []
        self.files = []
        self.profiles = []

    def at_path(self, path):
        """Set the path on the filesystem where the python package should be put,
        usually a temporary directory.
        No subdirectory is created, the ``setup.py`` is written directly
        into this path.
        """
        self.path = Path(path)
        return self

    def named(self, name):
        """Set the dottedname of the package.
        """
        self._validate_package_name(name)
        self.name = name
        self.package.with_i18n_domain(name)
        return self

    def with_version(self, version):
        """Change the package version.
        """
        self.version = version
        return self

    def with_subpackage(self, subpackage_builder):
        """Register a subpackage by passing a "subpackage" builder as argument.
        The subpackage builder should have a name (use .named()),
        the location / path is automatically set.
        """
        self.package.with_subpackage(subpackage_builder)
        return self

    def with_profile(self, profile_builder):
        """Register a generic setup profile for creation.
        """
        self.profiles.append(profile_builder.with_package_name(self.name).within(self.package))
        return self

    def with_root_directory(self, relative_path):
        """Creates a directory relative to the root directory.
        """
        self.directories.append(relative_path)
        return self

    def with_root_file(self, relative_path, contents, makedirs=False):
        """Creates a file relative to the root directory.
        """
        if makedirs and Path(relative_path).parent:
            self.with_root_directory(Path(relative_path).parent)

        self.files.append((relative_path, contents))
        return self

    def with_directory(self, relative_path):
        """Creates a directory relative to the package directory.
        """
        self.package.with_directory(relative_path)
        return self

    def with_file(self, relative_path, contents, makedirs=False):
        """Creates a file relative to the main package directory.
        """
        self.package.with_file(relative_path, contents, makedirs=makedirs)
        return self

    def with_zcml_file(self):
        """Trigger building a ZCML file.
        """
        self.package.with_zcml_file()
        return self

    def with_zcml_include(self, *args, **kwargs):
        """Delegates a ZCML inclusion to the configure.zcml builder.
        """
        self.package.with_zcml_include(*args, **kwargs)
        return self

    def with_zcml_node(self, *args, **kwargs):
        """Delegates a ZCML node declaration to the configure.zcml builder.
        """
        self.package.with_zcml_node(*args, **kwargs)
        return self

    def get_configure_zcml(self):
        """Returns the configure.zcml builder of the package.
        """
        return self.package.get_configure_zcml()

    def create(self):
        assert self.path, 'Use PackageBuilder.at_path(path) to' + \
            ' set a path to create the package in.'
        assert self.name, 'Use PackageBuilder.named(name) to' + \
            ' set the dottedname of the package.'
        self.path.mkdir_p()

        self.package.at_path(self.path.joinpath(*self.name.split('.')))
        self._create_setup()
        self._create_namespaces()
        profile_paths = dict((builder.name, create(builder))
                             for builder in self.profiles)
        package_path = create(self.package)

        for relative_path in self.directories:
            self.path.joinpath(relative_path).makedirs()

        for relative_path, contents in self.files:
            self.path.joinpath(relative_path).write_text(contents)

        self._build_egginfo()
        return Package(self.name, self.path, package_path,
                       profiles=profile_paths)

    def _create_setup(self):
        self.with_root_file('setup.py', SETUP_PY_TEMPLATE.format(
                name=self.name,
                version=self.version,
                namespaces=parent_namespaces(self.name)))

    def _create_namespaces(self):
        for dottedname in parent_namespaces(self.name):
            path = self.path.joinpath(*dottedname.split('.'))
            create(Builder('namespace package').at_path(path))

    def _build_egginfo(self):
        # The current Python (sys.executable) might not have setuptools
        # in its path.
        # For avoiding an error we generate an egginfo_builder script
        # which works around this problem.

        import setuptools
        setuptools_path = Path(setuptools.__file__).dirname().dirname()

        egginfo_builder = self.path.joinpath('egginfo_builder')
        egginfo_builder.write_text(EGGINFO_BUILDER.format(
                executable=sys.executable,
                setuptools_path=setuptools_path))

        try:
            egginfo_builder.chmod(stat.S_IRUSR | stat.S_IXUSR)

            process = subprocess.Popen(egginfo_builder, cwd=str(self.path),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            _, stderrdata = process.communicate()
            assert process.returncode == 0, 'Failed to run "{0}":\n{1}'.format(
                egginfo_builder, stderrdata)

        finally:
            egginfo_builder.remove()

    def _validate_package_name(self, name):
        """For avoiding import collisions package names which are already somehow used
        are not allowed.
        """

        def find_module(dottedname, paths=None):
            # imp.find_module does not support dottednames, it can only
            # resolve one name level at the time.
            # This find_module function does the recursion so that
            # dottednames work.
            if '.' in dottedname:
                name, dottedname = dottedname.split('.', 1)
            else:
                name = dottedname
                dottedname = None

            fp, pathname, description = imp.find_module(name, paths)
            if not dottedname:
                return fp, pathname, description
            else:
                return find_module(dottedname, [pathname])

        try:
            fp, pathname, description = find_module(name)
        except ImportError:
            return True

        else:
            raise ValueError(
                'Invalid package name "{0}": there is already'
                ' a package or module with the same name.'.format(name))


builder_registry.register('python package', PythonPackageBuilder)


class NamespacePackageBuilder(object):
    """The namespace package builder builds a single namespace level.
    """

    def __init__(self, session):
        self.session = session
        self.path = None

    def at_path(self, path):
        self.path = Path(path)
        return self

    def create(self):
        self.path.mkdir_p()
        self.path.joinpath('__init__.py').write_text(NAMESPACE_INIT_TEMPLATE)
        return self.path


builder_registry.register('namespace package', NamespacePackageBuilder)


class SubPackageBuilder(object):
    """The subpackage builder builds the deepest level of a python package.
    It may build a configure.zcml and can manage nested subpackages.

    The filesystem path of the subpackage is either defined by setting
    a name (with ``.named('name')``) and a parent package
    (using ``.within(parent_package)``)
    or by explicitly setting the path (with ``.at_path(path)``)
    """

    def __init__(self, session):
        self.session = session
        self.name = None
        self.parent_package = None
        self.path = None
        self.configure_zcml = None
        self.i18n_domain = None
        self.subpackages = []
        self.directories = []
        self.files = [('__init__.py', '')]

    def named(self, name):
        """The last part of the dottedname representing this subpackage.
        E.g. when building a browser subpackage, the name is just "browser".
        """
        if self.path:
            raise ValueError('Using .at_path() and .named() / .within()'
                             ' for the same builder is not allowed.')

        self.name = name
        return self

    def within(self, parent_package):
        """Register a parent package.
        """
        if self.path:
            raise ValueError('Using .at_path() and .named() / .within()'
                             ' for the same builder is not allowed.')

        self.parent_package = parent_package
        return self

    def at_path(self, path):
        """Set the absolute filesystem path for the subpackage.
        """
        if self.path or self.parent_package:
            raise ValueError('Using .at_path() and .named() / .within()'
                             ' for the same builder is not allowed.')

        self.path = Path(path)
        return self

    def with_subpackage(self, subpackage_builder):
        """Nest another subpackage builder within this subpackage.
        Nested subpackages will automatically be created when
        this package is created.
        """
        subpackage_builder.within(self)
        self.subpackages.append(subpackage_builder)
        return self

    def get_subpackage(self, name):
        """Returns a nested subpackage builder with a specific name.
        If there is already a builder with this name, the existing
        builder is returned.
        """
        for subbuilder in self.subpackages:
            if subbuilder.name == name:
                return subbuilder
        subbuilder = Builder('subpackage').named(name)
        self.with_subpackage(subbuilder)
        return subbuilder

    def with_i18n_domain(self, domain):
        """Set the i18n-domain for the ZCML file.
        This does not trigger ZCML file creation.
        """
        self.i18n_domain = domain
        return self

    def with_zcml_file(self):
        """Trigger creating a configure.zcml.
        """
        self.get_configure_zcml()
        return self

    def with_directory(self, relative_path):
        """Create a directory relative to the package directory.
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

    def with_zcml_include(self, *args, **kwargs):
        """Delegates a ZCML inclusion to the configure.zcml builder.
        """
        self.get_configure_zcml().include(*args, **kwargs)
        return self

    def with_zcml_node(self, *args, **kwargs):
        """Delegates a ZCML node declaration to the configure.zcml builder.
        """
        self.get_configure_zcml().with_node(*args, **kwargs)
        return self

    def get_configure_zcml(self):
        """Returns the configure.zcml builder.
        """
        if self.configure_zcml is not None:
            return self.configure_zcml

        self.configure_zcml = Builder('zcml')
        return self.configure_zcml

    def create(self):
        if not self.path:
            if not self.parent_package or not self.name:
                raise ValueError('Unknown target: use either .at_path()'
                                 ' or .named() and .within()')
            self.path = self.parent_package.path.joinpath(self.name)

        self.path.mkdir_p()
        map(create, self.subpackages)

        for relative_path in self.directories:
            self.path.joinpath(relative_path).makedirs()

        for relative_path, contents in self.files:
            self.path.joinpath(relative_path).write_text(contents)

        if self.configure_zcml is not None:
            if self.i18n_domain:
                self.configure_zcml.with_i18n_domain(self.i18n_domain)
            self.configure_zcml.at_path(self.path.joinpath('configure.zcml'))
            self.configure_zcml.create()

            if self.parent_package:
                self.parent_package.get_configure_zcml().include(
                    self.configure_zcml)

        return self.path


builder_registry.register('subpackage', SubPackageBuilder)
