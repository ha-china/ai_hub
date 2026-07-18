"""Error and service constants for AI Hub."""

from __future__ import annotations

from typing import Final

ERRORS: Final = {
    "getting_response": "Error getting response",
    "invalid_api_key": "Invalid API key",
    "cannot_connect": "Cannot connect to AI Hub service",
}

ERROR_GETTING_RESPONSE: Final = ERRORS["getting_response"]
ERROR_INVALID_API_KEY: Final = ERRORS["invalid_api_key"]
ERROR_CANNOT_CONNECT: Final = ERRORS["cannot_connect"]

SERVICES: Final = {
    "generate_image": "generate_image",
    "analyze_image": "analyze_image",
    "stt_transcribe": "stt_transcribe",
    "translate_components": "translate_components",
    "translate_blueprints": "translate_blueprints",
}

SERVICE_GENERATE_IMAGE: Final = SERVICES["generate_image"]
SERVICE_ANALYZE_IMAGE: Final = SERVICES["analyze_image"]
SERVICE_STT_TRANSCRIBE: Final = SERVICES["stt_transcribe"]
SERVICE_TRANSLATE_COMPONENTS: Final = SERVICES["translate_components"]
SERVICE_TRANSLATE_BLUEPRINTS: Final = SERVICES["translate_blueprints"]
