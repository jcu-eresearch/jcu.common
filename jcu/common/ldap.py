from __future__ import absolute_import
import inspect

from pyramid.settings import asbool
from pyramid.path import DottedNameResolver
import pyramid_ldap


def verify_ldap_roles(identity, request, _groupfinder=pyramid_ldap.groupfinder):
    """ Return groups to indicate the LDAP roles that a user has.
    """
    user_id = identity['repoze.who.userid']
    return _groupfinder('uid=' + user_id + ',ou=users,dc=jcu,dc=edu,dc=au',
                       request)


def extract_settings(settings, prefix, keys=()):
    """ Extract options from a settings structure, stripping the ``prefix``.
    """
    kwarg_names = [prefix + k for k in keys]
    size = len(prefix)
    return dict(((k[size:], settings[k]) for k in settings.keys() \
                   if k in kwarg_names))


def extract_settings_fn_args(settings, prefix, fn):
    """ Extract only options from settings that are suitable to pass to ``fn``.

    This method inspects the given callable and uses its arguments to
    determine the keys to extract from the settings.
    """
    keys = inspect.getargspec(fn).args
    return extract_settings(settings, prefix, keys)


def coerce_settings(settings, coercion):
    """ Apply callables within ``coercion`` to items within ``settings``.
    """
    coerced = {}
    for setting in settings:
        value = settings[setting]
        if setting in coercion:
            fn = coercion[setting]
            coerced[setting] = fn(value)
        else:
            coerced[setting] = value
    return coerced

def replace_user_dn(value):
    """ Tidy up the value's userdn entry to be suitable for string formatting.
    """

def as_ldap_scope(value):
    """ Resolve a given LDAP scope from a string into a value.

    This method either accepts a dotted name (eg ``ldap.SCOPE_SUBTREE``)
    or will accept the the specific integer relating to the value.
    """
    try:
        return DottedNameResolver().resolve(value)
    except ImportError:
        try:
            return int(value)
        except ValueError:
            return value


def includeme(config):
    """Include this within Pyramid to gain LDAP role integration in your app.

    Including this module will automatically include pyramid_ldap and also
    automatically configure all relevant methods, if configuration is
    present within the given settings. Settings will be automatically
    coerced from their string counterparts.

    An example configuration might be as follows.  Keep in mind that if
    an option isn't specified, then the default will be applied.  See
    `pyramid_ldap's API
    <http://docs.pylonsproject.org/projects/pyramid_ldap/en/latest/api.html>`_
    for more information.  The example is as verbose as it can possibly be,
    so that you're able to conceptualise all available options.  In reality
    and practice, most options may well be omitted.

    Also bear in mind that the ``prefix` options need not be specified if
    you'd like to use the default prefixes.  The defaults are what are shown
    in the following example, so any of the ``prefix`` lines can be omitted
    entirely without changing functionality.

    .. code:: ini

        [app:my-awesome-application]
        ...
        pyramid.includes =
            jcu.common.ldap
        ...
        pyramid_ldap.setup.prefix = ldap.setup.
        ldap.setup.uri = ldaps://ldap.example.com:636
        ldap.setup.bind = uid=david,dc=example,dc=com
        ldap.setup.passwd = itsasecret
        ldap.setup.pool_size = 10
        ldap.setup.retry_max = 3
        ldap.setup.retry_delay = 0.1
        ldap.setup.use_tls = false
        ldap.setup.timeout = 3
        ldap.setup.use_pool = true

        pyramid_ldap.login_query.prefix = ldap.login_query.
        ldap.login_query.base_dn = dc=example,dc=com
        ldap.login_query.filter_tmpl = (uid=${login})
        ldap.login_query.scope = ldap.SCOPE_ONELEVEL
        ldap.login_query.cache_period = 600

        pyramid_ldap.groups_query.prefix = ldap.groups_query.
        ldap.groups_query.base_dn = ou=org,dc=example,dc=com
        ldap.groups_query.filter_tmpl = (&(cn=RoleName)(roleOccupant=${userdn}))
        ldap.groups_query.scope = ldap.SCOPE_SUBTREE
        ldap.groups_query.cache_period = 600
    """
    config.include('pyramid_ldap')

    #General LDAP setup
    prefix = config.registry.settings.get('pyramid_ldap.setup.prefix',
                                          'ldap.setup.')
    setup_settings = extract_settings_fn_args(config.registry.settings,
                                              prefix,
                                              pyramid_ldap.ldap_setup)

    if setup_settings:
        setup_coercion = {'pool_size': int,
                          'retry_max': int,
                          'retry_delay': float,
                          'timeout': float,
                          'use_tls': asbool,
                          'use_pool': asbool
                         }
        config.ldap_setup(**coerce_settings(setup_settings, setup_coercion))

    #Configure LDAP Login query
    prefix = config.registry.settings.get('pyramid_ldap.login_query.prefix',
                                          'ldap.login_query.')
    login_query_settings = extract_settings_fn_args(
        config.registry.settings,
        prefix,
        pyramid_ldap.ldap_set_login_query)

    if login_query_settings:
        #Ensure ``filter_tmpl`` is converted for string formatting of login
        login_query_coercion = {
            'filter_tmpl': lambda v: v.replace('${login}', '%(login)s'),
            'scope': as_ldap_scope,
            'cache_period': float
        }
        config.ldap_set_login_query(**coerce_settings(login_query_settings,
                                                      login_query_coercion))
    #Configure LDAP Groups query
    prefix = config.registry.settings.get('pyramid_ldap.groups_query.prefix',
                                          'ldap.groups_query.')
    groups_query_settings = extract_settings_fn_args(
        config.registry.settings,
        prefix,
        pyramid_ldap.ldap_set_groups_query)

    if groups_query_settings:
        #Ensure ``filter_tmpl`` is converted for string formatting of userdn
        groups_query_coercion = {
            'filter_tmpl': lambda v: v.replace('${userdn}', '%(userdn)s'),
            'scope': as_ldap_scope,
            'cache_period': float
        }
        config.ldap_set_groups_query(**coerce_settings(groups_query_settings,
                                                       groups_query_coercion))
