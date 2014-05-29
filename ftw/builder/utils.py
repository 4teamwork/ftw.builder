import unicodedata


def strip_diacricits(text):
    if isinstance(text, str):
        text = text.decode('utf-8')
    normalized = unicodedata.normalize('NFKD', text)
    text = u''.join([c for c in normalized if not unicodedata.combining(c)])
    text = text.encode('utf-8')
    return text
