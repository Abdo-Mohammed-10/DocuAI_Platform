from services.api_gateway.middleware.auth import (
    create_token,
    create_token_pair,
    hash_password,
    verify_password,
)


def test_hash_and_verify():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_is_not_plaintext():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert len(hashed) > 20


def test_create_token_returns_string():
    token = create_token("user-123", expire_minutes=60)
    assert isinstance(token, str)
    assert len(token) > 10


def test_create_token_pair():
    pair = create_token_pair("user-123")
    assert pair.access_token
    assert pair.refresh_token
    assert pair.access_token != pair.refresh_token
    assert pair.token_type == "bearer"
