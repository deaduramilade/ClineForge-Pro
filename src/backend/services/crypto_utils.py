"""
Server-side AES-256-GCM decryption for encrypted script uploads.

Owned by: Cybersecurity Specialist

Mirrors ``src/frontend/lib/crypto.ts`` exactly so a file encrypted by the
browser's WebCrypto API can be decrypted here:

    [ 16 bytes salt ][ 12 bytes IV ][ ciphertext + 16-byte GCM tag ]

Key derivation: PBKDF2-HMAC-SHA256, 100,000 iterations, 256-bit key —
same parameters as the frontend's ``deriveKey()``.

Per SECURITY.md, this is **client-side encryption with local key
generation, not zero-knowledge**: the passphrase must be sent to the
server (over HTTPS, once, per request) so the server can decrypt the
script for parsing. It is never stored.
"""

from __future__ import annotations

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_LENGTH_BYTES = 16
IV_LENGTH_BYTES = 12
PBKDF2_ITERATIONS = 100_000
KEY_LENGTH_BYTES = 32  # 256 bits

_MIN_PAYLOAD_LENGTH = SALT_LENGTH_BYTES + IV_LENGTH_BYTES + 1


class DecryptionError(Exception):
    """Raised when an encrypted payload cannot be decrypted.

    Covers: malformed/too-short payload, wrong passphrase, and GCM
    authentication-tag failure (tampered or corrupted ciphertext). The
    message is intentionally generic — never reveals which of these
    occurred, to avoid leaking an oracle to a caller probing passphrases.
    """


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH_BYTES,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def decrypt_payload(encrypted: bytes, passphrase: str) -> bytes:
    """Decrypt a payload produced by the frontend's ``encryptFile()``.

    Args:
        encrypted: Raw bytes as uploaded — salt || iv || ciphertext+tag.
        passphrase: The same passphrase used to encrypt, as supplied by
            the client for this request only (never persisted).

    Returns:
        The original plaintext bytes.

    Raises:
        DecryptionError: if the payload is malformed, the passphrase is
            wrong, or the ciphertext fails GCM authentication.
    """
    if len(encrypted) < _MIN_PAYLOAD_LENGTH:
        raise DecryptionError(
            "Encrypted payload is too short to contain a valid "
            "salt + IV + ciphertext."
        )

    salt = encrypted[:SALT_LENGTH_BYTES]
    iv = encrypted[SALT_LENGTH_BYTES : SALT_LENGTH_BYTES + IV_LENGTH_BYTES]
    ciphertext = encrypted[SALT_LENGTH_BYTES + IV_LENGTH_BYTES :]

    key = _derive_key(passphrase, salt)

    try:
        return AESGCM(key).decrypt(iv, ciphertext, associated_data=None)
    except InvalidTag as exc:
        raise DecryptionError(
            "Failed to decrypt: wrong passphrase or corrupted data."
        ) from exc
