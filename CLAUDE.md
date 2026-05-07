# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI web diagnostics and control console for Supre dual-arm robots. The service exposes a REST API and a web UI for controlling robot joints, grippers, and torque.

## Commands

```bash
# Run in simulation mode (default)
python -m app.main --host 127.0.0.1 --port 8080

# Run with real SDK hardware
SUPRE_ROBOT_MODE=sdk \
SUPRE_ROBOT_SDK_PATH=../supre_robot_sdk \
SUPRE_ROBOT_CONFIG=../supre_robot_sdk/examples/robot_config.yaml \
python -m app.main --host 0.0.0.0 --port 8080

# Run tests (uses simulated backend, no hardware required)
python -m unittest discover -s tests
```

## Architecture

The system uses a **Protocol-based backend strategy** to support two operating modes:

```
RobotService (orchestration layer)
    └── RobotBackend (Protocol)
            ├── SimulatedRobot  (in-memory, for dev/tests)
            └── SdkRobotBackend (wraps supre_robot_sdk for real hardware)
```

**Key modules:**
- `app/robot_service.py` — Core business logic. Defines `RobotBackend` Protocol, `SimulatedRobot`, `SdkRobotBackend`, `RobotService`, and `RobotServiceError`. The `create_service_from_env()` factory instantiates the appropriate backend based on `SUPRE_ROBOT_MODE`.
- `app/main.py` — FastAPI app factory (`create_app()`), request models, and route handlers. Mounts a static web UI at `/`.

**Robot joint model:** 14 joints total — 7 per arm (`left_arm_joint_1` through `left_arm_joint_7` and `right_arm_joint_*`). Joint 7 is the gripper with value range `[0.0, 1.0]`; all other joints clamp to `[-180.0, 180.0]` degrees.

**Thread safety:** `RobotService` uses an `RLock` to serialize all backend operations.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPRE_ROBOT_MODE` | `sim` | `sim` or `sdk` |
| `SUPRE_ROBOT_SDK_PATH` | `../supre_robot_sdk` | Path to SDK source |
| `SUPRE_ROBOT_CONFIG` | `../supre_robot_sdk/examples/robot_config.yaml` | Robot config file |
| `SUPRE_ROBOT_INTERPOLATION` | `1` | Enable interpolation |
| `SUPRE_ROBOT_FREQUENCY` | `30` | Control frequency (Hz) |

## Design
**Always follow DESIGN.md for any UI generation.**
**Never invent visual styles.**
