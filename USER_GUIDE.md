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

**delong-datasets** is a Python library for accessing sensitive life sciences datasets with built-in security controls. It extends HuggingFace's `datasets` library with:

- **TEE (Trusted Execution Environment) Support**: Automatic attestation-based access control
- **Graceful Degradation**: Sample data in non-secure environments, real data in TEE
- **Backend-Controlled Security**: Zero-trust client design where backend makes all authorization decisions
- **Column Filtering**: Request only the data columns you need
- **Pagination**: Efficient handling of large datasets
- **Multiple Export Formats**: CSV, JSON, Parquet, and more

### Key Features

✅ **Automatic Environment Detection**: No manual configuration needed
✅ **Secure by Default**: Sample data returned outside TEE environments
✅ **Familiar API**: Built on HuggingFace datasets library
✅ **Flexible Access**: CLI and Python API
✅ **Policy Enforcement**: Built-in data export limits

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

### 1. TEE (Trusted Execution Environment)

A **Trusted Execution Environment** is a secure area of a processor that guarantees code and data are protected with respect to confidentiality and integrity. The library automatically detects TEE environments through attestation.

### 2. Attestation Flow

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│ Client  │────▶│ TEE Attestor │────▶│ Verification │────▶│ Backend │
│ Library │     │ (Unix Socket)│     │   Service    │     │   API   │
└─────────┘     └──────────────┘     └──────────────┘     └─────────┘
                      Token                Cipher            Decision
```

1. **Client** requests attestation token from local TEE service
2. **TEE Attestor** provides cryptographically signed token
3. **Verification Service** validates token and returns encrypted cipher
4. **Backend API** verifies cipher and grants access to real data

### 3. Data Access Modes

| Mode | Environment | Data Returned | Use Case |
|------|-------------|---------------|----------|
| **Local** | Non-TEE | Sample data | Development, testing, debugging |
| **TEE** | Secure TEE | Real data | Production analysis on sensitive data |

### 4. Zero-Trust Client

The client library does **NOT** decide whether it's running in a secure environment. It only:
- Fetches attestation credentials
- Forwards them to the backend
- **Backend makes all authorization decisions**

This prevents malicious clients from bypassing security controls.

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
    stream=False                                   # Streaming mode
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
table = data.to_pandas()  # Returns pyarrow.Table
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

---

## Configuration

### Environment Variables

Configure the library using environment variables:

| Variable | Description | 
|----------|-------------|
| `DS_ATTESTATION_ENDPOINT` | Remote attestation service URL |
| `DS_ATTESTATION_SOCKET` | Local TEE attestor socket path |
| `DS_ATTESTATION_AUDIENCE` | Attestation token audience |
| `DS_ATTESTATION_TIMEOUT` | Attestation timeout (seconds) |
| `DS_TIMEOUT` | API request timeout (seconds) |
| `DS_MAX_RETRIES` | Maximum retry attempts |
| `DS_DEFAULT_LIMIT` | Default row limit |
| `DS_MAX_LOCAL_EXPORT_ROWS` | Maximum rows for local export |

### Configuration File

Create a `.env` file in your project:

```bash

# Performance tuning
DS_TIMEOUT=60
DS_MAX_RETRIES=5
DS_DEFAULT_LIMIT=5000
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

### Zero-Trust Client Design

The client library is intentionally "dumb":

```python
# Client DOES NOT verify environment
# Client ONLY fetches and forwards credentials

def get_attestation_cipher() -> str:
    """
    Fetch cipher from attestation flow.
    Returns empty string if not in TEE.
    """
    token = fetch_from_unix_socket()      # Local attestation
    if not token:
        return ""                          # Not in TEE, return empty

    cipher = verify_with_remote(token)    # Remote verification
    return cipher or ""                   # Forward cipher to backend
```

**Backend verifies and decides:**

```python
# Backend code (conceptual)
def decrypt_dataset(dataset_id: str, runtime_key: str):
    if verify_cipher(runtime_key):
        return get_real_data(dataset_id)   # TEE verified
    else:
        return get_sample_data(dataset_id) # Not in TEE
```

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
- `ValueError`: Invalid parameters
- `requests.HTTPError`: API request failed
- `PolicyViolationError`: Policy violation

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
        offset: int = 0
    )
```

**Attributes:**
- `stream` (bool): Enable streaming mode
- `timeout_sec` (int): Request timeout in seconds
- `max_retries` (int): Maximum retry attempts
- `columns` (List[str]): Column filter (None = all columns)
- `limit` (int): Maximum rows to download
- `offset` (int): Starting row offset (for pagination)

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
