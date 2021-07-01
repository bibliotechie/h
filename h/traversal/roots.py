"""
Root resources for Pyramid traversal.

Root resources are reusable components that can handle things like looking up a
model object in the database, raising :py:exc:`KeyError` if the object doesn't
exist in the database, and checking whether the request has permission to
access the object.

In this app we use combined traversal and URL dispatch. For documentation of
this approach see:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hybrid.html

Usage:

.. code-block:: python

   config.add_route("activity.user_search", "/users/{username}",
                    factory="h.traversal:UserRoot",
                    traverse="/{username}")

When configuring a route in :py:mod:`h.routes` you can use the ``factory``
argument to tell it to use one of the root resource factories in this class
instead of the default root resource factory.

In this app we also always use the ``traverse`` argument to specify a traversal
pattern that Pyramid should use to find the ``context`` object to pass to the
view. And we always use a traversal path of length 1 (only one ``/`` in the
``traverse`` pattern, at the start).

For documentation of ``factory`` and ``traverse`` see
https://docs.pylonsproject.org/projects/pyramid/en/latest/api/config.html#pyramid.config.Configurator.add_route

The intended pattern in this app is that all root resources **should return
context objects** from :py:mod:`h.traversal.contexts` (or raise
:py:exc:`KeyError`), they shouldn't return other types of object (e.g. they
shouldn't return model objects directly).

.. note::

   Technically the *classes* in this module are Pyramid "root factories"
   (hence the ``factory`` argument to :py:func:`pyramid.config.Configurator.add_route`)
   and the *object instances* of these classes are the Pyramid "root resources"
   that the factories return when called (instantiated).

.. note::

   In order to encapsulate SQLAlchemy in the models and services, root
   resources should look up objects in the DB by calling a ``@classmethod`` of
   a :py:mod:`h.models` class or a method of a service from
   :py:mod:`h.services`, rather than by doing DB queries directly.

.. seealso::

   The Pyramid documentation on traversal:

   * https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hellotraversal.html
   * https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/muchadoabouttraversal.html
   * https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/traversal.html

"""

import sqlalchemy.exc
import sqlalchemy.orm.exc
from pyramid.security import ALL_PERMISSIONS, DENY_ALL, Allow

from h.auth import role
from h.models import AuthClient


class RootFactory:
    """Base class for all root resource factories."""

    def __init__(self, request):
        self.request = request


class Root(RootFactory):
    """This app's default root factory."""

    __acl__ = [
        (Allow, role.Staff, "admin_index"),
        (Allow, role.Staff, "admin_groups"),
        (Allow, role.Staff, "admin_mailer"),
        (Allow, role.Staff, "admin_organizations"),
        (Allow, role.Staff, "admin_users"),
        (Allow, role.Admin, ALL_PERMISSIONS),
        DENY_ALL,
    ]


class AuthClientRoot(RootFactory):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.AuthClientContext`.

    FIXME: This class should return AuthClientContext objects, not AuthClient
    objects.

    """

    def __getitem__(self, client_id):
        try:
            client = self.request.db.query(AuthClient).filter_by(id=client_id).one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise KeyError()
        except (
            sqlalchemy.exc.StatementError,
            sqlalchemy.exc.DataError,
        ):  # Happens when client_id is not a valid UUID.
            raise KeyError()

        # Add the default root factory to this resource's lineage so that the default
        # ACL is applied. This is needed so that permissions required by auth client
        # admin views (e.g. the "admin_oauthclients" permission) are granted to admin
        # users.
        #
        # For details on how ACLs work see the docs for Pyramid's ACLAuthorizationPolicy:
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/authorization.html
        client.__parent__ = Root(self.request)

        return client


class BulkAPIRoot(RootFactory):
    """Root factory for the Bulk API."""

    # Currently only LMS uses this end-point
    __acl__ = [(Allow, "client_authority:lms.hypothes.is", "bulk_action")]


class ProfileRoot(RootFactory):
    """
    Simple Root for API profile endpoints
    """

    __acl__ = [(Allow, role.User, "update")]
