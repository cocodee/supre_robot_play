# Supre Robot Play

FastAPI web diagnostics and control console for Supre dual-arm robots.

## Run in simulation mode

```bash
cd ../supre_robot_play
conda activate supre-robot-play
python -m app.main --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080`.

## Run with real SDK hardware

```bash
cd ../supre_robot_play
conda activate supre-robot-play
SUPRE_ROBOT_MODE=sdk \
SUPRE_ROBOT_SDK_PATH=../supre_robot_sdk \
SUPRE_ROBOT_CONFIG=../supre_robot_sdk/examples/robot_config.yaml \
python -m app.main --host 0.0.0.0 --port 8080
```

The service exposes interactive API docs at `/docs`.

## Test

```bash
cd ../supre_robot_play
conda activate supre-robot-play
python -m unittest discover -s tests
```

The test suite uses the simulated backend and does not require robot hardware.

## Conda environment

The dedicated environment used for this project is:

```bash
conda activate supre-robot-play
```

To recreate it:

```bash
conda env create -f environment.yml
conda activate supre-robot-play
python -m pip install -e . -e ../supre_robot_sdk
```
