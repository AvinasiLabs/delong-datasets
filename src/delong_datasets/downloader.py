"""
Dataset conversion utilities.

Converts backend API 2D array response format to datasets.Dataset objects.
"""
from typing import Any, Dict, List, Optional

from .metadata import decrypt_stream_iter


def response_to_dict_list(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert 2D array response to list of dictionaries.

    Args:
        response: Backend response with 'data' (2D array) and 'columns' (list)

    Returns:
        List of dictionaries, one per row
    """
    columns = response["columns"]
    data = response["data"]
    return [{col: row[i] for i, col in enumerate(columns)} for row in data]


def load_dataset_from_api(
    dataset_id: str,
    token: str,
    *,
    columns: Optional[List[str]] = None,
    streaming: bool = True,
    limit: Optional[int] = None,
    offset: int = 0,
    query: Optional[str] = None,
):
    """
    Load dataset via SSE stream and return as datasets.Dataset or IterableDataset.

    Args:
        dataset_id: Dataset identifier
        token: JWT bearer token
        columns: Optional list of columns to fetch
        streaming: If True, return IterableDataset; else return in-memory Dataset
        limit: Optional maximum number of rows to fetch (default: fetch all)
        offset: Starting row offset for pagination (default: 0)
        query: Optional SQL query string; when provided, columns filter is ignored by server

    Returns:
        datasets.Dataset or datasets.IterableDataset
    """
    from datasets import Dataset, IterableDataset

    if streaming:
        def gen():
            for row in decrypt_stream_iter(
                dataset_id,
                token,
                columns=columns,
                offset=offset,
                limit=limit,
                query=query,
            ):
                yield row

        return IterableDataset.from_generator(gen)

    # Non-streaming: collect all into memory
    rows: List[Dict[str, Any]] = []
    for row in decrypt_stream_iter(
        dataset_id,
        token,
        columns=columns,
        offset=offset,
        limit=limit,
        query=query,
    ):
        rows.append(row)

    # Convert all values to strings to avoid Arrow type inference issues
    # (e.g., source_version can be 14.0 or "1.0.0")
    if rows:
        for row in rows:
            for key in row:
                if row[key] is not None:
                    row[key] = str(row[key])

    return Dataset.from_list(rows)


