"""
Attestation module for remote verification.

Flow:
1. Fetch local attestation token from UNIX socket (/var/run/delong-attestor/socket)
2. Send token to remote verification service (/attestation/is_confidential)
3. Get encrypted cipher from remote service
4. Pass cipher as runtime_key to backend dataset API
5. Backend verifies cipher and returns real or sample data

Client does NOT decide if in TEE - backend decides based on cipher.
"""
import json
import socket
import urllib.request
from typing import Optional

from . import config


_cached_cipher: Optional[str] = None


def _read_http_response(sock: socket.socket) -> str:
    """Read HTTP response from socket."""
    data = b""
    # Read headers
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk

    header_part, _, body_rest = data.partition(b"\r\n\r\n")
    headers_text = header_part.decode("latin1")
    headers_lines = headers_text.split("\r\n")

    # Parse Content-Length
    content_length = None
    for line in headers_lines:
        if ":" in line:
            k, v = line.split(":", 1)
            if k.strip().lower() == "content-length":
                try:
                    content_length = int(v.strip())
                except Exception:
                    content_length = None
                break

    if content_length is not None:
        need = content_length - len(body_rest)
        chunks = [body_rest]
        while need > 0:
            chunk = sock.recv(min(4096, need))
            if not chunk:
                break
            chunks.append(chunk)
            need -= len(chunk)
        return b"".join(chunks).decode("utf-8")

    # Fallback: read until close
    chunks = [body_rest]
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8")


def fetch_local_attestation_token() -> Optional[str]:
    """
    Fetch attestation token from local UNIX socket.

    Returns:
        Attestation token string, or None if socket not available
    """
    try:
        # Connect to local attestor service
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(config.DS_ATTESTATION_TIMEOUT)
        sock.connect(config.DS_ATTESTATION_SOCKET)

        # Build HTTP request
        request_body = json.dumps({"audience": config.DS_ATTESTATION_AUDIENCE})
        http_request = (
            f"POST /token HTTP/1.1\r\n"
            f"Host: localhost\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length:{len(request_body)}\r\n\r\n"
            f"{request_body}"
        )

        # Send request
        sock.sendall(http_request.encode("utf-8"))

        # Read response
        response_body = _read_http_response(sock)
        sock.close()

        # Parse JSON response
        data = json.loads(response_body)
        return data.get("token")

    except Exception:
        # Socket not available or error - not in TEE environment
        return None


def request_attestation_cipher(token: str) -> Optional[str]:
    """
    Send attestation token to remote verification service.

    Args:
        token: Local attestation token from UNIX socket

    Returns:
        Encrypted cipher from remote service, or None if verification fails
    """
    if not config.DS_ATTESTATION_ENDPOINT:
        return None

    try:
        # Build request to remote verification service
        payload = json.dumps({"token": token}).encode("utf-8")
        req = urllib.request.Request(
            config.DS_ATTESTATION_ENDPOINT,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        # Send request
        with urllib.request.urlopen(req, timeout=config.DS_ATTESTATION_TIMEOUT) as resp:  # nosec - controlled endpoint
            if resp.getcode() != 200:
                return None

            raw = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
                # Remote service returns cipher in response
                # Accept both {"cipher": "..."} and {"token": "..."} for compatibility
                return data.get("cipher") or data.get("token")
            except Exception:
                return None

    except Exception:
        return None


def get_attestation_cipher() -> str:
    """
    Get attestation cipher to use as runtime_key.

    This is the main function to call. It:
    1. Fetches local attestation token (if in TEE)
    2. Sends token to remote verification service
    3. Returns encrypted cipher from remote service
    4. Returns empty string if not in TEE or verification fails

    Returns:
        Encrypted cipher string (to use as runtime_key), or empty string
    """
    global _cached_cipher

    # Return cached value if available
    if _cached_cipher is not None:
        return _cached_cipher

    # Try to fetch local attestation token
    local_token = fetch_local_attestation_token()
    if not local_token:
        # Not in TEE environment or socket not available
        _cached_cipher = ""
        return _cached_cipher

    # Request cipher from remote verification service
    cipher = request_attestation_cipher(local_token)
    _cached_cipher = cipher or ""

    return _cached_cipher


