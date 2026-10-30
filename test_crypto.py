"""Unit tests for AES-256-GCM message encryption."""

import base64
import os
import unittest

# Again like in test_messages.py, setting key here means tests never use the real key from .env
os.environ["MESSAGELOCK_ENCRYPTION_KEY"] = "0123456789abcdef" * 4

from crypto import decrypt_message, encrypt_message

NONCE_SIZE = 12
TAG_SIZE = 16


def flip_byte(encrypted_content, index):
    """Return the encrypted content with one byte changed."""
    packed = bytearray(base64.b64decode(encrypted_content))
    packed[index] ^= 0x01
    return base64.b64encode(bytes(packed)).decode("ascii")


class CryptoTests(unittest.TestCase):
    def test_round_trip(self):
        encrypted = encrypt_message("Hello, Bob!", 1, 2)
        self.assertEqual(decrypt_message(encrypted, 1, 2), "Hello, Bob!")

    def test_round_trip_unicode(self):
        text = "Héllo 👋 世界"
        encrypted = encrypt_message(text, 1, 2)
        self.assertEqual(decrypt_message(encrypted, 1, 2), text)

    def test_output_hides_plaintext(self):
        encrypted = encrypt_message("Top secret plans", 1, 2)
        packed = base64.b64decode(encrypted)

        self.assertNotIn(b"Top secret plans", packed)
        self.assertEqual(
            len(packed),
            NONCE_SIZE + len("Top secret plans") + TAG_SIZE,
        )

    def test_each_encryption_uses_new_nonce(self):
        first = base64.b64decode(encrypt_message("Same text", 1, 2))
        second = base64.b64decode(encrypt_message("Same text", 1, 2))

        self.assertNotEqual(first[:NONCE_SIZE], second[:NONCE_SIZE])
        self.assertNotEqual(first, second)

    def test_tampered_ciphertext_is_rejected(self):
        encrypted = encrypt_message("Original", 1, 2)

        with self.assertRaises(ValueError):
            decrypt_message(flip_byte(encrypted, NONCE_SIZE), 1, 2)

    def test_tampered_nonce_is_rejected(self):
        encrypted = encrypt_message("Original", 1, 2)

        with self.assertRaises(ValueError):
            decrypt_message(flip_byte(encrypted, 0), 1, 2)

    def test_tampered_tag_is_rejected(self):
        encrypted = encrypt_message("Original", 1, 2)

        with self.assertRaises(ValueError):
            decrypt_message(flip_byte(encrypted, -1), 1, 2)

    def test_wrong_sender_is_rejected(self):
        encrypted = encrypt_message("From user 1", 1, 2)

        with self.assertRaises(ValueError):
            decrypt_message(encrypted, 3, 2)

    def test_wrong_recipient_is_rejected(self):
        encrypted = encrypt_message("For user 2", 1, 2)

        with self.assertRaises(ValueError):
            decrypt_message(encrypted, 1, 3)

    def test_swapped_sender_and_recipient_is_rejected(self):
        encrypted = encrypt_message("From 1 to 2", 1, 2)

        with self.assertRaises(ValueError):
            decrypt_message(encrypted, 2, 1)

    def test_invalid_base64_is_rejected(self):
        with self.assertRaises(ValueError):
            decrypt_message("not base64!", 1, 2)

    def test_too_short_is_rejected(self):
        too_short = base64.b64encode(b"\x00" * 27).decode("ascii")

        with self.assertRaises(ValueError):
            decrypt_message(too_short, 1, 2)


if __name__ == "__main__":
    unittest.main()
