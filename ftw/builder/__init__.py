import pkg_resources

try:
    pkg_resources.get_distribution('plone.dexterity')
except pkg_resources.DistributionNotFound:
    HAS_DEXTERITY = False
else:
    HAS_DEXTERITY = True

from ftw.builder.registry import builder_registry

from ftw.builder.builder import Builder
from ftw.builder.builder import create

import ftw.builder.content
import ftw.builder.group
import ftw.builder.user
