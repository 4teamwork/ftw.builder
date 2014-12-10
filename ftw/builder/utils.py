import unicodedata


def strip_diacricits(text):
    if isinstance(text, str):
        text = text.decode('utf-8')
    normalized = unicodedata.normalize('NFKD', text)
    text = u''.join([c for c in normalized if not unicodedata.combining(c)])
    text = text.encode('utf-8')
    return text


def parent_namespaces(dottedname):
    """Returns a list of all parent dottednames for a dottedname.
    If the dottedname is already first-level (has no dots), an empty list is returned.
    """
    if dottedname.count('.') == 0:
        return []

    parent_dottedname = '.'.join(dottedname.split('.')[:-1])
    return parent_namespaces(parent_dottedname) + [parent_dottedname]
