# Configurazione locale Docker — sovrascrive superset_config.py
import logging
import os

logger = logging.getLogger(__name__)

# Necessario dietro reverse proxy (nginx) per leggere X-Forwarded-Proto/Host
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {"x_for": 1, "x_proto": 1, "x_host": 1, "x_port": 0, "x_prefix": 1}

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
