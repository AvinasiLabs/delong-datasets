"""
Dataset decryption streaming client (SSE).

Connects to GET /datasets/decrypt-stream and yields rows progressively.
"""
import json
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

from . import config
from .errors import AuthError, NetworkError, NotFoundError, RateLimitError, RemoteServerError, ParseError


def decrypt_stream_iter(
    dataset_id: str,
    token: str,
    *,
    columns: Optional[List[str]] = None,
    offset: int = 0,
    limit: Optional[int] = None,
    query: Optional[str] = None,
    timeout: int = config.DS_TIMEOUT,
) -> Iterator[Dict[str, Any]]:
    """
    Connect to SSE decrypt stream and yield rows as dicts.

    Args:
        dataset_id: Dataset identifier
        token: JWT bearer token
        columns: Optional list of columns (only effective when query is None)
        offset: Starting row offset (default 0)
        limit: Optional maximum number of rows to yield
        query: Optional SQL query string (server executes on DuckDB)
        timeout: Request timeout in seconds

    Yields:
        Dict[str, Any] for each row with keys per metadata.columns
    """
    if not config.DS_DECRYPT_STREAM_ENDPOINT:
        raise NotFoundError("DS_DECRYPT_STREAM_ENDPOINT is not configured")

    # Build URL with query parameters
    from urllib.parse import urlencode

    params: Dict[str, Any] = {
        "dataset_id": dataset_id,
        "metadata_uri": dataset_id,  # Use dataset_id as metadata_uri (required by backend)
    }
    if query:
        params["query"] = query
    else:
        if columns:
            params["columns"] = ",".join(columns)
    if offset:
        params["offset"] = offset
    if limit is not None:
        params["limit"] = limit

    url = f"{config.DS_DECRYPT_STREAM_ENDPOINT}?{urlencode(params)}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "text/event-stream")

    yielded = 0
    meta_columns: Optional[List[str]] = None

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - trusted endpoint configured by operator
            # Parse SSE: lines starting with "event:" or "data:", separated by blank line
            event_name: Optional[str] = None
            data_lines: List[str] = []

            def flush_event() -> Dict[str, Any]:
                nonlocal event_name, data_lines, meta_columns, yielded, limit
                if not event_name:
                    data_lines.clear()
                    return {"rows": [], "stop": False}
                raw = "\n".join(data_lines).strip()
                data_lines.clear()
                try:
                    payload = json.loads(raw) if raw else {}
                except Exception as e:
                    raise ParseError(f"Invalid SSE data JSON: {e}") from e

                ev = event_name
                event_name = None

                if ev == "metadata":
                    cols = payload.get("columns")
                    if not isinstance(cols, list):
                        raise ParseError("metadata.columns missing or invalid")
                    meta_columns = cols
                    return {"rows": [], "stop": False}
                if ev == "chunk":
                    rows = payload.get("rows", [])
                    if not isinstance(rows, list):
                        raise ParseError("chunk.rows missing or invalid")
                    out_rows: List[Dict[str, Any]] = []
                    for row in rows:
                        # Support both dict format (new) and list format (legacy)
                        if isinstance(row, dict):
                            row_dict = row
                        elif isinstance(row, list):
                            if meta_columns is None:
                                raise ParseError("Received list row before metadata with columns")
                            row_dict = {
                                col: row[idx] if idx < len(row) else None
                                for idx, col in enumerate(meta_columns)
                            }
                        else:
                            raise ParseError("chunk.rows[] must be dict or list")
                        if limit is None or yielded < limit:
                            out_rows.append(row_dict)
                            yielded += 1
                        if limit is not None and yielded >= limit:
                            break
                    return {"rows": out_rows, "stop": limit is not None and yielded >= limit}
                if ev == "done":
                    return {"rows": [], "stop": True}
                if ev == "error":
                    message = payload.get("message", "Unknown error")
                    # Heuristic mapping to auth error
                    lower_msg = str(message).lower()
                    if "access" in lower_msg or "permission" in lower_msg or "forbidden" in lower_msg:
                        raise AuthError(message)
                    raise RemoteServerError(message)
                # Ignore unknown events
                return {"rows": [], "stop": False}

            while True:
                line_bytes = resp.readline()
                if line_bytes == b"":  # EOF
                    break
                try:
                    line = line_bytes.decode("utf-8")
                except Exception:
                    # best-effort decoding
                    line = line_bytes.decode("latin-1", errors="ignore")
                line = line.rstrip("\r\n")
                if not line:
                    # event boundary
                    result = flush_event()
                    for r in result["rows"]:
                        yield r
                    if result["stop"]:
                        return
                    continue
                if line.startswith("event:"):
                    event_name = line[len("event:") :].strip()
                    continue
                if line.startswith("data:"):
                    data_lines.append(line[len("data:") :].lstrip())
                    continue
                # Ignore other fields like id:, retry:

            # Final flush in case stream ended without trailing newline
            result = flush_event()
            for r in result["rows"]:
                yield r
            if result["stop"]:
                return
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

