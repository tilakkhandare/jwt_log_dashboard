import unittest
import os
import shutil
from app import app, LOG_DIR


class LogDashboardTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_full_workflow_and_rotation(self):
        # 1. Verify /logs is protected without JWT
        unauth_res = self.client.get("/logs")
        self.assertEqual(unauth_res.status_code, 401)

        # 2. Login to get JWT
        login_res = self.client.post(
            "/login", json={"username": "admin", "password": "admin123"}
        )
        self.assertEqual(login_res.status_code, 200)
        token = login_res.get_json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Generate enough activity to trigger RotatingFileHandler (10KB threshold)
        for _ in range(3):
            act_res = self.client.post(
                "/activity",
                json={"count": 100, "message": "Testing size-based log rotation entry payload"},
                headers=headers,
            )
            self.assertEqual(act_res.status_code, 201)

        # Verify rotated backup log files were created
        log_files = os.listdir(LOG_DIR)
        self.assertTrue(any(f.startswith("app.log.") for f in log_files), f"Expected rotated logs, got: {log_files}")

        # 4. Fetch last 10 lines via /logs endpoint
        logs_res = self.client.get("/logs?lines=10", headers=headers)
        self.assertEqual(logs_res.status_code, 200)
        data = logs_res.get_json()
        self.assertEqual(data["returned_lines"], 10)
        print("\nSample /logs response (last 3 entries):")
        for entry in data["logs"][-3:]:
            print(" ", entry)


if __name__ == "__main__":
    unittest.main()
