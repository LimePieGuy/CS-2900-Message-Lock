"""Integration tests for authenticated, database-backed messaging routes."""

import atexit
import os
import tempfile
import unittest

# auth.py validates this during import. This test-only value is never used by the application outside this test process.
os.environ["MESSAGELOCK_SECRET_KEY"] = (
    "test-only-secret-key-that-is-long-enough-for-the-app"
)

# Set the database override before importing the app/database modules so all
# API requests use this temporary file instead of the real messagelock.db.
TEST_DATABASE_DIRECTORY = tempfile.TemporaryDirectory()
atexit.register(TEST_DATABASE_DIRECTORY.cleanup)
os.environ["MESSAGELOCK_DATABASE_PATH"] = os.path.join(
    TEST_DATABASE_DIRECTORY.name, "test_messagelock.db"
)

from fastapi.testclient import TestClient

from database import Base, engine
from main import app
import models


class MessagingApiTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

        self.alice_id = self.register_user("alice")
        self.bob_id = self.register_user("bob")
        self.alice_token = self.login("alice")
        self.bob_token = self.login("bob")

    def tearDown(self):
        self.client.close()
        engine.dispose()

    def register_user(self, username):
        response = self.client.post(
            "/auth/register",
            json={"username": username, "password": "test-password-123"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def login(self, username):
        response = self.client.post(
            "/auth/login",
            json={"username": username, "password": "test-password-123"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    @staticmethod
    def auth_header(token):
        return {"Authorization": f"Bearer {token}"}

    def test_users_can_send_and_retrieve_messages(self):
        send_response = self.client.post(
            "/messages/",
            json={"recipient_id": self.bob_id, "content": "Hello, Bob!"},
            headers=self.auth_header(self.alice_token),
        )

        self.assertEqual(send_response.status_code, 201, send_response.text)
        sent_message = send_response.json()
        self.assertEqual(sent_message["sender_id"], self.alice_id)
        self.assertEqual(sent_message["recipient_id"], self.bob_id)
        self.assertEqual(sent_message["content"], "Hello, Bob!")

        alice_messages = self.client.get(
            "/messages/", headers=self.auth_header(self.alice_token)
        )
        bob_messages = self.client.get(
            "/messages/", headers=self.auth_header(self.bob_token)
        )
        self.assertEqual(alice_messages.status_code, 200)
        self.assertEqual(bob_messages.status_code, 200)
        self.assertEqual(
            [message["id"] for message in alice_messages.json()],
            [sent_message["id"]],
        )
        self.assertEqual(
            [message["id"] for message in bob_messages.json()],
            [sent_message["id"]],
        )

        received_message = self.client.get(
            f"/messages/{sent_message['id']}",
            headers=self.auth_header(self.bob_token),
        )
        self.assertEqual(received_message.status_code, 200)
        self.assertEqual(received_message.json()["content"], "Hello, Bob!")

    def test_messages_require_authentication_and_are_private(self):
        unauthenticated = self.client.get("/messages/")
        self.assertEqual(unauthenticated.status_code, 401)

        send_response = self.client.post(
            "/messages/",
            json={"recipient_id": self.bob_id, "content": "Private"},
            headers=self.auth_header(self.alice_token),
        )
        self.assertEqual(send_response.status_code, 201, send_response.text)
        message_id = send_response.json()["id"]

        self.register_user("charlie")
        charlie_token = self.login("charlie")
        hidden_message = self.client.get(
            f"/messages/{message_id}",
            headers=self.auth_header(charlie_token),
        )
        self.assertEqual(hidden_message.status_code, 404)

        charlie_messages = self.client.get(
            "/messages/", headers=self.auth_header(charlie_token)
        )
        self.assertEqual(charlie_messages.status_code, 200)
        self.assertEqual(charlie_messages.json(), [])

    def test_unknown_recipient_is_rejected(self):
        response = self.client.post(
            "/messages/",
            json={"recipient_id": 999999, "content": "Hello"},
            headers=self.auth_header(self.alice_token),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Recipient not found")

    def test_message_survives_database_reconnect(self):
        send_response = self.client.post(
            "/messages/",
            json={"recipient_id": self.bob_id, "content": "Still here"},
            headers=self.auth_header(self.alice_token),
        )
        self.assertEqual(send_response.status_code, 201, send_response.text)
        message_id = send_response.json()["id"]
        
        self.client.close()
        engine.dispose()
        self.client = TestClient(app)

        response = self.client.get(
            f"/messages/{message_id}",
            headers=self.auth_header(self.alice_token),
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["content"], "Still here")


if __name__ == "__main__":
    unittest.main()