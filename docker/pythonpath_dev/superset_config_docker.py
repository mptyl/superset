# Configurazione locale Docker — sovrascrive superset_config.py
import logging
import os

logger = logging.getLogger(__name__)

# Necessario dietro reverse proxy (nginx) per leggere X-Forwarded-Proto/Host
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {"x_for": 1, "x_proto": 1, "x_host": 1, "x_port": 0, "x_prefix": 1}

# In locale abilitiamo il rendering HTML dei chart Handlebars/SafeMarkdown.
# Questo workspace e' per sviluppo interno; qui privilegiamo la fedelta' del rendering.
HTML_SANITIZATION = False

# Embedded dashboards for Kokoro.
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "DATASET_FOLDERS": True,
    "EMBEDDED_SUPERSET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}

_EMBED_FRAME_ANCESTORS = [
    origin.strip()
    for origin in os.environ.get(
        "SUPERSET_EMBED_FRAME_ANCESTORS",
        "http://localhost:8080 http://127.0.0.1:8080",
    )
    .replace(",", " ")
    .split()
    if origin.strip()
]

_EMBED_CSP = {
    "base-uri": ["'self'"],
    "default-src": ["'self'"],
    "frame-ancestors": ["'self'", *_EMBED_FRAME_ANCESTORS],
    "img-src": [
        "'self'",
        "blob:",
        "data:",
        "https://apachesuperset.gateway.scarf.sh",
        "https://static.scarf.sh/",
        "https://cdn.brandfolder.io",
        "ows.terrestris.de",
        "https://cdn.document360.io",
    ],
    "worker-src": ["'self'", "blob:"],
    "connect-src": [
        "'self'",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://api.mapbox.com",
        "https://events.mapbox.com",
        "https://tile.openstreetmap.org",
        "https://tile.osm.ch",
        "https://a.basemaps.cartocdn.com",
    ],
    "object-src": "'none'",
    "style-src": [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://fonts.gstatic.com",
        "https://use.typekit.net",
        "https://use.typekit.com",
    ],
    "font-src": [
        "'self'",
        "https://fonts.googleapis.com",
        "https://fonts.gstatic.com",
        "https://use.typekit.net",
        "https://use.typekit.com",
    ],
    "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
}

TALISMAN_CONFIG = {
    "content_security_policy": _EMBED_CSP,
    "content_security_policy_nonce_in": ["script-src"],
    "force_https": False,
    "frame_options": None,
    "session_cookie_secure": False,
}
TALISMAN_DEV_CONFIG = TALISMAN_CONFIG

GUEST_ROLE_NAME = os.environ.get("SUPERSET_GUEST_ROLE_NAME", "Gamma")
GUEST_TOKEN_JWT_SECRET = os.environ.get("SUPERSET_GUEST_TOKEN_SECRET")
GUEST_TOKEN_JWT_AUDIENCE = os.environ.get("SUPERSET_GUEST_TOKEN_AUDIENCE", "superset")
GUEST_TOKEN_JWT_EXP_SECONDS = int(
    os.environ.get("SUPERSET_GUEST_TOKEN_EXP_SECONDS", "300")
)

if os.environ.get("SUPERSET_AUTHENTIK_ENABLED", "").lower() == "true":
    try:
        from superset_config_authentik import *  # noqa: F401,F403

        logger.info("Authentik OIDC configuration loaded.")
    except ImportError:
        logger.error(
            "SUPERSET_AUTHENTIK_ENABLED=true ma superset_config_authentik.py "
            "non trovato. Fallback a AUTH_DB."
        )
else:
    logger.info("Authentik disabled; using AUTH_DB.")
