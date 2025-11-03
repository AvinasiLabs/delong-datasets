#!/usr/bin/env python3
"""
Mock remote attestation verification service.

Simulates the /attestation/is_confidential endpoint.

In production, this service cryptographically verifies TEE attestation tokens
and returns encrypted ciphers. For testing, we just return a fixed cipher
for any valid-looking token.
"""
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Mock Attestation Service", version="1.0.0")


class AttestationRequest(BaseModel):
    """Request body for attestation verification."""

    token: str


class AttestationResponse(BaseModel):
    """Response containing encrypted cipher."""

    cipher: str


# Fixed cipher for testing - represents successful TEE attestation
# In production, this would be cryptographically generated based on attestation proof
TEST_CIPHER = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"


@app.post("/attestation/is_confidential", response_model=AttestationResponse)
def verify_attestation(request: AttestationRequest):
    """
    Verify attestation token and return cipher.

    In production: cryptographically verify TEE attestation token
    For testing: return fixed cipher for any token

    Args:
        request: Attestation request with token

    Returns:
        Response with encrypted cipher

    Raises:
        HTTPException: If token is invalid
    """
    if not request.token:
        raise HTTPException(status_code=400, detail="Token is required")

    # For mock: any non-empty token is considered valid
    # Production would verify cryptographic signatures here
    print(f"✓ Verified attestation token: {request.token[:20]}...")

    return AttestationResponse(cipher=TEST_CIPHER)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "mock-attestation"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("ATTESTATION_PORT", "8001"))
    print(f"Starting Mock Attestation Service on port {port}")
    print(f"Endpoint: http://localhost:{port}/attestation/is_confidential")
    uvicorn.run(app, host="0.0.0.0", port=port)
