#!/usr/bin/env bash
set -euo pipefail

# Start all mock services for testing

echo "=========================================="
echo "Starting Mock Services"
echo "=========================================="
echo ""

# Check if services are already running
check_port() {
    local port=$1
    if netstat -tln 2>/dev/null | grep -q ":$port "; then
        return 0
    elif ss -tln 2>/dev/null | grep -q ":$port "; then
        return 0
    else
        return 1
    fi
}

# Kill existing services
cleanup() {
    echo "Cleaning up existing services..."
    pkill -f "mock_auth_server" || true
    pkill -f "mock_attestation_service" || true
    sleep 1
}

# Start dataset backend
start_backend() {
    echo "Starting Dataset Backend (port 3003)..."
    export MOCK_BEARER_TOKEN="demo-token"
    uvicorn scripts.mock_auth_server:app \
        --host 127.0.0.1 \
        --port 3003 \
        --log-level warning \
        > /tmp/mock_backend.log 2>&1 &

    sleep 2
    if check_port 3003; then
        echo "✓ Dataset Backend running on http://localhost:3003"
        echo "  API Docs: http://localhost:3003/docs"
    else
        echo "✗ Failed to start Dataset Backend"
        cat /tmp/mock_backend.log
        exit 1
    fi
}

# Start attestation service
start_attestation() {
    echo "Starting Attestation Service (port 8001)..."
    python scripts/mock_attestation_service.py \
        > /tmp/mock_attestation.log 2>&1 &

    sleep 2
    if check_port 8001; then
        echo "✓ Attestation Service running on http://localhost:8001"
        echo "  Endpoint: http://localhost:8001/attestation/is_confidential"
    else
        echo "✗ Failed to start Attestation Service"
        cat /tmp/mock_attestation.log
        exit 1
    fi
}

# Main
main() {
    cleanup

    start_backend
    echo ""
    start_attestation
    echo ""

    echo "=========================================="
    echo "All services started successfully!"
    echo "=========================================="
    echo ""
    echo "Services:"
    echo "  - Dataset Backend:     http://localhost:3003"
    echo "  - Attestation Service: http://localhost:8001"
    echo ""
    echo "Logs:"
    echo "  - Backend:     /tmp/mock_backend.log"
    echo "  - Attestation: /tmp/mock_attestation.log"
    echo ""
    echo "Test the setup:"
    echo "  source set-env.sh"
    echo "  python -m delong_datasets download demo-dataset-001 --token demo-token"
    echo ""
    echo "Or run full test suite:"
    echo "  bash scripts/test_e2e.sh"
    echo ""
    echo "Stop services:"
    echo "  pkill -f mock_auth_server"
    echo "  pkill -f mock_attestation_service"
    echo ""
}

main "$@"
