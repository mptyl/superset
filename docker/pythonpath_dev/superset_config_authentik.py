import os
from typing import Any

from flask_appbuilder.security.manager import AUTH_OAUTH
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


class AuthentikSecurityManager(SupersetSecurityManager):
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

OAUTH_PROVIDERS = [
    {
        "name": _provider_name,
        "icon": os.getenv("SUPERSET_AUTHENTIK_ICON", "fa-lock"),
        "token_key": "access_token",
        "remote_app": {
            "client_id": _required_env("SUPERSET_AUTHENTIK_CLIENT_ID"),
            "client_secret": _required_env("SUPERSET_AUTHENTIK_CLIENT_SECRET"),
            "server_metadata_url": _required_env("SUPERSET_AUTHENTIK_METADATA_URL"),
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
