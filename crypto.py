# MessageLock cryptographic functions
#
# Milestone 3
#
# Planned implementation:
# - AES-256-GCM encryption
# - AES-256-GCM decryption
# - Secure nonce generation
# - Encryption key handling

import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()

# Load the encryption key from .env.
key_text = os.environ.get("MESSAGELOCK_ENCRYPTION_KEY")

if not key_text:
    raise RuntimeError("Set MESSAGELOCK_ENCRYPTION_KEY in your .env file.")

try:
    key = bytes.fromhex(key_text)
except ValueError as exc:
    raise RuntimeError("Encryption key must be hexadecimal.") from exc

if len(key) != 32:
    raise RuntimeError("Encryption key must contain exactly 32 bytes.")

cipher = AESGCM(key)


def message_context(sender_id: int, recipient_id: int) -> bytes:
    """Bind the encrypted message to its sender and recipient."""
    return f"messagelock:v1:{sender_id}:{recipient_id}".encode("utf-8")


def encrypt_message(
    plaintext: str,
    sender_id: int,
    recipient_id: int
) -> str:
    """Encrypt a message using AES-256-GCM."""
    nonce = os.urandom(12)
    context = message_context(sender_id, recipient_id)

    ciphertext = cipher.encrypt(
        nonce,
        plaintext.encode("utf-8"),
        context
    )

    # Save the nonce, ciphertext, and authentication tag together.
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_message(
    encrypted_content: str,
    sender_id: int,
    recipient_id: int
) -> str:
    """Verify the message's integrity and decrypt its content."""
    try:
        packed = base64.b64decode(encrypted_content, validate=True)

        # Require a 12-byte nonce and a 16-byte authentication tag.
        if len(packed) < 28:
            raise ValueError("Invalid encrypted message.")

        nonce = packed[:12]
        ciphertext = packed[12:]
        context = message_context(sender_id, recipient_id)

        plaintext = cipher.decrypt(nonce, ciphertext, context)

        return plaintext.decode("utf-8")

    except (InvalidTag, ValueError, binascii.Error) as exc:
        raise ValueError(
            "Message could not be verified or decrypted."
        ) from exc