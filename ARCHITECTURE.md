# Architecture Overview

## Design Principle

**Simple and Secure: Backend decides everything based on cryptographic proof.**

The client is deliberately "dumb" - it just fetches and forwards attestation cipher to the backend. The backend makes all authorization decisions.

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Client (delong_datasets)                                        │
│                                                                  │
│  1. Call download_dataset(dataset_id, token)                    │
│                                                                  │
│  2. Try to get attestation cipher:                              │
│     - Check if UNIX socket exists                               │
│     - If yes: fetch token → send to verification service        │
│     - Get cipher or empty string                                │
│                                                                  │
│  3. POST /api/datasets/decrypt                                  │
│     {                                                            │
│       "dataset_id": "...",                                       │
│       "runtime_key": "cipher-or-empty-string",                  │
│       "offset": 0,                                               │
│       "limit": 1000                                              │
│     }                                                            │
│                                                                  │
│  4. Receive response:                                            │
│     {                                                            │
│       "data": [[...], ...],                                      │
│       "columns": [...],                                          │
│       "data_type": "real" or "sample"  ← Backend's decision     │
│     }                                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Backend (dataset management service)                            │
│                                                                  │
│  1. Receive request with runtime_key                            │
│                                                                  │
│  2. Verify cipher cryptographically:                            │
│     - Valid cipher from TEE → return REAL data                  │
│     - Empty/invalid cipher → return SAMPLE data                 │
│                                                                  │
│  3. Apply pagination, column filtering                          │
│                                                                  │
│  4. Return response with data_type indicator                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Decisions

### 1. **Client Does NOT Verify Environment**

❌ **Bad (old design):**
```python
if is_tee_environment():
    # Request full data
else:
    # Request sample data
```

✅ **Good (current design):**
```python
# Always try to get cipher, let backend decide
cipher = get_attestation_cipher()  # Empty string if not in TEE
send_to_backend(runtime_key=cipher)  # Backend makes decision
```

**Why:**
- Client cannot be trusted to determine its own environment
- Only backend can cryptographically verify TEE attestation
- Simpler client code with fewer dependencies

### 2. **Attestation Flow**

```
TEE Environment:
  UNIX socket exists → fetch token → get cipher → backend returns real data

Local Environment:
  No UNIX socket → empty cipher → backend returns sample data

Production Backend:
  Cryptographically verifies cipher using private keys
  Only valid TEE attestations can produce verifiable ciphers

Mock Backend (testing):
  Any non-empty string → real data
  Empty string → sample data
```

### 3. **No Client-Side Policy Enforcement**

The client does not:
- ❌ Decide if user can access full data
- ❌ Block operations based on environment detection
- ❌ Verify cryptographic signatures

The client only:
- ✅ Fetches attestation cipher (if available)
- ✅ Forwards cipher to backend
- ✅ Enforces export row limits (configurable via env var)

---

## Module Responsibilities

| Module | Responsibility | Environment Check? |
|--------|---------------|-------------------|
| `attestation.py` | Fetch cipher from remote service | No |
| `metadata.py` | Call backend API with cipher | No |
| `downloader.py` | Convert backend response to Dataset | No |
| `api.py` | Public API interface | No |
| `env.py` | **DEPRECATED** - always returns False | No |
| `policy.py` | Only check export row limits | No |

---

## Configuration

### Required
```bash
export DS_API_BASE_URL="http://localhost:3003"
```

### Attestation (TEE only)
```bash
export DS_ATTESTATION_ENDPOINT="http://verification-service/attestation/is_confidential"
export DS_ATTESTATION_SOCKET="/var/run/delong-attestor/socket"  # Provided by TEE infrastructure
export DS_ATTESTATION_AUDIENCE="https://delongapi.internal"
```

### Optional
```bash
export DS_TIMEOUT=30                      # Request timeout
export DS_DEFAULT_LIMIT=1000              # Pagination default
export DS_MAX_LOCAL_EXPORT_ROWS=10000    # Export limit
```

---

## Security Properties

1. **Zero Trust Client**
   - Client cannot fake TEE environment
   - Client cannot decrypt or forge ciphers
   - Client cannot access real data without valid attestation

2. **Backend Authority**
   - Backend has cryptographic keys to verify attestation
   - Backend makes all access decisions
   - Backend logs all access for audit

3. **Graceful Degradation**
   - No attestation available → automatic sample data
   - Network errors → fail safely
   - Invalid cipher → sample data

4. **Minimal Attack Surface**
   - No crypto libraries on client
   - No secret keys on client
   - No complex policy logic on client

---

## Testing

### Local Development (Sample Data)
```bash
source set-env.sh
uvicorn scripts.mock_auth_server:app --port 3003
python -m delong_datasets download demo-dataset-001 --token demo-token
# Gets sample data (no attestation available)
```

### TEE Environment (Real Data)
```bash
# Requires:
# - TEE infrastructure providing /var/run/delong-attestor/socket
# - Attestation verification service running
# - Backend with cryptographic verification

export DS_ATTESTATION_ENDPOINT="http://verification-service/attestation/is_confidential"
python -m delong_datasets download dataset-id --token $TOKEN
# Gets real data (valid attestation cipher)
```

---

## API Contract

### Client → Backend Request
```json
POST /api/datasets/decrypt
{
  "dataset_id": "medical_imaging_2024",
  "runtime_key": "hex-encoded-cipher-or-empty",
  "columns": ["patient_id", "diagnosis"],
  "offset": 0,
  "limit": 1000
}
```

### Backend → Client Response
```json
{
  "data": [
    ["PT-001", "malignant"],
    ["PT-002", "benign"]
  ],
  "columns": ["patient_id", "diagnosis"],
  "row_count": 2,
  "total_rows": 5000,
  "has_more": true,
  "data_type": "real"  // or "sample"
}
```

**Key Point:** `data_type` field tells client what it received, but client does nothing different based on this - it's informational only.

---

## Migration from Old Design

| Old Design | New Design |
|-----------|-----------|
| Client generates runtime_key locally | Client fetches cipher from remote service |
| Client needs `DS_RUNTIME_KEY_SECRET` | No secrets needed |
| Client needs `pycryptodome` | No crypto dependencies |
| Client has `is_secure_env()` logic | Deprecated - always returns False |
| Policy enforcement based on env | Only enforce export limits |

---

## Questions & Answers

**Q: How does the backend verify the cipher?**
A: Backend has private keys to verify cryptographic signatures from TEE attestation. Client cannot forge valid ciphers.

**Q: What if attestation service is down?**
A: Client gets empty cipher → backend returns sample data. System stays available.

**Q: Can client "trick" backend by sending fake cipher?**
A: No. Backend cryptographically verifies cipher. Invalid ciphers → sample data.

**Q: Why not let client decide based on environment variables?**
A: Client can be compromised. Only backend decision is trustworthy.

**Q: What about export restrictions in TEE?**
A: Backend returns limited data + policy tags. Backend-side enforcement is primary.

---

**Version:** 1.0
**Last Updated:** 2025-01-04
**Status:** Current design - no environment verification on client
