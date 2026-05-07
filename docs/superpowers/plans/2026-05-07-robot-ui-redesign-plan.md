# Robot UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the robot web UI's stylesheet and HTML structure to match the Airtable editorial design system, reorganizing the joint control layout from a flat 14-item list into two arm-grouped columns.

**Architecture:** Pure frontend refactor of `static/index.html`, `static/styles.css`, and `static/app.js`. No backend changes. HTML/CSS uses Airtable design tokens as CSS custom properties. JS rendering is adapted to produce two arm-grouped card containers instead of a single flat list.

**Tech Stack:** Vanilla HTML/CSS/JS (no framework change), Inter font via Google Fonts, existing FastAPI backend unchanged.

---

## File Map

| File | Responsibility |
|------|----------------|
| `static/index.html` | Page structure: topbar, hero band, status grid, gripper toolbar, left/right arm card containers |
| `static/styles.css` | All CSS: design tokens, layout grids, button components, slider styling, responsive breakpoints |
| `static/app.js` | Rendering logic adapted to two-column arm layout; API calls unchanged |

---

## Side Quest (verify existing tests still pass before starting)

- [ ] Run `python -m unittest discover -s tests` and confirm all 5 tests pass before making changes

---

## Task 1: Rewrite `static/index.html`

**Files:**
- Modify: `static/index.html` (full rewrite)

- [ ] **Step 1: Write new HTML structure**

Replace the entire file with this structure:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Supre Robot Play</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="/styles.css" />
  </head>
  <body>
    <!-- TOPBAR -->
    <header class="topbar">
      <div class="topbar-wordmark">Supre Robot Play</div>
      <div class="actions">
        <button id="connectBtn" class="btn-primary">连接</button>
        <button id="disconnectBtn" class="btn-secondary">断开</button>
        <button id="refreshBtn" class="btn-secondary">刷新</button>
      </div>
    </header>

    <!-- HERO BAND -->
    <section class="hero-band">
      <h1>Robot Diagnostics</h1>
      <p class="hero-subtitle">Web diagnostics and control for Supre dual-arm robots.</p>
    </section>

    <!-- MAIN CONTENT -->
    <main>
      <!-- STATUS GRID -->
      <section class="status-grid" aria-label="诊断状态">
        <div class="status-card">
          <span class="status-label">模式</span>
          <strong class="status-value" id="mode">-</strong>
        </div>
        <div class="status-card">
          <span class="status-label">连接</span>
          <strong class="status-value connection-value">
            <span id="connectionDot" class="dot dot-gray"></span>
            <span id="connected">未连接</span>
          </strong>
        </div>
        <div class="status-card">
          <span class="status-label">关节数</span>
          <strong class="status-value" id="jointCount">-</strong>
        </div>
        <div class="status-card">
          <span class="status-label">扭矩</span>
          <label class="torque-label">
            <input id="torqueToggle" type="checkbox" checked />
            <span id="torqueState">已使能</span>
          </label>
        </div>
      </section>

      <!-- GRIPPER TOOLBAR -->
      <section class="gripper-toolbar" aria-label="夹爪控制">
        <div class="gripper-group">
          <button data-gripper-arm="left" data-gripper-action="open" class="btn-primary">左夹爪打开</button>
          <button data-gripper-arm="left" data-gripper-action="close" class="btn-secondary">左夹爪关闭</button>
        </div>
        <span class="toolbar-divider">|</span>
        <div class="gripper-group">
          <button data-gripper-arm="right" data-gripper-action="open" class="btn-primary">右夹爪打开</button>
          <button data-gripper-arm="right" data-gripper-action="close" class="btn-secondary">右夹爪关闭</button>
        </div>
      </section>

      <!-- ARM CONTROL CARDS -->
      <section class="arm-grid" aria-label="关节控制">
        <div class="arm-card arm-card-left">
          <h2 class="arm-title">Left Arm</h2>
          <div id="leftArmControls" class="joint-list"></div>
        </div>
        <div class="arm-card arm-card-right">
          <h2 class="arm-title">Right Arm</h2>
          <div id="rightArmControls" class="joint-list"></div>
        </div>
      </section>

      <!-- STATUS MESSAGE -->
      <div id="message" class="message" role="status"></div>
    </main>

    <script src="/app.js"></script>
  </body>
</html>
```

---

## Task 2: Rewrite `static/styles.css`

**Files:**
- Modify: `static/styles.css` (full rewrite)

- [ ] **Step 1: Write design tokens and base styles**

```css
/* === DESIGN TOKENS === */
:root {
  /* Colors */
  --color-primary: #181d26;
  --color-primary-active: #0d1218;
  --color-canvas: #ffffff;
  --color-surface-soft: #f8fafc;
  --color-surface-strong: #e0e2e6;
  --color-hairline: #dddddd;
  --color-ink: #181d26;
  --color-body: #333840;
  --color-muted: #41454d;
  --color-on-primary: #ffffff;
  --color-signature-coral: #aa2d00;
  --color-signature-forest: #0a2e0e;
  --color-info: #254fad;
  --color-success: #006400;
  --color-disconnected: #9297a0;
  --color-error: #b42318;

  /* Spacing */
  --space-xxs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-xxl: 48px;
  --space-section: 96px;

  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 12px;

  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* === RESET & BASE === */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
}

body {
  background: var(--color-canvas);
  color: var(--color-body);
  font: 14px / 1.25 var(--font-family);
  min-height: 100vh;
}

/* === TOPBAR === */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 var(--space-lg);
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.topbar-wordmark {
  font-size: 24px;
  font-weight: 500;
  letter-spacing: 0.12px;
}

/* === BUTTONS === */
.btn-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-md) var(--space-lg);
  font: 16px / 1.4 var(--font-family);
  font-weight: 500;
  cursor: pointer;
  min-height: 48px;
}

.btn-primary:active {
  background: var(--color-primary-active);
  border-color: var(--color-primary-active);
}

.btn-secondary {
  background: var(--color-canvas);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-lg);
  font: 16px / 1.4 var(--font-family);
  font-weight: 500;
  cursor: pointer;
  min-height: 48px;
}

.btn-secondary:disabled,
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* === HERO BAND === */
.hero-band {
  padding: var(--space-section) var(--space-xxl);
  background: var(--color-canvas);
  text-align: center;
}

.hero-band h1 {
  font: 400 40px / 1.2 var(--font-family);
  color: var(--color-ink);
  margin-bottom: var(--space-md);
}

.hero-subtitle {
  font: 14px / 1.25 var(--font-family);
  color: var(--color-muted);
}

/* === MAIN CONTENT === */
main {
  width: min(1280px, calc(100vw - 96px));
  margin: 0 auto;
  padding: 0 var(--space-xxl) var(--space-xxl);
}

/* === STATUS GRID === */
.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.status-card {
  background: var(--color-surface-soft);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.status-label {
  font-size: 14px;
  color: var(--color-muted);
}

.status-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
}

.connection-value {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-gray { background: var(--color-disconnected); }
.dot-green { background: var(--color-success); }

/* === TORQUE TOGGLE === */
.torque-label {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  cursor: pointer;
  font-size: 14px;
  color: var(--color-body);
}

.torque-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
}

/* === GRIPPER TOOLBAR === */
.gripper-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.gripper-group {
  display: flex;
  gap: var(--space-xs);
}

.toolbar-divider {
  color: var(--color-muted);
  font-size: 20px;
  padding: 0 var(--space-xs);
}

/* === ARM GRID === */
.arm-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

.arm-card {
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.arm-card-left {
  background: var(--color-signature-forest);
  color: var(--color-on-primary);
}

.arm-card-right {
  background: var(--color-signature-coral);
  color: var(--color-on-primary);
}

.arm-title {
  font: 500 20px / 1.3 var(--font-family);
  margin-bottom: var(--space-lg);
  color: var(--color-on-primary);
}

/* === JOINT LIST === */
.joint-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.joint-row {
  display: grid;
  grid-template-columns: minmax(130px, 1fr) minmax(140px, 2fr) 70px 70px;
  align-items: center;
  gap: var(--space-sm);
  background: rgba(255,255,255,0.08);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-md);
}

.joint-name {
  font-size: 14px;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.joint-range {
  width: 100%;
  height: 6px;
  accent-color: var(--color-on-primary);
}

.arm-card-left .joint-range {
  accent-color: var(--color-on-primary);
}

.arm-card-right .joint-range {
  accent-color: var(--color-on-primary);
}

/* Gripper slider thumb highlight */
.joint-row.is-gripper .joint-range {
  accent-color: #aa2d00;
}

.metric {
  text-align: right;
}

.metric span {
  display: block;
  font-size: 12px;
  color: rgba(255,255,255,0.6);
}

.metric strong {
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  color: var(--color-on-primary);
}

/* === MESSAGE === */
.message {
  margin-top: var(--space-lg);
  font-size: 14px;
  color: var(--color-muted);
  min-height: 20px;
}

.message.error {
  color: var(--color-error);
}

/* === RESPONSIVE === */
@media (max-width: 768px) {
  main {
    width: calc(100vw - 32px);
    padding: 0 var(--space-md) var(--space-lg);
  }

  .status-grid {
    grid-template-columns: 1fr 1fr;
  }

  .arm-grid {
    grid-template-columns: 1fr;
  }

  .topbar {
    flex-direction: column;
    height: auto;
    padding: var(--space-md);
    gap: var(--space-md);
    align-items: flex-start;
  }

  .hero-band {
    padding: var(--space-xxl) var(--space-md);
  }

  .joint-row {
    grid-template-columns: 1fr 1fr;
  }
}
```

---

## Task 3: Adapt `static/app.js`

**Files:**
- Modify: `static/app.js` (targeted changes to rendering logic only; API calls and state management unchanged)

The `renderJoints()` function is the only part that needs significant change — it currently renders all 14 joints into a single list. Split into left/right arm containers.

- [ ] **Step 1: Add arm split constants at top of file**

After the existing `isGripper()` helper, add:

```javascript
const LEFT_ARM_JOINTS = [
  "left_arm_joint_1",
  "left_arm_joint_2",
  "left_arm_joint_3",
  "left_arm_joint_4",
  "left_arm_joint_5",
  "left_arm_joint_6",
  "left_arm_joint_7",
];

const RIGHT_ARM_JOINTS = [
  "right_arm_joint_1",
  "right_arm_joint_2",
  "right_arm_joint_3",
  "right_arm_joint_4",
  "right_arm_joint_5",
  "right_arm_joint_6",
  "right_arm_joint_7",
];
```

- [ ] **Step 2: Add `renderArmControl(containerId, jointNames)` function**

Replace the existing inline joint rendering in `renderJoints()`. This function renders a joint row for each joint in `jointNames` into the DOM element identified by `containerId`.

```javascript
function renderArmControl(containerId, jointNames) {
  const container = document.getElementById(containerId);
  const active = document.activeElement;
  const activeJoint = active?.dataset?.joint;

  container.replaceChildren(
    ...jointNames.map((joint) => {
      const row = document.createElement("div");
      row.className = "joint-row" + (isGripper(joint) ? " is-gripper" : "");

      const name = document.createElement("div");
      name.className = "joint-name";
      name.textContent = joint;

      const slider = document.createElement("input");
      slider.className = "joint-range";
      slider.type = "range";
      slider.dataset.joint = joint;
      slider.min = isGripper(joint) ? "0" : "-180";
      slider.max = isGripper(joint) ? "1" : "180";
      slider.step = isGripper(joint) ? "0.01" : "0.1";
      slider.value = String(state.positions[joint] ?? 0);
      slider.disabled = !state.connected;
      slider.addEventListener("input", () => {
        row.querySelector("[data-role='target']").textContent = format(slider.value, isGripper(joint) ? 2 : 1);
      });
      slider.addEventListener("change", async () => {
        await sendJoint(joint, Number(slider.value));
      });

      const target = metric("目标", format(slider.value, isGripper(joint) ? 2 : 1), "target");
      const force = metric("力", format(state.forces[joint], 2));

      row.append(name, slider, target, force);
      if (joint === activeJoint) {
        requestAnimationFrame(() => row.querySelector("input")?.focus());
      }
      return row;
    }),
  );
}
```

- [ ] **Step 3: Replace `renderJoints()` body**

Change `renderJoints()` to call the new function for both arms:

```javascript
function renderJoints() {
  renderArmControl("leftArmControls", LEFT_ARM_JOINTS);
  renderArmControl("rightArmControls", RIGHT_ARM_JOINTS);
}
```

- [ ] **Step 4: Update `render()` — fix connection display**

In `render()`, replace the connected text section:

```javascript
// Connection dot + text
const dot = document.getElementById("connectionDot");
const connectedEl = document.getElementById("connected");
if (state.connected) {
  dot.className = "dot dot-green";
  connectedEl.textContent = "已连接";
} else {
  dot.className = "dot dot-gray";
  connectedEl.textContent = "未连接";
}

// Torque
torqueToggle.checked = Boolean(data.torque_enabled);
torqueToggle.disabled = !state.connected;
document.getElementById("torqueState").textContent = data.torque_enabled ? "已使能" : "已关闭";
```

- [ ] **Step 5: Verify all existing API handlers remain unchanged**

Confirm these handlers still wire up correctly — `connectBtn`, `disconnectBtn`, `refreshBtn`, `torqueToggle`, `[data-gripper-arm]` all already exist in the new HTML and their event listeners in `app.js` use the same IDs and data attributes.

---

## Task 4: Verify

- [ ] **Step 1: Run existing Python tests**

```bash
cd /root/data1/kdi/workspace/supre_robot_play && python -m unittest discover -s tests
```
Expected: all 5 tests pass (tests are backend-only, no regression from frontend changes)

- [ ] **Step 2: CSS token verification**

Open browser DevTools → Inspect the topbar element and verify:
- `.topbar` has `height: 64px` and `background: #181d26`
- `.topbar-wordmark` has `font-size: 24px` and `font-weight: 500`
- `.btn-secondary` has `border-radius: 10px`
- `.arm-card-left` has `background: #0a2e0e`
- `.arm-card-right` has `background: #aa2d00`
- `.joint-row.is-gripper .joint-range` has `accent-color: #aa2d00`

- [ ] **Step 3: Manual verification — run the server**

```bash
python -m app.main --host 127.0.0.1 --port 8080
```
Open `http://127.0.0.1:8080`. Visually verify:
- Topbar is dark navy (#181d26) with white wordmark and 3 buttons right-aligned
- Hero band: white canvas, "Robot Diagnostics" headline, subtitle below
- Status grid: 4 cards with Surface Soft (#f8fafc) background
- Connection card shows colored dot (gray when disconnected, green when connected)
- Gripper toolbar: 4 buttons with `|` divider between arms
- Two arm cards: left = deep forest green (#0a2e0e), right = dark coral (#aa2d00)
- Joint sliders grouped under correct arm headers
- Torque toggle in status card
- Responsive at <768px: arm cards stack vertically

- [ ] **Step 4: Test connect/disconnect cycle**

Click Connect → verify dot turns green, sliders become enabled, torque toggle is enabled.
Click Disconnect → verify dot turns gray, sliders become disabled, torque toggle is disabled.

- [ ] **Step 5: Test joint movement**

Connect → adjust a slider → verify position value updates and no errors.

---

## Task 5: Commit

```bash
git add static/index.html static/styles.css static/app.js
git commit -m "feat: redesign robot UI with Airtable editorial system and arm-grouped layout"
```
