#!/usr/bin/env bash
set -euo pipefail

# End-to-end test script for delong-datasets library
# Tests both local (sample data) and simulated TEE (real data) scenarios

echo "=========================================="
echo "delong-datasets End-to-End Test"
echo "=========================================="
echo ""

# Check if services are running
check_service() {
    local url=$1
    local name=$2
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✓ $name is running"
        return 0
    else
        echo "✗ $name is NOT running"
        return 1
    fi
}

# Test 1: Local environment (no attestation) - should get sample data
test_local_mode() {
    echo "=========================================="
    echo "Test 1: Local Mode (Sample Data)"
    echo "=========================================="
    echo ""
    echo "Environment: No attestation available"
    echo "Expected: Sample data returned"
    echo ""

    # Unset attestation config
    unset DS_ATTESTATION_ENDPOINT
    unset DS_ATTESTATION_SOCKET

    echo "Running: python -m delong_datasets download demo-dataset-001 --token demo-token --limit 3"
    echo ""
    python -m delong_datasets download demo-dataset-001 --token demo-token --limit 3

    echo ""
    echo "✓ Test 1 completed"
    echo ""
}

# Test 2: Simulated TEE environment - should get real data
test_tee_mode() {
    echo "=========================================="
    echo "Test 2: TEE Mode (Real Data)"
    echo "=========================================="
    echo ""
    echo "Environment: Attestation service available"
    echo "Expected: Real data returned"
    echo ""

    # Set attestation config
    export DS_ATTESTATION_ENDPOINT="http://localhost:8001/attestation/is_confidential"

    echo "Running: python -m delong_datasets download demo-dataset-001 --token demo-token --limit 3"
    echo ""
    python -m delong_datasets download demo-dataset-001 --token demo-token --limit 3

    echo ""
    echo "✓ Test 2 completed"
    echo ""
}

# Test 3: Column filtering
test_column_filter() {
    echo "=========================================="
    echo "Test 3: Column Filtering"
    echo "=========================================="
    echo ""

    export DS_ATTESTATION_ENDPOINT="http://localhost:8001/attestation/is_confidential"

    echo "Running: download with columns filter (patient_id, diagnosis)"
    echo ""
    python -m delong_datasets download demo-dataset-001 \
        --token demo-token \
        --columns patient_id,diagnosis \
        --limit 3

    echo ""
    echo "✓ Test 3 completed"
    echo ""
}

# Test 4: Pagination
test_pagination() {
    echo "=========================================="
    echo "Test 4: Pagination"
    echo "=========================================="
    echo ""

    export DS_ATTESTATION_ENDPOINT="http://localhost:8001/attestation/is_confidential"

    echo "Page 1 (limit 3):"
    python -m delong_datasets download demo-dataset-001 \
        --token demo-token \
        --limit 3

    echo ""
    echo "✓ Test 4 completed"
    echo ""
}

# Test 5: Export
test_export() {
    echo "=========================================="
    echo "Test 5: Data Export"
    echo "=========================================="
    echo ""

    export DS_ATTESTATION_ENDPOINT="http://localhost:8001/attestation/is_confidential"

    local output_file="/tmp/test_export.csv"

    echo "Exporting to: $output_file"
    echo ""
    python -m delong_datasets export demo-dataset-001 \
        --token demo-token \
        --format csv \
        --output "$output_file" \
        --limit 5

    echo ""
    echo "Export file contents:"
    cat "$output_file"

    rm -f "$output_file"

    echo ""
    echo "✓ Test 5 completed"
    echo ""
}

# Main test flow
main() {
    # Check prerequisites
    echo "Checking services..."
    echo ""

    if ! check_service "http://localhost:3003/docs" "Dataset Backend (port 3003)"; then
        echo ""
        echo "Please start the dataset backend first:"
        echo "  uvicorn scripts.mock_auth_server:app --host 127.0.0.1 --port 3003"
        exit 1
    fi

    if ! check_service "http://localhost:8001/health" "Attestation Service (port 8001)"; then
        echo ""
        echo "Warning: Attestation service not running (TEE tests will be skipped)"
        echo "To run full tests, start it with:"
        echo "  python scripts/mock_attestation_service.py"
        echo ""
        SKIP_TEE=1
    else
        SKIP_TEE=0
    fi

    echo ""

    # Set base config
    export DS_API_BASE_URL="http://127.0.0.1:3003"
    export TOKEN="demo-token"

    # Run tests
    test_local_mode

    if [ "$SKIP_TEE" -eq 0 ]; then
        test_tee_mode
        test_column_filter
        test_pagination
        test_export
    fi

    echo "=========================================="
    echo "All tests completed!"
    echo "=========================================="
}

main "$@"
