const state = {
  connected: false,
  pending: false,
  positions: {},
  forces: {},
  jointOrder: [],
};

let motionDuration = 1.0;

let message = null;
let torqueToggle = null;
let hardwareCheckBtn = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await response.text();
  if (!text) {
    throw new Error(`HTTP ${response.status}: empty response`);
  }
  const payload = JSON.parse(text);
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function post(path, body = {}) {
  return api(path, { method: "POST", body: JSON.stringify(body) });
}

function setMessage(text, isError = false) {
  if (!message) return;
  message.textContent = text;
  message.classList.toggle("error", isError);
}

function isGripper(joint) {
  return joint.endsWith("_joint_7");
}

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

function format(value, digits = 2) {
  return Number(value || 0).toFixed(digits);
}

function renderArmControl(containerId, jointNames) {
  const container = document.getElementById(containerId);
  if (!container) return;
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
        await sendJoint(joint, Number(slider.value), motionDuration);
      });

      const target = metric("目标", format(slider.value, isGripper(joint) ? 2 : 1), "target");
      const force = metric("力", format(state.forces[joint], 2));

      const resetBtn = document.createElement("button");
      resetBtn.className = "reset-btn";
      resetBtn.textContent = "⏺";
      resetBtn.title = "复位到 0";
      resetBtn.addEventListener("click", async () => {
        await sendJoint(joint, 0, motionDuration);
      });

      row.append(name, slider, target, force, resetBtn);
      if (joint === activeJoint) {
        requestAnimationFrame(() => row.querySelector("input")?.focus());
      }
      return row;
    }),
  );
}

function render(data) {
  state.connected = Boolean(data.connected);
  state.positions = data.positions || state.positions || {};
  state.forces = data.forces || state.forces || {};
  state.jointOrder = data.joint_order || state.jointOrder || [];

  document.getElementById("mode").textContent = data.mode || "-";
  document.getElementById("jointCount").textContent = String(data.joint_count ?? state.jointOrder.length);

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

  renderJoints();
}

function renderJoints() {
  renderArmControl("leftArmControls", LEFT_ARM_JOINTS);
  renderArmControl("rightArmControls", RIGHT_ARM_JOINTS);
}

function metric(label, value, role) {
  const node = document.createElement("div");
  node.className = "metric";
  const small = document.createElement("span");
  small.textContent = label;
  const strong = document.createElement("strong");
  strong.textContent = value;
  if (role) strong.dataset.role = role;
  node.append(small, strong);
  return node;
}

function selectedHardwareCheckMode() {
  return document.querySelector("input[name='hardwareCheckMode']:checked")?.value || "passive";
}

function statusLabel(ok) {
  return ok ? "通过" : "失败";
}

function statusClass(ok) {
  return ok ? "check-pass" : "check-fail";
}

function renderHardwareCheck(data) {
  const summary = document.getElementById("hardwareCheckSummary");
  const results = document.getElementById("hardwareCheckResults");
  if (!summary || !results) return;

  summary.textContent = data.summary || (data.ok ? "硬件检测通过" : "硬件检测发现问题");
  summary.className = data.ok ? "summary-pass" : "summary-fail";

  const interfaces = Array.isArray(data.interfaces) ? data.interfaces : [];
  if (!interfaces.length) {
    results.replaceChildren(emptyHardwareCheckResult("没有可显示的硬件接口结果"));
    return;
  }

  results.replaceChildren(
    ...interfaces.map((item) => {
      const card = document.createElement("article");
      card.className = `hardware-result ${statusClass(Boolean(item.ok))}`;

      const header = document.createElement("div");
      header.className = "hardware-result-header";
      const title = document.createElement("strong");
      title.textContent = item.name || item.configured_type || item.type || "unknown";
      const badge = document.createElement("span");
      badge.className = "hardware-result-badge";
      badge.textContent = statusLabel(Boolean(item.ok));
      header.append(title, badge);

      const type = document.createElement("div");
      type.className = "hardware-result-type";
      type.textContent = item.configured_type || item.type || "";

      const messageNode = document.createElement("p");
      messageNode.textContent = item.message || (item.ok ? "检测通过" : "检测失败");

      card.append(header, type, messageNode);
      if (item.suggestion) {
        const suggestion = document.createElement("p");
        suggestion.className = "hardware-suggestion";
        suggestion.textContent = item.suggestion;
        card.append(suggestion);
      }

      const details = hardwareDetails(item);
      if (details.length) {
        const detailList = document.createElement("ul");
        detailList.className = "hardware-detail-list";
        details.forEach((detail) => {
          const li = document.createElement("li");
          li.textContent = detail;
          detailList.append(li);
        });
        card.append(detailList);
      }
      return card;
    }),
  );
}

function hardwareDetails(item) {
  const details = [];
  if (Array.isArray(item.events)) {
    item.events.slice(0, 3).forEach((event) => {
      const scope = [event.joint_name, event.node_id != null ? `node ${event.node_id}` : ""].filter(Boolean).join(" ");
      details.push(`${event.stage || "event"}${scope ? ` (${scope})` : ""}: ${event.message || ""}`);
    });
  }
  if (Array.isArray(item.joints)) {
    item.joints.filter((joint) => joint && joint.ok === false).slice(0, 4).forEach((joint) => {
      const parts = [joint.joint_name, joint.node_id != null ? `node ${joint.node_id}` : ""].filter(Boolean).join(" ");
      details.push(`${parts || "joint"}: ${joint.message || "检测失败"}`);
    });
  }
  return details;
}

function emptyHardwareCheckResult(text) {
  const node = document.createElement("div");
  node.className = "hardware-empty";
  node.textContent = text;
  return node;
}

async function runHardwareCheck() {
  const mode = selectedHardwareCheckMode();
  try {
    hardwareCheckBtn.disabled = true;
    hardwareCheckBtn.textContent = "检测中";
    setMessage(mode === "activate" ? "正在执行 activate 诊断..." : "正在执行非 activate 诊断...");
    const result = await api(`/api/hardware-check?mode=${encodeURIComponent(mode)}`);
    renderHardwareCheck(result);
    setMessage(result.ok ? "硬件检测通过" : "硬件检测发现问题", !result.ok);
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    hardwareCheckBtn.disabled = false;
    hardwareCheckBtn.textContent = "开始检测";
  }
}

async function refresh() {
  try {
    render(await api("/api/diagnostics"));
    setMessage("状态已刷新");
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function sendJoint(joint, value, duration = 1.0) {
  try {
    render(await post("/api/joint", { joint, value, duration }));
    setMessage(`${joint} → ${value} (${duration}s)`);
  } catch (error) {
    setMessage(error.message, true);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  message = document.getElementById("message");
  torqueToggle = document.getElementById("torqueToggle");
  hardwareCheckBtn = document.getElementById("hardwareCheckBtn");

  const durationInput = document.getElementById("durationInput");
  durationInput.addEventListener("change", () => {
    motionDuration = Math.min(Math.max(parseFloat(durationInput.value) || 1.0, 0.1), 60);
  });

  document.getElementById("connectBtn").addEventListener("click", async () => {
    try {
      render(await post("/api/connect"));
      setMessage("机器人已连接");
    } catch (error) {
      setMessage(error.message, true);
    }
  });

  document.getElementById("disconnectBtn").addEventListener("click", async () => {
    try {
      render(await post("/api/disconnect"));
      setMessage("机器人已断开");
    } catch (error) {
      setMessage(error.message, true);
    }
  });

  document.getElementById("refreshBtn").addEventListener("click", refresh);
  hardwareCheckBtn.addEventListener("click", runHardwareCheck);

  torqueToggle.addEventListener("change", async () => {
    try {
      render(await post("/api/torque", { enabled: torqueToggle.checked }));
      setMessage(torqueToggle.checked ? "扭矩已使能" : "扭矩已关闭");
    } catch (error) {
      setMessage(error.message, true);
    }
  });

  document.querySelectorAll("[data-gripper-arm]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        render(await post("/api/gripper", {
          arm: button.dataset.gripperArm,
          action: button.dataset.gripperAction,
        }));
        setMessage("夹爪命令已发送");
      } catch (error) {
        setMessage(error.message, true);
      }
    });
  });

  document.querySelectorAll(".reset-all-btn").forEach((button) => {
    button.addEventListener("click", async () => {
      const arm = button.dataset.resetArm;
      const joints = arm === "left" ? LEFT_ARM_JOINTS : RIGHT_ARM_JOINTS;
      setMessage("复位中...");
      for (const joint of joints) {
        try {
          await post("/api/joint", { joint, value: 0, duration: motionDuration });
        } catch (error) {
          setMessage(error.message, true);
          return;
        }
      }
      try {
        render(await api("/api/diagnostics"));
        setMessage("所有关节已复位");
      } catch (error) {
        setMessage(error.message, true);
      }
    });
  });

  refresh();
  setInterval(refresh, 2000);
});
