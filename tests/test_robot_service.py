import unittest

from app.robot_service import RobotService, RobotServiceError, SimulatedRobot


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


if __name__ == "__main__":
    unittest.main()

