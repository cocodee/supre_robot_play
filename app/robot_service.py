from __future__ import annotations

import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


DEFAULT_JOINT_ORDER = [
    "left_arm_joint_1",
    "left_arm_joint_2",
    "left_arm_joint_3",
    "left_arm_joint_4",
    "left_arm_joint_5",
    "left_arm_joint_6",
    "left_arm_joint_7",
    "right_arm_joint_1",
    "right_arm_joint_2",
    "right_arm_joint_3",
    "right_arm_joint_4",
    "right_arm_joint_5",
    "right_arm_joint_6",
    "right_arm_joint_7",
]

ARM_LIMITS_DEG = (-180.0, 180.0)
GRIPPER_LIMITS = (0.0, 1.0)


class RobotBackend(Protocol):
    @property
    def is_connected(self) -> bool:
        ...

    @property
    def joint_order(self) -> list[str]:
        ...

    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def get_joint_positions(self) -> dict[str, float]:
        ...

    def get_joint_forces(self) -> dict[str, float]:
        ...

    def move_joint(self, joint_name: str, target: float) -> None:
        ...

    def move_joints(self, targets: dict[str, float]) -> None:
        ...

    def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
        ...

    def set_enable_torque(self, enable: bool) -> None:
        ...

    def open_gripper(self, arm: str) -> None:
        ...

    def close_gripper(self, arm: str) -> None:
        ...


@dataclass
class SimulatedRobot:
    """In-memory backend used for tests and UI development without hardware."""

    _joint_order: list[str] = field(default_factory=lambda: list(DEFAULT_JOINT_ORDER))
    _connected: bool = False
    _torque_enabled: bool = True
    _positions: dict[str, float] = field(default_factory=dict)
    _forces: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._positions = {name: 0.0 for name in self._joint_order}
        self._forces = {name: 0.0 for name in self._joint_order}
        for name in ("left_arm_joint_7", "right_arm_joint_7"):
            self._positions[name] = 0.5

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def joint_order(self) -> list[str]:
        return list(self._joint_order)

    @property
    def torque_enabled(self) -> bool:
        return self._torque_enabled

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def get_joint_positions(self) -> dict[str, float]:
        self._require_connected()
        return dict(self._positions)

    def get_joint_forces(self) -> dict[str, float]:
        self._require_connected()
        return dict(self._forces)

    def move_joint(self, joint_name: str, target: float) -> None:
        self.move_joints({joint_name: target})

    def move_joints(self, targets: dict[str, float]) -> None:
        self._require_connected()
        for joint_name, target in targets.items():
            if joint_name not in self._positions:
                raise KeyError(joint_name)
            self._positions[joint_name] = clamp_joint_value(joint_name, target)
            self._forces[joint_name] = min(abs(float(target)) / 180.0, 1.0)

    def set_enable_torque(self, enable: bool) -> None:
        self._require_connected()
        self._torque_enabled = bool(enable)

    def open_gripper(self, arm: str) -> None:
        self.move_joint(gripper_joint_name(arm), 1.0)

    def close_gripper(self, arm: str) -> None:
        self.move_joint(gripper_joint_name(arm), 0.0)

    def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
        self._require_connected()
        clamped = clamp_joint_value(joint_name, target)
        if clamped == self._positions.get(joint_name):
            return
        start = self._positions[joint_name]
        steps = max(3, int(30 * duration))  # fixed 30Hz
        for i in range(1, steps + 1):
            alpha = i / steps
            self._positions[joint_name] = start + alpha * (clamped - start)
            self._forces[joint_name] = min(abs(self._positions[joint_name]) / 180.0, 1.0)
            time.sleep(duration / steps)
        self._positions[joint_name] = clamped

    def _require_connected(self) -> None:
        if not self._connected:
            raise RobotServiceError("Robot is not connected.", status=409)


class SdkRobotBackend:
    def __init__(self, config_path: str, sdk_path: str | None, use_interpolation: bool, control_frequency: float):
        if sdk_path:
            src_path = str(Path(sdk_path).resolve() / "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
        from supre_robot_sdk import SupreRobot

        self._robot = SupreRobot(
            config_path,
            use_interpolation=use_interpolation,
            control_frequency=control_frequency,
        )
        self._torque_enabled = True

    @property
    def is_connected(self) -> bool:
        return bool(self._robot.is_connected)

    @property
    def joint_order(self) -> list[str]:
        return self._robot.joint_order if self.is_connected else list(DEFAULT_JOINT_ORDER)

    @property
    def torque_enabled(self) -> bool:
        return self._torque_enabled

    def connect(self) -> None:
        self._robot.connect()

    def disconnect(self) -> None:
        self._robot.disconnect()

    def get_joint_positions(self) -> dict[str, float]:
        return self._robot.get_joint_positions()

    def get_joint_forces(self) -> dict[str, float]:
        return self._robot.get_joint_forces()

    def move_joint(self, joint_name: str, target: float) -> None:
        self._robot.move_joint(joint_name, clamp_joint_value(joint_name, target))

    def move_joints(self, targets: dict[str, float]) -> None:
        self._robot.move_joints({name: clamp_joint_value(name, value) for name, value in targets.items()})

    def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
        clamped = clamp_joint_value(joint_name, target)
        self._robot.execute_trajectory({joint_name: clamped}, duration=duration)

    def set_enable_torque(self, enable: bool) -> None:
        self._robot.set_enable_torque(enable)
        self._torque_enabled = bool(enable)

    def open_gripper(self, arm: str) -> None:
        self._robot.open_gripper(arm)

    def close_gripper(self, arm: str) -> None:
        self._robot.close_gripper(arm)


class RobotServiceError(Exception):
    def __init__(self, message: str, *, status: int = 400):
        super().__init__(message)
        self.status = status


class RobotService:
    def __init__(self, backend: RobotBackend):
        self._backend = backend
        self._lock = threading.RLock()
        self._started_at = time.time()
        self._last_error: str | None = None

    def status(self) -> dict[str, object]:
        with self._lock:
            return {
                "mode": backend_mode(self._backend),
                "connected": self._backend.is_connected,
                "joint_count": len(self._backend.joint_order),
                "joint_order": self._backend.joint_order,
                "torque_enabled": bool(getattr(self._backend, "torque_enabled", True)),
                "uptime_seconds": round(time.time() - self._started_at, 3),
                "last_error": self._last_error,
            }

    def connect(self) -> dict[str, object]:
        return self._call(lambda: self._backend.connect())

    def disconnect(self) -> dict[str, object]:
        return self._call(lambda: self._backend.disconnect())

    def diagnostics(self) -> dict[str, object]:
        with self._lock:
            base = self.status()
            if not self._backend.is_connected:
                base["positions"] = {}
                base["forces"] = {}
                return base
            base["positions"] = self._backend.get_joint_positions()
            base["forces"] = self._backend.get_joint_forces()
            return base

    def set_joint(self, joint: str, value: float, duration: float = 1.0) -> dict[str, object]:
        if duration <= 0:
            return self._call(lambda: self._backend.move_joint(joint, value))
        return self._call(lambda: self._backend.execute_joint_trajectory(joint, value, duration))

    def set_joints(self, targets: dict[str, float]) -> dict[str, object]:
        return self._call(lambda: self._backend.move_joints(targets))

    def set_torque(self, enabled: bool) -> dict[str, object]:
        return self._call(lambda: self._backend.set_enable_torque(enabled))

    def gripper(self, arm: str, action: str) -> dict[str, object]:
        normalized = action.lower()
        if normalized == "open":
            return self._call(lambda: self._backend.open_gripper(arm))
        if normalized == "close":
            return self._call(lambda: self._backend.close_gripper(arm))
        raise RobotServiceError("action must be 'open' or 'close'")

    def _call(self, operation) -> dict[str, object]:
        with self._lock:
            try:
                operation()
                self._last_error = None
                return self.diagnostics()
            except RobotServiceError:
                raise
            except KeyError as exc:
                self._last_error = str(exc)
                raise RobotServiceError(f"Unknown joint: {exc}", status=404) from exc
            except Exception as exc:
                self._last_error = str(exc)
                raise RobotServiceError(str(exc), status=500) from exc


def clamp_joint_value(joint_name: str, value: float) -> float:
    numeric = float(value)
    low, high = GRIPPER_LIMITS if joint_name.endswith("_joint_7") else ARM_LIMITS_DEG
    return min(max(numeric, low), high)


def gripper_joint_name(arm: str) -> str:
    arm_name = arm.lower()
    if arm_name not in {"left", "right"}:
        raise RobotServiceError("arm must be 'left' or 'right'")
    return f"{arm_name}_arm_joint_7"


def backend_mode(backend: RobotBackend) -> str:
    return "sim" if isinstance(backend, SimulatedRobot) else "sdk"


def create_service_from_env() -> RobotService:
    mode = os.getenv("SUPRE_ROBOT_MODE", "sim").lower()
    if mode == "sdk":
        config_path = os.getenv("SUPRE_ROBOT_CONFIG", "../supre_robot_sdk/examples/robot_config.yaml")
        sdk_path = os.getenv("SUPRE_ROBOT_SDK_PATH", "../supre_robot_sdk")
        use_interpolation = os.getenv("SUPRE_ROBOT_INTERPOLATION", "1") not in {"0", "false", "False"}
        frequency = float(os.getenv("SUPRE_ROBOT_FREQUENCY", "30"))
        return RobotService(SdkRobotBackend(config_path, sdk_path, use_interpolation, frequency))
    if mode == "sim":
        return RobotService(SimulatedRobot())
    raise RobotServiceError("SUPRE_ROBOT_MODE must be 'sim' or 'sdk'")
