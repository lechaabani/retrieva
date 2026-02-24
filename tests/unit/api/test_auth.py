"""Unit tests for authentication: API keys and JWT tokens."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from api.auth.api_keys import generate_api_key, verify_api_key
from api.auth.jwt import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    verify_token,
)


# =============================================================================
# API Key generation and verification
# =============================================================================

class TestApiKeyGeneration:
    """Tests for API key generation."""

    def test_generate_returns_tuple(self):
        """generate_api_key should return a (raw_key, hashed_key) tuple."""
        raw, hashed = generate_api_key()

        assert isinstance(raw, str)
        assert isinstance(hashed, str)
        assert raw != hashed

    def test_raw_key_has_prefix(self):
        """The raw key should start with the 'rtv_' prefix."""
        raw, _ = generate_api_key()
        assert raw.startswith("rtv_")

    def test_raw_key_is_unique(self):
        """Two generated keys should be different."""
        raw_1, _ = generate_api_key()
        raw_2, _ = generate_api_key()
        assert raw_1 != raw_2

    def test_hashed_key_is_bcrypt(self):
        """The hashed key should be a bcrypt hash (starts with $2b$)."""
        _, hashed = generate_api_key()
        assert hashed.startswith("$2b$")


class TestApiKeyVerification:
    """Tests for API key verification."""

    def test_valid_key_verifies(self):
        """A raw key should verify against its own hash."""
        raw, hashed = generate_api_key()
        assert verify_api_key(raw, hashed) is True

    def test_wrong_key_does_not_verify(self):
        """A different raw key should not verify against a given hash."""
        raw_1, hashed_1 = generate_api_key()
        raw_2, _ = generate_api_key()
        assert verify_api_key(raw_2, hashed_1) is False

    def test_empty_key_does_not_verify(self):
        """An empty string should not verify against any hash."""
        _, hashed = generate_api_key()
        assert verify_api_key("", hashed) is False

    def test_tampered_key_does_not_verify(self):
        """A modified key should not verify."""
        raw, hashed = generate_api_key()
        tampered = raw + "x"
        assert verify_api_key(tampered, hashed) is False


# =============================================================================
# JWT token creation and verification
# =============================================================================

class TestJWTTokenCreation:
    """Tests for JWT token creation."""

    def test_create_token_returns_string(self):
        """create_access_token should return a non-empty JWT string."""
        token = create_access_token(data={"sub": str(uuid.uuid4())})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_claims(self):
        """The token should contain the provided claims when decoded."""
        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id, "role": "admin"})
        payload = verify_token(token)

        assert payload["sub"] == user_id
        assert payload["role"] == "admin"

    def test_token_has_expiry(self):
        """The token should contain an 'exp' claim."""
        token = create_access_token(data={"sub": "test"})
        payload = verify_token(token)
        assert "exp" in payload

    def test_token_has_issued_at(self):
        """The token should contain an 'iat' claim."""
        token = create_access_token(data={"sub": "test"})
        payload = verify_token(token)
        assert "iat" in payload

    def test_custom_expiry(self):
        """A custom expires_delta should be respected."""
        token = create_access_token(
            data={"sub": "test"},
            expires_delta=timedelta(hours=24),
        )
        payload = verify_token(token)
        # The expiry should be roughly 24h from now
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = exp - now
        assert 23 * 3600 <= diff.total_seconds() <= 25 * 3600


class TestJWTTokenVerification:
    """Tests for JWT token verification."""

    def test_valid_token_verifies(self):
        """A properly created token should verify without error."""
        token = create_access_token(data={"sub": "user-123"})
        payload = verify_token(token)
        assert payload["sub"] == "user-123"

    def test_expired_token_raises(self):
        """An expired token should raise HTTPException 401."""
        token = create_access_token(
            data={"sub": "test"},
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    def test_invalid_token_raises(self):
        """A malformed token string should raise HTTPException 401."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not-a-valid-jwt-token")
        assert exc_info.value.status_code == 401

    def test_token_without_sub_raises(self):
        """A token missing the 'sub' claim should raise HTTPException 401."""
        from jose import jwt as jose_jwt

        token = jose_jwt.encode(
            {"role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    def test_token_with_wrong_secret_raises(self):
        """A token signed with a different secret should fail verification."""
        from jose import jwt as jose_jwt

        token = jose_jwt.encode(
            {"sub": "test", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret-key",
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401


# =============================================================================
# Auth middleware
# =============================================================================

class TestAuthMiddleware:
    """Tests for authentication middleware rejecting invalid credentials."""

    async def test_missing_bearer_header_returns_401(self, test_client):
        """Requests without Authorization header should get 401."""
        response = await test_client.get("/api/v1/documents")
        assert response.status_code == 401

    async def test_empty_bearer_token_returns_401(self, test_client):
        """An empty Bearer token should be rejected."""
        response = await test_client.get(
            "/api/v1/documents",
            headers={"Authorization": "Bearer "},
        )
        # FastAPI's HTTPBearer may return 401 or 403 for empty tokens
        assert response.status_code in (401, 403)

    async def test_malformed_auth_header_returns_401(self, test_client):
        """A malformed Authorization header should be rejected."""
        response = await test_client.get(
            "/api/v1/documents",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert response.status_code in (401, 403)
