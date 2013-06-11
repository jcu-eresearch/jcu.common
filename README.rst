.. contents::

Introduction
============

This is a common Pyramid application package for JCU deployments. It probably
isn't suitable for anything else outside of JCU due to close coupling but 
it attempts to only require the bare essentials depending on the ``extras``
dependencies you select.  If you want the whole-shebang then you do this::

    jcu.common[static,forms,auth,ldap]

which will include all of the multiple ``setuptools``  extras.

Todo
----

* Consider ``pyramid_whoauth`` -- it seems to do quite a bit of what we already
  do here. Whether it'll play ball for CAS, though, is another question.

LDAP Integration
----------------

*Usage*::

    jcu.common[ldap]

This package provides LDAP helpers for use with ``pyramid_ldap``.  It means
that you can configure your LDAP directly from your settings ini files,
rather than having to hard-code information into your project (or repeat
your boilerplate across projects).

See https://github.com/jcu-eresearch/jcu.common/blob/master/jcu/common/ldap.py
for more information about what the ini configuration should look like.

Fanstatic resources
-------------------

*Usage*::

    jcu.common[static]

This package provides static resources for use with Fanstatic. These are
available for perusal within ``jcu/common/static`` and definitions within
``jcu.common.static``.  These can be included within your application by::

    import jcu.common
    jcu.common.static.alerts.need()

which would include the CSS resources necessary for Bootstrap-style alerts.

Deform common schemas
---------------------

*Usage*::

    jcu.common[forms]

Nothing yet. The original usage of this extra was supplanted by
``pyramid_deform.CSRFSchema``.

Auth with CAS
-------------

*Usage*::

    jcu.common[auth]

Provides various helpers for Pyramid for authentication. Use the ``includeme``
functionality provided by Pyramid and include ``jcu.common.auth``. You can
do this either within your Paste configuration::

    pyramid.includes = ...
                       pyramid_beaker
                       jcu.common.auth

or within your ``main()`` function, where you can have a route prefix
for the given routes (``/login`` and ``/logout``) registered by this include::

    def main(global_config, **settings):
        ...
        config.include('jcu.common.auth', route_prefix='/profiles')
        ...
     ...

You need to configure several options within your Paste configuration too::

    #String name of where you'd like users to come back to after logging in
    #or out.
    jcu.auth.return_route = home

    #Boolean as to whether you want to force the login link to use HTTPS
    jcu.auth.force_ssl = true

    #Callable class accepting ``identity`` and ``request`` as positional
    #arguments to check groups for a user (eg you can deny access here).
    jcu.auth.auth_callback = jcu.common.auth.VerifyUser

    #By default, the callback class provided here will check the following
    #option and if the user is in this list, they will be said to be in
    #the 'groups:Administrators' group.
    jcu.auth.admins = 
        jc123456
        jc987654
        ...

    #Who configuration file location for ``pyramid_who``
    jcu.auth.who_config_file = %(here)s/who.ini

You should use the pre-constructed ``who.ini`` file by adding this to your
buildout configuration for your WSGI project.  This automatically pulls
in the relevant templating buildout for ``repoze.who`` and produces a
``who.ini`` file in your buildout directory::

    [buildout]
    extends = https://raw.github.com/jcu-eresearch/jcu.common/master/auth.cfg

    [settings]
    cas-url = https://cas.secure.jcu.edu.au/cas/
    auth-tkt-secret = password
    auth-tkt-cookie-name = cookie-name

Note that you get the above ``[settings]`` section by default, so if you just
want to test you probably don't need to re-specify the settings.  The nature
of buildout, however, means that you can override the options as you need to.

Once you've done this, we'll automatically figure out the SSO URL from your
``who.ini`` configuration upon running your application.

Check a user's groups by doing the following in your application::

    from pyramid.security import effective_principals
    effective_principals(request)

