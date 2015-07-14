import logging
import urllib

from zope.interface import implements
from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IRoutePregenerator
from pyramid.response import Response
from pyramid import security, settings
from pyramid.settings import asbool
from pyramid.security import Allow
from pyramid.view import view_config, forbidden_view_config
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid_who.whov2 import WhoV2AuthenticationPolicy

from jcu.common.resolver import resolve_dotted

RETURN_ROUTE = 'jcu.auth.return_route'
FORCE_SSL = 'jcu.auth.force_ssl'
AUTH_CALLBACK = 'jcu.auth.auth_callbacks'
USER_CLASS = 'jcu.auth.user_class'
CONFIG_FILE = 'jcu.auth.who_config_file'
ENABLE_SLO = 'jcu.auth.enable_single_log_out'
SSO_URL = 'jcu.auth.sso_url'
ADMINISTRATORS_KEY = 'jcu.auth.admins'

log = logging.getLogger(__name__)


class AuthenticatedPredicate(object):
    """Check whether the current user is authenticated or not.
    """

    def __init__(self, value, config):
        self.value = value

    def text(self):
        """Useful message for identifying predicate failures.
        """
        return 'authenticated = ' + ('True' if self.value else 'False')

    #: Unique identifier for predicate and value provided
    phash = text

    def __call__(self, context, request):
        """Returns a Boolean value if current user is/is not authenticated.
        """
        test = security.Authenticated in security.effective_principals(request)
        return self.value == test


class BaseView(object):
    """Base view for handling incoming view variables.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request


@forbidden_view_config(authenticated=False)
@view_config(route_name='auth-login')
class LoginView(BaseView):
    def __call__(self):
        """Challenge for auth if not logged in yet, else redirect to listing.
        """
        force_ssl = self.request.registry.settings[FORCE_SSL]
        if security.authenticated_userid(self.request) is None:
            # Place current URL into the request environment for CAS plugin
            return_url = self.request.referrer or ''
            if return_url and force_ssl:
                return_url = return_url.replace('http://', 'https://')
            qs = urllib.urlencode({'return': return_url})
            self.request.environ['QUERY_STRING'] = qs
            return Response(status=401)
        else:
            # Load the user's previous URL out of the request
            return_url = self.request.params.get('return')
            if not return_url:
                return_route = self.request.registry.settings[RETURN_ROUTE]
                return_url = self.request.route_url(
                    return_route,
                    _scheme='https' if force_ssl else 'http')
            return HTTPFound(location=return_url)


@view_config(route_name='auth-logout')
class LogoutView(BaseView):
    def __call__(self):
        """Log the user out by deleting cookies and redirecting to CAS logout.
        """
        if security.authenticated_userid(self.request):
            # Return to this view once we've logged out.
            here = self.request.route_url(self.request.matched_route.name)
            here += '?return=' + self.request.referrer
            response = HTTPFound(location=here)

            # Drop the current session for the user. Copy the session to the
            # new response so the cookies get cleared.
            response.session = self.request.session
            response.session.invalidate()

            # Forget the user's login cookie
            forget_headers = security.forget(self.request)
            response.headerlist.extend(forget_headers)
            return response
        else:
            # Once cookies are gone, sign out. Either SSO or redirection.
            route = self.request.registry.settings[RETURN_ROUTE]
            # Go back to the original page, or the default
            return_url = self.request.params.get('return',
                                                 self.request.route_url(route))

            sso_url = self.request.registry.settings[SSO_URL]
            logout_url = (sso_url + '?url=' + return_url) if \
                self.request.registry.settings[ENABLE_SLO] else return_url

            return HTTPFound(location=logout_url)


class SchemeSelection(object):
    implements(IRoutePregenerator)

    def __call__(self, request, elements, kw):
        if request.registry.settings.get(FORCE_SSL):
            kw['_scheme'] = 'https'
        return (elements, kw)


class User(object):
    """ Simple structure representing an authenticated user in the application.
    """

    attributes = None
    user_id = None
    display_name = None

    def __init__(self, request, user_id=None):
        """
        Provide a default ``user_id`` attribute if you know it already.
        This will help speed things along and short-circuit the ID lookup.
        """
        self.request = request
        self.user_id = user_id or security.authenticated_user_id(request)
        identity = request.environ.get('repoze.who.identity')
        self.attributes = identity and identity.get('attributes')
        self.display_name = self.get_display_name()

    def get_display_name(self):
        """ Return the user ID or the display name of the user if we know it.
        """
        display_name = self.user_id
        if self.attributes:
            display_name = self.attributes['givenname'] + ' ' + \
                self.attributes['surname']
        return display_name

    @property
    def is_manager(self):
        """ Return a Boolean value representing if the user is a Manager.

        Checks against the Root object rather than the current context.
        """
        return security.has_permission('manage',
                                       self.request.root,
                                       self.request)


def allow_acl(identifier):
    """ Create a permissive ACL entry for Pyramid.
    """
    return [(Allow, identifier, 'view'),
            (Allow, identifier, 'edit')]


def get_user(user_class=User):
    def wrapped(request):
        """ Create a user from the given request.
        """
        user_id = security.authenticated_userid(request)
        if user_id:
            return user_class(request, user_id=user_id)
    return wrapped


def verify_administators(identity, request):
    """ Return groups to indicate if the user is a system administator.

    This method uses the relevant user ID configuration from the application to
    determine if a user is an administrator.
    """
    admins = request.registry.settings.get(ADMINISTRATORS_KEY, tuple())
    if identity['repoze.who.userid'] in admins:
        return ['group:Administrators']


def callback_fn(callbacks):
    def callback(identity, request):
        """ Run all callbacks that were configured within the application.

        Any groups returned here will be available within Pyramid by calling
        pyramid.security.effective_principals, so you can use them within
        any __acl__ you so desire.

        *Arguments*

        identity: repoze.who Identity dict-like object with user attributes
                  present. For instance, these may be `mail`, `login`, `cn`,
                  `repoze.who.userid` and so forth, depending on what is
                  released by the CAS server.
        request:  pyramid Request instance representing the current request.
        """
        groups = set(['group:Authenticated'])
        for fn in callbacks:
            result = fn(identity, request)
            if result:
                groups.update(result)
        log.debug("Access groups determined: %r", groups)
        return groups

    return callback


def includeme(config):
    """Include this module within Pyramid to gain repoze.who auth in your app.

    This method configures an authentication and authorization policy for
    your configurator, as well as setting up views and routes for
    authentication.
    """
    config.registry.settings[FORCE_SSL] = \
        asbool(config.registry.settings.get(FORCE_SSL, False))
    config.add_view_predicate('authenticated', AuthenticatedPredicate)

    # Adjust settings in config
    admins = config.registry.settings.get(ADMINISTRATORS_KEY)
    if admins:
        config.registry.settings[ADMINISTRATORS_KEY] = \
            settings.aslist(admins)

    # Resolve callbacks from settings
    callbacks_dotted = config.registry.settings.get(AUTH_CALLBACK, '').split()
    callbacks = [resolve_dotted(dotted) for dotted in callbacks_dotted]

    # Load pyramid_who configuration
    config_file = config.registry.settings.get(CONFIG_FILE)
    authentication_policy = WhoV2AuthenticationPolicy(
        config_file=config_file,
        identifier_id='auth_tkt',
        callback=callback_fn(callbacks)
    )

    # Figure out the logout URL for CAS
    for obj in authentication_policy._api_factory.challengers:
        plugin = obj[1]
        if hasattr(plugin, 'cas_url'):
            cas_url = plugin.cas_url
    config.registry.settings[SSO_URL] = '%slogout' % cas_url
    config.registry.settings[ENABLE_SLO] = \
        asbool(config.registry.settings.get(ENABLE_SLO, False))

    authorization_policy = ACLAuthorizationPolicy()

    # Session already configured via pyramid_beaker include
    config.set_authentication_policy(authentication_policy)
    config.set_authorization_policy(authorization_policy)

    # Add a special lazy attributes/methods to the request
    user_class_dotted = config.registry.settings.get(USER_CLASS)
    user_class = resolve_dotted(user_class_dotted, User)
    config.add_request_method(get_user(user_class), 'user', reify=True)

    # Auth routes
    config.add_route('auth-login',
                     pattern='/login',
                     pregenerator=SchemeSelection())
    config.add_route('auth-logout',
                     pattern='/logout')
    config.scan('.')
