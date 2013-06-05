from pyramid.path import DottedNameResolver

def resolve_dotted(dotted, default=None):
    """ Resolve a dotted class string into an actual callable.
    """
    return DottedNameResolver().resolve(dotted) if dotted else default

