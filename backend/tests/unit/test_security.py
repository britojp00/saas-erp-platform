from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    password = "mypassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_different_hashes_for_same_password():
    password = "mypassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_wrong_password_fails():
    hashed = get_password_hash("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_create_and_decode():
    data = {"sub": "user-id-123", "tenant_id": "tenant-id-456"}
    token = create_access_token(data)

    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-id-123"
    assert decoded["tenant_id"] == "tenant-id-456"
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_with_custom_expiration():
    data = {"sub": "user-id-123", "tenant_id": "tenant-id-456"}
    expires_delta = timedelta(hours=1)
    token = create_access_token(data, expires_delta=expires_delta)

    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-id-123"


def test_jwt_invalid_signature():
    data = {"sub": "user-id-123", "tenant_id": "tenant-id-456"}
    fake_token = jwt.encode(
        data,
        "wrong-secret-key",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(fake_token)


def test_jwt_with_wrong_algorithm():
    data = {"sub": "user-id-123", "tenant_id": "tenant-id-456"}
    fake_token = jwt.encode(
        data,
        settings.jwt_secret_key,
        algorithm="HS512",
    )
    with pytest.raises(jwt.InvalidAlgorithmError):
        decode_access_token(fake_token)
