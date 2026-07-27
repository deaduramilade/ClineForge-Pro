"""
Tests for the encrypted-upload path added to POST /api/scripts/upload.

Encrypts a plaintext script the same way lib/crypto.ts's encryptFile()
does (salt||iv||AES-256-GCM ciphertext), uploads it with a `passphrase`
form field, and confirms the server decrypts and parses it identically
to an equivalent plaintext upload. Also confirms the original
plaintext-only behaviour (no passphrase field) is unchanged.
"""

import os

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.backend.services.script_store as script_store
from src.backend.routers.scripts import router as scripts_router
from src.backend.services.crypto_utils import IV_LENGTH_BYTES, SALT_LENGTH_BYTES, _derive_key

_app = FastAPI()
_app.include_router(scripts_router, prefix="/api/scripts")
_client = TestClient(_app, raise_server_exceptions=True)

_SCRIPT_TEXT = "INT. BAKERY - DAWN\nMira kneads dough alone, exhausted.\n"


@pytest.fixture(autouse=True)
def _clean_store():
    script_store.clear()
    yield
    script_store.clear()


def _encrypt(plaintext: bytes, passphrase: str) -> bytes:
    salt = os.urandom(SALT_LENGTH_BYTES)
    iv = os.urandom(IV_LENGTH_BYTES)
    key = _derive_key(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(iv, plaintext, None)
    return salt + iv + ciphertext


def test_encrypted_upload_is_decrypted_and_parsed():
    passphrase = "correct horse battery staple"
    encrypted = _encrypt(_SCRIPT_TEXT.encode("utf-8"), passphrase)

    # Filename must keep its original extension -- the parser dispatches
    # on it *after* decryption.
    resp = _client.post(
        "/api/scripts/upload",
        files={"file": ("script.txt", encrypted, "application/octet-stream")},
        data={"passphrase": passphrase},
    )

    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["scene_count"] == 1
    assert body["language"] == "en"


def test_encrypted_upload_with_wrong_passphrase_returns_400():
    encrypted = _encrypt(_SCRIPT_TEXT.encode("utf-8"), "right-passphrase")

    resp = _client.post(
        "/api/scripts/upload",
        files={"file": ("script.txt", encrypted, "application/octet-stream")},
        data={"passphrase": "wrong-passphrase"},
    )

    assert resp.status_code == 400


def test_plaintext_upload_without_passphrase_still_works():
    """Backward compatibility: omitting `passphrase` preserves original MVP behaviour."""
    resp = _client.post(
        "/api/scripts/upload",
        files={"file": ("script.txt", _SCRIPT_TEXT.encode("utf-8"), "text/plain")},
    )

    assert resp.status_code == 202, resp.text
    assert resp.json()["scene_count"] == 1


def test_same_plaintext_encrypted_twice_dedupes_to_same_script_id():
    """script_id is derived AFTER decryption, from plaintext content -- so
    two encrypted uploads of the same underlying script correctly dedupe
    to one script_id even though the ciphertext differs each time (random
    salt/iv per encryption)."""
    passphrase = "a-passphrase"
    encrypted_a = _encrypt(_SCRIPT_TEXT.encode("utf-8"), passphrase)
    encrypted_b = _encrypt(_SCRIPT_TEXT.encode("utf-8"), passphrase)
    assert encrypted_a != encrypted_b

    resp_a = _client.post(
        "/api/scripts/upload",
        files={"file": ("a.txt", encrypted_a, "application/octet-stream")},
        data={"passphrase": passphrase},
    )
    resp_b = _client.post(
        "/api/scripts/upload",
        files={"file": ("b.txt", encrypted_b, "application/octet-stream")},
        data={"passphrase": passphrase},
    )

    assert resp_a.json()["script_id"] == resp_b.json()["script_id"]
