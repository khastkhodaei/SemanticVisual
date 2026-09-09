// ==========================================================================
// SemanticDFL Storyboard Simulator - Step 1 & Step 2 Controller
// ACM 2026 Reference Implementation
// ==========================================================================

let currentStep = 1;
let currentSession = null;
let simulationData = {};
let step1Topology = null;
let cy = null;

const DATASET_CLASSES = {
  0: { name: "Cat", icon: "🐱", slice: [0, 4] },
  1: { name: "Car", icon: "🚗", slice: [5, 9] },
  2: { name: "Airplane", icon: "✈️", slice: [10, 14] },
  3: { name: "Dog", icon: "🐶", slice: [15, 19] },
  4: { name: "Frog", icon: "🐸", slice: [20, 24] },
  5: { name: "Horse", icon: "🐴", slice: [25, 29] },
  6: { name: "Ship", icon: "🚢", slice: [30, 34] },
  7: { name: "Truck", icon: "🚚", slice: [35, 39] },
  8: { name: "Bird", icon: "🐦", slice: [40, 44] },
  9: { name: "Deer", icon: "🦌", slice: [45, 49] },
};

document.addEventListener("DOMContentLoaded", () => {
  renderClassLegend();
  initCytoscape();
  bindActionButtons();
  // Auto-initialize Step 1
  initializeNetwork();
});

// Render the 10 Dataset Classes in the Left Panel
function renderClassLegend() {
  const container = document.getElementById("classList");
  if (!container) return;

  container.innerHTML = "";
  for (let cid = 0; cid < 10; cid++) {
    const cls = DATASET_CLASSES[cid];
    const item = document.createElement("div");
    item.className = "class-chip text-slate-700";
    item.dataset.classId = cid;

    item.innerHTML = `
      <div class="flex items-center space-x-1.5">
        <span class="text-sm">${cls.icon}</span>
        <span class="font-bold text-[11px] text-slate-800">${cls.name}</span>
        <span class="text-[9px] text-slate-400 font-mono">(C${cid})</span>
      </div>
      <div class="text-[9px] font-mono px-1 py-0.5 rounded bg-slate-100 border border-slate-200 text-blue-700 font-semibold">
        [${cls.slice[0]}-${cls.slice[1]}]
      </div>
    `;

    item.addEventListener("mouseenter", () => highlightClassNodes(cid));
    item.addEventListener("mouseleave", () => resetNodeHighlights());
    container.appendChild(item);
  }
}

// 1. Initialize Cytoscape Canvas with Academic Paper Styling
function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById("cy"),
    elements: [],
    style: [
      {
        selector: "node",
        style: {
          "label": "data(label)",
          "color": "#0f172a",
          "font-size": "9.5px",
          "font-family": "ui-monospace, monospace",
          "font-weight": "bold",
          "text-valign": "bottom",
          "text-margin-y": 4,
          "text-background-color": "rgba(255, 255, 255, 0.90)",
          "text-background-opacity": 0.92,
          "text-background-padding": 2,
          "text-background-shape": "roundrectangle",
          "background-color": "#2563eb", // Royal blue for all clients
          "border-color": "#1d4ed8",
          "border-width": 2,
          "width": 26,
          "height": 26,
          "transition-property": "background-color, border-color, width, height, border-width, opacity",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: "node.step2-node",
        style: {
          "background-color": "#2563eb",
          "border-color": "#0284c7",
          "border-width": 2.5,
          "width": 28,
          "height": 28
        }
      },
      {
        selector: "node.highlighted",
        style: {
          "background-color": "#0284c7",
          "border-color": "#0369a1",
          "border-width": 3.5,
          "width": 32,
          "height": 32,
          "z-index": 99
        }
      },
      {
        selector: "node.dimmed",
        style: {
          "opacity": 0.22
        }
      },
      {
        selector: "edge",
        style: {
          "width": 1.5,
          "line-color": "#64748b", // Clear slate links
          "curve-style": "straight",
          "opacity": 0.50,
          "transition-property": "line-color, width, opacity",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: "edge.highlighted",
        style: {
          "line-color": "#2563eb",
          "width": 2.2,
          "opacity": 0.95,
          "z-index": 50
        }
      },
      {
        selector: "edge.dimmed",
        style: {
          "opacity": 0.12
        }
      }
    ],
    layout: { name: "preset" },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
    minZoom: 0.4,
    maxZoom: 2.5
  });

  // Node Hover Tooltip Interactions
  cy.on("mouseover", "node", (evt) => {
    const n = evt.target.data();
    showNodeTooltip(n);
  });

  cy.on("mouseout", "node", () => {
    hideNodeTooltip();
  });
}

// Show Paper Tooltip Card
function showNodeTooltip(nodeData) {
  const card = document.getElementById("nodeInfoCard");
  if (!card) return;

  const cardNodeId = document.getElementById("cardNodeId");
  const cardStatusBadge = document.getElementById("cardStatusBadge");

  cardNodeId.textContent = `NODE #C${nodeData.peer_id || nodeData.id}`;
  
  if (currentStep >= 2 && nodeData.vrf_score !== null && nodeData.vrf_score !== undefined) {
    cardStatusBadge.textContent = "COMPUTED (Awaiting Exchange)";
    cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200";
  } else {
    cardStatusBadge.textContent = nodeData.status || "NOT_ASSIGNED";
    cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200";
  }

  const roleElem = document.getElementById("cardRole");
  if (roleElem) {
    roleElem.textContent = nodeData.role || "CLIENT";
  }

  const classId = nodeData.class_id !== undefined ? nodeData.class_id : (nodeData.category_id || 0);
  const cls = DATASET_CLASSES[classId] || { name: "Class", icon: "📦", slice: [0, 4] };

  document.getElementById("cardClass").textContent = `${cls.name} ${cls.icon} (Class ${classId})`;
  document.getElementById("cardDegree").textContent = `${nodeData.degree || 0} neighbors`;

  const x = nodeData.coords ? Math.round(nodeData.coords.x) : (nodeData.x ? Math.round(nodeData.x) : "-");
  const y = nodeData.coords ? Math.round(nodeData.coords.y) : (nodeData.y ? Math.round(nodeData.y) : "-");
  const cardCoords = document.getElementById("cardCoords");
  if (cardCoords) cardCoords.textContent = `(${x}, ${y})`;

  // Step 2 VRF Computation Section
  const vrfSection = document.getElementById("cardVrfSection");
  const vrfScoreVal = document.getElementById("cardVrfScoreVal");
  if (currentStep >= 2 && nodeData.vrf_score !== null && nodeData.vrf_score !== undefined) {
    if (vrSection()) vrfSection.classList.remove("hidden");
    if (vrfScoreVal) vrfScoreVal.textContent = Number(nodeData.vrf_score).toFixed(4);
  } else {
    if (vrfSection) vrfSection.classList.add("hidden");
  }

  // Draw 50D parameter vector preview
  renderTooltipVectorPreview(nodeData.weights || [], classId);

  card.classList.remove("hidden");
}

function vrSection() {
  return document.getElementById("cardVrfSection");
}

function hideNodeTooltip() {
  const card = document.getElementById("nodeInfoCard");
  if (card) card.classList.add("hidden");
}

// Render Mini 50-Dimension Vector Bar Chart Preview
function renderTooltipVectorPreview(weights, classId) {
  const canvas = document.getElementById("tooltipVectorCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(203, 213, 225, 0.8)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, height - 3);
  ctx.lineTo(width, height - 3);
  ctx.stroke();

  const numBars = 50;
  const barGap = 1;
  const totalBarWidth = (width - (numBars - 1) * barGap) / numBars;
  const activeStart = classId * 5;
  const activeEnd = activeStart + 5;

  for (let i = 0; i < numBars; i++) {
    const x = i * (totalBarWidth + barGap);
    const val = weights[i] !== undefined ? Math.abs(weights[i]) : 0;
    const isActive = (i >= activeStart && i < activeEnd);

    const barHeight = Math.max(2, Math.min(height - 5, val * (height - 5)));
    const y = (height - 3) - barHeight;

    if (isActive) {
      ctx.fillStyle = "#2563eb";
      ctx.fillRect(x, y, totalBarWidth, barHeight);
      ctx.fillStyle = "#dbeafe";
      ctx.fillRect(x, y, totalBarWidth, 1);
    } else {
      ctx.fillStyle = "#cbd5e1";
      ctx.fillRect(x, y, totalBarWidth, barHeight);
    }
  }
}

// Highlight nodes with specific class
function highlightClassNodes(classId) {
  if (!cy) return;
  cy.batch(() => {
    cy.nodes().forEach(node => {
      const nid = node.data("class_id");
      if (nid === classId) {
        node.addClass("highlighted").removeClass("dimmed");
      } else {
        node.addClass("dimmed").removeClass("highlighted");
      }
    });
    cy.edges().addClass("dimmed");
  });
}

function resetNodeHighlights() {
  if (!cy) return;
  cy.batch(() => {
    cy.nodes().removeClass("highlighted").removeClass("dimmed");
    cy.edges().removeClass("highlighted").removeClass("dimmed");
  });
}

// 2. Action Buttons & Navigation Event Bindings
function bindActionButtons() {
  const btnReset = document.getElementById("btnReset");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      resetToStep1();
    });
  }

  const btnPrev = document.getElementById("btnPrev");
  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      if (currentStep === 2) {
        revertToStep1();
      }
    });
  }

  const btnNext = document.getElementById("btnNext");
  if (btnNext) {
    btnNext.addEventListener("click", () => {
      if (currentStep === 1) {
        executeStep2VRF();
      }
    });
  }

  const btnClearLogs = document.getElementById("btnClearLogs");
  if (btnClearLogs) {
    btnClearLogs.addEventListener("click", () => {
      const logs = document.getElementById("terminalLogs");
      if (logs) logs.innerHTML = '<div class="text-slate-400">[SYSTEM] Terminal logs cleared.</div>';
    });
  }
}

// 3. API Call: Initialize 50-Node Storyboard Network (Step 1)
async function initializeNetwork() {
  setNavButtonsDisabled(true);
  logToTerminal("INIT", "Deploying ground-truth 50-node ad-hoc mesh from backend engine...");

  try {
    const payload = {
      benchmark: "Non-IID 10-Class Storyboard",
      num_nodes: 50,
      d_limit: 0.35,
      r_hops: 2,
      max_zone_size: 10,
      theta: 0.70,
      q: 0.20
    };

    const res = await fetch("/api/v1/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Failed to initialize network: ${res.statusText}`);
    }

    const data = await res.json();
    currentSession = data.session_id;
    simulationData = data;
    step1Topology = JSON.parse(JSON.stringify(data));

    applyStep1UI(data);

    logToTerminal("SUCCESS", `Step 1 Base Topology deployed: 50 nodes, ${data.edges.length} undirected physical links.`);
    logToTerminal("INFO", "Non-IID Class Allocation: Cat 🐱 (C1, C2, C20, C21, C22, C35 separated across network).");
    logToTerminal("INFO", "Pure overlay-free mesh: All nodes in CLIENT role with status NOT_ASSIGNED. VRF scores null.");

  } catch (err) {
    logToTerminal("ERROR", `Initialization failure: ${err.message}`);
    console.error("Initialization Error:", err);
  } finally {
    setNavButtonsDisabled(false);
  }
}

// Apply Step 1 UI State
function applyStep1UI(data) {
  currentStep = 1;

  // Session Badge
  const sessionVal = document.getElementById("sessionVal");
  if (sessionVal) {
    sessionVal.textContent = currentSession ? currentSession.substring(0, 8) + "..." : "Active";
  }

  // Stepper Indicator
  updateStepper(1);

  // Active step badge & button labels
  const activeBadge = document.getElementById("activeStepBadge");
  if (activeBadge) {
    activeBadge.textContent = "Step 1: Physical Mesh Setup";
    activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200";
  }

  const btnPrev = document.getElementById("btnPrev");
  if (btnPrev) {
    btnPrev.disabled = true;
    btnPrev.innerHTML = `<span>◀️</span><span>Previous Step</span>`;
  }

  const btnNext = document.getElementById("btnNext");
  if (btnNext) {
    btnNext.disabled = false;
    btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 shadow-sm transition-colors";
    btnNext.innerHTML = `<span>Next Step (Step 2: VRF Compute)</span><span>▶️</span>`;
  }

  // Narrative Banner
  document.getElementById("stepTag").textContent = "STEP 1 / FIGURE 3(a)";
  document.getElementById("stepTag").className = "px-2 py-0.5 text-[10px] font-bold font-mono tracking-wide rounded bg-blue-100 text-blue-800";
  document.getElementById("stepTitle").textContent = "Physical Ad-Hoc Network Topology & Non-IID Data Distribution";
  document.getElementById("stepDescription").textContent = "50 decentralized clients in an ad-hoc mesh. Each client holds local data from 1 dataset class. VRF scores are uncomputed.";

  // Render Step 1 Formula in Sidebar
  renderSidebarFormula(
    "Network Topology Model",
    "G = (V, E), \\quad \\mathbf{w}_i \\in \\mathbb{R}^{50}",
    "Physical ad-hoc mesh. Each peer holds local dataset samples and a 50-dimensional parameter vector.",
    "Overlay-Free"
  );

  // Summary Stats
  document.getElementById("statNodes").textContent = data.nodes ? data.nodes.length : 50;
  if (data.metadata) {
    document.getElementById("statDegree").textContent = `${data.metadata.avg_degree || 3.9} (3-6)`;
  }
  document.getElementById("statVrfStatus").textContent = "Uncomputed";
  document.getElementById("statVrfStatus").className = "text-xs font-bold text-slate-400";

  document.getElementById("canvasViewLabel").textContent = `Physical Ad-Hoc Mesh (50 Nodes, ${data.edges.length} Edges)`;

  const legendVrf = document.getElementById("vrfComputedLegend");
  if (legendVrf) legendVrf.classList.add("hidden");

  // Render Mesh
  renderMesh(data.nodes, data.edges, false);
}

// 4. API Call: Execute Step 2 (Pure Local VRF Computation)
async function executeStep2VRF() {
  if (!currentSession) {
    await initializeNetwork();
  }

  setNavButtonsDisabled(true);
  logToTerminal("VRF", "Executing Step 2: Local Verifiable Random Function (VRF) score calculation...");

  try {
    const res = await fetch("/api/v1/step/vrf-compute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSession })
    });

    if (!res.ok) {
      throw new Error(`VRF compute step failed: ${res.statusText}`);
    }

    const data = await res.json();
    simulationData = data;

    // Apply Step 2 UI
    applyStep2UI(data);

    // Stream logs to console
    if (data.logs && Array.isArray(data.logs)) {
      data.logs.forEach(l => logToTerminal("VRF", l.message));
    }

    logToTerminal("SUCCESS", "Step 2 Complete: All 50 peers evaluated local verifiable VRF scores σ_p ∈ [0, 1).");
    logToTerminal("INFO", "No messages sent yet. Peers await neighborhood exchange in Step 3.");

  } catch (err) {
    logToTerminal("ERROR", `Step 2 execution failure: ${err.message}`);
    console.error("VRF Compute Error:", err);
  } finally {
    setNavButtonsDisabled(false);
  }
}

// Apply Step 2 UI State (Pure Local Computation)
function applyStep2UI(data) {
  currentStep = 2;

  // Stepper Indicator
  updateStepper(2);

  // Active step badge & button labels
  const activeBadge = document.getElementById("activeStepBadge");
  if (activeBadge) {
    activeBadge.textContent = "Step 2: VRF Local Calculation";
    activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-800 border border-blue-300";
  }

  const btnPrev = document.getElementById("btnPrev");
  if (btnPrev) {
    btnPrev.disabled = false;
    btnPrev.innerHTML = `<span>◀️</span><span>Previous Step (Step 1)</span>`;
  }

  const btnNext = document.getElementById("btnNext");
  if (btnNext) {
    btnNext.disabled = true; // Disabled until Step 3 is implemented
    btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 opacity-50 cursor-not-allowed";
    btnNext.innerHTML = `<span>Next Step (Step 3: Exchange)</span><span>▶️</span>`;
  }

  // Narrative Banner
  document.getElementById("stepTag").textContent = "STEP 2 / LOCAL COMPUTATION";
  document.getElementById("stepTag").className = "px-2 py-0.5 text-[10px] font-bold font-mono tracking-wide rounded bg-blue-100 text-blue-800";
  document.getElementById("stepTitle").textContent = "Local Verifiable Random Function (VRF) Score Calculation";
  document.getElementById("stepDescription").textContent = "Each peer locally computes its verifiable score σ_p using its secret key and epoch seed. No messages are sent and no leaders are elected yet.";

  // Render Step 2 Formula in Sidebar
  renderSidebarFormula(
    "VRF Local Score (Eq. 1)",
    "\\sigma_p = \\text{VRF}_{sk_p}(\\text{seed}_{e-1}) \\in [0, 1)",
    "Peers locally compute a verifiable pseudorandom score using their private key and epoch seed. No messages are sent yet.",
    "Local Computation"
  );

  // Update Summary Stats
  document.getElementById("statVrfStatus").textContent = "50 Evaluated";
  document.getElementById("statVrfStatus").className = "text-xs font-bold text-blue-600";

  document.getElementById("canvasViewLabel").textContent = "VRF Local Calculation (50 Peers, All Roles = CLIENT)";

  const legendVrf = document.getElementById("vrfComputedLegend");
  if (legendVrf) legendVrf.classList.remove("hidden");

  // Render Mesh with VRF scores visible on nodes, preserving exact topology
  renderMesh(data.nodes, step1Topology ? step1Topology.edges : [], true);
}

// Render KaTeX Formula inside the Sidebar Formula Card
function renderSidebarFormula(title, texStr, description, badgeText) {
  const titleEl = document.getElementById("formulaCardTitle");
  if (titleEl) titleEl.textContent = title;

  const badgeEl = document.getElementById("formulaCardBadge");
  if (badgeEl) badgeEl.textContent = badgeText;

  const descEl = document.getElementById("sidebarFormulaDesc");
  if (descEl) descEl.textContent = description;

  const mathEl = document.getElementById("sidebarFormula");
  if (mathEl && window.katex) {
    try {
      window.katex.render(texStr, mathEl, {
        displayMode: true,
        throwOnError: false
      });
    } catch (e) {
      mathEl.textContent = texStr;
    }
  }
}

// Stepper Navigation Indicator update
function updateStepper(step) {
  for (let s = 1; s <= 5; s++) {
    const item = document.getElementById(`stepNav${s}`);
    if (!item) continue;

    item.classList.remove("active", "completed");
    if (s < step) {
      item.classList.add("completed");
    } else if (s === step) {
      item.classList.add("active");
    }
  }
}

// Revert smoothly from Step 2 to Step 1
function revertToStep1() {
  if (!step1Topology) {
    initializeNetwork();
    return;
  }
  applyStep1UI(step1Topology);
  logToTerminal("INFO", "Reverted to Step 1: Physical Ad-Hoc Mesh view.");
}

// Reset everything to Step 1
function resetToStep1() {
  initializeNetwork();
}

function setNavButtonsDisabled(disabled) {
  const btnReset = document.getElementById("btnReset");
  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");

  if (btnReset) btnReset.disabled = disabled;
  if (btnPrev && currentStep === 2) btnPrev.disabled = disabled;
  if (btnNext && currentStep === 1) btnNext.disabled = disabled;
}

// 5. Render Mesh in Cytoscape
function renderMesh(nodes, edges, showScores = false) {
  if (!cy) return;

  const elements = [];

  nodes.forEach(n => {
    const classId = n.class_id !== undefined ? n.class_id : (n.category_id !== undefined ? n.category_id : (n.category || 0));
    const cls = DATASET_CLASSES[classId] || { name: "Node", icon: "📦" };
    
    // In Step 2, display C{id} (σ: {score})
    const scoreStr = (showScores && n.vrf_score !== null && n.vrf_score !== undefined) 
      ? ` (σ:${Number(n.vrf_score).toFixed(3)})` 
      : "";
    const label = `C${n.id}${scoreStr} ${cls.icon}`;

    elements.push({
      group: "nodes",
      classes: showScores ? "step2-node" : "",
      data: {
        id: `node_${n.id}`,
        peer_id: n.id,
        label: label,
        status: n.status || "NOT_ASSIGNED",
        role: "CLIENT", // Strictly CLIENT in Step 2
        class_id: classId,
        category_id: classId,
        class_name: cls.name,
        category_name: cls.name,
        emoji: cls.icon,
        degree: n.degree || 0,
        vrf_score: n.vrf_score !== undefined ? n.vrf_score : null,
        coords: n.coords,
        weights: n.weights || []
      },
      position: {
        x: n.coords ? n.coords.x : 100,
        y: n.coords ? n.coords.y : 100
      }
    });
  });

  // Edges
  edges.forEach((e, idx) => {
    elements.push({
      group: "edges",
      data: {
        id: `edge_${idx}`,
        source: `node_${e.source}`,
        target: `node_${e.target}`,
        distance: e.distance,
        distance_norm: e.distance_norm
      }
    });
  });

  cy.elements().remove();
  cy.add(elements);
  cy.layout({ name: "preset" }).run();
  cy.fit(undefined, 35);
}

// 6. Console Terminal Logger Helper
function logToTerminal(level, message) {
  const terminal = document.getElementById("terminalLogs");
  if (!terminal) return;

  const row = document.createElement("div");
  row.className = "flex items-start space-x-2 font-mono text-[11px] leading-tight";

  const timeStr = new Date().toLocaleTimeString("en-US", { hour12: false });
  let badgeColor = "text-blue-400";

  if (level === "ERROR") badgeColor = "text-rose-400";
  else if (level === "SUCCESS") badgeColor = "text-emerald-400";
  else if (level === "WARN") badgeColor = "text-amber-400";
  else if (level === "VRF") badgeColor = "text-sky-400";

  row.innerHTML = `
    <span class="text-slate-500 select-none">[${timeStr}]</span>
    <span class="${badgeColor} font-bold select-none">[${level}]</span>
    <span class="text-slate-200">${message}</span>
  `;

  terminal.appendChild(row);
  terminal.scrollTop = terminal.scrollHeight;
}
