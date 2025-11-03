import json
import os
from typing import Any, Dict, Optional


def _get_env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _get_env_json(name: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


# External service base URL for dataset API
DS_API_BASE_URL: Optional[str] = os.getenv("DS_API_BASE_URL", "https://delong-datasets.avinasi.org")

# Dataset decrypt endpoint (backend API: POST /api/datasets/decrypt)
DS_DECRYPT_ENDPOINT: str = os.getenv("DS_DECRYPT_ENDPOINT", f"{DS_API_BASE_URL}/api/datasets/decrypt")

# Timeouts and retries
DS_TIMEOUT: int = _get_env_int("DS_TIMEOUT", 30)
DS_MAX_RETRIES: int = _get_env_int("DS_MAX_RETRIES", 3)

# Pagination defaults
DS_DEFAULT_LIMIT: int = _get_env_int("DS_DEFAULT_LIMIT", 1000)
DS_MAX_LIMIT: int = _get_env_int("DS_MAX_LIMIT", 10000)

# Local export limits
MAX_LOCAL_EXPORT_ROWS: int = _get_env_int("DS_MAX_LOCAL_EXPORT_ROWS", 10000)

# Attestation settings - for fetching cipher from remote verification service
DS_ATTESTATION_SOCKET: str = os.getenv("DS_ATTESTATION_SOCKET", "/var/run/delong-attestor/socket")
DS_ATTESTATION_AUDIENCE: str = os.getenv("DS_ATTESTATION_AUDIENCE", "https://delongapi.internal")
DS_ATTESTATION_ENDPOINT: Optional[str] = os.getenv("DS_ATTESTATION_ENDPOINT", "http://34.111.110.19/attestation/is_confidential")
DS_ATTESTATION_TIMEOUT: int = _get_env_int("DS_ATTESTATION_TIMEOUT", 10)


