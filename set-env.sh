#!/usr/bin/env bash
# Environment configuration for delong-datasets testing

# Client configuration
export DS_API_BASE_URL="http://127.0.0.1:3003"
export TOKEN="demo-token"

# Attestation configuration (uncomment to simulate TEE environment)
# export DS_ATTESTATION_ENDPOINT="http://127.0.0.1:8001/attestation/is_confidential"
# export DS_ATTESTATION_SOCKET="/tmp/delong-attestor.sock"
# export DS_ATTESTATION_AUDIENCE="https://delongapi.internal"

# Optional customization
# export DS_TIMEOUT=30
# export DS_MAX_RETRIES=3
# export DS_DEFAULT_LIMIT=1000
# export DS_MAX_LOCAL_EXPORT_ROWS=10000

echo "=========================================="
echo "delong-datasets Environment"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Backend API: $DS_API_BASE_URL"
echo "  Token: $TOKEN"
echo ""
echo "Available datasets:"
echo "  - demo-dataset-001 (10 rows)"
echo "  - medical_imaging_2024 (5 rows)"
echo "  - genomics_study_2024 (5 rows)"
echo ""
echo "Quick start:"
echo ""
echo "  1. Start all services:"
echo "     bash scripts/start_mock_services.sh"
echo ""
echo "  2. Run test suite:"
echo "     bash scripts/test_e2e.sh"
echo ""
echo "  3. Try manual commands:"
echo "     python -m delong_datasets download demo-dataset-001 --token \$TOKEN"
echo "     python -m delong_datasets download medical_imaging_2024 --token \$TOKEN --limit 3"
echo "     python -m delong_datasets download demo-dataset-001 --token \$TOKEN --columns patient_id,diagnosis"
echo ""
echo "=========================================="