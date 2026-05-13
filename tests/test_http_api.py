import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.robot_service import RobotService, SimulatedRobot


class HttpApiTest(unittest.TestCase):
    def setUp(self):
        service = RobotService(SimulatedRobot())
        self.client = TestClient(create_app(service))

    def test_health(self):
        response = self.client.get("/api/health")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["mode"], "sim")

    def test_connect_and_joint_api(self):
        connect_response = self.client.post("/api/connect", json={})
        joint_response = self.client.post(
            "/api/joint",
            json={"joint": "right_arm_joint_2", "value": -12.5},
        )

        self.assertEqual(connect_response.status_code, 200)
        self.assertTrue(connect_response.json()["connected"])
        self.assertEqual(joint_response.status_code, 200)
        self.assertEqual(joint_response.json()["positions"]["right_arm_joint_2"], -12.5)

    def test_unknown_joint_returns_404(self):
        self.client.post("/api/connect", json={})
        response = self.client.post("/api/joint", json={"joint": "missing", "value": 1})

        self.assertEqual(response.status_code, 404)
        self.assertIn("Unknown joint", response.json()["error"])

    def test_hardware_check_api(self):
        response = self.client.get("/api/hardware-check?mode=passive")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["mode"], "passive")
        self.assertEqual(data["backend"], "sim")
        self.assertEqual(data["interfaces"][0]["name"], "simulated_robot")

    def test_hardware_check_rejects_invalid_mode(self):
        response = self.client.get("/api/hardware-check?mode=bad")

        self.assertEqual(response.status_code, 400)
        self.assertIn("mode must be", response.json()["error"])

    def test_runtime_api(self):
        response = self.client.get("/api/runtime")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("python", data)
        self.assertIn("pythonpath", data)
        self.assertIn("eu_motor_py", data)

    def test_index_page_is_served(self):
        response = self.client.get("/")
        body = response.text

        self.assertEqual(response.status_code, 200)
        self.assertIn("Supre Robot Play", body)
        self.assertIn("leftArmControls", body)
        self.assertIn("rightArmControls", body)
        self.assertIn("arm-card-left", body)
        self.assertIn("arm-card-right", body)
        self.assertIn("hardwareCheckBtn", body)
        self.assertIn('id="hardwareCheckBtn" type="button"', body)
        self.assertIn('onclick="runHardwareCheck()"', body)
        self.assertIn("/app.js?v=hardware-check-20260513", body)
        self.assertIn("hardwareCheckResults", body)

    def test_joint_api_with_duration(self):
        self.client.post("/api/connect", json={})
        response = self.client.post(
            "/api/joint",
            json={"joint": "left_arm_joint_2", "value": -15.0, "duration": 0.1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(response.json()["positions"]["left_arm_joint_2"], -15.0, places=1)

    def test_joint_api_duration_default(self):
        self.client.post("/api/connect", json={})
        response = self.client.post(
            "/api/joint",
            json={"joint": "right_arm_joint_1", "value": 10.0},
        )
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(response.json()["positions"]["right_arm_joint_1"], 10.0, places=1)


if __name__ == "__main__":
    unittest.main()
