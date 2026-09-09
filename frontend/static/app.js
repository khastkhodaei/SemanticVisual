// ==========================================================================
// SemanticDFL Storyboard Simulator - Step 1 & Step 2 Controller
// ACM 2026 Reference Implementation
// ==========================================================================

let currentStep = 1;
let currentSession = null;
let simulationData = {};
let step1Topology = null;
let vrfElectionResult = null;
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
  // Auto-bootstrap Step 1
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
      <div class="flex items-center space-x-2">
        <span class="text-sm">${cls.icon}</span>
        <span class="font-bold text-xs text-slate-800">${cls.name}</span>
        <span class="text-[10px] text-slate-400 font-mono">(C${cid})</span>
      </div>
      <div class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-blue-700 font-semibold">
        Dims ${cls.slice[0]}-${cls.slice[1]}
      </div>
    `;

    // Interactive filter highlight on hover
    item.addEventListener("mouseenter", () => highlightClassNodes(cid));
    item.addEventListener("mouseleave", () => resetNodeHighlights());
    container.appendChild(item);
  }
}

// 1. Initialize Cytoscape Canvas with Clean Paper Styles
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
          "font-size": "10px",
          "font-family": "ui-monospace, monospace",
          "font-weight": "bold",
          "text-valign": "bottom",
          "text-margin-y": 5,
          "text-background-color": "rgba(255, 255, 255, 0.85)",
          "text-background-opacity": 0.9,
          "text-background-padding": 2,
          "text-background-shape": "roundrectangle",
          "background-color": "#2563eb", // Royal blue for clients
          "border-color": "#1d4ed8",
          "border-width": 2,
          "width": 28,
          "height": 28,
          "transition-property": "background-color, border-color, width, height, border-width, opacity",
          "transition-duration": "0.25s"
        }
      },
      {
        selector: "node.initiator-node",
        style: {
          "background-color": "#d97706", // Amber gold for leaders
          "border-color": "#92400e",
          "border-width": 3.5,
          "width": 34,
          "height": 34,
          "color": "#92400e",
          "font-size": "11px",
          "z-index": 80
        }
      },
      {
        selector: "node.highlighted",
        style: {
          "background-color": "#0284c7",
          "border-color": "#0369a1",
          "border-width": 3.5,
          "width": 34,
          "height": 34,
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
          "width": 1.8,
          "line-color": "#94a3b8", // Crisp slate lines for physical links
          "curve-style": "straight",
          "opacity": 0.65,
          "transition-property": "line-color, width, opacity",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: "edge.highlighted",
        style: {
          "line-color": "#2563eb",
          "width": 2.6,
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

  // Node Hover Tooltip
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

  const isInitiator = nodeData.role === "INITIATOR";
  const cardNodeId = document.getElementById("cardNodeId");
  const cardStatusBadge = document.getElementById("cardStatusBadge");

  cardNodeId.textContent = `NODE #C${nodeData.peer_id || nodeData.id}`;
  if (isInitiator) {
    cardNodeId.innerHTML = `<span class="text-amber-700">👑 NODE #C${nodeData.peer_id || nodeData.id}</span>`;
    cardStatusBadge.textContent = "ASSIGNED (INITIATOR)";
    cardStatusBadge.className = "text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300";
  } else {
    cardNodeId.className = "text-blue-700 font-bold text-sm tracking-tight";
    cardStatusBadge.textContent = nodeData.status || "NOT_ASSIGNED";
    cardStatusBadge.className = "text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200";
  }

  const roleElem = document.getElementById("cardRole");
  if (roleElem) {
    roleElem.textContent = nodeData.role || "CLIENT";
    roleElem.className = isInitiator ? "text-amber-800 font-mono font-bold" : "text-slate-800 font-mono font-bold";
  }

  const classId = nodeData.class_id !== undefined ? nodeData.class_id : (nodeData.category_id || 0);
  const cls = DATASET_CLASSES[classId] || { name: "Class", icon: "📦", slice: [0, 4] };

  document.getElementById("cardClass").textContent = `${cls.name} ${cls.icon} (Class ${classId})`;
  document.getElementById("cardSlice").textContent = `Dims [${cls.slice[0]} - ${cls.slice[1]}]`;
  document.getElementById("cardDegree").textContent = `${nodeData.degree || 0} neighbors`;

  const x = nodeData.coords ? Math.round(nodeData.coords.x) : (nodeData.x ? Math.round(nodeData.x) : "-");
  const y = nodeData.coords ? Math.round(nodeData.coords.y) : (nodeData.y ? Math.round(nodeData.y) : "-");
  const cardCoords = document.getElementById("cardCoords");
  if (cardCoords) cardCoords.textContent = `(${x}, ${y})`;

  // Step 2: Show VRF Score if available
  const vrfRow = document.getElementById("cardVrfRow");
  const cardVrf = document.getElementById("cardVrf");
  if (currentStep >= 2 && nodeData.vrf_score !== null && nodeData.vrf_score !== undefined) {
    if (vrfRow) vrfRow.classList.remove("hidden");
    if (cardVrf) cardVrf.textContent = Number(nodeData.vrf_score).toFixed(3);
  } else {
    if (vrfRow) vrfRow.classList.add("hidden");
  }

  // Draw 50D parameter vector preview
  renderTooltipVectorPreview(nodeData.weights || [], classId, isInitiator);

  card.classList.remove("hidden");
}

function hideNodeTooltip() {
  const card = document.getElementById("nodeInfoCard");
  if (card) card.classList.add("hidden");
}

// Render Mini 50-Dimension Vector Bar Chart Preview
function renderTooltipVectorPreview(weights, classId, isInitiator = false) {
  const canvas = document.getElementById("tooltipVectorCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  // Baseline axis
  ctx.strokeStyle = "rgba(203, 213, 225, 0.8)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, height - 4);
  ctx.lineTo(width, height - 4);
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

    const barHeight = Math.max(2, Math.min(height - 6, val * (height - 6)));
    const y = (height - 4) - barHeight;

    if (isActive) {
      ctx.fillStyle = isInitiator ? "#d97706" : "#2563eb";
      ctx.fillRect(x, y, totalBarWidth, barHeight);
      ctx.fillStyle = isInitiator ? "#fef3c7" : "#dbeafe";
      ctx.fillRect(x, y, totalBarWidth, 1.5);
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
  logToTerminal("INIT", "Requesting ground-truth 50-node ad-hoc mesh from backend engine...");

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
    vrfElectionResult = null;

    // Set UI for Step 1
    applyStep1UI(data);

    logToTerminal("SUCCESS", `Step 1 Base Topology deployed: 50 nodes, ${data.edges.length} undirected physical links.`);
    logToTerminal("INFO", "Non-IID Class Allocation: Cat 🐱 (C1, C2, C20, C21, C22, C35 separated across network).");
    logToTerminal("INFO", "Pure overlay-free mesh: All nodes are in CLIENT role with status NOT_ASSIGNED.");

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
    sessionVal.textContent = currentSession.substring(0, 8) + "...";
  }

  // Stepper Indicator
  updateStepper(1);

  // Active step badge & button labels
  const activeBadge = document.getElementById("activeStepBadge");
  if (activeBadge) {
    activeBadge.textContent = "Step 1: Physical Mesh";
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
    btnNext.innerHTML = `<span>Next Step (Step 2: VRF)</span><span>▶️</span>`;
  }

  // Narrative Banner
  document.getElementById("stepTag").textContent = "STEP 1 / FIGURE 3(a)";
  document.getElementById("stepTag").className = "px-2 py-0.5 text-[11px] font-bold font-mono tracking-wide rounded bg-blue-100 text-blue-800";
  document.getElementById("stepTitle").textContent = "Physical Ad-Hoc Network Topology & Non-IID Data Distribution";
  document.getElementById("stepDescription").textContent = "50 decentralized clients in an ad-hoc mesh. Each client holds local data from 1 dataset class. Nodes with identical classes are dispersed across the physical network.";

  // Hide Step 2 specific components
  document.getElementById("formulaBanner").classList.add("hidden");
  document.getElementById("initiatorBox").classList.add("hidden");
  const legendLeader = document.getElementById("legendLeaderItem");
  if (legendLeader) legendLeader.classList.add("hidden");

  // Summary Stats
  document.getElementById("statNodes").textContent = data.nodes ? data.nodes.length : 50;
  if (data.metadata) {
    document.getElementById("statDegree").textContent = `${data.metadata.avg_degree || 3.9} (3-6)`;
  }
  document.getElementById("statLeaders").textContent = "0 Initiators";
  document.getElementById("statLeaders").className = "text-sm font-bold text-slate-400";

  document.getElementById("canvasViewLabel").textContent = `Physical Ad-Hoc Mesh (50 Nodes, ${data.edges.length} Edges)`;

  // Render Step 1 Mesh (All Royal Blue)
  renderMesh(data.nodes, data.edges, false);
}

// 4. API Call: Execute Step 2 (VRF Leader Election)
async function executeStep2VRF() {
  if (!currentSession) {
    await initializeNetwork();
  }

  setNavButtonsDisabled(true);
  logToTerminal("VRF", "Initiating Step 2: Verifiable Random Function (VRF) leader election protocol...");

  try {
    const res = await fetch("/api/v1/step/vrf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSession })
    });

    if (!res.ok) {
      throw new Error(`VRF step failed: ${res.statusText}`);
    }

    const data = await res.json();
    vrfElectionResult = data;
    simulationData = data;

    // Apply Step 2 UI
    applyStep2UI(data);

    // Stream logs to console
    if (data.logs && Array.isArray(data.logs)) {
      data.logs.forEach(l => logToTerminal(l.level || "VRF", l.message));
    }

    logToTerminal("SUCCESS", `Step 2 Complete: 10 Initiators elected deterministically with pairwise hop distance > 2.`);
    logToTerminal("INFO", "Initiators: C2, C7, C13, C17, C22, C28, C32, C37, C42, C47.");

  } catch (err) {
    logToTerminal("ERROR", `Step 2 execution failure: ${err.message}`);
    console.error("VRF Step Error:", err);
  } finally {
    setNavButtonsDisabled(false);
  }
}

// Apply Step 2 UI State
function applyStep2UI(data) {
  currentStep = 2;

  // Stepper Indicator
  updateStepper(2);

  // Active step badge & button labels
  const activeBadge = document.getElementById("activeStepBadge");
  if (activeBadge) {
    activeBadge.textContent = "Step 2: VRF Leader Election";
    activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-100 text-amber-900 border border-amber-300";
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
    btnNext.innerHTML = `<span>Next Step (Step 3: Zones)</span><span>▶️</span>`;
  }

  // Narrative Banner
  document.getElementById("stepTag").textContent = "STEP 2 / VRF ELECTION";
  document.getElementById("stepTag").className = "px-2 py-0.5 text-[11px] font-bold font-mono tracking-wide rounded bg-amber-100 text-amber-800";
  document.getElementById("stepTitle").textContent = "Verifiable Random Function (VRF) Leader Election";
  document.getElementById("stepDescription").textContent = "Each node evaluates a pseudo-random VRF score σ_p. Nodes possessing the local minimum in their 2-hop neighborhood self-promote to INITIATOR to act as zone seeds.";

  // Render KaTeX Formula Banner
  renderKaTeXBanner();

  // Show Initiator Box in Sidebar
  renderInitiatorList(data.initiators || []);

  // Show Leader Legend
  const legendLeader = document.getElementById("legendLeaderItem");
  if (legendLeader) legendLeader.classList.remove("hidden");

  // Update Summary Stats
  document.getElementById("statLeaders").textContent = `${data.initiators ? data.initiators.length : 10} Initiators`;
  document.getElementById("statLeaders").className = "text-sm font-bold text-amber-600";

  document.getElementById("canvasViewLabel").textContent = "VRF Leaders Elected (10 Initiators, 40 Clients)";

  // Update Cytoscape Mesh with Amber Initiators
  renderMesh(data.nodes, step1Topology ? step1Topology.edges : [], true);
}

// Render KaTeX Formula in Banner
function renderKaTeXBanner() {
  const formulaBox = document.getElementById("formulaBanner");
  if (!formulaBox) return;

  formulaBox.classList.remove("hidden");

  const katexContainer = document.getElementById("katexFormula");
  if (katexContainer && window.katex) {
    const texStr = "\\sigma_p = \\text{VRF}_{sk_p}(\\text{seed}_{e-1}), \\quad m_p = \\min_{q \\in N_R(p)} (\\sigma_q, id_q)";
    try {
      window.katex.render(texStr, katexContainer, {
        displayMode: true,
        throwOnError: false
      });
    } catch (e) {
      katexContainer.textContent = "σ_p = VRF_{sk_p}(seed_{e-1}),  m_p = min_{q ∈ N_R(p)} (σ_q, id_q)";
    }
  }
}

// Render List of Elected Initiators in Sidebar
function renderInitiatorList(initiators) {
  const box = document.getElementById("initiatorBox");
  const list = document.getElementById("initiatorList");
  if (!box || !list) return;

  box.classList.remove("hidden");
  list.innerHTML = "";

  initiators.forEach(id => {
    const chip = document.createElement("div");
    chip.className = "px-2 py-1 bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 rounded text-xs font-mono font-bold flex items-center gap-1 cursor-pointer transition-colors";
    chip.innerHTML = `<span>👑</span><span>C${id}</span>`;
    chip.title = `Click to center on Initiator C${id}`;

    chip.addEventListener("click", () => {
      if (!cy) return;
      const target = cy.$(`#node_${id}`);
      if (target.length) {
        cy.animate({
          center: { eles: target },
          zoom: 1.4,
          duration: 400
        });
        target.flashClass("highlighted", 1200);
      }
    });

    list.appendChild(chip);
  });
}

// Stepper Navigation Indicator update
function updateStepper(step) {
  for (let s = 1; s <= 5; s++) {
    const item = document.getElementById(`stepNav${s}`);
    if (!item) continue;

    item.classList.remove("active", "completed", "step-amber");
    if (s < step) {
      item.classList.add("completed");
    } else if (s === step) {
      item.classList.add("active");
      if (step === 2) {
        item.classList.add("step-amber");
      }
    }
  }
}

// Revert from Step 2 to Step 1 smoothly
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
function renderMesh(nodes, edges, showLeaders = false) {
  if (!cy) return;

  const elements = [];

  nodes.forEach(n => {
    const isInitiator = showLeaders && (n.role === "INITIATOR" || n.status === "ASSIGNED");
    const classId = n.class_id !== undefined ? n.class_id : (n.category_id !== undefined ? n.category_id : (n.category || 0));
    const cls = DATASET_CLASSES[classId] || { name: "Node", icon: "📦" };
    
    // Label format: 👑 C{id} in Step 2 for leaders, or C{id}
    const label = isInitiator ? `👑 C${n.id} ${cls.icon}` : `C${n.id} ${cls.icon}`;

    elements.push({
      group: "nodes",
      classes: isInitiator ? "initiator-node" : "",
      data: {
        id: `node_${n.id}`,
        peer_id: n.id,
        label: label,
        status: isInitiator ? "ASSIGNED" : (n.status || "NOT_ASSIGNED"),
        role: isInitiator ? "INITIATOR" : (n.role || "CLIENT"),
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
  else if (level === "VRF" || level === "LEADER") badgeColor = "text-amber-300";

  row.innerHTML = `
    <span class="text-slate-500 select-none">[${timeStr}]</span>
    <span class="${badgeColor} font-bold select-none">[${level}]</span>
    <span class="text-slate-200">${message}</span>
  `;

  terminal.appendChild(row);
  terminal.scrollTop = terminal.scrollHeight;
}
