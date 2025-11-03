#!/usr/bin/env python3
"""
Mock server for delong-datasets backend API.

Implements POST /api/datasets/decrypt endpoint matching the real backend.

For testing purposes:
- Empty runtime_key → returns sample data
- Non-empty runtime_key → returns real data (simulates successful TEE verification)

Real backend would verify the cipher cryptographically.
"""
import os
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Mock Delong Datasets API", version="1.0.0")

REQUIRED_TOKEN = os.getenv("MOCK_BEARER_TOKEN", "demo-token")


# Mock dataset storage - simulates encrypted datasets in backend
MOCK_DATASETS = {
    "demo-dataset-001": {
        "data": [
            ["PT-00001", 45, "malignant", 23.5],
            ["PT-00002", 62, "benign", 12.8],
            ["PT-00003", 38, "malignant", 31.2],
            ["PT-00004", 55, "benign", 8.4],
            ["PT-00005", 71, "malignant", 45.6],
            ["PT-00006", 48, "malignant", 18.7],
            ["PT-00007", 59, "benign", 9.3],
            ["PT-00008", 66, "malignant", 42.1],
            ["PT-00009", 41, "benign", 11.5],
            ["PT-00010", 73, "malignant", 38.9],
        ],
        "columns": ["patient_id", "age", "diagnosis", "tumor_size_mm"],
    },
    "medical_imaging_2024": {
        "data": [
            ["PT-10001", 50, "malignant", 28.3],
            ["PT-10002", 67, "benign", 15.1],
            ["PT-10003", 42, "malignant", 35.7],
            ["PT-10004", 58, "benign", 12.4],
            ["PT-10005", 45, "malignant", 29.8],
        ],
        "columns": ["patient_id", "age", "diagnosis", "tumor_size_mm"],
    },
    "genomics_study_2024": {
        "data": [
            ["GEN-001", "BRCA1", "positive", 0.85],
            ["GEN-002", "BRCA2", "negative", 0.15],
            ["GEN-003", "TP53", "positive", 0.92],
            ["GEN-004", "KRAS", "positive", 0.78],
            ["GEN-005", "EGFR", "negative", 0.22],
        ],
        "columns": ["sample_id", "gene", "mutation_status", "confidence"],
    },
}

# Sample data returned when no valid attestation cipher provided
SAMPLE_DATA = {
    "data": [
        ["sample_001", 40, "benign", 10.0],
        ["sample_002", 50, "malignant", 20.0],
        ["sample_003", 45, "benign", 15.0],
    ],
    "columns": ["patient_id", "age", "diagnosis", "tumor_size_mm"],
}


class DecryptRequest(BaseModel):
    """Request body for /api/datasets/decrypt"""

    dataset_id: str
    runtime_key: str
    columns: Optional[List[str]] = None
    offset: int = 0
    limit: int = 1000


def _require_bearer(authorization: Optional[str] = Header(None)) -> str:
    """Validate JWT bearer token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split(" ", 1)[1]
    if token != REQUIRED_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token


def _verify_runtime_key(runtime_key: str) -> bool:
    """
    Verify runtime_key (attestation cipher).

    For mock server:
    - Empty string → not in TEE, return sample data
    - Non-empty string → assume valid TEE cipher, return real data

    Real backend would cryptographically verify the cipher.

    Args:
        runtime_key: Attestation cipher from client

    Returns:
        True if should return real data (TEE verified), False for sample data
    """
    # Mock: any non-empty string is considered valid TEE cipher
    return bool(runtime_key)


@app.post("/api/datasets/decrypt")
def decrypt_dataset(request: DecryptRequest, _token: str = Depends(_require_bearer)):
    """
    Decrypt and return dataset data.

    Matches real backend API specification.
    """
    # Validate dataset exists
    if request.dataset_id not in MOCK_DATASETS:
        raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")

    # Verify runtime_key (attestation cipher) to determine if returning real or sample data
    is_real_data = _verify_runtime_key(request.runtime_key)

    # Select data source
    if is_real_data:
        dataset = MOCK_DATASETS[request.dataset_id]
        data_type = "real"
    else:
        dataset = SAMPLE_DATA
        data_type = "sample"

    all_data = dataset["data"]
    all_columns = dataset["columns"]

    # Apply column filtering
    if request.columns:
        try:
            column_indices = [all_columns.index(col) for col in request.columns]
            filtered_data = [[row[i] for i in column_indices] for row in all_data]
            filtered_columns = request.columns
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid column name: {e}")
    else:
        filtered_data = all_data
        filtered_columns = all_columns

    # Apply pagination
    total_rows = len(filtered_data)
    start = request.offset
    end = min(start + request.limit, total_rows)
    paginated_data = filtered_data[start:end]
    row_count = len(paginated_data)
    has_more = end < total_rows

    return {
        "data": paginated_data,
        "columns": filtered_columns,
        "row_count": row_count,
        "total_rows": total_rows,
        "has_more": has_more,
        "data_type": data_type,
    }



