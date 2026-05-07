#!/bin/bash
set -e

cd "$(dirname "$0")"

export SUPRE_ROBOT_MODE=sdk
export SUPRE_ROBOT_CONFIG=../supre_robot_sdk/examples/robot_config_repeat.yaml
export SUPRE_ROBOT_SDK_PATH=../supre_robot_sdk

python -m app.main --host 127.0.0.1 --port 8090
