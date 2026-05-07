# Joint Interpolation — Design Spec

## 1. Concept & Vision

在关节运动时引入平滑插值，防止大幅快速动作对机械臂造成冲击。用户拖动关节滑块并松开后，关节以指定时长平滑运动到目标位置，而非瞬间跳变。

## 2. Design Language

沿用现有 Airtable editorial system（参见 `DESIGN.md`）。无新增视觉组件。

## 3. Layout & Structure

在 gripper toolbar 下方、arm grid 上方插入一行 duration 控制：

```
[ 运动时长: [1.0] 秒 ]      ← number input，右侧单位标签
```

- `min=0.1`, `max=5.0`, `step=0.1`, `default=1.0`
- 采用与 status-card 相同的 Surface Soft 背景，圆角 10px，内边距 12px
- 宽度自适应，内容居中

## 4. Features & Interactions

### Motion Flow
1. 用户拖动关节滑块，滑块实时更新目标值预览（数值变化）
2. 用户**松开**滑块，触发 `change` 事件
3. JS 发送 `POST /api/joint { joint, value, duration }`
4. 后端调用 SDK `execute_trajectory` 执行插值运动
5. 插值期间（duration 秒）：所有控件**保持可用**，可继续拖动其他关节
6. 插值完成后，状态自动刷新

### Backend Behavior
- `duration` 为**建议时长**，SDK 按控制频率分步执行线性插值
- 若 `duration <= 0`，等同于原有 `move_joint`（瞬时到位）
- SDK `execute_trajectory` 内部已实现线性插值（见 `supre_robot_sdk/core/robot.py:109`）

### Simulated Backend
- `SimulatedRobot.move_joint` 不支持插值（跳过）
- 新增 `SimulatedRobot.execute_joint_trajectory`：在内存中模拟插值，将目标位置分 N 步写入 `_positions`，每步 `duration/N` 秒后更新
- 插值期间仍可响应其他关节操作（各自独立 timing）

## 5. Component Inventory

### Duration Input
- Type: `<input type="number">`
- CSS class: `.duration-control`
- Background: `#f8fafc`, rounded 10px, padding 12px
- Input: width 64px, centered text, step 0.1
- Label: 14px muted text "运动时长"

## 6. Technical Approach

### API Changes

**`JointCommand` (app/main.py)**
```python
class JointCommand(BaseModel):
    joint: str = Field(min_length=1)
    value: float
    duration: float = 1.0  # 新增：插值时长（秒）
```

**`/api/joint` handler**
```python
@app.post("/api/joint")
def set_joint(command: JointCommand) -> dict[str, object]:
    return robot().set_joint(command.joint, command.value, command.duration)
```

### Protocol Changes

**`RobotBackend` Protocol (app/robot_service.py)**
```python
def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
    ...
```

### Backend Implementation

**`SdkRobotBackend`**
```python
def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
    clamped = clamp_joint_value(joint_name, target)
    self._robot.execute_trajectory({joint_name: clamped}, duration=duration)
```

**`SimulatedRobot`**
```python
def execute_joint_trajectory(self, joint_name: str, target: float, duration: float) -> None:
    clamped = clamp_joint_value(joint_name, target)
    if clamped == self._positions.get(joint_name):
        return
    start = self._positions[joint_name]
    steps = max(3, int(self._control_frequency * duration))
    for i in range(1, steps + 1):
        alpha = i / steps
        self._positions[joint_name] = start + alpha * (clamped - start)
        time.sleep(duration / steps)
    self._positions[joint_name] = clamped
```

**`RobotService.set_joint`**
```python
def set_joint(self, joint: str, value: float, duration: float = 1.0) -> dict[str, object]:
    if duration <= 0:
        return self._call(lambda: self._backend.move_joint(joint, value))
    return self._call(lambda: self._backend.execute_joint_trajectory(joint, value, duration))
```

### Frontend Changes

**HTML: `static/index.html`**
```html
<div class="duration-control">
  <label>运动时长</label>
  <input type="number" id="durationInput" min="0.1" max="5.0" step="0.1" value="1.0" />
  <span>秒</span>
</div>
```

**CSS: `static/styles.css`**
```css
.duration-control {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-soft);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-lg);
}

.duration-control input {
  width: 64px;
  text-align: center;
  font-size: 14px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
}
```

**JS: `static/app.js`**
```javascript
// Top: add duration state
let motionDuration = 1.0;

// In DOMContentLoaded: init duration input
const durationInput = document.getElementById("durationInput");
durationInput.addEventListener("change", () => {
  motionDuration = parseFloat(durationInput.value) || 1.0;
});

// In renderArmControl slider change handler:
slider.addEventListener("change", async () => {
  await sendJoint(joint, Number(slider.value), motionDuration);
});

// Update sendJoint signature:
async function sendJoint(joint, value, duration = 1.0) {
  try {
    render(await post("/api/joint", { joint, value, duration }));
    setMessage(`${joint} → ${value} (${duration}s)`);
  } catch (error) {
    setMessage(error.message, true);
  }
}
```

### File Changes Summary

| File | Change |
|------|--------|
| `app/main.py` | `JointCommand` 新增 `duration` 字段 |
| `app/robot_service.py` | Protocol 新增 `execute_joint_trajectory`；`RobotService.set_joint` 新增 duration 参数 |
| `static/index.html` | 新增 duration input 行 |
| `static/styles.css` | 新增 `.duration-control` 样式 |
| `static/app.js` | 新增 duration input 绑定，`sendJoint` 增加 duration 参数 |
| `tests/test_robot_service.py` | 新增插值相关测试用例 |
| `tests/test_http_api.py` | 新增 duration 参数的 API 测试 |
