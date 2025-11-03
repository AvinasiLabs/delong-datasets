"""
Dataset conversion utilities.

Converts backend API 2D array response format to datasets.Dataset objects.
"""
from typing import Any, Dict, Iterator, List, Optional

from . import config
from .metadata import decrypt_dataset


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


def fetch_all_pages(
    dataset_id: str,
    token: str,
    *,
    columns: Optional[List[str]] = None,
    page_size: int = 1000,
    start_offset: int = 0,
) -> Iterator[Dict[str, Any]]:
    """
    Fetch all pages from backend and yield rows as dictionaries.

    Args:
        dataset_id: Dataset identifier
        token: JWT bearer token
        columns: Optional column filter
        page_size: Rows per page
        start_offset: Starting offset for pagination

    Yields:
        Dict representing each row
    """
    offset = start_offset
    has_more = True

    while has_more:
        response = decrypt_dataset(
            dataset_id,
            token,
            columns=columns,
            offset=offset,
            limit=page_size,
        )

        # Convert and yield rows
        for row_dict in response_to_dict_list(response):
            yield row_dict

        # Update pagination
        offset += response["row_count"]
        has_more = response["has_more"]


def load_dataset_from_api(
    dataset_id: str,
    token: str,
    *,
    columns: Optional[List[str]] = None,
    streaming: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
):
    """
    Load dataset from backend API and return as datasets.Dataset or IterableDataset.

    Args:
        dataset_id: Dataset identifier
        token: JWT bearer token
        columns: Optional list of columns to fetch
        streaming: If True, return IterableDataset; if False, fetch all and return Dataset
        limit: Maximum number of rows to fetch (default: fetch all)
        offset: Starting row offset for pagination (default: 0)

    Returns:
        datasets.Dataset or datasets.IterableDataset
    """
    from datasets import Dataset, IterableDataset

    if streaming:
        # Return iterable dataset that lazily fetches pages
        def gen():
            for row in fetch_all_pages(dataset_id, token, columns=columns, page_size=config.DS_DEFAULT_LIMIT, start_offset=offset):
                yield row

        return IterableDataset.from_generator(gen)

    # Non-streaming: fetch all pages into memory
    all_rows: List[Dict[str, Any]] = []
    page_size = limit if limit and limit < config.DS_DEFAULT_LIMIT else config.DS_DEFAULT_LIMIT

    for row in fetch_all_pages(dataset_id, token, columns=columns, page_size=page_size, start_offset=offset):
        all_rows.append(row)
        if limit and len(all_rows) >= limit:
            break

    return Dataset.from_list(all_rows)


