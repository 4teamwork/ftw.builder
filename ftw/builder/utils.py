from six.moves import map
import inspect
import re
import six
import unicodedata


def strip_diacricits(text):
    text = six.ensure_text(text)
    normalized = unicodedata.normalize('NFKD', text)
    text = u''.join([c for c in normalized if not unicodedata.combining(c)])
    text = six.ensure_str(text)
    return text


def parent_namespaces(dottedname):
    """Returns a list of all parent dottednames for a dottedname.
    If the dottedname is already first-level (has no dots), an empty list is returned.
    """
    if dottedname.count('.') == 0:
        return []

    parent_dottedname = '.'.join(dottedname.split('.')[:-1])
    return parent_namespaces(parent_dottedname) + [parent_dottedname]


def serialize_callable(callable_, *to_import):
    """Serialize a callable to a string.
    If the callable is a class, import statements are automatically
    added for each superclass, unless it is a builtin.

    All other used globales need to be declared by passing them
    to ``serialize_callable`` as optional positional arguments.
    """
    if not callable(callable_):
        raise ValueError('A callable is required.')

    def dedent(source):
        indentation = re.match('^\W*', source).group()
        return re.sub(r'(^|\n){0}'.format(indentation), r'\g<1>', source)

    def get_import_string(thing):
        if thing.__module__ in ['__builtin__', 'builtins']:
            return None
        return 'from {0} import {1}'.format(thing.__module__, thing.__name__)

    if inspect.isclass(callable_):
        to_import += callable_.__bases__

    imports_source = '\n'.join(sorted(
            [_f for _f in map(get_import_string, to_import) if _f]))
    callable_source = dedent(inspect.getsource(callable_))
    return '\n\n\n'.join((imports_source, callable_source)).lstrip()
