import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app, SESSIONS

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        SESSIONS.clear()

    def test_chat_completions_missing_messages(self):
        response = self.client.post("/v1/chat/completions", json={"model": "test"})
        self.assertEqual(response.status_code, 400)

    def test_chat_completions_missing_user_message(self):
        response = self.client.post("/v1/chat/completions", json={"messages": [{"role": "system", "content": "hello"}]})
        self.assertEqual(response.status_code, 400)

    @patch('app.google_client')
    def test_chat_completions_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.name = "mock_interaction_123"
        mock_response.text = "Hello from mock antigravity"

        mock_client.interactions.create.return_value = mock_response

        req_data = {
            "model": "antigravity-preview-latest",
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }

        response = self.client.post("/v1/chat/completions", json=req_data)

        self.assertEqual(response.status_code, 200)
        resp_json = response.json()

        self.assertIn("choices", resp_json)
        self.assertEqual(len(resp_json["choices"]), 1)
        self.assertEqual(resp_json["choices"][0]["message"]["content"], "Hello from mock antigravity")

        self.assertIn("X-Session-Id", response.headers)
        session_id = response.headers["X-Session-Id"]

        self.assertIn(session_id, SESSIONS)
        self.assertEqual(SESSIONS[session_id], "mock_interaction_123")

        mock_client.interactions.create.assert_called_once()
        args, kwargs = mock_client.interactions.create.call_args
        self.assertEqual(kwargs['agent'], 'antigravity-preview-latest')
        self.assertEqual(kwargs['environment'], {'type': 'remote'})
        self.assertEqual(kwargs['contents'], ['Hello'])
        self.assertNotIn('name', kwargs)

    @patch('app.google_client')
    def test_chat_completions_continue_session(self, mock_client):
        mock_response = MagicMock()
        mock_response.name = "existing_interaction_abc"
        mock_response.text = "Second reply"
        mock_client.interactions.create.return_value = mock_response

        SESSIONS["existing_session_xyz"] = "existing_interaction_abc"

        req_data = {
            "model": "antigravity-preview-latest",
            "messages": [
                {"role": "user", "content": "How are you?"}
            ]
        }

        response = self.client.post("/v1/chat/completions", json=req_data, headers={"X-Session-Id": "existing_session_xyz"})

        self.assertEqual(response.status_code, 200)

        mock_client.interactions.create.assert_called_once()
        args, kwargs = mock_client.interactions.create.call_args
        self.assertEqual(kwargs['agent'], 'antigravity-preview-latest')
        self.assertEqual(kwargs['environment'], {'type': 'remote'})
        self.assertEqual(kwargs['contents'], ['How are you?'])
        self.assertEqual(kwargs['name'], 'existing_interaction_abc')

    def test_static_files(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Antigravity Chat", response.text)

if __name__ == '__main__':
    unittest.main()
