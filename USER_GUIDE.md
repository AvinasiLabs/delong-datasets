# delong-datasets User Guide

Complete guide to using the delong-datasets library for secure life sciences data access.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Basic Usage](#basic-usage)
6. [Advanced Features](#advanced-features)
7. [Configuration](#configuration)
8. [Security Model](#security-model)
9. [API Reference](#api-reference)
10. [CLI Reference](#cli-reference)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Overview
**delong-datasets** provides a unified SSE (Server-Sent Events) streaming interface compatible with HuggingFace `datasets`, and supports:

- **Unified SSE endpoint**: single entry for raw data and SQL queries
- **Server-side SQL (DuckDB)**: returns only result sets to minimize transfer
- **Column filtering and pagination**: `columns`, `offset`, `limit`
- **Multiple export formats**: CSV, JSON, Parquet, etc.

### Key Features
✅ **Unified access**: SSE streaming interface  
✅ **Server-side compute**: DuckDB executes SQL  
✅ **Familiar API**: built on HuggingFace datasets  
✅ **Flexible retrieval**: column filtering/pagination/streaming  
✅ **Policy enforcement**: export row limits

---

## Installation

### Basic Installation

```bash
pip install delong-datasets
```

### Development Installation

```bash
git clone git@github.com:AvinasiLabs/delong-datasets.git
cd delong-datasets
pip install -e .
```

### With Mock Services (Testing)

```bash
pip install -e .[mock]
```

### Requirements

- Python 3.9 or higher
- `datasets` >= 2.14

---

## Quick Start

### Python API

```python
from delong_datasets import download_dataset, DownloadOptions

# Basic usage - download full dataset
data = download_dataset(
    dataset_id="medical_imaging_2024",
    token="your-access-token"
)

print(f"Loaded {data.num_rows} rows")
print(f"Columns: {data.column_names}")

# Convert to pandas DataFrame
import pandas as pd
df = pd.DataFrame(data)
print(df.head())
```

### Command Line

```bash
# Set environment
export TOKEN="your-access-token"

# Download dataset
python -m delong_datasets download medical_imaging_2024 --token $TOKEN

# With options
python -m delong_datasets download medical_imaging_2024 \
    --token $TOKEN \
    --columns patient_id,diagnosis,age \
    --limit 100 \
    --preview 10
```

---

## Core Concepts
### 1. Unified SSE Interface

`GET /datasets/decrypt-stream` is the single entry point:
- Without `query`: streams the full dataset in raw data mode
- With `query`: executes SQL on the server (DuckDB) and streams only the results

Events in the stream:
- `metadata`: column info and chunking details
- `chunk`: data rows as a 2D array; column order matches `metadata.columns`
- `done`: completion marker
- `error`: error details

### 2. Data Access Modes

- **Raw data stream**: returns the full dataset in chunks; good for downloads/local analysis
- **SQL query mode**: returns only query results; ideal for aggregation, filtering, preview, and stats

---

## Basic Usage

### Downloading Datasets

#### Simple Download

```python
from delong_datasets import download_dataset

# Minimal usage
data = download_dataset("demo-dataset-001", "your-token")
print(data)
```

#### With Options

```python
from delong_datasets import download_dataset, DownloadOptions

# Configure download options
opts = DownloadOptions(
    columns=["patient_id", "diagnosis", "age"],  # Column filtering
    limit=1000,                                    # Row limit
    stream=False                                   # Streaming mode (False = materialize in-memory dataset)
)

data = download_dataset("demo-dataset-001", "your-token", opts)
```

#### Streaming Large Datasets

```python
from delong_datasets import download_dataset, DownloadOptions

# Stream dataset (memory efficient)
opts = DownloadOptions(stream=True)
dataset = download_dataset("large-genomics-data", "your-token", opts)

# Iterate over batches
for batch in dataset.iter(batch_size=100):
    process_batch(batch)
```

### Working with Data

#### Convert to Pandas

```python
import pandas as pd
from delong_datasets import download_dataset

data = download_dataset("medical_imaging_2024", "your-token")
df = pd.DataFrame(data)

# Standard pandas operations
print(df.describe())
print(df.groupby('diagnosis').size())
```

#### Convert to PyArrow

```python
data = download_dataset("medical_imaging_2024", "your-token")
table = data.to_pandas()  # Returns pandas.DataFrame; for Arrow/Parquet use to_parquet or pandas+pyarrow
```

#### Access as NumPy

```python
data = download_dataset("medical_imaging_2024", "your-token")

# Get specific column as numpy array
ages = data['age'].to_numpy()
print(f"Mean age: {ages.mean()}")
```

### Exporting Data

#### Export to CSV

```python
from delong_datasets import download_dataset, export_data

# Download data
data = download_dataset("demo-dataset-001", "your-token")

# Export to CSV
export_data(data, format="csv", path="/tmp/output.csv")
```

#### Export to Parquet

```python
export_data(data, format="parquet", path="/tmp/output.parquet")
```

#### Export to JSON

```python
export_data(data, format="json", path="/tmp/output.json")
```

#### CLI Export

```bash
python -m delong_datasets export demo-dataset-001 \
    --token $TOKEN \
    --format csv \
    --output /tmp/data.csv \
    --limit 5000
```

---

## Advanced Features

### Column Filtering

Request only the columns you need to reduce bandwidth and improve performance:

```python
from delong_datasets import download_dataset, DownloadOptions

# Only download specific columns
opts = DownloadOptions(columns=["patient_id", "diagnosis"])
data = download_dataset("demo-dataset-001", "your-token", opts)

print(data.column_names)  # ['patient_id', 'diagnosis']
```

**Benefits:**
- Reduced network bandwidth
- Faster downloads
- Lower memory usage
- Privacy: don't access columns you don't need

### Pagination

Handle large datasets efficiently with pagination:

```python
from delong_datasets import download_dataset, DownloadOptions

# Download in pages
page_size = 1000
offset = 0

while True:
    opts = DownloadOptions(limit=page_size, offset=offset)
    data = download_dataset("large-dataset", "your-token", opts)

    if data.num_rows == 0:
        break

    process_page(data)
    offset += page_size
```

### Streaming Mode

For very large datasets that don't fit in memory:

```python
from delong_datasets import download_dataset, DownloadOptions

opts = DownloadOptions(stream=True)
dataset = download_dataset("huge-genomics-data", "your-token", opts)

# Process in batches
for batch in dataset.iter(batch_size=1000):
    # Each batch is a dict of column_name -> list of values
    patient_ids = batch['patient_id']
    diagnoses = batch['diagnosis']

    # Process this batch
    results = analyze_batch(patient_ids, diagnoses)
    save_results(results)
```

### Custom Timeout and Retries

```python
from delong_datasets import download_dataset, DownloadOptions

opts = DownloadOptions(
    timeout_sec=60,      # Wait up to 60 seconds
    max_retries=5        # Retry up to 5 times on failure
)

data = download_dataset("demo-dataset-001", "your-token", opts)
```

### Working with Multiple Datasets

```python
from delong_datasets import download_dataset

datasets = {}
dataset_ids = ["medical_imaging_2024", "genomics_study_2024"]

for dataset_id in dataset_ids:
    datasets[dataset_id] = download_dataset(dataset_id, "your-token")
    print(f"Loaded {dataset_id}: {datasets[dataset_id].num_rows} rows")

# Combine datasets
import pandas as pd
combined_df = pd.concat([
    pd.DataFrame(datasets["medical_imaging_2024"]),
    pd.DataFrame(datasets["genomics_study_2024"])
], ignore_index=True)
```

### SQL Query (server-side)

Use `DownloadOptions.query` to execute SQL via DuckDB on the server; only results are streamed back:

```python
from delong_datasets import download_dataset, DownloadOptions

opts = DownloadOptions(
    query="SELECT sex, COUNT(*) AS cnt FROM data GROUP BY sex"
)
data = download_dataset("demo-dataset-001", "your-token", opts)
```

---

## Configuration

### Environment Variables

Configure the library using these environment variables:

| Variable | Description | 
|----------|-------------|
| `DS_API_BASE_URL` | Base API URL (used to derive defaults) |
| `DS_DECRYPT_STREAM_ENDPOINT` | SSE endpoint (defaults to `DS_API_BASE_URL + /datasets/decrypt-stream`) |
| `DS_TIMEOUT` | Request timeout (seconds) |
| `DS_MAX_RETRIES` | Maximum retry attempts |
| `DS_DEFAULT_LIMIT` | Default row limit |
| `DS_MAX_LOCAL_EXPORT_ROWS` | Maximum rows for local export |

### Configuration File

Create a `.env` file in your project:

```bash
# Performance
export DS_TIMEOUT=60
export DS_MAX_RETRIES=5
export DS_DEFAULT_LIMIT=5000

# Endpoint (optional; derived from DS_API_BASE_URL if not set)
export DS_DECRYPT_STREAM_ENDPOINT="https://your-host/datasets/decrypt-stream"
```

Load with:

```python
from dotenv import load_dotenv
load_dotenv()

from delong_datasets import download_dataset
data = download_dataset("demo-dataset-001", "your-token")
```

### Runtime Configuration

```python
from delong_datasets import download_dataset, DownloadOptions

# Override defaults per-request
opts = DownloadOptions(
    timeout_sec=90,
    max_retries=10
)

data = download_dataset("demo-dataset-001", "your-token", opts)
```

---

## Security Model

### Threat Model

**Assumptions:**
- Backend API is trusted and secure
- TEE hardware provides secure execution
- Attestation service correctly verifies TEE credentials
- Network communication can be monitored (use HTTPS)

**Protected Against:**
- ✅ Unauthorized access to sensitive data
- ✅ Malicious clients claiming to be in TEE
- ✅ Data exfiltration outside secure environment
- ✅ Tampering with client code

**Not Protected Against:**
- ❌ Compromised backend server
- ❌ Hardware attacks on TEE
- ❌ Authorized user exfiltrating data (insider threat)
- ❌ Side-channel attacks

### Access Control
Clients authenticate with JWT and access the unified SSE endpoint; the backend handles authorization and data return. Operators can configure IP allowlists and ownership checks on the server. For error semantics and event structure, see the “SSE Data Access” section above.

### Data Classification

| Data Type | Access | Environment | Export Limit |
|-----------|--------|-------------|--------------|
| **Sample Data** | Anyone | Any | Unlimited |
| **Real Data** | Authorized + TEE | TEE only | Configurable |

### Export Policy

Export limits prevent bulk data exfiltration:

```python
from delong_datasets import download_dataset, export_data

# Download large dataset (allowed)
data = download_dataset("demo-dataset-001", "your-token")

# Export limited rows (controlled by policy)
try:
    export_data(data, format="csv", path="/tmp/data.csv")
except PolicyViolationError as e:
    print(f"Export denied: {e}")
    # Suggestion: Use streaming mode or process in chunks
```

**Default limits:**
- Local export: 10,000 rows
- Configurable via `DS_MAX_LOCAL_EXPORT_ROWS`

---

## API Reference

### Core Functions

#### `download_dataset()`

Download a dataset from the backend API.

```python
def download_dataset(
    dataset_id: str,
    token: str,
    options: Optional[DownloadOptions] = None
) -> datasets.Dataset | datasets.IterableDataset
```

**Parameters:**
- `dataset_id` (str): Unique identifier for the dataset
- `token` (str): Bearer token for authentication
- `options` (DownloadOptions, optional): Download configuration

**Returns:**
- `datasets.Dataset`: In-memory dataset (default)
- `datasets.IterableDataset`: Streaming dataset (if `stream=True`)

**Raises:**
- `AuthError`: authentication/authorization failed
- `NotFoundError`: dataset not found
- `NetworkError`: network or server error
- `RateLimitError`: rate limited
- `RemoteServerError`: remote server error
- `PolicyViolationError`: export policy violation

**Example:**
```python
data = download_dataset("demo-dataset-001", "my-token")
```

#### `export_data()`

Export dataset to a file.

```python
def export_data(
    dataset: datasets.Dataset,
    format: str,
    path: str
) -> None
```

**Parameters:**
- `dataset` (Dataset): Dataset to export
- `format` (str): Output format (`csv`, `json`, `parquet`, `arrow`)
- `path` (str): Output file path

**Raises:**
- `PolicyViolationError`: Exceeds export row limit

**Example:**
```python
export_data(data, format="csv", path="/tmp/output.csv")
```

### Configuration Classes

#### `DownloadOptions`

Configuration for dataset downloads.

```python
class DownloadOptions:
    def __init__(
        self,
        stream: bool = False,
        timeout_sec: int = 30,
        max_retries: int = 3,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        query: Optional[str] = None,   # Server-side SQL query
    )
```

**Attributes:**
- `stream` (bool): Enable streaming mode
- `timeout_sec` (int): Request timeout in seconds
- `max_retries` (int): Maximum retry attempts
- `columns` (List[str]): Column filter (None = all columns)
- `limit` (int): Maximum rows to download
- `offset` (int): Starting row offset (for pagination)
- `query` (str | None): SQL executed on the server (when provided, `columns` filter is ignored)

**Example:**
```python
opts = DownloadOptions(
    columns=["patient_id", "diagnosis"],
    limit=100,
    stream=False
)
```

### Exceptions

#### `PolicyViolationError`

Raised when an operation violates data access policy.

```python
from delong_datasets.policy import PolicyViolationError

try:
    export_data(large_dataset, "csv", "/tmp/data.csv")
except PolicyViolationError as e:
    print(f"Export denied: {e}")
```

---

## CLI Reference

### Commands

#### `download`

Download and preview a dataset.

```bash
python -m delong_datasets download <dataset_id> [OPTIONS]
```

**Options:**
- `--token TEXT`: Bearer token (required, or set `$TOKEN`)
- `--columns TEXT`: Comma-separated column names
- `--limit INTEGER`: Maximum rows to download
- `--preview INTEGER`: Number of rows to preview (default: 5)
- `--stream`: Enable streaming mode

**Examples:**
```bash
# Basic download
python -m delong_datasets download demo-dataset-001 --token $TOKEN

# With column filter
python -m delong_datasets download demo-dataset-001 \
    --token $TOKEN \
    --columns patient_id,diagnosis

# With limit and preview
python -m delong_datasets download demo-dataset-001 \
    --token $TOKEN \
    --limit 100 \
    --preview 10

# Streaming mode
python -m delong_datasets download large-dataset \
    --token $TOKEN \
    --stream
```

#### `export`

Export dataset to a file.

```bash
python -m delong_datasets export <dataset_id> [OPTIONS]
```

**Options:**
- `--token TEXT`: Bearer token (required)
- `--format TEXT`: Output format (`csv`, `json`, `parquet`) (required)
- `--output TEXT`: Output file path (required)
- `--columns TEXT`: Column filter
- `--limit INTEGER`: Row limit

**Examples:**
```bash
# Export to CSV
python -m delong_datasets export demo-dataset-001 \
    --token $TOKEN \
    --format csv \
    --output /tmp/data.csv

# Export with filters
python -m delong_datasets export demo-dataset-001 \
    --token $TOKEN \
    --format parquet \
    --output /tmp/data.parquet \
    --columns patient_id,age,diagnosis \
    --limit 5000
```

---

## Best Practices

### 1. Token Management

**Don't hardcode tokens:**
```python
# ❌ Bad
data = download_dataset("dataset", "hardcoded-token-here")

# ✅ Good
import os
token = os.environ['TOKEN']
data = download_dataset("dataset", token)
```

**Use secure token storage:**
```bash
# Store in environment
export TOKEN=$(cat ~/.config/delong/token)

# Or use secret management
export TOKEN=$(aws secretsmanager get-secret-value --secret-id delong-token --query SecretString --output text)
```

### 2. Column Filtering

**Always filter columns:**
```python
# ❌ Bad - downloads all columns
data = download_dataset("large-dataset", token)

# ✅ Good - only needed columns
opts = DownloadOptions(columns=["patient_id", "diagnosis"])
data = download_dataset("large-dataset", token, opts)
```

### 3. Memory Management

**Use streaming for large datasets:**
```python
# ❌ Bad - loads entire dataset into memory
data = download_dataset("100gb-dataset", token)
df = pd.DataFrame(data)  # OOM!

# ✅ Good - stream and process in chunks
opts = DownloadOptions(stream=True)
dataset = download_dataset("100gb-dataset", token, opts)

for batch in dataset.iter(batch_size=1000):
    process_and_save(batch)
```

### 4. Error Handling

**Always handle errors:**
```python
from delong_datasets import download_dataset
from requests import HTTPError

try:
    data = download_dataset("demo-dataset-001", token)
except HTTPError as e:
    if e.response.status_code == 401:
        print("Invalid token")
    elif e.response.status_code == 404:
        print("Dataset not found")
    else:
        print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 5. Testing

**Use mock services for development:**
```bash
# Start mock services
bash scripts/start_mock_services.sh

# Set test environment
export TOKEN="demo-token"

# Run your code
python my_analysis.py

# Stop services
pkill -f mock_auth_server
pkill -f mock_attestation_service
```

### 6. Performance

**Enable connection pooling:**
```python
# The library automatically reuses connections
# Download multiple datasets efficiently
for dataset_id in dataset_list:
    data = download_dataset(dataset_id, token)
    process(data)
```

**Use pagination for large exports:**
```python
# Instead of one large export
page_size = 5000
for i in range(0, total_rows, page_size):
    opts = DownloadOptions(limit=page_size, offset=i)
    data = download_dataset("dataset", token, opts)
    export_data(data, "csv", f"/tmp/part_{i}.csv")
```

### 7. Security

**Verify you're in TEE when needed:**
```python
from delong_datasets import download_dataset

data = download_dataset("sensitive-dataset", token)

# Check data type in response metadata (if available)
# Real data will have different characteristics than sample data
if data.num_rows < 10 and "sample" in str(data[0]):
    print("WARNING: Received sample data, not in TEE!")
    exit(1)
```

**Don't cache sensitive data:**
```python
# ❌ Bad - caches real data to disk
data = download_dataset("sensitive-dataset", token)
data.save_to_disk("/tmp/cache")  # Violates security!

# ✅ Good - process in memory only
data = download_dataset("sensitive-dataset", token)
results = analyze(data)
save_results_only(results)  # Only save aggregated results
```

---

## Troubleshooting

### Connection Errors

**Problem:** `Connection refused` or `Connection timeout`

**Solutions:**
```bash
# Increase timeout
export DS_TIMEOUT=60
```

### Authentication Errors

**Problem:** `401 Unauthorized`

**Solutions:**
```bash
# Verify token is set
echo $TOKEN
```

### Attestation Errors

**Problem:** Getting sample data when expecting real data

**Solutions:**
```bash
# Check attestation socket exists
ls -l $DS_ATTESTATION_SOCKET

# Verify attestation endpoint
curl $DS_ATTESTATION_ENDPOINT

# Check attestation service logs
# (In TEE environment, contact administrator)

# For testing, start mock attestor
python scripts/mock_tee_attestor.py --mode unix --socket /tmp/delong-attestor.sock
```

### Memory Errors

**Problem:** `MemoryError` or OOM when loading large datasets

**Solutions:**
```python
# Use streaming mode
opts = DownloadOptions(stream=True)
dataset = download_dataset("large-dataset", token, opts)

# Or paginate
opts = DownloadOptions(limit=1000)
data = download_dataset("large-dataset", token, opts)

# Or filter columns
opts = DownloadOptions(columns=["id", "label"])
data = download_dataset("large-dataset", token, opts)
```

### Export Policy Errors

**Problem:** `PolicyViolationError: Export exceeds limit`

**Solutions:**
```python
# Solution 1: Export in chunks
for i in range(0, total, chunk_size):
    opts = DownloadOptions(limit=chunk_size, offset=i)
    chunk = download_dataset("dataset", token, opts)
    export_data(chunk, "csv", f"/tmp/chunk_{i}.csv")

# Solution 2: Use streaming (no export limit)
opts = DownloadOptions(stream=True)
dataset = download_dataset("dataset", token, opts)
for batch in dataset.iter(batch_size=1000):
    process(batch)  # Process without exporting

# Solution 3: Request higher limit (contact administrator)
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'delong_datasets'`

**Solutions:**
```bash
# Reinstall package
pip uninstall delong-datasets
pip install delong-datasets

# Or install in development mode
pip install -e .

# Verify installation
pip list | grep delong-datasets
python -c "import delong_datasets; print(delong_datasets.__version__)"
```

### Data Format Issues

**Problem:** Unexpected data format or types

**Solutions:**
```python
# Check dataset info
print(data.info)
print(data.features)

# Convert types explicitly
import pandas as pd
df = pd.DataFrame(data)
df['age'] = df['age'].astype(int)
df['diagnosis'] = df['diagnosis'].astype('category')

# Handle missing values
df = df.fillna({'tumor_size_mm': 0})
```

---

## Support

### Documentation

- **User Guide**: This document
- **Quick Start**: `QUICKSTART.md`
- **Architecture**: `ARCHITECTURE.md`
- **Migration Guide**: `MIGRATION_GUIDE.md`
- **API Specification**: `docs/decrypt_datasets_api.md`

### Getting Help

1. **Check Documentation**: Review this guide and related docs
2. **Search Issues**: Check GitHub issues for similar problems
3. **Ask Questions**: Open a GitHub discussion
4. **Report Bugs**: Open a GitHub issue with reproduction steps

### Example Projects

See `examples/` directory for:
- Basic usage examples
- Advanced filtering and pagination
- Integration with ML pipelines
- TEE deployment examples

---

## Acknowledgments

This library is built on top of the excellent [🤗 Datasets](https://github.com/huggingface/datasets) library by HuggingFace, which provides the foundational dataset loading and processing capabilities.

### Citation

If you use delong-datasets in your research, please consider citing both this library and the underlying HuggingFace Datasets library:

**HuggingFace Datasets:**

```bibtex
@inproceedings{lhoest-etal-2021-datasets,
    title = "Datasets: A Community Library for Natural Language Processing",
    author = "Lhoest, Quentin and others",
    booktitle = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing: System Demonstrations",
    month = nov,
    year = "2021",
    address = "Online and Punta Cana, Dominican Republic",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.emnlp-demo.21",
    pages = "175--184",
}
```

For the complete BibTeX entry, see [README.md](README.md#citation) or [CITATION.cff](CITATION.cff).

---

## SSE Data Access (Server-Sent Events)

This SDK uses a unified SSE (Server-Sent Events) streaming interface for data access. It supports two modes via a single endpoint:

- Raw data stream: no `query` parameter — returns the full dataset in chunks
- SQL query mode: provide `query` — executed on the server (DuckDB), returning only the result set

---

### Endpoint

```
GET /datasets/decrypt-stream?dataset_id={id}[&query={sql}][&columns={cols}][&offset={n}][&limit={n}]
```

Authentication header:

```
Authorization: Bearer {jwt_token}
```

Query parameters:

- `dataset_id` (string, required): Dataset ID
- `query` (string, optional): SQL query. When provided, the server executes it via DuckDB on the dataset
- `columns` (string, optional): Comma-separated column names (only applies in raw data mode)
- `offset` (number, optional): Row offset (default 0)
- `limit` (number, optional): Row limit

---

### SSE Events and Payloads

Event types:

- `metadata`: Dataset metadata including column names
- `chunk`: Data chunk containing rows
- `done`: Completion marker
- `error`: Error message

1) `metadata`

Raw data mode example:

```json
{
  "event": "metadata",
  "columns": ["id", "name", "age", "sex"],
  "total_chunks": 10,
  "chunk_size": 10000,
  "data_type": "csv"
}
```

SQL query mode example:

```json
{
  "event": "metadata",
  "columns": ["sex", "count"],
  "total_chunks": 1,
  "chunk_size": 2,
  "data_type": "query_result"
}
```

2) `chunk`

```json
{
  "event": "chunk",
  "chunk_idx": 0,
  "rows": [
    ["1", "Alice", "30", "F"],
    ["2", "Bob", "25", "M"],
    ["3", "Charlie", "35", "M"]
  ],
  "row_count": 3
}
```

Important: `rows` is a 2D array of row values; column order matches `metadata.columns`.

3) `done`

Raw data mode example:

```json
{
  "event": "done",
  "total_rows": 230516,
  "total_chunks": 24
}
```

SQL query mode adds:

```json
{
  "event": "done",
  "total_rows": 2,
  "total_chunks": 1,
  "execution_time_ms": 45,
  "cache_hit": true
}
```

4) `error`

```json
{
  "event": "error",
  "message": "User does not have access to dataset: 69"
}
```

---

### Full SSE Examples

Raw data stream:

```
event: metadata
data: {"event":"metadata","columns":["id","name","age","sex"],"total_chunks":3,"chunk_size":100000,"data_type":"csv"}

event: chunk
data: {"event":"chunk","chunk_idx":0,"rows":[["1","Alice","30","F"],["2","Bob","25","M"]],"row_count":2}

event: chunk
data: {"event":"chunk","chunk_idx":1,"rows":[["3","Charlie","35","M"]],"row_count":1}

event: done
data: {"event":"done","total_rows":3,"total_chunks":2}
```

SQL query:

```
event: metadata
data: {"event":"metadata","columns":["sex","count"],"total_chunks":1,"chunk_size":2,"data_type":"query_result"}

event: chunk
data: {"event":"chunk","chunk_idx":0,"rows":[["M",150000],["F",80516]],"row_count":2}

event: done
data: {"event":"done","total_rows":2,"total_chunks":1,"execution_time_ms":45,"cache_hit":true}
```

---

### Request Examples

Raw data:

```bash
# Full dataset
curl -N "http://localhost:20011/datasets/decrypt-stream?dataset_id=69" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Specific columns + limit
curl -N "http://localhost:20011/datasets/decrypt-stream?dataset_id=69&columns=name,age&limit=100" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

SQL query:

```bash
# Simple query
curl -N "http://localhost:20011/datasets/decrypt-stream?dataset_id=69&query=SELECT%20*%20FROM%20data%20LIMIT%205" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Aggregation
curl -N "http://localhost:20011/datasets/decrypt-stream?dataset_id=69&query=SELECT%20COUNT(*)%20FROM%20data" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Grouped stats
curl -N "http://localhost:20011/datasets/decrypt-stream?dataset_id=69&query=SELECT%20sex,COUNT(*)%20FROM%20data%20GROUP%20BY%20sex" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### SQL Capabilities and Limits

- Supported operations: SELECT with filter, aggregation, grouping, sorting, pagination
  - Examples:
    - `SELECT * FROM data WHERE age > 30`
    - `SELECT COUNT(*), AVG(age) FROM data`
    - `SELECT sex, COUNT(*) FROM data GROUP BY sex`
    - `SELECT * FROM data ORDER BY age DESC`
    - `SELECT * FROM data LIMIT 100 OFFSET 200`
- Restrictions:
  - Only `SELECT` queries are allowed
  - Mutating statements (`INSERT/UPDATE/DELETE/DROP`) are disallowed
  - Table name is fixed to `data`

---

### Usage Recommendations

- Small datasets (< 10MB): SQL — `SELECT * FROM data`
- Large-scale analysis: SQL — `SELECT ... GROUP BY ...`
- Full large dataset download: Raw data stream (no `query`)
- Preview: SQL — `SELECT * FROM data LIMIT 100`
- Counting: SQL — `SELECT COUNT(*) FROM data`

---

### Access Control (Server Configuration)

Environment variables (example for local/dev):

```bash
# IP allowlist (comma-separated; IPv4/IPv6/CIDR supported)
ALLOWED_DECRYPT_IPS=127.0.0.1,::1,10.124.0.0/16,172.21.0.0/16

# Trust X-Forwarded-For (true for local dev and managed ingress)
TRUST_PROXY=true

# Ownership check (allow dataset owner direct access in dev)
ENABLE_OWNERSHIP_CHECK=true
```

Allowlist formats:

- Single IPv4: `192.168.1.100`
- Single IPv6: `::1`
- CIDR: `10.124.0.0/16`

Security note: Do not set `TRUST_PROXY=true` unless behind a trusted reverse proxy, otherwise clients could spoof IPs.

Ownership check modes:

- `ENABLE_OWNERSHIP_CHECK=true`: dataset owner (`project_address == wallet`) can access directly
- `ENABLE_OWNERSHIP_CHECK=false`: only contract-based access (`hasValidAccess`) is used

---

### Error Handling

HTTP status codes:

- 401: Authentication failed (invalid or expired JWT)
- 403: No permission or IP not in allowlist
- 404: Dataset not found
- 400: Bad request or SQL syntax error
- 500: Internal server error

SSE `error` event contains a descriptive message.

---

### Performance Characteristics

- Parquet caching: First query caches data as Parquet; subsequent queries are faster
- DuckDB on server: SQL executed server-side; only results are streamed
- SSE streaming: Low memory footprint; supports large datasets
- Cache hit indicator: `cache_hit: true` in `done` event

---

## Changelog

### v0.1.0 (Current)

**Features:**
- Initial release
- TEE attestation support
- Column filtering
- Pagination
- Streaming mode
- Multiple export formats
- CLI interface

**Security:**
- Zero-trust client design
- Backend-controlled authorization
- Export policy enforcement

---

## License

See `LICENSE` file for details.

---

**Questions?** Check the [Quick Start Guide](QUICKSTART.md) or [Architecture Documentation](ARCHITECTURE.md).

**Happy analyzing!** 🔬
