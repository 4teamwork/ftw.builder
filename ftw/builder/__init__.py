import pkg_resources

try:
    pkg_resources.get_distribution('z3c.relationfield')
except pkg_resources.DistributionNotFound:
    HAS_RELATION = False
else:
    HAS_RELATION = True

from ftw.builder.registry import builder_registry

from ftw.builder.builder import Builder
from ftw.builder.builder import ticking_creator
from ftw.builder.builder import create

import ftw.builder.content
import ftw.builder.group
import ftw.builder.user
import ftw.builder.zcml
import ftw.builder.package
import ftw.builder.genericsetup
import ftw.builder.portlets
