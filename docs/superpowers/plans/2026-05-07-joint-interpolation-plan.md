# Joint Interpolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add smooth joint interpolation so robot arms move gradually to target positions over a configurable duration instead of snapping instantly.

**Architecture:** Extend `RobotBackend` Protocol with `execute_joint_trajectory`; implement in both `SdkRobotBackend` (delegates to SDK) and `SimulatedRobot` (threaded in-memory interpolation). Add `duration` field to API command; expose duration input in UI.

**Tech Stack:** Python (backend), Vanilla JS + CSS (frontend), existing FastAPI + uvicorn.

---

## Side Quest (verify tests pass before starting)

- [ ] Run `conda run -n supre-robot-play python -m unittest discover -s tests` and confirm all 9 tests pass

---

## File Map

| File | Change |
|------|--------|
| `app/robot_service.py` | Protocol 新增 `execute_joint_trajectory`；`RobotService.set_joint` 新增 duration 参数；`SimulatedRobot` 新增 `execute_joint_trajectory` 实现 |
| `app/main.py` | `JointCommand` 新增 `duration` 字段；API handler 透传 duration |
| `static/index.html` | gripper toolbar 之后、arm grid 之前插入 duration input 行 |
| `static/styles.css` | 新增 `.duration-control` 样式 |
| `static/app.js` | 新增 duration state 和 input 绑定；`sendJoint` 增加 duration 参数 |
| `tests/test_robot_service.py` | 新增插值相关测试 |
| `tests/test_http_api.py` | 新增 duration 参数的 API 测试 |

---

## Task 1: Update `RobotBackend` Protocol + `SdkRobotBackend`

**Files:**
- Modify: `app/robot_service.py`

- [ ] **Step 1: Add `execute_joint_trajectory` to Protocol (line ~56)**

Find the `RobotBackend` Protocol class and add after `move_joints`:
```python
def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
    ...
```

- [ ] **Step 2: Implement `execute_joint_trajectory` in `SdkRobotBackend` (after line 178)**

```python
def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
    clamped = clamp_joint_value(joint_name, target)
    self._robot.execute_trajectory({joint_name: clamped}, duration=duration)
```

- [ ] **Step 3: Run tests**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```
Expected: all pass (no new tests yet, just verifying no regression)

- [ ] **Step 4: Commit**

```bash
git add app/robot_service.py
git commit -m "feat: add execute_joint_trajectory to RobotBackend protocol"
```

---

## Task 2: Implement `SimulatedRobot.execute_joint_trajectory`

**Files:**
- Modify: `app/robot_service.py` — add to `SimulatedRobot` class

- [ ] **Step 1: Add `execute_joint_trajectory` to `SimulatedRobot` (after line ~131)**

```python
def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
    self._require_connected()
    clamped = clamp_joint_value(joint_name, target)
    if clamped == self._positions.get(joint_name):
        return
    start = self._positions[joint_name]
    steps = max(3, int(30 * duration))  # 固定 30Hz
    for i in range(1, steps + 1):
        alpha = i / steps
        self._positions[joint_name] = start + alpha * (clamped - start)
        time.sleep(duration / steps)
    self._positions[joint_name] = clamped
```

- [ ] **Step 2: Verify no import needed — `time` is already imported at top of file**

- [ ] **Step 3: Run tests**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```
Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add app/robot_service.py
git commit -m "feat: implement execute_joint_trajectory in SimulatedRobot"
```

---

## Task 3: Update `RobotService.set_joint` with duration parameter

**Files:**
- Modify: `app/robot_service.py` — update `RobotService` class

- [ ] **Step 1: Update `set_joint` method (around line 236)**

Change from:
```python
def set_joint(self, joint: str, value: float) -> dict[str, object]:
    return self._call(lambda: self._backend.move_joint(joint, value))
```

To:
```python
def set_joint(self, joint: str, value: float, duration: float = 1.0) -> dict[str, object]:
    if duration <= 0:
        return self._call(lambda: self._backend.move_joint(joint, value))
    return self._call(lambda: self._backend.execute_joint_trajectory(joint, value, duration))
```

- [ ] **Step 2: Run tests**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add app/robot_service.py
git commit -m "feat: add duration parameter to RobotService.set_joint"
```

---

## Task 4: Update API — `JointCommand` + handler

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: Update `JointCommand` (after line 20)**

Change from:
```python
class JointCommand(BaseModel):
    joint: str = Field(min_length=1)
    value: float
```

To:
```python
class JointCommand(BaseModel):
    joint: str = Field(min_length=1)
    value: float
    duration: float = 1.0
```

- [ ] **Step 2: Update `/api/joint` handler (around line 67)**

Change from:
```python
@app.post("/api/joint")
def set_joint(command: JointCommand) -> dict[str, object]:
    return robot().set_joint(command.joint, command.value)
```

To:
```python
@app.post("/api/joint")
def set_joint(command: JointCommand) -> dict[str, object]:
    return robot().set_joint(command.joint, command.value, command.duration)
```

- [ ] **Step 3: Run tests**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```
Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add app/main.py
git commit -m "feat: add duration parameter to /api/joint endpoint"
```

---

## Task 5: Add Duration Input to HTML

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Insert duration control between gripper toolbar and arm grid**

Find `<section class="gripper-toolbar">` block (ends around line 67) and `<section class="arm-grid">` (starts around line 71). Insert after the closing `</section>` of gripper-toolbar and before `<section class="arm-grid">`:

```html
      <!-- DURATION CONTROL -->
      <div class="duration-control">
        <label>运动时长</label>
        <input type="number" id="durationInput" min="0.1" max="5.0" step="0.1" value="1.0" />
        <span>秒</span>
      </div>
```

- [ ] **Step 2: Commit**

```bash
git add static/index.html
git commit -m "feat: add duration control input to HTML"
```

---

## Task 6: Add Duration Input CSS

**Files:**
- Modify: `static/styles.css`

- [ ] **Step 1: Add duration control styles (at end of file)**

```css
/* === DURATION CONTROL === */
.duration-control {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-soft);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-lg);
}

.duration-control label {
  font-size: 14px;
  color: var(--color-muted);
}

.duration-control span {
  font-size: 14px;
  color: var(--color-muted);
}

.duration-control input {
  width: 64px;
  text-align: center;
  font-size: 14px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  background: var(--color-canvas);
  color: var(--color-ink);
}

.duration-control input:focus {
  outline: 2px solid var(--color-info);
  outline-offset: 1px;
}
```

- [ ] **Step 2: Commit**

```bash
git add static/styles.css
git commit -m "feat: add duration control CSS styles"
```

---

## Task 7: Update Frontend JS — Duration State + sendJoint

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Add `motionDuration` state variable (after line 7)**

```javascript
let motionDuration = 1.0;
```

- [ ] **Step 2: Update `sendJoint` function signature (around line 158)**

Change from:
```javascript
async function sendJoint(joint, value) {
  try {
    render(await post("/api/joint", { joint, value }));
    setMessage(`${joint} 已发送`);
  } catch (error) {
    setMessage(error.message, true);
  }
}
```

To:
```javascript
async function sendJoint(joint, value, duration = 1.0) {
  try {
    render(await post("/api/joint", { joint, value, duration }));
    setMessage(`${joint} → ${value} (${duration}s)`);
  } catch (error) {
    setMessage(error.message, true);
  }
}
```

- [ ] **Step 3: Add duration input initialization in `DOMContentLoaded` (after `message = ...` line)**

Inside `DOMContentLoaded` callback, after `torqueToggle = ...` line, add:
```javascript
const durationInput = document.getElementById("durationInput");
durationInput.addEventListener("change", () => {
  motionDuration = parseFloat(durationInput.value) || 1.0;
});
```

- [ ] **Step 4: Update slider `change` event to pass `motionDuration` (in `renderArmControl`)**

Find this in `renderArmControl`:
```javascript
slider.addEventListener("change", async () => {
  await sendJoint(joint, Number(slider.value));
});
```

Change to:
```javascript
slider.addEventListener("change", async () => {
  await sendJoint(joint, Number(slider.value), motionDuration);
});
```

- [ ] **Step 5: Verify tests pass**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```

- [ ] **Step 6: Commit**

```bash
git add static/app.js
git commit -m "feat: wire duration input to sendJoint API calls"
```

---

## Task 8: Add Backend Tests

**Files:**
- Modify: `tests/test_robot_service.py`

- [ ] **Step 1: Add test for `execute_joint_trajectory` on SimulatedRobot**

Add after existing tests:
```python
def test_simulated_robot_execute_joint_trajectory_sets_positions(self):
    service = RobotService(SimulatedRobot())
    service.connect()
    data = service.set_joint("left_arm_joint_1", 45.0, duration=0.1)
    self.assertEqual(data["positions"]["left_arm_joint_1"], 45.0)

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
```

- [ ] **Step 2: Run tests**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```
Expected: all pass including new tests

- [ ] **Step 3: Commit**

```bash
git add tests/test_robot_service.py
git commit -m "test: add joint interpolation tests"
```

---

## Task 9: Add API Tests

**Files:**
- Modify: `tests/test_http_api.py`

- [ ] **Step 1: Add test for joint API with duration parameter**

Add after existing tests:
```python
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
```

- [ ] **Step 2: Run tests**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_http_api.py
git commit -m "test: add duration parameter to joint API tests"
```

---

## Task 10: Final Verification

- [ ] **Step 1: Run all tests**

```bash
conda run -n supre-robot-play python -m unittest discover -s tests
```

- [ ] **Step 2: Manual smoke test**

```bash
# In one terminal:
conda activate supre-robot-play
./run_sim.sh

# In browser: http://127.0.0.1:8080
# Verify:
# - Duration input visible (default 1.0)
# - Changing duration and moving joint slider works
# - Status updates after motion completes
```

- [ ] **Step 3: Commit all remaining changes**

```bash
git status
git add -u
git commit -m "feat: add joint interpolation with configurable duration"
```
