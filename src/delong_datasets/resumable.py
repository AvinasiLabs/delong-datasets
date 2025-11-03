import os
import tempfile
from typing import Dict, Iterable, Optional, Tuple

from . import config


def _http_head(url: str, headers: Dict[str, str], timeout: int) -> Tuple[int, Dict[str, str]]:
    import urllib.request

    req = urllib.request.Request(url, method="HEAD")
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - trusted endpoint configured by operator
        status = resp.getcode()
        # urllib on some servers may not return headers for HEAD; fallback to GET small range if needed in future
        hdrs = {k.lower(): v for k, v in resp.headers.items()}  # type: ignore[attr-defined]
        return status, hdrs


def _http_get(
    url: str, headers: Dict[str, str], timeout: int, range_start: Optional[int]
) -> Tuple[int, Optional[int], Iterable[bytes]]:
    import urllib.request

    req = urllib.request.Request(url, method="GET")
    for k, v in headers.items():
        req.add_header(k, v)
    if range_start is not None and range_start > 0:
        req.add_header("Range", f"bytes={range_start}-")

    resp = urllib.request.urlopen(req, timeout=timeout)  # nosec - endpoint controlled
    status = resp.getcode()
    length = resp.headers.get("Content-Length")  # type: ignore[attr-defined]
    try:
        length_int = int(length) if length is not None else None
    except Exception:
        length_int = None

    def _iter():
        try:
            while True:
                chunk = resp.read(1024 * 64)
                if not chunk:
                    break
                yield chunk
        finally:
            try:
                resp.close()
            except Exception:
                pass

    return status, length_int, _iter()


def resumable_download(url: str, headers: Dict[str, str], dest_path: str) -> str:
    """
    Download URL to dest_path with basic Range resume support.
    - If dest_path.part exists, resume from its size when server supports Range (206).
    - On 200 responses, restart from scratch.
    """
    part_path = dest_path + ".part"
    timeout = config.DS_TIMEOUT

    existing = 0
    if os.path.exists(part_path):
        existing = os.path.getsize(part_path)

    # Probe server for range support (best-effort)
    try:
        status, hdrs = _http_head(url, headers, timeout)
        accept_ranges = hdrs.get("accept-ranges", "").lower()
        supports_range = "bytes" in accept_ranges or status == 200
    except Exception:
        supports_range = True  # fall back to try

    range_start = existing if (existing > 0 and supports_range) else None

    status, _length, stream = _http_get(url, headers, timeout, range_start)

    # If server ignores range and returns 200, we restart
    mode = "ab" if status == 206 and range_start else "wb"
    with open(part_path, mode) as f:
        for chunk in stream:
            f.write(chunk)

    # Commit
    if os.path.exists(dest_path):
        os.remove(dest_path)
    os.replace(part_path, dest_path)
    return dest_path


def download_to_tempfile(url: str, headers: Dict[str, str]) -> str:
    fd, path = tempfile.mkstemp(prefix="ds_resumable_", suffix=".bin")
    os.close(fd)
    # use path without relying on created empty file; resumable will write to path.part then move
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    return resumable_download(url, headers, path)


