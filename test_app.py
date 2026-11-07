import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app
import os
import uuid

# Mock the interactions client so we don't actually hit the Google API during testing
class MockEvent:
    def __init__(self, text):
        self.text = text

class MockResponse:
    def __init__(self, text):
        self.text = text
    def __iter__(self):
        yield MockEvent(self.text)

class MockInteraction:
    def send(self, message):
        return MockResponse("mocked reply")

class MockClientInteractions:
    def create(self, agent, environment):
        return MockInteraction()

class MockClient:
    def __init__(self, http_options=None):
        self.interactions = MockClientInteractions()

@patch('app.client', MockClient())
class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Google InteractionsAPI to ACP", response.content)

    def test_chat_new_interaction(self):
        response = self.client.post("/chat", json={"message": "hello"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("interaction_id", data)
        self.assertEqual(data["reply"], "mocked reply")

    def test_chat_existing_interaction(self):
        test_id = str(uuid.uuid4())
        import app as backend_app
        backend_app.interactions[test_id] = MockInteraction()

        response = self.client.post("/chat", json={"message": "hello again", "interaction_id": test_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["interaction_id"], test_id)
        self.assertEqual(data["reply"], "mocked reply")

if __name__ == "__main__":
    unittest.main()
