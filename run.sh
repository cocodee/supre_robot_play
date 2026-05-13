#!/bin/bash
set -e

cd "$(dirname "$0")"

export SUPRE_ROBOT_MODE=sdk
export SUPRE_ROBOT_CONFIG=../supre_robot_sdk/examples/robot_config_repeat.yaml
export SUPRE_ROBOT_SDK_PATH=../supre_robot_sdk

EU_MOTOR_ROOT="${EU_MOTOR_ROOT:-$HOME/workspace/eu_motor}"
if [ -d "$EU_MOTOR_ROOT/build/lib" ]; then
  export PYTHONPATH="$EU_MOTOR_ROOT/build/lib${PYTHONPATH:+:$PYTHONPATH}"
  export LD_LIBRARY_PATH="$EU_MOTOR_ROOT/build/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if [ -d "$EU_MOTOR_ROOT/lib" ]; then
  export LD_LIBRARY_PATH="$EU_MOTOR_ROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

JODELL_GRIPPER_PYTHONPATH="${JODELL_GRIPPER_PYTHONPATH:-$HOME/workspace/misumi_grippper/src/build}"
if [ -d "$JODELL_GRIPPER_PYTHONPATH" ]; then
  export PYTHONPATH="$JODELL_GRIPPER_PYTHONPATH${PYTHONPATH:+:$PYTHONPATH}"
fi

python -m app.main --host 127.0.0.1 --port 8090
