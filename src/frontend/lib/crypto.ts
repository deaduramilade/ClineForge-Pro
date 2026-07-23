/**
 * CineForge AI Pro — Client-side AES-256-GCM Encryption
 *
 * Owned by: Cybersecurity Specialist
 *
 * All script files MUST be encrypted using this module before
 * being transmitted to the backend API.
 *
 * Algorithm: AES-256-GCM (via WebCrypto API)
 * Key derivation: PBKDF2 with SHA-256, 100,000 iterations
 */

const PBKDF2_ITERATIONS = 100_000
const KEY_LENGTH_BITS = 256
const IV_LENGTH_BYTES = 12 // 96-bit IV for AES-GCM

/**
 * Derive an AES-256-GCM key from a passphrase using PBKDF2.
 *
 * @param passphrase - User-provided passphrase (never transmitted)
 * @param salt - Random salt (should be stored alongside the ciphertext)
 */
export async function deriveKey(
  passphrase: string,
  salt: Uint8Array,
): Promise<CryptoKey> {
  const encoder = new TextEncoder()
  const keyMaterial = await window.crypto.subtle.importKey(
    'raw',
    encoder.encode(passphrase),
    'PBKDF2',
    false,
    ['deriveKey'],
  )

  return window.crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt as BufferSource,
      iterations: PBKDF2_ITERATIONS,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: KEY_LENGTH_BITS },
    false,
    ['encrypt', 'decrypt'],
  )
}

/**
 * Encrypt a file's contents using AES-256-GCM.
 *
 * Returns the ciphertext with the salt and IV prepended:
 *   [ 16 bytes salt ][ 12 bytes IV ][ ciphertext... ]
 *
 * @param plaintext - Raw file bytes
 * @param passphrase - User passphrase for key derivation
 */
export async function encryptFile(
  plaintext: ArrayBuffer,
  passphrase: string,
): Promise<ArrayBuffer> {
  const salt = window.crypto.getRandomValues(new Uint8Array(16))
  const iv = window.crypto.getRandomValues(new Uint8Array(IV_LENGTH_BYTES))
  const key = await deriveKey(passphrase, salt)

  const ciphertext = await window.crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv as BufferSource },
    key,
    plaintext,
  )

  // Prepend salt + IV to ciphertext
  const result = new Uint8Array(salt.length + iv.length + ciphertext.byteLength)
  result.set(salt, 0)
  result.set(iv, salt.length)
  result.set(new Uint8Array(ciphertext), salt.length + iv.length)
  return result.buffer
}

/**
 * Decrypt a file encrypted with encryptFile().
 *
 * Expects the layout: [ 16 bytes salt ][ 12 bytes IV ][ ciphertext... ]
 *
 * @param encryptedData - Encrypted file bytes (salt + IV + ciphertext)
 * @param passphrase - User passphrase used during encryption
 */
export async function decryptFile(
  encryptedData: ArrayBuffer,
  passphrase: string,
): Promise<ArrayBuffer> {
  const data = new Uint8Array(encryptedData)
  const salt = data.slice(0, 16)
  const iv = data.slice(16, 16 + IV_LENGTH_BYTES)
  const ciphertext = data.slice(16 + IV_LENGTH_BYTES)

  const key = await deriveKey(passphrase, salt)

  return window.crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: iv as BufferSource },
    key,
    ciphertext,
  )
}
