# Migration Guide: Updated to Backend API v1.0

## Overview

The delong-datasets library has been updated to match the actual backend API (`POST /api/datasets/decrypt`). This document outlines the changes and migration steps.

---

## Key Changes

### 1. **Single Request Architecture**

**Before:** Two-phase approach (metadata → download file)
```python
meta = get_dataset_metadata(dataset_id, token)  # Phase 1
data = download_dataset(dataset_id, token)      # Phase 2
```

**After:** Single unified request
```python
data = download_dataset(dataset_id, token)  # All-in-one
```

### 2. **Remote Attestation Flow**

**Before:** Client fetched attestation token and sent directly to backend

**After:** Client fetches cipher from remote verification service
1. Fetch local attestation token from UNIX socket (`/var/run/delong-attestor/socket`)
2. Send token to remote verification service (`/attestation/is_confidential`)
3. Receive encrypted cipher from verification service
4. Pass cipher as `runtime_key` to backend
5. **Backend** verifies cipher and decides real vs sample data

Client does NOT decide if in TEE - backend makes authoritative decision.

### 3. **Direct Data Response (No File Download)**

**Before:** Backend returned `download_uri`, client downloaded and parsed file
```json
{
  "download_uri": "https://...",
  "file_ext": "csv",
  "parser_hint": "csv"
}
```

**After:** Backend returns data directly as 2D array
```json
{
  "data": [["row1val1", "row1val2"], ...],
  "columns": ["col1", "col2"],
  "row_count": 100,
  "total_rows": 1000,
  "has_more": true,
  "data_type": "real"
}
```

### 4. **Built-in Pagination Support**

**New:**
```python
opts = DownloadOptions(
    columns=["patient_id", "diagnosis"],
    limit=100  # Fetch only 100 rows
)
```

### 5. **Removed Public API**

- `get_dataset_metadata()` - no longer needed (internal only)
- CLI `meta` command - removed

---

## Environment Variables

### Required Variables

```bash
# Backend API base URL
export DS_API_BASE_URL="http://localhost:3003"
```

### Attestation Variables (for TEE environments)

```bash
# Remote attestation verification service
export DS_ATTESTATION_ENDPOINT="http://34.111.110.19/attestation/is_confidential"

# Local attestation socket (TEE only)
export DS_ATTESTATION_SOCKET="/var/run/delong-attestor/socket"

# Attestation audience
export DS_ATTESTATION_AUDIENCE="https://delongapi.internal"
```

### Removed Variables

```bash
# No longer needed:
DS_RUNTIME_KEY_SECRET    # Client doesn't encrypt, just fetches cipher
DS_SAMPLING_DEFAULT      # Backend controls sampling based on cipher
```

---

## Code Migration Examples

### Example 1: Basic Download

**Before:**
```python
from delong_datasets import get_dataset_metadata, download_dataset

token = "your-jwt-token"
meta = get_dataset_metadata("demo-dataset-001", token)
print(meta["name"])

data = download_dataset("demo-dataset-001", token)
```

**After:**
```python
from delong_datasets import download_dataset

token = "your-jwt-token"

data = download_dataset("demo-dataset-001", token)
print(f"Loaded {data.num_rows} rows with {len(data.column_names)} columns")
```

### Example 2: Column Filtering

**Before:** Not supported

**After:**
```python
from delong_datasets import DownloadOptions, download_dataset

opts = DownloadOptions(
    columns=["patient_id", "diagnosis", "tumor_size_mm"]
)
data = download_dataset("medical_imaging_2024", token, opts)
```

### Example 3: Limited Download

**Before:** Download all, then slice

**After:**
```python
opts = DownloadOptions(limit=1000)  # Fetch only 1000 rows
data = download_dataset("large-dataset", token, opts)
```

### Example 4: CLI Usage

**Before:**
```bash
# Metadata
python -m delong_datasets meta demo-dataset-001 --token "$TOKEN"

# Download
python -m delong_datasets download demo-dataset-001 --token "$TOKEN"
```

**After:**
```bash
# Download with preview (meta command removed)
python -m delong_datasets download demo-dataset-001 \
  --token "$TOKEN" \
  --columns patient_id,diagnosis \
  --limit 100 \
  --preview 5

# Export
python -m delong_datasets export demo-dataset-001 \
  --token "$TOKEN" \
  --format csv \
  --output output.csv \
  --columns patient_id,diagnosis
```

---

## Mock Server Setup

### Start Mock Server

```bash
# Install dependencies
pip install -e .[mock]

# Start server
export MOCK_BEARER_TOKEN="demo-token"
uvicorn scripts.mock_auth_server:app --host 127.0.0.1 --port 3003
```

### Configure Client

```bash
export DS_API_BASE_URL="http://127.0.0.1:3003"
export TOKEN="demo-token"

# Optional: To test with simulated attestation
export DS_ATTESTATION_ENDPOINT="http://your-attestation-service/is_confidential"
```

### Test

```bash
python -m delong_datasets download demo-dataset-001 --token "$TOKEN"
```

---

## Dependencies

No new dependencies required:

```toml
dependencies = [
  "datasets>=2.14",
]
```

**Installation:**
```bash
pip install -e .
```

**Note:** `pycryptodome` was previously required but has been removed. Attestation cipher is now fetched from remote service, not generated locally.

---

## Breaking Changes Summary

| Item | Before | After |
|------|--------|-------|
| **API calls** | 2 calls (metadata + download) | 1 call (unified) |
| **Auth method** | `attestation_cipher` parameter | `runtime_key` (cipher from remote verification) |
| **Data format** | File URL → download → parse | Direct 2D array in JSON |
| **Pagination** | Manual (client-side) | Built-in (server-side) |
| **Column filter** | Not supported | Supported via `columns` param |
| **Public API** | `get_dataset_metadata()` exposed | Removed (internal only) |
| **CLI commands** | `meta`, `download`, `export` | `download`, `export` only |
| **Required env** | `DS_FILE_ENDPOINT` | `DS_API_BASE_URL` |
| **Dependencies** | `datasets` only | `datasets` only (no crypto lib) |

---

## Testing Checklist

- [ ] Set `DS_API_BASE_URL` to backend endpoint
- [ ] Test basic download: `download_dataset(dataset_id, token)`
- [ ] Test column filtering: `DownloadOptions(columns=[...])`
- [ ] Test pagination: `DownloadOptions(limit=...)`
- [ ] Test export: `export_data(data, format="csv", path="...")`
- [ ] Verify attestation flow works in TEE environment:
  - [ ] UNIX socket `/var/run/delong-attestor/socket` accessible
  - [ ] Attestation service returns valid cipher
  - [ ] Backend returns real data when cipher provided
- [ ] Verify policy enforcement (export blocked in TEE)

---

## Support

For issues or questions:
- Check backend API documentation: `docs/decrypt_datasets_api.md`
- Review examples in `scripts/example_download.sh`
- See `dev_doc.md` for architecture details

---

**Version:** 0.1.0
**Last Updated:** 2025-01-04
