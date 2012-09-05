.. contents::

Introduction
============

This is a common Pyramid application package for JCU deployments. It probably
isn't suitable for anything else outside of JCU due to close coupling but 
it attempts to only require the bare essentials depending on the ``extras``
dependencies you select.  If you want the whole-shebang then you do this::

    jcu.common[static,forms,auth]

which will include all of the multiple ``setuptools``  extras.

Todo
----

* Consider ``pyramid_whoauth`` -- it seems to do quite a bit of what we already
  do here. Whether it'll play ball for CAS, though, is another question.
* CAS metadata plugin -- doesn't look like it exists yet

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

This package provides a common set of CSRF schemas and validators for use
in Deform/Pyramid applications.

Simply import, and use.  Ensure that you include the schema in the correct
order when using multiple inheritance::

    from jcu.common.schemas import CSRFSchema

    class AddKeywordsSchema(CSRFSchema, colander.MappingSchema):
        ...

and after doing this, your form will now include a CSRF authenticator field
using the default session implementation in your Pyramid application.

See http://deformdemo.repoze.org/pyramid_csrf_demo/ for more details.
This is effectively a copy-paste of the demo and could probably be tidied 
up a bit.


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

