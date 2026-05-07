#!/bin/bash
set -e

cd "$(dirname "$0")"

export SUPRE_ROBOT_MODE=sim

python -m app.main --host 127.0.0.1 --port 8080
