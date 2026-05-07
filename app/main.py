from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.robot_service import RobotService, RobotServiceError, create_service_from_env


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"


class JointCommand(BaseModel):
    joint: str = Field(min_length=1)
    value: float
    duration: float = 1.0


class JointsCommand(BaseModel):
    targets: dict[str, float]


class TorqueCommand(BaseModel):
    enabled: bool


class GripperCommand(BaseModel):
    arm: str
    action: str


def create_app(service: RobotService | None = None) -> FastAPI:
    app = FastAPI(
        title="Supre Robot Play",
        description="Web diagnostics and control API for Supre robots.",
        version="0.1.0",
    )
    app.state.robot_service = service or create_service_from_env()

    def robot() -> RobotService:
        return app.state.robot_service

    @app.exception_handler(RobotServiceError)
    async def robot_service_exception_handler(_request, exc: RobotServiceError):
        return JSONResponse(status_code=exc.status, content={"error": str(exc)})

    @app.get("/api/health")
    def health() -> dict[str, object]:
        return {"ok": True, **robot().status()}

    @app.get("/api/diagnostics")
    def diagnostics() -> dict[str, object]:
        return robot().diagnostics()

    @app.post("/api/connect")
    def connect() -> dict[str, object]:
        return robot().connect()

    @app.post("/api/disconnect")
    def disconnect() -> dict[str, object]:
        return robot().disconnect()

    @app.post("/api/joint")
    def set_joint(command: JointCommand) -> dict[str, object]:
        return robot().set_joint(command.joint, command.value, command.duration)

    @app.post("/api/joints")
    def set_joints(command: JointsCommand) -> dict[str, object]:
        return robot().set_joints(command.targets)

    @app.post("/api/torque")
    def set_torque(command: TorqueCommand) -> dict[str, object]:
        return robot().set_torque(command.enabled)

    @app.post("/api/gripper")
    def gripper(command: GripperCommand) -> dict[str, object]:
        return robot().gripper(command.arm, command.action)

    @app.get("/api/config")
    def config() -> dict[str, object]:
        status = robot().status()
        return {
            "mode": status["mode"],
            "joint_order": status["joint_order"],
            "joint_count": status["joint_count"],
        }

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Supre robot web diagnostics and control service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

