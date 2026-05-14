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
GUEST_TOKEN_JWT_SECRET = os.environ.get("SUPERSET_GUEST_TOKEN_SECRET")
GUEST_TOKEN_JWT_AUDIENCE = os.environ.get("SUPERSET_GUEST_TOKEN_AUDIENCE", "superset")
GUEST_TOKEN_JWT_EXP_SECONDS = int(os.environ.get("SUPERSET_GUEST_TOKEN_EXP_SECONDS", "300"))
GUEST_ROLE_NAME = os.environ.get("SUPERSET_GUEST_ROLE_NAME", "Gamma")

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
