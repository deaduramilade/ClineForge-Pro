"""
Tests for services/crypto_utils.py.

Encrypts test payloads using the same primitives lib/crypto.ts uses
(AES-256-GCM, PBKDF2-HMAC-SHA256, salt||iv||ciphertext layout) to confirm
the server-side decrypt function is format-compatible with what the
browser's WebCrypto API actually produces.
"""

import os

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.backend.services.crypto_utils import (
    IV_LENGTH_BYTES,
    SALT_LENGTH_BYTES,
    DecryptionError,
    _derive_key,
    decrypt_payload,
)


def _encrypt(plaintext: bytes, passphrase: str) -> bytes:
    salt = os.urandom(SALT_LENGTH_BYTES)
    iv = os.urandom(IV_LENGTH_BYTES)
    key = _derive_key(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(iv, plaintext, None)
    return salt + iv + ciphertext


def test_decrypt_round_trips_with_correct_passphrase():
    plaintext = b"INT. BAKERY - DAWN\nMira kneads dough alone, exhausted."
    payload = _encrypt(plaintext, "correct horse battery staple")

    assert decrypt_payload(payload, "correct horse battery staple") == plaintext


def test_decrypt_rejects_wrong_passphrase():
    payload = _encrypt(b"secret script contents", "right-passphrase")

    with pytest.raises(DecryptionError):
        decrypt_payload(payload, "wrong-passphrase")


def test_decrypt_rejects_tampered_ciphertext():
    payload = bytearray(_encrypt(b"secret script contents", "a-passphrase"))
    payload[-1] ^= 0xFF

    with pytest.raises(DecryptionError):
        decrypt_payload(bytes(payload), "a-passphrase")


def test_decrypt_rejects_too_short_payload():
    with pytest.raises(DecryptionError, match="too short"):
        decrypt_payload(b"short", "any-passphrase")


def test_decrypt_handles_empty_plaintext():
    payload = _encrypt(b"", "passphrase")

    assert decrypt_payload(payload, "passphrase") == b""


def test_decrypt_handles_unicode_content():
    plaintext = "مشهد داخلي - المخبز - الفجر".encode("utf-8")
    payload = _encrypt(plaintext, "passphrase")

    assert decrypt_payload(payload, "passphrase") == plaintext


def test_different_salts_produce_different_ciphertext_for_same_plaintext():
    a = _encrypt(b"same plaintext", "same-passphrase")
    b = _encrypt(b"same plaintext", "same-passphrase")

    assert a != b
