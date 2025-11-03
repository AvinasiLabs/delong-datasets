"""
Dataset decryption API client.

Calls backend POST /api/datasets/decrypt endpoint to fetch dataset data.
Returns data directly as 2D array with metadata.
"""
import json
import urllib.request
from typing import Any, Dict, List, Optional

from . import config
from .errors import AuthError, NetworkError, NotFoundError, RateLimitError, RemoteServerError
from .attestation import get_attestation_cipher


def _request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    method: str = "POST",
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Make HTTP request and handle common error responses."""
    data_bytes = None
    if json_body is not None:
        data_bytes = json.dumps(json_body).encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if json_body is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - trusted endpoint configured by operator
            status = resp.getcode()
            body = resp.read().decode("utf-8")
            if status == 200:
                return json.loads(body)
            if status in (401, 403):
                raise AuthError(body)
            if status == 404:
                raise NotFoundError(body)
            if status == 429:
                raise RateLimitError(body)
            if 500 <= status < 600:
                raise RemoteServerError(body)
            raise RemoteServerError(f"Unexpected status {status}: {body}")
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        body_text = ""
        try:
            body_text = e.read().decode("utf-8")
        except Exception:
            pass
        if e.code in (401, 403):
            raise AuthError(body_text or str(e))
        if e.code == 404:
            raise NotFoundError(body_text or str(e))
        if e.code == 429:
            raise RateLimitError(body_text or str(e))
        if 500 <= e.code < 600:
            raise RemoteServerError(body_text or str(e))
        raise NetworkError(body_text or str(e))
    except Exception as e:  # noqa: BLE001
        raise NetworkError(str(e))


def decrypt_dataset(
    dataset_id: str,
    token: str,
    *,
    columns: Optional[List[str]] = None,
    offset: int = 0,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    Call backend /api/datasets/decrypt endpoint.

    Args:
        dataset_id: Dataset identifier
        token: JWT bearer token
        columns: Optional list of column names to return
        offset: Pagination offset (default 0)
        limit: Number of rows to return (default 1000)

    Returns:
        Dict containing:
            - data: List[List[Any]] - 2D array of row data
            - columns: List[str] - column names
            - row_count: int - number of rows returned
            - total_rows: int - total rows in dataset
            - has_more: bool - whether more data exists
            - data_type: str - "real" or "sample"

    Raises:
        NotFoundError: Dataset not found
        AuthError: Authentication/authorization failed
        NetworkError: Network or server error
    """
    if not config.DS_DECRYPT_ENDPOINT:
        raise NotFoundError("DS_DECRYPT_ENDPOINT is not configured")

    headers = {"Authorization": f"Bearer {token}"}

    # Get attestation cipher (empty string if not in TEE)
    runtime_key = get_attestation_cipher()

    body: Dict[str, Any] = {
        "dataset_id": dataset_id,
        "runtime_key": runtime_key,  # Empty string if not in TEE, cipher if in TEE
        "offset": offset,
        "limit": limit,
    }

    if columns:
        body["columns"] = columns

    response = _request(
        config.DS_DECRYPT_ENDPOINT, headers=headers, timeout=config.DS_TIMEOUT, method="POST", json_body=body
    )

    # Validate response structure
    required_keys = ["data", "columns", "row_count", "total_rows", "has_more", "data_type"]
    for key in required_keys:
        if key not in response:
            raise RemoteServerError(f"Invalid response: missing key '{key}'")

    return response


