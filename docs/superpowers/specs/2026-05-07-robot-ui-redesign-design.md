# Robot UI Redesign — Design Spec

## 1. Concept & Vision

将 Supre Robot Play 的前端从功能性诊断工具升级为兼具品牌感与实用性的专业控制台。视觉语言采用 Airtable 的 editorial 系统——白底黑字、近黑 CTA、签名色卡片作为信息分区的视觉锚点。信息架构上，将平铺的14个关节重组为左右双臂分组，让控制台更符合人类对双机械臂操作的心智模型。

## 2. Design Language

### Aesthetic Direction
Airtable editorial system — near-black primary, white canvas, signature surface cards for brand voltage.

### Color Palette
| Role | Hex | Use |
|------|-----|-----|
| Primary | `#181d26` | Topbar, primary buttons, h1/h2 display type |
| Primary Active | `#0d1218` | Button press state |
| Canvas | `#ffffff` | Page background |
| Surface Soft | `#f8fafc` | Status cards background |
| Disconnected | `#9297a0` | Disconnected status dot |
| Error | `#b42318` | Error message text |
| Surface Strong | `#e0e2e6` | Light gray bands (unused initially) |
| Hairline | `#dddddd` | Input borders, dividers |
| Ink / Body | `#181d26` / `#333840` | Text hierarchy |
| Muted | `#41454d` | Captions, meta |
| On Primary | `#ffffff` | Text on dark surfaces |
| Signature Coral | `#aa2d00` | Right arm card background |
| Signature Forest | `#0a2e0e` | Left arm card background |
| Info | `#254fad` | Links, focused inputs |
| Success | `#006400` | Connected indicator |

### Typography
- Font stack: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- Fallback rationale: Inter is the closest open-source substitute for Haas Grotesk
- Scale:
  - Display (h1): 40px / 400 / 1.2
  - Title (h2): 24px / 400 / 1.35
  - Label: 16px / 500
  - Body: 14px / 400 / 1.25
  - Caption: 14px / 500 / 1.35

### Spatial System
- Base unit: 4px
- Major spacing: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 96px
- Card internal padding: 24–32px
- Section gap: 32–48px

### Motion Philosophy
No animation documented (per Airtable system rule: no hover states documented). Static rendering only.

### Visual Assets
- No icons beyond text labels and CSS-only circular status dots
- No photography or illustrations
- Gripper joint uses a different accent color (#aa2d00 coral) to visually distinguish from arm joints

## 3. Layout & Structure

```
┌─────────────────────────────────────────┐
│  TOPBAR (dark navy #181d26)             │
│  [Supre Robot Play]  [Connect][Disconnect][Refresh] │
├─────────────────────────────────────────┤
│  HERO BAND (white canvas)               │
│  Robot Diagnostics                       │
│  Web diagnostics and control for Supre  │
│  dual-arm robots.                        │
├─────────────────────────────────────────┤
│  STATUS GRID (4 cards, Surface Soft)    │
│  [Mode] [Connection●] [Joints: 14] [Torque toggle]  │
├─────────────────────────────────────────┤
│  GRIPPER TOOLBAR                        │
│  [L Open][L Close]  |  [R Open][R Close]│
├──────────────────────┬──────────────────┤
│  LEFT ARM CARD       │  RIGHT ARM CARD  │
│  (Signature Forest)  │  (Signature Coral)│
│  "Left Arm"          │  "Right Arm"      │
│  joint_1 [slider]    │  joint_1 [slider] │
│  joint_2 [slider]    │  joint_2 [slider] │
│  ...                 │  ...              │
│  joint_7 gripper [●] │  joint_7 gripper [●]│
└──────────────────────┴──────────────────┘
```

### Responsive Strategy
- **Mobile (<768px)**: Single column, left/right arm cards stack vertically
- **Tablet/Desktop**: Two-column side-by-side arm cards
- Status grid: 4 columns → 2 columns (tablet) → 1 column (mobile)

## 4. Features & Interactions

### Connection Management
- **Connect button**: POST `/api/connect`, updates status grid on success
- **Disconnect button**: POST `/api/disconnect`
- **Refresh button**: GET `/api/diagnostics`, polls every 2 seconds auto-refresh
- Connection state shown as colored dot: green (#006400) = connected, gray (#9297a0) = disconnected

### Torque Toggle
- Checkbox toggle in status grid
- POST `/api/torque` with `{ enabled: true/false }` on change
- Disabled when robot is not connected

### Gripper Quick Controls
- Four buttons: L Open, L Close, R Open, R Close
- POST `/api/gripper` with `{ arm: "left"|"right", action: "open"|"close" }`
- Use Airtable button-primary (dark) and button-secondary (white outline) style

### Joint Control (Core)
- 14 joints split into left arm (7) and right arm (7)
- Each joint row: `[joint name label] [range slider] [current position value] [force value]`
- Slider range: -180° to +180° for arm joints, 0–1 for gripper (joint_7)
- On slider change: POST `/api/joint`, then re-render with new values
- Gripper joint (joint_7) visually differentiated with coral accent color
- All controls disabled when robot is not connected

### Error Handling
- API errors shown in message area with red text
- Slider reverts to last known value on failure
- 409 Conflict shown when trying to control while disconnected

### States
- **Loading**: No spinner. The single slider being adjusted stays interactive (user can continue sliding); all other controls are disabled during a pending request.
- **Disconnected**: All sliders disabled, grayed out, connection dot gray
- **Connected**: Sliders enabled, connection dot green
- **Error**: Error text shown in `#b42318`; auto-clears on next successful action

## 5. Component Inventory

### Topbar
- 64px tall, `#181d26` background, white text
- Left: "Supre Robot Play" wordmark in 24px/500
- Right: Connect (primary), Disconnect (secondary), Refresh (secondary) buttons

### Status Cards (4-up grid)
- Background: `#f8fafc`, rounded 10px, padding 16px
- Each card: label (14px muted) + value (20px bold)
- Connection card: value includes colored circle dot before text
- Grid gap: 12px between cards

### Gripper Toolbar
- Horizontal button group with `|` divider (16px gap on each side, vertically centered)
- Primary button: `#181d26` bg, white text, 12px radius, padding 16px 24px
- Secondary button: white bg, hairline border, `#181d26` text, 12px radius, padding 16px 24px

### Arm Control Card
- **Left**: Background `#0a2e0e` (Signature Forest), white text, rounded 12px
- **Right**: Background `#aa2d00` (Signature Coral), white text, rounded 12px
- Internal padding: 32px
- Card title: 20px/500 "Left Arm" / "Right Arm"
- Joint rows: label (16px/500), slider, position value (tabular nums), force value (muted)
- Joint row gap: 12px vertical gap between rows

### Joint Slider
- `<input type="range">` with CSS styling
- Track: hairline color `#dddddd`
- Thumb: primary `#181d26`
- Gripper slider thumb: coral `#aa2d00`
- Disabled state: 50% opacity, not-allowed cursor

## 6. Technical Approach

### Stack
- Vanilla HTML/CSS/JS (no framework change)
- Existing FastAPI backend unchanged
- Only `static/` files modified: `index.html`, `styles.css`, `app.js`

### API Endpoints Used
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/diagnostics` | Full state: positions, forces, connection |
| GET | `/api/health` | Lightweight status check |
| POST | `/api/connect` | Connect to robot |
| POST | `/api/disconnect` | Disconnect |
| POST | `/api/torque` | `{ enabled: bool }` |
| POST | `/api/joint` | `{ joint: str, value: float }` |
| POST | `/api/gripper` | `{ arm: str, action: str }` |

### Data Model
- Robot state held in `app.js` `state` object
- State updated on every successful API response
- Sliders render from `state.positions`, forces from `state.forces`

### Font Loading
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
```

### File Changes
1. `static/index.html` — Restructure DOM to match layout spec
2. `static/styles.css` — Replace all CSS variables and styles with Airtable system
3. `static/app.js` — Adapt rendering logic to two-column arm layout; rest unchanged
