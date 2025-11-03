# Quick Start Guide

Complete guide to testing delong-datasets library with mock services.

---

## Prerequisites

```bash
# Install the library
pip install -e .

# Install mock server dependencies
pip install -e .[mock]
```

---

## Option 1: Automated Testing (Recommended)

### Start All Services

```bash
# Start dataset backend + attestation service
bash scripts/start_mock_services.sh
```

This will start:
- **Dataset Backend** on `http://localhost:3003`
- **Attestation Service** on `http://localhost:8001`

### Run Test Suite

```bash
# Load environment
source set-env.sh

# Run end-to-end tests
bash scripts/test_e2e.sh
```

The test suite covers:
1. Local mode (sample data)
2. TEE mode (real data with attestation)
3. Column filtering
4. Pagination
5. Data export

### Stop Services

```bash
pkill -f mock_auth_server
pkill -f mock_attestation_service
```

---

## Option 2: Manual Testing

### Step 1: Start Dataset Backend

```bash
# Terminal 1
export MOCK_BEARER_TOKEN="demo-token"
uvicorn scripts.mock_auth_server:app --host 127.0.0.1 --port 3003
```

API documentation available at: http://localhost:3003/docs

### Step 2: Configure Environment

```bash
# Terminal 2
source set-env.sh
```

### Step 3: Test Local Mode (Sample Data)

Without attestation service, you'll get sample data:

```bash
# Download dataset
python -m delong_datasets download demo-dataset-001 --token demo-token

# With options
python -m delong_datasets download demo-dataset-001 \
    --token demo-token \
    --columns patient_id,diagnosis \
    --limit 3
```

**Expected output:**
```
Dataset loaded: 3 rows, 4 columns
Columns: ['patient_id', 'age', 'diagnosis', 'tumor_size_mm']

Preview (first 3 rows):
  patient_id  age diagnosis  tumor_size_mm
0  sample_001   40    benign           10.0
1  sample_002   50 malignant           20.0
2  sample_003   45    benign           15.0
```

### Step 4: Test TEE Mode (Real Data)

Start attestation service:

```bash
# Terminal 3
python scripts/mock_attestation_service.py
```

Enable attestation in client:

```bash
# Terminal 2
export DS_ATTESTATION_ENDPOINT="http://localhost:8001/attestation/is_confidential"

# Now download with attestation
python -m delong_datasets download demo-dataset-001 --token demo-token --limit 3
```

**Expected output:**
```
Dataset loaded: 3 rows, 4 columns
Columns: ['patient_id', 'age', 'diagnosis', 'tumor_size_mm']

Preview (first 3 rows):
  patient_id  age diagnosis  tumor_size_mm
0  PT-00001   45 malignant           23.5
1  PT-00002   62    benign           12.8
2  PT-00003   38 malignant           31.2
```

Note: Data is different (real vs sample)!

---

## Available Datasets

| Dataset ID | Rows | Columns | Description |
|-----------|------|---------|-------------|
| `demo-dataset-001` | 10 | 4 | Medical imaging demo |
| `medical_imaging_2024` | 5 | 4 | Medical imaging study |
| `genomics_study_2024` | 5 | 4 | Genomics research data |

---

## Example Commands

### Basic Download
```bash
python -m delong_datasets download demo-dataset-001 --token demo-token
```

### Column Filtering
```bash
python -m delong_datasets download demo-dataset-001 \
    --token demo-token \
    --columns patient_id,diagnosis
```

### Pagination
```bash
python -m delong_datasets download demo-dataset-001 \
    --token demo-token \
    --limit 5 \
    --preview 3
```

### Export to File
```bash
python -m delong_datasets export demo-dataset-001 \
    --token demo-token \
    --format csv \
    --output /tmp/data.csv \
    --limit 5
```

### Streaming Mode
```bash
python -m delong_datasets download demo-dataset-001 \
    --token demo-token \
    --stream
```

---

## Python API Usage

```python
from delong_datasets import download_dataset, DownloadOptions, export_data

# Basic usage
data = download_dataset("demo-dataset-001", "demo-token")
print(f"Loaded {data.num_rows} rows")

# With options
opts = DownloadOptions(
    columns=["patient_id", "diagnosis"],
    limit=100,
    stream=False
)
data = download_dataset("medical_imaging_2024", "demo-token", opts)

# Export
export_data(data, format="csv", path="/tmp/output.csv")
```

---

## Service Endpoints

### Dataset Backend (port 3003)

```bash
# API endpoint
POST http://localhost:3003/api/datasets/decrypt

# Request
{
  "dataset_id": "demo-dataset-001",
  "runtime_key": "cipher-or-empty",
  "columns": ["patient_id", "diagnosis"],
  "offset": 0,
  "limit": 1000
}

# Response
{
  "data": [["PT-001", "malignant"], ...],
  "columns": ["patient_id", "diagnosis"],
  "row_count": 10,
  "total_rows": 10,
  "has_more": false,
  "data_type": "real"
}
```

### Attestation Service (port 8001)

```bash
# Verification endpoint
POST http://localhost:8001/attestation/is_confidential

# Request
{
  "token": "local-attestation-token"
}

# Response
{
  "cipher": "a1b2c3d4e5f6..."
}
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 3003
lsof -i :3003

# Kill process
kill -9 <PID>
```

### Services Not Starting

Check logs:
```bash
tail -f /tmp/mock_backend.log
tail -f /tmp/mock_attestation.log
```

### Import Errors

```bash
# Reinstall
pip uninstall delong-datasets
pip install -e .
```

### Authentication Errors

Check token matches:
```bash
echo $TOKEN
# Should output: demo-token
```

---

## Architecture

```
Local Mode (No Attestation):
  Client → Backend → Returns sample data

TEE Mode (With Attestation):
  Client → Local Attestor (UNIX socket) → Get token
       → Verification Service → Get cipher
       → Backend (with cipher) → Returns real data
```

See `ARCHITECTURE.md` for detailed architecture documentation.

---

## Next Steps

1. ✅ Run automated test suite: `bash scripts/test_e2e.sh`
2. ✅ Try manual commands with different options
3. ✅ Test with your own datasets (add to `mock_auth_server.py`)
4. ✅ Review API documentation: http://localhost:3003/docs
5. ✅ Read full architecture: `ARCHITECTURE.md`

---

**Questions?** Check:
- `ARCHITECTURE.md` - Architecture details
- `MIGRATION_GUIDE.md` - Migration from old design
- `docs/decrypt_datasets_api.md` - Backend API specification

**Have fun testing!** 🎉
