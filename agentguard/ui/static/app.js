const byId = (id) => document.getElementById(id);

function setDecision(value) {
  const el = byId("decision");
  el.textContent = value;
  el.className = `decision ${value.toLowerCase()}`;
}

async function loadHealth() {
  try {
    const response = await fetch("/api/v1/health");
    const data = await response.json();
    byId("health").textContent = data.status === "ok" ? "Online" : "Unavailable";
  } catch {
    byId("health").textContent = "Offline";
  }
}

async function loadAudit() {
  const response = await fetch("/api/v1/audit?limit=20");
  const rows = await response.json();
  const body = byId("audit-body");
  body.innerHTML = rows.map((item) => `
    <tr>
      <td>${item.request_id.slice(0, 10)}</td>
      <td>${item.role}</td>
      <td>${item.tool}</td>
      <td><span class="mini ${item.decision.toLowerCase()}">${item.decision}</span></td>
      <td>${item.risk_score}</td>
      <td>${new Date(item.created_at).toLocaleString()}</td>
    </tr>
  `).join("");
}

byId("guard-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  let argumentsValue;
  try {
    argumentsValue = JSON.parse(byId("arguments").value || "{}");
  } catch {
    setDecision("DENY");
    byId("reasons").textContent = "Arguments must be valid JSON.";
    return;
  }

  const payload = {
    agent_id: byId("agent_id").value,
    user_id: byId("user_id").value,
    role: byId("role").value,
    task: byId("task").value,
    tool: byId("tool").value,
    arguments: argumentsValue,
  };

  setDecision("CHECKING");
  const response = await fetch("/api/v1/guard/check", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    setDecision("DENY");
    byId("reasons").textContent = JSON.stringify(data, null, 2);
    return;
  }
  setDecision(data.decision);
  byId("risk").textContent = data.risk_score;
  byId("tool-result").textContent = data.tool;
  byId("executed").textContent = data.executed ? "Yes" : "No";
  byId("reasons").textContent = data.reasons.length ? data.reasons.join("\n") : "None";
  byId("findings").textContent = data.findings.length ? JSON.stringify(data.findings, null, 2) : "No findings";
  byId("result").textContent = data.result ? JSON.stringify(data.result, null, 2) : "No tool result";

  const aiSection = byId("ai-section");
  const aiExplanation = byId("ai-explanation");
  const aiThinkingDetails = byId("ai-thinking-details");
  const aiThinking = byId("ai-thinking");

  if (data.explanation) {
    aiSection.classList.remove("hidden");
    aiExplanation.textContent = data.explanation;
  } else {
    aiSection.classList.add("hidden");
  }

  if (data.thinking) {
    aiThinkingDetails.classList.remove("hidden");
    aiThinking.textContent = data.thinking;
    aiThinkingDetails.open = false;
  } else {
    aiThinkingDetails.classList.add("hidden");
  }

  await loadAudit();
});

byId("refresh").addEventListener("click", loadAudit);
loadHealth();
loadAudit();
