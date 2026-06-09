import os
from typing import Any

from flask import g, redirect
from flask_appbuilder.security.manager import AUTH_OAUTH
from flask_appbuilder.security.decorators import no_cache
from flask_appbuilder.security.views import AuthOAuthView, expose
from superset.security import SupersetSecurityManager


def _required_env(name: str) -> str:
    if value := os.getenv(name):
        return value
    raise RuntimeError(f"{name} must be set when SUPERSET_AUTHENTIK_ENABLED=true")


def _csv_env(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _oauth_role_mapping() -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for group_name in _csv_env("SUPERSET_AUTHENTIK_GAMMA_GROUPS", "superset-users"):
        mapping[group_name] = ["Gamma"]
    for group_name in _csv_env("SUPERSET_AUTHENTIK_ALPHA_GROUPS"):
        mapping[group_name] = ["Alpha", "Gamma"]
    for group_name in _csv_env("SUPERSET_AUTHENTIK_ADMIN_GROUPS", "superset-admins"):
        mapping[group_name] = ["Admin"]
    return mapping


def _truthy_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AuthentikAuthOAuthView(AuthOAuthView):
    @expose("/login/")
    @expose("/login/<provider>")
    @expose("/login/<provider>/<register>")
    def login(self, provider=None, register=None):
        if provider is None and _truthy_env("SUPERSET_AUTHENTIK_AUTO_LOGIN", True):
            provider_name = os.getenv("SUPERSET_AUTHENTIK_PROVIDER_NAME", "authentik")
            return redirect(f"{self.appbuilder.get_url_for_login}{provider_name}")
        return super().login(provider)


class AuthentikSecurityManager(SupersetSecurityManager):
    authoauthview = AuthentikAuthOAuthView

    def register_views(self) -> None:
        import superset.views.auth as superset_auth

        class AuthentikSupersetAuthView(superset_auth.SupersetAuthView):
            @expose("/")
            @no_cache
            def login(self, provider=None):
                if g.user is not None and g.user.is_authenticated:
                    return redirect(self.appbuilder.get_url_for_index)
                if _truthy_env("SUPERSET_AUTHENTIK_AUTO_LOGIN", True):
                    provider_name = os.getenv("SUPERSET_AUTHENTIK_PROVIDER_NAME", "authentik")
                    return redirect(f"{self.appbuilder.get_url_for_login}{provider_name}")
                return super().login(provider)

        original_auth_view = superset_auth.SupersetAuthView
        superset_auth.SupersetAuthView = AuthentikSupersetAuthView
        try:
            super().register_views()
        finally:
            superset_auth.SupersetAuthView = original_auth_view

    def oauth_user_info(
        self,
        provider: str,
        response: Any | None = None,
    ) -> dict[str, Any]:
        provider_name = os.getenv("SUPERSET_AUTHENTIK_PROVIDER_NAME", "authentik")
        if provider != provider_name:
            return {}

        groups_claim = os.getenv("SUPERSET_AUTHENTIK_GROUPS_CLAIM", "groups")
        me = self.appbuilder.sm.oauth_remotes[provider].userinfo()

        groups = me.get(groups_claim, [])
        if isinstance(groups, str):
            groups = [groups]
        elif not isinstance(groups, list):
            groups = list(groups or [])

        username = (
            me.get("preferred_username")
            or me.get("nickname")
            or me.get("sub")
            or me.get("email")
        )
        email = me.get("email") or f"{username}@invalid.local"
        full_name = me.get("name") or username
        first_name = me.get("given_name") or full_name
        last_name = me.get("family_name") or ""

        return {
            "id": me.get("sub") or username,
            "username": username,
            "name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role_keys": groups,
        }


AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = os.getenv("SUPERSET_AUTHENTIK_REGISTRATION_ROLE", "Gamma")
AUTH_ROLES_SYNC_AT_LOGIN = True
AUTH_ROLES_MAPPING = _oauth_role_mapping()
CUSTOM_SECURITY_MANAGER = AuthentikSecurityManager

_provider_name = os.getenv("SUPERSET_AUTHENTIK_PROVIDER_NAME", "authentik")
_ca_bundle = os.getenv(
    "SUPERSET_AUTHENTIK_CA_BUNDLE",
    "/app/docker/pythonpath_dev/authentik-ca.crt",
)
os.environ.setdefault("REQUESTS_CA_BUNDLE", _ca_bundle)
os.environ.setdefault("CURL_CA_BUNDLE", _ca_bundle)

OAUTH_PROVIDERS = [
    {
        "name": _provider_name,
        "icon": os.getenv("SUPERSET_AUTHENTIK_ICON", "fa-lock"),
        "token_key": "access_token",
        "remote_app": {
            "client_id": _required_env("SUPERSET_AUTHENTIK_CLIENT_ID"),
            "client_secret": _required_env("SUPERSET_AUTHENTIK_CLIENT_SECRET"),
            "server_metadata_url": _required_env("SUPERSET_AUTHENTIK_METADATA_URL"),
            "verify": _ca_bundle,
            "client_kwargs": {
                "scope": os.getenv(
                    "SUPERSET_AUTHENTIK_SCOPES",
                    "openid profile email",
                ),
            },
        },
    }
]

LOGOUT_REDIRECT_URL = os.getenv("SUPERSET_AUTHENTIK_LOGOUT_REDIRECT_URL")
