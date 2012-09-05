.. contents::

Introduction
============

Todo
----

* Consider ``pyramid_whoauth`` -- it seems to do quite a bit of what we already
  do here. Whether it'll play ball for CAS, though, is another question.
* CAS metadata plugin -- doesn't look like it exists yet

Auth
----

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

We'll automatically figure out the SSO URL from your ``who.ini`` configuration.

Check a user's groups by looking up::

    from pyramid.security import effective_principals
    effective_principals(request)

