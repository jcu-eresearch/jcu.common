from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid import security, settings
from pyramid.path import DottedNameResolver
from pyramid.view import view_config
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid_who.whov2 import WhoV2AuthenticationPolicy

RETURN_ROUTE = 'jcu.auth.return_route'
AUTH_CALLBACK = 'jcu.auth.auth_callback'
CONFIG_FILE = 'jcu.auth.who_config_file'
SSO_URL = 'jcu.auth.sso_url'
ADMINISTRATORS_KEY = 'jcu.auth.admins'


class VerifyUser(object):
    """Verification class for use in applications.
    
    Either subclass or re-create the same functionality in your own
    application. Needs to be a callable class due to lookup limitations
    in Pyramid.
    """

    def __call__(self, identity, request):
        """Return groups based on some processing on the repoze.who identity.

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
        groups = ['group:Authenticated']

        admins = request.registry.settings.get(ADMINISTRATORS_KEY, tuple())
        if identity['repoze.who.userid'] in admins:
            groups.append('group:Administrators')

        return groups


class BaseView(object):
    """Base view for handling incoming view variables.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request


@view_config(context='pyramid.httpexceptions.HTTPForbidden')
@view_config(route_name='auth-login')
class LoginView(BaseView):
    def __call__(self):
        """Challenge for auth if not logged in yet, else redirect to listing.
        """
        if security.authenticated_userid(self.request) is None:
            #TODO Should pass the current URL back to CAS so user can come back
            #repoze.who.plugins.cas munges the ticket processing URL, though.
            return Response(status=401)
        else:
            route = self.request.registry.settings[RETURN_ROUTE]
            return HTTPFound(location=self.request.route_url(route))

@view_config(route_name='auth-logout')
class LogoutView(BaseView):
    def __call__(self):
        """Log the user out by deleting cookies and redirecting to CAS logout.
        """
        if security.authenticated_userid(self.request):
            #Return to this view once we've logged out.
            here = self.request.route_url(self.request.matched_route.name)
            response = HTTPFound(location=here)

            #Drop the current session for the user. Copy the session to the
            #new response so the cookies get cleared.
            response.session = self.request.session
            response.session.invalidate()

            #Forget the user's login cookie
            forget_headers = security.forget(self.request)
            response.headerlist.extend(forget_headers)
            return response
        else:
            #Once cookies are gone, then do Single Sign Out (SSO)
            route = self.request.registry.settings[RETURN_ROUTE]
            return_url = self.request.route_url(route)
            sso_url = self.request.registry.settings[SSO_URL]
            return HTTPFound(location='%s?url=%s' % (sso_url, return_url))

def includeme(config):
    """Include this module within Pyramid to gain repoze.who auth in your app.

    This method configures an authentication and authorization policy for
    your configurator, as well as setting up views and routes for
    authentication.
    """
    #Adjust settings in config
    admins = config.registry.settings.get(ADMINISTRATORS_KEY)
    if admins:
        config.registry.settings[ADMINISTRATORS_KEY] = \
                settings.aslist(admins)

    #Resolve callback
    resolver = DottedNameResolver()
    callback_dotted = config.registry.settings.get(AUTH_CALLBACK)
    if callback_dotted:
        callback_cls = resolver.resolve(callback_dotted)
    else:
        callback_cls = VerifyUser
    callback = callback_cls()

    #Load pyramid_who configuration
    config_file=config.registry.settings.get(CONFIG_FILE)
    authentication_policy = WhoV2AuthenticationPolicy(
        config_file=config_file,
        identifier_id='auth_tkt',
        callback=callback
    )

    #Figure out the logout URL for CAS
    for obj in authentication_policy._api_factory.challengers:
        plugin = obj[1]
        if hasattr(plugin, 'cas_url'):
            cas_url = plugin.cas_url
    config.registry.settings[SSO_URL] = '%slogout' % cas_url

    authorization_policy = ACLAuthorizationPolicy()

    #Session already configured via pyramid_beaker include
    config.set_authentication_policy(authentication_policy)
    config.set_authorization_policy(authorization_policy)

    #Auth routes
    config.add_route('auth-login',
                     pattern='/login')
    config.add_route('auth-logout',
                     pattern='/logout')
    config.scan('.')
