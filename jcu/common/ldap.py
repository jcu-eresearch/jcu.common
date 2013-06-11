from __future__ import absolute_import
import inspect

import ldap
from pyramid.settings import asbool
from pyramid.path import DottedNameResolver
import pyramid_ldap

LDAP_ROLE = 'jcu.ldap.role'


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
    return value.replace('${userdn}', '%(userdn)')

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
    """
    config.include('pyramid_ldap')

    #LDAP setup
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

    #LDAP Login query
    prefix = config.registry.settings.get('pyramid_ldap.login_query.prefix',
                                          'ldap.login_query.')
    login_query_settings = extract_settings_fn_args(
        config.registry.settings,
        prefix,
        pyramid_ldap.ldap_set_login_query)

    if login_query_settings:
        login_query_coercion = {'scope': as_ldap_scope,
                                'cache_period': float}
        config.ldap_set_login_query(**coerce_settings(login_query_settings,
                                                      login_query_coercion))
    #LDAP Groups query
    prefix = config.registry.settings.get('pyramid_ldap.groups_query.prefix',
                                          'ldap.groups_query.')
    groups_query_settings = extract_settings_fn_args(
        config.registry.settings,
        prefix,
        pyramid_ldap.ldap_set_groups_query)

    if groups_query_settings:
        groups_query_coercion = {'filter_tmpl': replace_user_dn,
                                 'scope': as_ldap_scope,
                                 'cache_period': float}
        import ipdb; ipdb.set_trace()
        config.ldap_set_groups_query(**coerce_settings(groups_query_settings,
                                                       groups_query_coercion))
