import unittest

from app.robot_service import RobotService, RobotServiceError, SdkRobotBackend, SimulatedRobot


class FakeSdkRobotWithHardwareCheck:
    def __init__(self):
        self.is_connected = False
        self.connected_count = 0
        self.disconnected_count = 0
        self.checked_modes = []

    def connect(self):
        self.is_connected = True
        self.connected_count += 1

    def disconnect(self):
        self.is_connected = False
        self.disconnected_count += 1

    def hardware_check(self, mode):
        self.checked_modes.append(mode)
        return {
            "ok": True,
            "interfaces": [
                {
                    "name": "fake_sdk",
                    "ok": True,
                }
            ],
        }


class RobotServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = RobotService(SimulatedRobot())

    def test_initial_status_is_disconnected_sim(self):
        status = self.service.status()

        self.assertEqual(status["mode"], "sim")
        self.assertFalse(status["connected"])
        self.assertEqual(status["joint_count"], 14)

    def test_connect_and_control_joint(self):
        self.service.connect()
        data = self.service.set_joint("left_arm_joint_1", 45.5)

        self.assertTrue(data["connected"])
        self.assertEqual(data["positions"]["left_arm_joint_1"], 45.5)
        self.assertGreater(data["forces"]["left_arm_joint_1"], 0)

    def test_joint_values_are_clamped(self):
        self.service.connect()

        arm = self.service.set_joint("left_arm_joint_1", 999)
        gripper = self.service.set_joint("left_arm_joint_7", 9)

        self.assertEqual(arm["positions"]["left_arm_joint_1"], 180.0)
        self.assertEqual(gripper["positions"]["left_arm_joint_7"], 1.0)

    def test_gripper_actions(self):
        self.service.connect()

        closed = self.service.gripper("left", "close")
        opened = self.service.gripper("left", "open")

        self.assertEqual(closed["positions"]["left_arm_joint_7"], 0.0)
        self.assertEqual(opened["positions"]["left_arm_joint_7"], 1.0)

    def test_rejects_unknown_joint(self):
        self.service.connect()

        with self.assertRaises(RobotServiceError) as ctx:
            self.service.set_joint("bad_joint", 1)

        self.assertEqual(ctx.exception.status, 404)

    def test_simulated_robot_execute_joint_trajectory_sets_positions(self):
        service = RobotService(SimulatedRobot())
        service.connect()
        data = service.set_joint("left_arm_joint_1", 45.0, duration=0.1)
        self.assertAlmostEqual(data["positions"]["left_arm_joint_1"], 45.0, places=1)

    def test_set_joint_with_duration_calls_execute_trajectory(self):
        service = RobotService(SimulatedRobot())
        service.connect()
        data = service.set_joint("right_arm_joint_3", -30.0, duration=0.2)
        self.assertAlmostEqual(data["positions"]["right_arm_joint_3"], -30.0, places=1)

    def test_set_joint_zero_duration_is_instant(self):
        service = RobotService(SimulatedRobot())
        service.connect()
        data = service.set_joint("left_arm_joint_1", 90.0, duration=0)
        self.assertEqual(data["positions"]["left_arm_joint_1"], 90.0)

    def test_sdk_backend_prefers_sdk_hardware_check(self):
        backend = SdkRobotBackend.__new__(SdkRobotBackend)
        backend._robot = FakeSdkRobotWithHardwareCheck()
        backend._config_path = "/tmp/robot_config.yaml"

        data = backend.hardware_check("activate")

        self.assertEqual(backend._robot.connected_count, 1)
        self.assertEqual(backend._robot.disconnected_count, 1)
        self.assertEqual(backend._robot.checked_modes, ["activate"])
        self.assertTrue(data["ok"])
        self.assertEqual(data["mode"], "activate")
        self.assertEqual(data["backend"], "sdk")
        self.assertEqual(data["config_path"], "/tmp/robot_config.yaml")
        self.assertTrue(data["deactivated_after_check"])

    def test_sdk_backend_keeps_existing_connection_after_activate_check(self):
        backend = SdkRobotBackend.__new__(SdkRobotBackend)
        backend._robot = FakeSdkRobotWithHardwareCheck()
        backend._robot.is_connected = True
        backend._config_path = "/tmp/robot_config.yaml"

        data = backend.hardware_check("activate")

        self.assertEqual(backend._robot.connected_count, 0)
        self.assertEqual(backend._robot.disconnected_count, 0)
        self.assertTrue(backend._robot.is_connected)
        self.assertFalse(data["deactivated_after_check"])


if __name__ == "__main__":
    unittest.main()
