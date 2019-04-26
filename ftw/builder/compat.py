"""
This module handles compatibility issues between Python 2 and Python 3.
"""
import six


if six.PY2:
    import imp
    import sys

    def find_module(name):
        """Return True if a module with the given name can be found."""

        def _find_module(dottedname, paths=None):
            # imp.find_module does not support dottednames, it can only
            # resolve one name level at the time.
            # This find_module function does the recursion so that
            # dottednames work.
            if '.' in dottedname:
                name, dottedname = dottedname.split('.', 1)
            else:
                name = dottedname
                dottedname = None

            if paths is None:
                paths = []
                for path in sys.path:
                    try:
                        fp, pathname, description = imp.find_module(
                            name, [path])
                    except ImportError:
                        pass
                    else:
                        if not dottedname:
                            return fp, pathname, description
                        paths.append(pathname)
                return _find_module(dottedname, paths)
            else:
                fp, pathname, description = imp.find_module(name, paths)
                if not dottedname:
                    return fp, pathname, description
                else:
                    return _find_module(dottedname, [pathname])

        try:
            fp, pathname, description = _find_module(name)
        except ImportError:
            return False
        else:
            return True

else:
    from importlib.util import find_spec

    def find_module(name):
        """Return True if a module with the given name can be found."""
        try:
            spec = find_spec(name)
        except ModuleNotFoundError:
            return False
        if spec:
            return True
        else:
            return False
