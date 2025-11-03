"""
Public API for delong_datasets library.

Provides simplified interface for downloading and exporting datasets.
"""
from typing import List, Optional

from . import config
from .downloader import load_dataset_from_api


class DownloadOptions:
    """Options for dataset download."""

    def __init__(
        self,
        stream: bool = False,
        timeout_sec: int = config.DS_TIMEOUT,
        max_retries: int = config.DS_MAX_RETRIES,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> None:
        """
        Initialize download options.

        Args:
            stream: If True, return IterableDataset (lazy loading); if False, fetch all data
            timeout_sec: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            columns: Optional list of column names to fetch
            limit: Optional maximum number of rows to fetch
            offset: Starting row offset for pagination (default 0)
        """
        self.stream = stream
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.columns = columns
        self.limit = limit
        self.offset = offset


def download_dataset(dataset_id: str, token: str, options: Optional[DownloadOptions] = None):
    """
    Download dataset from backend API.

    Flow:
    1. Client attempts to get attestation cipher (TEE only)
    2. Client sends cipher as runtime_key to backend
    3. Backend verifies cipher and decides: real data (valid cipher) or sample data (no/invalid cipher)

    Client does NOT determine environment - backend makes all decisions.

    Args:
        dataset_id: Dataset identifier
        token: JWT bearer token
        options: Optional download options

    Returns:
        datasets.Dataset (if streaming=False) or datasets.IterableDataset (if streaming=True)
        Data type (real/sample) is determined by backend based on runtime_key

    Raises:
        NotFoundError: Dataset not found
        AuthError: Authentication/authorization failed
        NetworkError: Network or server error

    Example:
        >>> data = download_dataset("medical_imaging_2024", token)
        >>> print(f"Loaded {data.num_rows} rows")
        >>> print(data.column_names)
    """
    opts = options or DownloadOptions()

    return load_dataset_from_api(
        dataset_id,
        token,
        columns=opts.columns,
        streaming=opts.stream,
        limit=opts.limit,
        offset=opts.offset,
    )


def export_data(data, *, format: str, path: str) -> None:
    """
    Export dataset to file.

    Enforces row limits for export operations.

    Args:
        data: Dataset to export (datasets.Dataset or similar)
        format: Export format ('csv' or 'json')
        path: Output file path

    Raises:
        PolicyViolationError: If export exceeds row limits
        ValueError: If format is unsupported

    Example:
        >>> export_data(dataset, format="csv", path="/tmp/output.csv")
    """
    # Import policy enforcement here to avoid circular dependency
    from .policy import enforce_export_policy

    # Check export limits
    rows = getattr(data, "num_rows", None)
    enforce_export_policy(rows=rows)

    fmt = format.lower()
    try:
        # Use datasets native exporters if available
        if hasattr(data, "to_csv") and fmt == "csv":
            data.to_csv(path)  # type: ignore[attr-defined]
            return
        if hasattr(data, "to_json") and fmt == "json":
            data.to_json(path)  # type: ignore[attr-defined]
            return
        if hasattr(data, "to_parquet") and fmt == "parquet":
            data.to_parquet(path)  # type: ignore[attr-defined]
            return
    except Exception as e:  # noqa: BLE001
        raise e

    # Fallback: try pandas export
    try:
        import pandas as pd

        if hasattr(data, "to_pandas"):
            df = data.to_pandas()  # type: ignore[attr-defined]
        else:
            # best-effort conversion
            df = pd.DataFrame(list(data))
        if fmt == "csv":
            df.to_csv(path, index=False)
        elif fmt == "json":
            df.to_json(path, orient="records", lines=True, force_ascii=False)
        elif fmt == "parquet":
            df.to_parquet(path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    except Exception as e:  # noqa: BLE001
        # Return the original exception
        raise e


