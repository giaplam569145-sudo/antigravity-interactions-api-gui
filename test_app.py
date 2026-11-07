import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestAppEndpoints(unittest.TestCase):
    def test_health(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertTrue(data.get("has_api_key_configured"))

    def test_models(self):
        response = client.get("/api/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        model_ids = [m["id"] for m in data["models"]]
        self.assertIn("antigravity-preview-latest", model_ids)

    def test_code_snippet_generation(self):
        payload = {
            "agent": "antigravity-preview-latest",
            "input_text": "Erkläre Antigravity",
            "system_instruction": "Sei kurz.",
            "previous_interaction_id": "v1_test_prev_id",
            "environment_type": "remote",
            "stream": True
        }
        response = client.post("/api/code-snippet", json=payload)
        self.assertEqual(response.status_code, 200)
        snippets = response.json()
        self.assertIn("python", snippets)
        self.assertIn("curl", snippets)
        self.assertIn("javascript", snippets)

        # Verify content
        self.assertIn("agent='antigravity-preview-latest'", snippets["python"])
        self.assertIn("previous_interaction_id='v1_test_prev_id'", snippets["python"])
        self.assertIn("v1beta/interactions", snippets["curl"])
        self.assertIn("v1_test_prev_id", snippets["curl"])
        self.assertIn("v1_test_prev_id", snippets["javascript"])

    def test_static_index(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Google Antigravity GUI", response.text)

if __name__ == "__main__":
    unittest.main()
