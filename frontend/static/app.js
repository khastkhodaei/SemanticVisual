// ==========================================================================
// SemanticDFL Storyboard Simulator - 10-Node CIFAR-10 Network
// Ground-Truth Specification from 'backend/scenario_data.json'
// ACM 2026 Reference Implementation
// ==========================================================================

let currentStep = 1;
let currentConfig = null;
let currentStepData = null;
let cy = null;
let activeSelectedNodeId = null;
let activeSelectedNodeData = null;
let activeAnimationId = null;

// CIFAR-10 10-Class Definitions (C1 to C10)
const CIFAR10_CLASSES = {
  1: { id: 1, name: "Airplane", english: "Airplane", icon: "✈️", code: "C1" },
  2: { id: 2, name: "Automobile", english: "Automobile", icon: "🚗", code: "C2" },
  3: { id: 3, name: "Bird", english: "Bird", icon: "🐦", code: "C3" },
  4: { id: 4, name: "Cat", english: "Cat", icon: "🐱", code: "C4" },
  5: { id: 5, name: "Deer", english: "Deer", icon: "🦌", code: "C5" },
  6: { id: 6, name: "Dog", english: "Dog", icon: "🐶", code: "C6" },
  7: { id: 7, name: "Frog", english: "Frog", icon: "🐸", code: "C7" },
  8: { id: 8, name: "Horse", english: "Horse", icon: "🐴", code: "C8" },
  9: { id: 9, name: "Ship", english: "Ship", icon: "🚢", code: "C9" },
  10: { id: 10, name: "Truck", english: "Truck", icon: "🚚", code: "C10" },
  // Backward compatibility alias
  0: { id: 1, name: "Airplane", english: "Airplane", icon: "✈️", code: "C1" },
};

// Ground-Truth 10D Semantic Vectors (L1-Normalized, Σ=1.0) from STEPS.md & storyboard_10nodes.py
const STORYBOARD_10_VECTORS = {
  1: [0.46, 0.17, 0.37, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
  2: [0.19, 0.24, 0.57, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
  3: [0.00, 0.00, 0.00, 0.34, 0.20, 0.46, 0.00, 0.00, 0.00, 0.00],
  4: [0.00, 0.00, 0.00, 0.62, 0.21, 0.17, 0.00, 0.00, 0.00, 0.00],
  5: [0.00, 0.00, 0.00, 0.53, 0.12, 0.35, 0.00, 0.00, 0.00, 0.00],
  6: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.23, 0.19, 0.34, 0.24],
  7: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.11, 0.41, 0.21, 0.27],
  8: [0.00, 0.00, 0.00, 0.32, 0.38, 0.30, 0.00, 0.00, 0.00, 0.00],
  9: [0.45, 0.32, 0.23, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
  10: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.12, 0.43, 0.33, 0.12]
};

// Ground-Truth Deterministic Local VRF Scores from STEPS.md & storyboard_10nodes.py
const STORYBOARD_10_VRF_SCORES = {
  1: 0.1543,
  2: 0.0837,
  3: 0.2318,
  4: 0.0412,
  5: 0.3185,
  6: 0.4721,
  7: 0.3564,
  8: 0.0275,
  9: 0.2947,
  10: 0.4126
};

function getCifarClass(keyOrId) {
  if (typeof keyOrId === "string" && keyOrId.startsWith("C")) {
    const num = parseInt(keyOrId.slice(1), 10);
    return CIFAR10_CLASSES[num] || { id: num, name: keyOrId, icon: "📦", code: keyOrId };
  }
  const num = parseInt(keyOrId, 10);
  return CIFAR10_CLASSES[num] || { id: num, name: `Class ${num}`, icon: "📦", code: `C${num}` };
}

// 10 Distinct Zone Colors for the 10 Nodes
const ZONE_COLOR_MAP = {
  1: "#06b6d4",   // C1: Cyan
  2: "#10b981",   // C2: Green
  3: "#8b5cf6",   // C3: Purple
  4: "#f97316",   // C4: Orange
  5: "#ec4899",   // C5: Pink
  6: "#14b8a6",   // C6: Teal
  7: "#2563eb",   // C7: Blue
  8: "#eab308",   // C8: Yellow
  9: "#6366f1",   // C9: Indigo
  10: "#84cc16",  // C10: Lime
};

function getZoneColor(zone) {
  if (zone === null || zone === undefined) return "#2563eb";
  if (typeof zone === "number") {
    if (ZONE_COLOR_MAP[zone]) return ZONE_COLOR_MAP[zone];
  }
  const str = String(zone).trim();
  const m = str.match(/(\d+)/);
  if (m) {
    const num = parseInt(m[1], 10);
    if (ZONE_COLOR_MAP[num]) return ZONE_COLOR_MAP[num];
  }
  return "#2563eb";
}


document.addEventListener("DOMContentLoaded", async () => {
  initCytoscape();
  bindActionButtons();
  setupPacketCanvas();
  await loadGlobalConfig();
  await loadStep(1);
});

// 1. Initialize Cytoscape.js with strict preset coordinates
function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById("cy"),
    elements: [],
    style: [
      {
        selector: "node",
        style: {
          "label": function(ele) {
            const raw = ele.data("node_id_num") || ele.data("id");
            const clean = String(raw).replace("node_", "").replace("C", "");
            return "C" + clean;
          },
          "color": "#ffffff",
          "font-size": "11px",
          "font-family": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
          "font-weight": "bold",
          "text-valign": "center",
          "text-halign": "center",
          "background-color": "#2563eb",
          "border-color": "#1d4ed8",
          "border-width": 2,
          "width": 32,
          "height": 32,
          "transition-property": "background-color, border-color, width, height, border-width, opacity, shadow-blur, shadow-opacity",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: "node.initiator-node",
        style: {
          "background-color": "#f59e0b",
          "border-color": "#b45309",
          "border-width": 4.5,
          "width": 44,
          "height": 44,
          "color": "#78350f",
          "font-size": "12px",
          "shadow-blur": 22,
          "shadow-color": "#f59e0b",
          "shadow-opacity": 0.9,
          "z-index": 90
        }
      },
      {
        selector: "node.selected-node",
        style: {
          "border-color": "#0284c7",
          "border-width": 5,
          "width": 44,
          "height": 44,
          "z-index": 100
        }
      },
      {
        selector: "node.initiator-node.selected-node",
        style: {
          "border-color": "#78350f",
          "border-width": 5,
          "width": 46,
          "height": 46,
          "z-index": 100
        }
      },
      {
        selector: "node.highlighted",
        style: {
          "background-color": "#2563eb",
          "border-color": "#38bdf8",
          "border-width": 4,
          "width": 38,
          "height": 38,
          "z-index": 95
        }
      },
      {
        selector: "node.dimmed",
        style: {
          "opacity": 0.25
        }
      },
      {
        selector: "edge",
        style: {
          "width": 2,
          "line-color": "#64748b",
          "curve-style": "straight",
          "opacity": 0.6,
          "transition-property": "line-color, width, opacity",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: "edge.boundary-edge",
        style: {
          "line-style": "dashed",
          "line-color": "#f87171",
          "line-dash-pattern": [6, 4],
          "width": 2.6,
          "opacity": 0.95,
          "z-index": 60
        }
      },
      {
        selector: "edge.intra-zone-edge",
        style: {
          "line-style": "solid",
          "line-color": "#475569",
          "width": 2.2,
          "opacity": 0.80
        }
      },
      {
        selector: "edge.wave-active",
        style: {
          "line-color": "#38bdf8",
          "width": 2.8,
          "opacity": 1.0,
          "z-index": 80
        }
      },
      {
        selector: "edge.highlighted",
        style: {
          "line-color": "#2563eb",
          "width": 2.4,
          "opacity": 0.95,
          "z-index": 50
        }
      },
      {
        selector: "edge.dimmed",
        style: {
          "opacity": 0.25
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

  // Transparent lookup wrapper for cy.getElementById supporting String(id), numeric id, and "node_" + id
  const origGetById = cy.getElementById.bind(cy);
  cy.getElementById = function(id) {
    let res = origGetById(id);
    if (res && res.length > 0) return res;
    const s = String(id);
    if (s.startsWith("node_")) {
      res = origGetById(s.replace("node_", ""));
      if (res && res.length > 0) return res;
    } else {
      res = origGetById(`node_${s}`);
      if (res && res.length > 0) return res;
    }
    const num = s.replace(/\D/g, "");
    if (num && num !== s) {
      res = origGetById(num);
      if (res && res.length > 0) return res;
      res = origGetById(`node_${num}`);
      if (res && res.length > 0) return res;
    }
    return res;
  };

  // Click-to-Toggle Node Modal Interaction
  cy.on("tap", "node", (evt) => {
    const node = evt.target;
    const nid = node.data("node_id_num");

    if (activeSelectedNodeId === nid) {
      hideNodeModal();
    } else {
      activeSelectedNodeId = nid;
      activeSelectedNodeData = node.data();
      showNodeModal(node.data());

      // Highlight selected node without dimming other nodes or links
      cy.nodes().removeClass("selected-node");
      node.addClass("selected-node");
    }
  });

  // Tap on background to dismiss modal and restore full canvas opacity
  cy.on("tap", (evt) => {
    if (evt.target === cy) {
      hideNodeModal();
    }
  });

  // Modal close button event
  const btnCloseModal = document.getElementById("btnCloseModal");
  if (btnCloseModal) {
    btnCloseModal.addEventListener("click", hideNodeModal);
  }

  // Handle resize & pan for packet overlay canvas
  cy.on("pan zoom resize", () => {
    syncPacketCanvasSize();
  });
}

// 2. Setup Packet Animation Overlay Canvas
function setupPacketCanvas() {
  window.addEventListener("resize", syncPacketCanvasSize);
  syncPacketCanvasSize();
}

function syncPacketCanvasSize() {
  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const container = cy.container();
  const rect = container.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
}

function stopCurrentPacketAnimation() {
  if (activeAnimationId) {
    cancelAnimationFrame(activeAnimationId);
    activeAnimationId = null;
  }
  const canvas = document.getElementById("packetCanvas");
  if (canvas) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  if (cy) {
    cy.edges().removeClass("wave-active");
  }
}

// 3. Load Global Network Configuration (Sheet 1)
async function loadGlobalConfig() {
  try {
    const res = await fetch("/api/v1/storyboard/config");
    if (!res.ok) throw new Error("Failed to load config");
    const data = await res.json();
    currentConfig = data;
    renderDatasetClassLegend(data.classes || []);

    const statNodes = document.getElementById("statNodes");
    if (statNodes) statNodes.textContent = data.num_nodes || 10;
    const statDegree = document.getElementById("statDegree");
    if (statDegree) statDegree.textContent = `${data.avg_degree || 3.4} (${data.total_edges || 18} links)`;

    const sessionVal = document.getElementById("sessionVal");
    if (sessionVal) sessionVal.textContent = "10-Node CIFAR-10 Storyboard";
  } catch (err) {
    console.error("Config Load Error:", err);
    logToTerminal("ERROR", `Failed to load network configuration: ${err.message}`);
  }
}

// Render Dataset Class Legend in Left Sidebar
// Active Dataset Class Filter State
let activeClassFilterId = null;

// Render Dataset Class Legend in Left Sidebar
function renderDatasetClasses(classes) {
  const container = document.getElementById("classList");
  if (!container) return;
  container.innerHTML = "";

  classes.forEach(cls => {
    const nodeCount = cls.count !== undefined ? cls.count : (cls.clients ? cls.clients.length : 0);
    const classId = cls.id !== undefined ? cls.id : (cls.class_id !== undefined ? cls.class_id + 1 : 0);
    const className = cls.name || cls.english_name || `Class ${classId}`;

    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
      <div class="class-item flex items-center justify-between p-2 rounded hover:bg-slate-100 cursor-pointer border border-transparent transition" data-class-id="${classId}">
        <div class="flex items-center space-x-2">
          <span class="font-bold text-slate-700 text-xs">${className}</span>
          <span class="text-[10px] text-slate-400 font-mono">(C${classId})</span>
        </div>
        <span class="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">${nodeCount} nodes</span>
      </div>
    `;
    const itemEl = wrapper.firstElementChild;
    container.appendChild(itemEl);
  });

  setupClassFilterEvents();
}

function renderDatasetClassLegend(classes) {
  renderDatasetClasses(classes);
}

// 1. Event Listener for Class Items
function setupClassFilterEvents() {
  document.querySelectorAll(".class-item, [data-class-id]").forEach(item => {
    if (item._filterAttached) return;
    item._filterAttached = true;

    item.addEventListener("click", (e) => {
      const target = e.currentTarget;
      const classId = parseInt(target.getAttribute("data-class-id"), 10);
      highlightNodesByClass(classId);
    });
  });
}

// Check if a Cytoscape node holds the given class
function isNodeHoldingClass(n, classId) {
  const d = n.data ? n.data() : n;
  if (!d) return false;

  let classNum;
  if (typeof classId === "string") {
    classNum = parseInt(classId.replace(/[^0-9]/g, ""), 10);
  } else {
    classNum = Number(classId);
  }

  // Determine exact 0-indexed position (0..9) and class code ("C1".."C10")
  const zeroIdx = classNum === 0 ? 0 : classNum - 1;
  const targetClassNum = zeroIdx + 1;
  const classCode = `C${targetClassNum}`;

  // 1. Exact check on data_distribution / distribution (e.g. {"C1": 46, "C2": 17, "C3": 37})
  const dist = d.data_distribution || d.distribution;
  if (dist && typeof dist === "object") {
    if (dist[classCode] !== undefined && Number(dist[classCode]) > 0) {
      return true;
    }
  }

  // 2. Exact check on 10D Vector (e.g. [0.46, 0.17, 0.37, 0.0, ...])
  const vec = d.vector_10d || d.vector || d.normalized_vector || (Array.isArray(d.weights) ? d.weights : null);
  if (Array.isArray(vec)) {
    if (zeroIdx >= 0 && zeroIdx < vec.length && Number(vec[zeroIdx]) > 0.001) {
      return true;
    }
  }

  // 3. Exact check on assigned_classes array (e.g. [0, 1, 2])
  const assigned = d.assigned_classes;
  if (Array.isArray(assigned)) {
    if (assigned.includes(zeroIdx)) {
      return true;
    }
  }

  // 4. Exact check on class_distribution dictionary (keys 0..9)
  const cdist = d.class_distribution;
  if (cdist && typeof cdist === "object") {
    if ((cdist[zeroIdx] !== undefined && Number(cdist[zeroIdx]) > 0) ||
        (cdist[String(zeroIdx)] !== undefined && Number(cdist[String(zeroIdx)]) > 0)) {
      return true;
    }
  }

  return false;
}

// 2. Highlight / Filter Implementation (highlightNodesByClass)
function highlightNodesByClass(classId, forceReapply = false) {
  if (!cy) return;

  // Check if already selected -> if so, clear selection and reset all nodes and edges to default opacity (1.0)
  if (!forceReapply && activeClassFilterId === classId) {
    clearClassFilter();
    return;
  }

  activeClassFilterId = classId;

  // Toggle .active-class-filter on the clicked row in the sidebar
  document.querySelectorAll(".class-item, [data-class-id]").forEach(item => {
    const cid = parseInt(item.getAttribute("data-class-id"), 10);
    if (cid === classId) {
      item.classList.add("active-class-filter", "active-filter");
    } else {
      item.classList.remove("active-class-filter", "active-filter");
    }
  });

  // Find matching nodes holding this class
  const matchingNodes = [];
  const nonMatchingNodes = [];

  cy.nodes().forEach(n => {
    if (isNodeHoldingClass(n, classId)) {
      matchingNodes.push(n);
    } else {
      nonMatchingNodes.push(n);
    }
  });

  // Highlight matching nodes: opacity 1.0, maintain default blue background & sky-blue highlight ring
  matchingNodes.forEach(n => {
    n.removeClass("dimmed").addClass("highlighted");
    n.style({
      "opacity": 1.0,
      "background-color": "#2563eb",
      "border-color": "#38bdf8",
      "border-width": 4,
      "z-index": 100
    });
  });

  // Dim non-matching nodes strictly to opacity 0.25, keeping default blue background
  nonMatchingNodes.forEach(n => {
    n.removeClass("highlighted").addClass("dimmed");
    n.style({
      "opacity": 0.25,
      "background-color": "#2563eb",
      "border-color": "#94a3b8",
      "border-width": 1.5,
      "z-index": 1
    });
  });

  // Update edges: keep connecting matching nodes with network blue, dim others strictly to 0.25
  cy.edges().forEach(e => {
    const src = e.source();
    const tgt = e.target();
    const srcMatch = isNodeHoldingClass(src, classId);
    const tgtMatch = isNodeHoldingClass(tgt, classId);

    if (srcMatch && tgtMatch) {
      e.removeClass("dimmed").addClass("highlighted");
      e.style({
        "opacity": 0.95,
        "line-color": "#3b82f6",
        "width": 2.6,
        "z-index": 50
      });
    } else {
      e.removeClass("highlighted").addClass("dimmed");
      e.style({
        "opacity": 0.25,
        "line-color": "#cbd5e1",
        "width": 1.5,
        "z-index": 1
      });
    }
  });

  logToTerminal("TOPOLOGY", `Filtered by class (ID: ${classId}). ${matchingNodes.length} nodes highlighted.`);
}

function clearClassFilter() {
  activeClassFilterId = null;

  // Clear sidebar chip highlights
  document.querySelectorAll(".class-item, [data-class-id]").forEach(item => {
    item.classList.remove("active-class-filter", "active-filter");
  });

  if (!cy) return;

  // Reset all nodes and edges to uniform full opacity (1.0)
  cy.elements().removeClass("highlighted dimmed");
  cy.nodes().forEach(n => {
    n.removeStyle();
  });
  cy.edges().forEach(e => {
    e.removeStyle();
  });
  cy.fit(undefined, 35);
  logToTerminal("INFO", "Cleared class filter. All 10 nodes restored to full opacity.");
}

// 4. Main Step Loading Function (Steps 1 to 4)
async function loadStep(stepNumber) {
  if (stepNumber < 1 || stepNumber > 4) return;
  setNavButtonsDisabled(true);
  hideNodeModal();
  stopCurrentPacketAnimation();
  clearClassFilter();

  try {
    const res = await fetch(`/api/v1/storyboard/step/${stepNumber}`);
    if (!res.ok) throw new Error(`Step ${stepNumber} fetch failed: ${res.statusText}`);
    const data = await res.json();
    currentStep = stepNumber;
    currentStepData = data;

    updateUIHeaders(data);
    updateStepper(stepNumber);
    updateNavButtons(stepNumber);

    if (data.classes || data.dataset_classes) {
      renderDatasetClasses(data.classes || data.dataset_classes);
    }

    if (stepNumber === 1) {
      renderStep1(data);
    } else if (stepNumber === 2) {
      renderStep2(data);
    } else if (stepNumber === 3) {
      renderStep3(data);
    } else if (stepNumber === 4) {
      renderStep4(data);
    }

    // Stream initial terminal logs
    if (data.terminal_logs && Array.isArray(data.terminal_logs)) {
      data.terminal_logs.forEach(log => {
        let lvl = "INFO";
        if (log.startsWith("[Topology]")) lvl = "TOPOLOGY";
        else if (log.startsWith("[LOCAL TRAINING]")) lvl = "TRAINING";
        else if (log.startsWith("[VRF")) lvl = "VRF";
        else if (log.startsWith("[Algorithm")) lvl = "VRF";
        else if (log.startsWith("[FIRST-WINS]")) lvl = "SUCCESS";
        else if (log.startsWith("[CONFLICT")) lvl = "WARN";
        else if (log.startsWith("[PROBE") || log.startsWith("[Zone")) lvl = "ZONE";
        logToTerminal(lvl, log);
      });
    }

  } catch (err) {
    console.error(`Step ${stepNumber} Error:`, err);
    logToTerminal("ERROR", `Failed loading step ${stepNumber}: ${err.message}`);
  } finally {
    setNavButtonsDisabled(false);
  }
}

// Update Top Headers and Narrative Cards
function updateUIHeaders(data) {
  const step = data.step || currentStep || 1;
  const activeBadge = document.getElementById("activeStepBadge");
  const stepTag = document.getElementById("stepTag");
  const stepTitle = document.getElementById("stepTitle");
  const stepDesc = document.getElementById("stepDescription");

  if (step === 1) {
    if (activeBadge) {
      activeBadge.textContent = "Step 1: Network Creation";
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200";
    }
    if (stepTag) stepTag.textContent = "STEP 1 / NETWORK CREATION";
    if (stepTitle) stepTitle.textContent = "Step 1: Network Creation & Non-IID Data Distribution";
    if (stepDesc) stepDesc.textContent = "10 decentralized edge clients connected via 18 physical ad-hoc links. Each node holds local CIFAR-10 data.";
  } else if (step === 2) {
    if (activeBadge) {
      activeBadge.textContent = "Step 2: Local Vectors";
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-cyan-50 text-cyan-700 border border-cyan-200";
    }
    if (stepTag) stepTag.textContent = "STEP 2 / LOCAL TRAINING & VECTORS";
    if (stepTitle) stepTitle.textContent = "Step 2: Local Training & Normalized 10D Vector Generation";
    if (stepDesc) stepDesc.textContent = "Each client trains on local CIFAR-10 data, outputting a normalized 10-dimensional vector representing class proportions.";
  } else if (step === 3) {
    if (activeBadge) {
      activeBadge.textContent = "Step 3: Local VRF";
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 border border-amber-200";
    }
    if (stepTag) stepTag.textContent = "STEP 3 / LOCAL VRF GENERATION";
    if (stepTitle) stepTitle.textContent = "Step 3: Local VRF Score Calculation";
    if (stepDesc) stepDesc.textContent = "Each peer independently calculates its local VRF score σ_p = VRF(seed_{e-1}) using its private key. Scores are not transmitted or received in this step.";
  } else if (step === 4) {
    if (activeBadge) {
      activeBadge.textContent = "Step 4: Initiator Election";
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-300";
    }
    if (stepTag) stepTag.textContent = "STEP 4 / 1-HOP EXCHANGE & INITIATOR ELECTION";
    if (stepTitle) stepTitle.textContent = "Step 4: 1-Hop Neighbor Score Exchange & Initiator Election";
    if (stepDesc) stepDesc.textContent = "Clients exchange VRF scores with direct 1-hop physical neighbors and elect closed-ball minimums. Nodes 2, 4, and 8 are crowned as Initiators.";
  }
}

// 5. STEP 1: Base Physical Topology & Non-IID Data Distribution
function renderStep1(data) {
  renderSidebarFormula(
    "Step 1: Network Creation & Non-IID Data Distribution",
    "G = (V, E), \\quad |V| = 10, \\quad |E| = 18, \\quad \\sum_{c=1}^{10} \\text{Data}_{i, c} = 100\\%",
    "10 decentralized edge clients connected via 18 physical ad-hoc links. Each node holds local CIFAR-10 data.",
    "Network Creation",
    false
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Physical Ad-Hoc Topology (10 Nodes, 18 Links)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.add("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.textContent = "0 Initiators";
    statLeaders.className = "text-xs font-bold text-slate-400";
  }

  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: false,
    useZoneColors: false,
    showBoundaryEdges: false
  });
}

// 6. STEP 2: Local Training & Normalized 10D Vector Generation
function renderStep2(data) {
  renderSidebarFormula(
    "Local Training & Vector Generation",
    "\\mathbf{w}_i = [C_1, C_2, \\dots, C_{10}], \\quad \\sum_{c=1}^{10} w_{i, c} = 1.0",
    "Each client maps local trained parameter distribution to a 10-dimensional normalized vector representing class proportions.",
    "Step 2: Vectors",
    false
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 2: Local Training & Normalized 10D Vectors (10 Clients)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.add("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.textContent = "0 Initiators (Step 2)";
    statLeaders.className = "text-xs font-bold text-slate-500";
  }

  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: false,
    useZoneColors: false,
    showBoundaryEdges: false
  });
}

// 7. STEP 3: Local VRF Score Calculation (No score transmission)
function renderStep3(data) {
  stopCurrentPacketAnimation();

  renderSidebarFormula(
    "Local VRF Score Calculation",
    "\\sigma_p = \\text{VRF}_{sk_p}(\\text{seed}_{e-1})",
    "Each client calculates its local deterministic VRF score independently. Scores are not transmitted or received from neighbors in this step.",
    "Step 3: Local VRF",
    false,
    "amber"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 3: Local VRF Score Calculation (10 Clients, Independent Scores)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.add("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.textContent = "0 Initiators (Step 3: Local VRF)";
    statLeaders.className = "text-xs font-bold text-slate-500";
  }

  // Render nodes: uniform default neutral client blue, label C{id}, no initiator crown or zone coloring
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: false,
    useZoneColors: false,
    showBoundaryEdges: false
  });
}

// 8. STEP 4: Zone Formation, First-Wins & Probe Conflicts (Algorithm 3)
// Direct Cytoscape Node Color Override exactly matching Algorithm 3 & Sheet 3 specifications
function applyNodeZoneColor(nodeElOrId, nodeData) {
  if (!cy) return;
  let cyNode = null;
  if (typeof nodeElOrId === "object" && nodeElOrId !== null && nodeElOrId.isNode && nodeElOrId.isNode()) {
    cyNode = nodeElOrId;
  } else {
    cyNode = cy.getElementById(String(nodeData ? nodeData.id : nodeElOrId));
  }
  if (!cyNode || !cyNode.isNode || !cyNode.isNode()) return;

  const data = nodeData || cyNode.data() || {};
  const zoneColor = getZoneColor(data.assigned_zone || data.zone_id || data.winner_initiator_id);
  const isInit = !!data.is_initiator;
  const isBnd = !!data.is_boundary;
  const borderColor = isInit ? '#d97706' : (isBnd ? '#f87171' : '#ffffff');
  const borderWidth = isInit ? 4 : (isBnd ? 2.5 : 1.5);

  // Update Cytoscape element data attributes
  cyNode.data("bg_color", zoneColor);
  cyNode.data("border_color", borderColor);
  cyNode.data("border_width", borderWidth);

  // Direct Cytoscape background color override
  cyNode.style({
    'background-color': zoneColor,
    'border-color': borderColor,
    'border-width': borderWidth
  });
}

// Enforce that all 50 nodes are permanently in their assigned zone colors
function applyAllStep4FinalZoneColors(nodes) {
  const list = nodes || currentStepData?.nodes || [];
  list.forEach(nodeData => {
    const el = cy.getElementById(String(nodeData.id));
    if (el && el.isNode()) {
      applyNodeZoneColor(el, nodeData);
    }
  });

  if (cy) {
    cy.edges().forEach(e => {
      if (e.data("is_inter_zone")) {
        e.addClass("boundary-edge");
        e.style({
          "line-style": "dashed",
          "line-color": "#f87171",
          "line-dash-pattern": [6, 4],
          "width": 2.4,
          "opacity": 0.95
        });
      }
    });
  }
}

// 8. Storyboard Step 4: 1-Hop Neighbor Score Exchange & Initiator Election
function renderStep4(data) {
  stopCurrentPacketAnimation();

  renderSidebarFormula(
    "1-Hop Exchange & Initiator Election",
    "m_p = \\min_{q \\in \\mathcal{N}_1(p) \\cup \\{p\\}} (\\sigma_q, id_q), \\quad (\\sigma_p, id_p) == m_p \\rightarrow \\text{Initiator}",
    "Direct 1-hop physical neighbors exchange their VRF scores. Each peer evaluates the closed-ball minimum. Nodes 2, 4, and 8 hold the minimum score in their respective 1-hop balls and elect themselves as Initiators.",
    "Step 4: Election",
    false,
    "amber"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 4: 1-Hop Neighbor Score Exchange & Initiator Election (10 Nodes, 3 Initiators: C2, C4, C8)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.textContent = "3 Initiators (C2, C4, C8)";
    statLeaders.className = "text-xs font-bold text-amber-600";
  }

  // Render nodes: Nodes 2, 4, 8 show Initiator styling (Golden/Amber with glowing halo and crown 👑)
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useZoneColors: false,
    showBoundaryEdges: false
  });

  // Animate 1-hop score packet exchanges along edges exclusively in Step 4
  if (data.packet_exchanges && data.packet_exchanges.length > 0) {
    animateVrfScoreExchangePackets(data.packet_exchanges, data.nodes);
  }
}

// Draw an elegant floating pill badge on HTML5 Canvas
function drawCanvasFloatingBadge(ctx, text, x, y, bgColor, textColor, borderColor) {
  ctx.save();
  ctx.font = "bold 9.5px ui-monospace, monospace";
  const metrics = ctx.measureText(text);
  const paddingX = 6;
  const paddingY = 3.5;
  const w = metrics.width + paddingX * 2;
  const h = 18;
  const rx = x - w / 2;
  const ry = y - h / 2;
  const r = 4;

  ctx.beginPath();
  ctx.moveTo(rx + r, ry);
  ctx.lineTo(rx + w - r, ry);
  ctx.quadraticCurveTo(rx + w, ry, rx + w, ry + r);
  ctx.lineTo(rx + w, ry + h - r);
  ctx.quadraticCurveTo(rx + w, ry + h, rx + w - r, ry + h);
  ctx.lineTo(rx + r, ry + h);
  ctx.quadraticCurveTo(rx, ry + h, rx, ry + h - r);
  ctx.lineTo(rx, ry + r);
  ctx.quadraticCurveTo(rx, ry, rx + r, ry);
  ctx.closePath();

  ctx.fillStyle = bgColor;
  ctx.shadowColor = "rgba(0, 0, 0, 0.15)";
  ctx.shadowBlur = 6;
  ctx.fill();

  if (borderColor) {
    ctx.strokeStyle = borderColor;
    ctx.lineWidth = 1.2;
    ctx.stroke();
  }

  ctx.shadowBlur = 0;
  ctx.fillStyle = textColor;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, x, y + 0.5);
  ctx.restore();
}

// Animate 1-hop VRF score exchange packets along the 18 physical links in Step 3
function animateVrfScoreExchangePackets(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 2400; // ms
  const startTime = performance.now();
  const activeList = packets || [];

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);
    const ease = easeInOutQuad(progress);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    activeList.forEach(pkt => {
      const srcNode = cy.getElementById(String(pkt.from));
      const tgtNode = cy.getElementById(String(pkt.to));
      if (!srcNode || !tgtNode || !srcNode.isNode || !srcNode.isNode() || !tgtNode.isNode || !tgtNode.isNode()) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      // Interpolate position along physical edge
      const curX = p1.x + (p2.x - p1.x) * ease;
      const curY = p1.y + (p2.y - p1.y) * ease;

      // Draw floating score badge
      const scoreStr = Number(pkt.score).toFixed(4);
      drawCanvasFloatingBadge(
        ctx,
        `\u03c3:${scoreStr}`,
        curX,
        curY,
        "rgba(255, 255, 255, 0.96)",
        "#0369a1",
        "#38bdf8"
      );
    });

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      // Loop smoothly after a brief pause if still on Step 3
      setTimeout(() => {
        if (currentStep === 3) {
          animateVrfScoreExchangePackets(packets, allNodes);
        }
      }, 1600);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// Animate PROBE packet flooding in Step 4 across 3 waves with dynamic color morphing
function animateProbeFloodingWaves(waves, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const wave1Packets = waves.wave1 || [];
  const wave2Packets = waves.wave2 || [];
  const wave3Packets = waves.wave3 || [];

  const waveDuration = 1600; // ms per wave
  let currentWaveIndex = 1;
  let waveStartTime = performance.now();

  const morphedNodes = new Set(currentStepData?.initiator_ids || [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]);
  const discoveredBoundaries = new Set();
  const ripples = []; // { x, y, radius, maxRadius, color, alpha }
  const reverseAlerts = []; // { startX, startY, endX, endY, startTime, duration, color }

  function logWaveTransition(waveIdx) {
    if (waveIdx === 1) {
      logToTerminal("ZONE", `[Wave 1] 10 Initiators broadcast PROBE(TTL=3) to ${wave1Packets.length} direct physical neighbors.`);
    } else if (waveIdx === 2) {
      logToTerminal("ZONE", `[Wave 2] Hop 1 peers forward PROBE(TTL=2) to ${wave2Packets.length} 2-hop physical neighbors.`);
    } else if (waveIdx === 3) {
      logToTerminal("ZONE", `[Wave 3] Hop 2 peers forward PROBE(TTL=1) to ${wave3Packets.length} 3-hop boundary interfaces.`);
    }
  }

  logWaveTransition(1);

  function runWaveFrame(now) {
    const elapsed = now - waveStartTime;
    const progress = Math.min(elapsed / waveDuration, 1.0);
    const easeProgress = easeInOutQuad(progress);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let activePackets = [];
    if (currentWaveIndex === 1) activePackets = wave1Packets;
    else if (currentWaveIndex === 2) activePackets = wave2Packets;
    else if (currentWaveIndex === 3) activePackets = wave3Packets;

    // Check impact on nodes when progress >= 0.88
    if (easeProgress >= 0.88) {
      const nodeMap = new Map((allNodes || []).map(n => [n.id, n]));

      activePackets.forEach(pkt => {
        const tgtNode = cy.getElementById(String(pkt.target));
        const p2 = tgtNode && tgtNode.isNode() ? tgtNode.renderedPosition() : null;
        if (!p2) return;

        if (pkt.is_first_wins && !morphedNodes.has(pkt.target)) {
          morphedNodes.add(pkt.target);
          const targetNodeData = nodeMap.get(pkt.target);
          if (targetNodeData) {
            applyNodeZoneColor(tgtNode, targetNodeData);
          } else {
            const zColor = getZoneColor(pkt.initiator);
            tgtNode.data("bg_color", zColor);
            tgtNode.style({
              'background-color': zColor,
              'border-color': '#ffffff',
              'border-width': 1.5
            });
          }
          tgtNode.data("status", `ASSIGNED (Zone C${pkt.initiator})`);

          const zColor = getZoneColor(pkt.initiator);
          ripples.push({
            x: p2.x,
            y: p2.y,
            radius: 10,
            maxRadius: 36,
            color: zColor,
            alpha: 0.95
          });

          if (currentWaveIndex === 1) {
            logToTerminal("SUCCESS", `[HOP 1 ACCEPT] C${pkt.target} adopted Zone C${pkt.initiator} via First-Wins.`);
          } else {
            logToTerminal("SUCCESS", `[HOP ${currentWaveIndex} ACCEPT] C${pkt.target} accepted PROBE from C${pkt.initiator} at Hop ${currentWaveIndex}. Status: ASSIGNED to Zone C${pkt.initiator}.`);
          }
        } else if (pkt.is_conflict) {
          const edgeId = pkt.edge_id || `e${Math.min(pkt.source, pkt.target)}_${Math.max(pkt.source, pkt.target)}`;
          if (!discoveredBoundaries.has(edgeId)) {
            discoveredBoundaries.add(edgeId);
            const edge = cy.getElementById(edgeId);
            if (edge && edge.isEdge()) {
              edge.addClass("boundary-edge");
            }
            ripples.push({
              x: p2.x,
              y: p2.y,
              radius: 8,
              maxRadius: 30,
              color: "#f43f5e",
              alpha: 1.0
            });

            // Algorithm 3 lines 18-19: Dual reverse alerts emitted by frontier node
            const targetNodeData = nodeMap.get(pkt.target);
            const ownInitId = targetNodeData ? targetNodeData.winner_initiator_id : null;
            const compInitId = pkt.initiator;

            // Pulse 1: travels back to Own Initiator
            if (ownInitId) {
              const ownNode = cy.getElementById(`node_${ownInitId}`);
              const pOwn = ownNode && ownNode.isNode() ? ownNode.renderedPosition() : null;
              if (pOwn) {
                reverseAlerts.push({
                  startX: p2.x,
                  startY: p2.y,
                  endX: pOwn.x,
                  endY: pOwn.y,
                  startTime: now,
                  duration: 750,
                  color: "#f59e0b",
                  label: `Alert ➜ Own C${ownInitId}`,
                });
              }
            }

            // Pulse 2: travels back to Competing Initiator
            const compNode = cy.getElementById(`node_${pkt.source}`);
            const pComp = compNode && compNode.isNode() ? compNode.renderedPosition() : null;
            if (pComp) {
              reverseAlerts.push({
                startX: p2.x,
                startY: p2.y,
                endX: pComp.x,
                endY: pComp.y,
                startTime: now,
                duration: 750,
                color: "#f43f5e",
                label: `Alert ➜ Competing C${compInitId}`,
              });
            }

            logToTerminal("WARN", `[NEIGHBOR ALERT] Frontier node C${pkt.target} sent boundary notification to its Initiator C${ownInitId}.`);
            logToTerminal("WARN", `[NEIGHBOR ALERT] Frontier node C${pkt.target} sent boundary notification to competing Initiator C${compInitId}.`);
          }
        }
      });
    }

    // Render traveling forward PROBE packets
    activePackets.forEach(pkt => {
      const srcNode = cy.getElementById(`node_${pkt.source}`);
      const tgtNode = cy.getElementById(`node_${pkt.target}`);
      if (!srcNode || !tgtNode || !srcNode.isNode() || !tgtNode.isNode()) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      const curX = p1.x + (p2.x - p1.x) * easeProgress;
      const curY = p1.y + (p2.y - p1.y) * easeProgress;

      const packetColor = pkt.is_first_wins ? "#10b981" : "#f43f5e";

      ctx.beginPath();
      ctx.arc(curX, curY, 7.5, 0, Math.PI * 2);
      ctx.fillStyle = packetColor;
      ctx.shadowBlur = 10;
      ctx.shadowColor = packetColor;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(curX, curY, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.shadowBlur = 0;
      ctx.fill();
    });

    // Render expanding impact ripples
    for (let i = ripples.length - 1; i >= 0; i--) {
      const r = ripples[i];
      r.radius += 1.4;
      r.alpha -= 0.035;
      if (r.alpha <= 0 || r.radius >= r.maxRadius) {
        ripples.splice(i, 1);
      } else {
        ctx.save();
        ctx.beginPath();
        ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
        ctx.strokeStyle = r.color;
        ctx.lineWidth = 2.5;
        ctx.globalAlpha = Math.max(r.alpha, 0);
        ctx.stroke();
        ctx.restore();
      }
    }

    // Render reverse boundary alerts (Alg 3 L18-L19 dual pulses)
    for (let i = reverseAlerts.length - 1; i >= 0; i--) {
      const a = reverseAlerts[i];
      const aElapsed = now - a.startTime;
      const aProg = Math.min(aElapsed / a.duration, 1.0);
      const easeA = easeInOutQuad(aProg);
      const ax = a.startX + (a.endX - a.startX) * easeA;
      const ay = a.startY + (a.endY - a.startY) * easeA;

      ctx.save();
      ctx.beginPath();
      ctx.arc(ax, ay, 6.0, 0, Math.PI * 2);
      ctx.fillStyle = a.color;
      ctx.shadowBlur = 10;
      ctx.shadowColor = a.color;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(ax, ay, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.shadowBlur = 0;
      ctx.fill();

      if (a.label && aProg > 0.15 && aProg < 0.85) {
        drawCanvasFloatingBadge(
          ctx,
          a.label,
          ax,
          ay - 14,
          a.color === "#f59e0b" ? "rgba(254, 243, 199, 0.98)" : "rgba(255, 241, 242, 0.98)",
          a.color === "#f59e0b" ? "#92400e" : "#9f1239",
          a.color
        );
      }
      ctx.restore();

      if (aProg >= 1.0) {
        reverseAlerts.splice(i, 1);
      }
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runWaveFrame);
    } else {
      // Advance to next wave
      if (currentWaveIndex === 1 && wave2Packets.length > 0) {
        // Enforce all 1-hop receivers visually adopted zone colors
        allNodes.filter(n => n.hops_to_initiator === 1).forEach(n => {
          applyNodeZoneColor(n.id, n);
        });
        currentWaveIndex = 2;
        waveStartTime = performance.now();
        logWaveTransition(2);
        activeAnimationId = requestAnimationFrame(runWaveFrame);
      } else if (currentWaveIndex === 2 && wave3Packets.length > 0) {
        // Enforce all 2-hop receivers visually adopted zone colors
        allNodes.filter(n => n.hops_to_initiator <= 2).forEach(n => {
          applyNodeZoneColor(n.id, n);
        });
        currentWaveIndex = 3;
        waveStartTime = performance.now();
        logWaveTransition(3);
        activeAnimationId = requestAnimationFrame(runWaveFrame);
      } else {
        // Animation finished: Ensure all 50 nodes and boundary edges reflect final state
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        activeAnimationId = null;

        applyAllStep4FinalZoneColors(allNodes);

        const statLeaders = document.getElementById("statLeaders");
        if (statLeaders) {
          statLeaders.textContent = "10 Zones Formed";
        }

        logToTerminal("SUCCESS", "[PROBE Complete] All 50 nodes successfully morphed into 10 semantic zones.");
        logToTerminal("SUCCESS", "[Algorithm 3 L17-L19] 29 boundary bridge interfaces registered with zone initiators.");
      }
    }
  }

  activeAnimationId = requestAnimationFrame(runWaveFrame);
}

function easeInOutQuad(t) {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

// 9. Core Cytoscape Rendering Pipeline
function renderCytoscapeGraph(nodes, edges, options = {}) {
  if (!cy) return;

  const elements = [];

  nodes.forEach(n => {
    const isInit = options.showInitiators && n.is_initiator;
    const domName = n.dominant_class_name || n.class_title || "CIFAR-10";
    const domIcon = n.dominant_class_icon || n.class_icon || "";
    const label = isInit ? `👑 C${n.id}` : `C${n.id}`;

    let bgColor = "#2563eb";
    let borderColor = "#1d4ed8";

    if (options.useZoneColors && n.assigned_zone) {
      bgColor = getZoneColor(n.assigned_zone || n.zone_id || n.winner_initiator_id);
      borderColor = isInit ? "#d97706" : (n.is_boundary ? "#f87171" : "#ffffff");
    } else if (isInit) {
      bgColor = "#f59e0b";
      borderColor = "#b45309";
    }

    elements.push({
      group: "nodes",
      classes: isInit ? "initiator-node" : "",
      data: {
        id: `node_${n.id}`,
        node_id_num: n.id,
        node_id_str: n.node_id || `C${n.id}`,
        label: label,
        role: isInit ? "👑 Initiator" : (n.role || "CLIENT"),
        status: n.status || "NOT_ASSIGNED",
        bg_color: bgColor,
        border_color: borderColor,
        class_id: n.class_id,
        class_title: domName,
        class_icon: domIcon,
        dominant_class: n.dominant_class,
        dominant_class_id: n.dominant_class_id,
        dominant_class_name: domName,
        assigned_classes: n.assigned_classes || [],
        class_distribution: n.class_distribution || {},
        vector_10d: n.vector_10d || n.vector || n.normalized_vector || (Array.isArray(n.weights) ? n.weights : []),
        data_distribution: n.data_distribution || n.distribution || {},
        distribution: n.distribution || n.data_distribution || {},
        vector: n.vector || n.vector_10d || n.normalized_vector || (Array.isArray(n.weights) ? n.weights : null),
        normalized_vector: n.normalized_vector || n.vector_10d || n.vector || (Array.isArray(n.weights) ? n.weights : null),
        sk: n.sk,
        vrf_formula: n.vrf_formula,
        vrf_score: n.vrf_score,
        is_initiator: n.is_initiator,
        assigned_zone: n.assigned_zone,
        zone_color: n.zone_color,
        initiator_color: n.initiator_color,
        hops_to_initiator: n.hops_to_initiator,
        hops_label: n.hops_label,
        neighbors: n.neighbors || [],
        neighbors_str: n.neighbors_str || [],
        scoreboard_3hop: n.scoreboard_3hop,
        decision_result: n.decision_result,
        winner_id: n.winner_id,
        winner_score: n.winner_score,
        winner_initiator: n.winner_initiator,
        winner_initiator_id: n.winner_initiator_id,
        first_wins_text: n.first_wins_text,
        accepted_probe: n.accepted_probe,
        accepted_probe_from: n.accepted_probe_from,
        rejected_probes: n.rejected_probes || n.competing_probes_rejected || [],
        rejected_probe_from: n.rejected_probe_from || [],
        competing_probes_rejected: n.competing_probes_rejected || [],
        forwarded_to: n.forwarded_to || [],
        boundary_notifications_emitted: n.boundary_notifications_emitted || [],
        dual_neighbor_alerts: n.dual_neighbor_alerts || [],
        discovered_neighbor_zones: n.discovered_neighbor_zones || [],
        discovered_neighbor_zone_names: n.discovered_neighbor_zone_names || [],
        is_boundary: n.is_boundary,
        boundary_neighbors: n.boundary_neighbors || [],
        boundary_status: n.boundary_status,
        status_tag: n.status_tag,
      },
      position: {
        x: n.x,
        y: n.y
      }
    });
  });

  edges.forEach((e, idx) => {
    const isBoundary = options.showBoundaryEdges && !!e.is_inter_zone;
    elements.push({
      group: "edges",
      classes: isBoundary ? "boundary-edge" : "intra-zone-edge",
      data: {
        id: e.id || `edge_${idx}`,
        source: `node_${e.source_num || parseInt(e.source.replace('C', ''))}`,
        target: `node_${e.target_num || parseInt(e.target.replace('C', ''))}`,
        is_inter_zone: isBoundary,
      }
    });
  });

  cy.elements().remove();
  cy.add(elements);
  cy.layout({ name: "preset" }).run();
  cy.fit(undefined, 35);

  if (options.useZoneColors) {
    nodes.forEach(n => {
      if (n.assigned_zone) {
        applyNodeZoneColor(n.id, n);
      }
    });
  } else if (options.initiatorColorSeeds) {
    nodes.forEach(n => {
      if (n.is_initiator) {
        applyNodeZoneColor(n.id, n);
      }
    });
  }
}

// 10. Click-to-Toggle Node Details Modal (Strict Step 1 Scope)
function showNodeModal(nodeData) {
  const card = document.getElementById("nodeInfoCard");
  if (!card) return;

  const cardNodeId = document.getElementById("cardNodeId");
  const cardStatusBadge = document.getElementById("cardStatusBadge");
  const cardDegree = document.getElementById("cardDegree");
  const cardNeighbors = document.getElementById("cardNeighbors");
  const distTableBody = document.getElementById("cardDataDistributionTableBody");

  const idNum = nodeData.node_id_num || nodeData.id;

  // Header: Node C{id}
  if (cardNodeId) {
    cardNodeId.innerHTML = `<span class="text-blue-700 font-bold font-mono text-sm">Node C${idNum}</span>`;
  }

  // Status: NOT_ASSIGNED
  if (cardStatusBadge) {
    cardStatusBadge.textContent = nodeData.status || "NOT_ASSIGNED";
    cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200";
  }

  // Direct physical neighbors list
  const neighArr = (nodeData.neighbors_str && nodeData.neighbors_str.length)
    ? nodeData.neighbors_str
    : (nodeData.neighbors || []).map(x => `C${x}`);

  if (cardDegree) {
    const deg = neighArr.length;
    cardDegree.textContent = `${deg} neighbor${deg === 1 ? '' : 's'}`;
  }
  if (cardNeighbors) {
    cardNeighbors.textContent = neighArr.length ? neighArr.join(", ") : "None";
  }

  // Local Data Distribution: Clean percentage table showing ONLY classes this client actually holds
  // In Steps 2, 3, and 4, remove redundant data percentage from node information box to free up space (Issue #1)
  const distSection = document.getElementById("cardDataDistributionSection");
  if (currentStep >= 2) {
    if (distSection) distSection.classList.add("hidden");
  } else {
    if (distSection) distSection.classList.remove("hidden");
    if (distTableBody) {
      distTableBody.innerHTML = "";
      const dist = nodeData.data_distribution || nodeData.distribution || {};
      const entries = Object.entries(dist).filter(([_, pct]) => Number(pct) > 0);

      if (entries.length === 0) {
        distTableBody.innerHTML = '<tr><td colspan="3" class="py-1 px-2 text-slate-400 italic">No local distribution data</td></tr>';
      } else {
        entries.forEach(([clsKey, pct]) => {
          const clsInfo = getCifarClass(clsKey);
          const tr = document.createElement("tr");
          tr.className = "hover:bg-slate-50 transition-colors";
          tr.innerHTML = `
            <td class="py-1.5 px-2 font-bold text-blue-700 font-mono">${clsKey}</td>
            <td class="py-1.5 px-2 text-slate-800 font-sans font-medium">${clsInfo.name}</td>
            <td class="py-1.5 px-2 text-right font-mono">
              <span class="inline-block px-1.5 py-0.5 rounded font-bold text-slate-900 bg-slate-100 border border-slate-200">${pct}%</span>
            </td>
          `;
          distTableBody.appendChild(tr);
        });
      }
    }
  }

  // Step 2 & Step 3: Normalized 10D Semantic Vector (w_i) - Kept in Step 3 per Issue #2
  const vectorSection = document.getElementById("cardVectorSection");
  const vectorArrayEl = document.getElementById("cardVectorArray");
  const vectorBreakdownBody = document.getElementById("cardVectorBreakdownBody");

  if (currentStep === 2 || currentStep === 3) {
    if (cardStatusBadge && currentStep === 2) {
      cardStatusBadge.textContent = "LOCAL_TRAINED";
      cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-cyan-50 text-cyan-800 border border-cyan-300";
    }

    if (vectorSection) vectorSection.classList.remove("hidden");

    let vec = nodeData.vector_10d || nodeData.normalized_vector || nodeData.vector;
    if (!vec || !Array.isArray(vec) || vec.length === 0) {
      vec = STORYBOARD_10_VECTORS[idNum] || [];
    }

    if (vectorArrayEl) {
      vectorArrayEl.textContent = `[${vec.map(v => Number(v).toFixed(2)).join(", ")}]`;
    }

    if (vectorBreakdownBody) {
      vectorBreakdownBody.innerHTML = "";
      vec.forEach((val, idx) => {
        const classId = idx + 1;
        const cls = getCifarClass(classId);
        const numVal = Number(val);
        const tr = document.createElement("tr");
        tr.className = numVal > 0
          ? "bg-cyan-50/40 hover:bg-cyan-50 font-semibold transition-colors"
          : "text-slate-400 hover:bg-slate-50 transition-colors";
        tr.innerHTML = `
          <td class="py-1 px-2 font-mono ${numVal > 0 ? "text-cyan-700 font-bold" : "text-slate-400"}">C${classId}</td>
          <td class="py-1 px-2 font-sans ${numVal > 0 ? "text-slate-800" : "text-slate-400"}">${cls.name}</td>
          <td class="py-1 px-2 text-right font-mono">
            <span class="inline-block px-1.5 py-0.2 rounded ${numVal > 0 ? "bg-cyan-100 text-cyan-900 border border-cyan-300 font-bold" : "bg-slate-100 text-slate-400"}">${numVal.toFixed(2)}</span>
          </td>
        `;
        vectorBreakdownBody.appendChild(tr);
      });
    }
  } else {
    if (vectorSection) vectorSection.classList.add("hidden");
  }

  // Step 3 & Step 4: Local VRF Score & 1-Hop Neighborhood Scoreboard / Initiator Election
  const vrfSection = document.getElementById("cardVrfSection");
  const vrfBadge = document.getElementById("cardVrfScoreBadge");
  const scoreboardContainer = document.getElementById("cardNeighborhoodScoreboardContainer");
  const scoreboardBody = document.getElementById("cardNeighborhoodScoreboardBody");
  const electionBanner = document.getElementById("cardElectionBanner");
  const scoreboardTitle = document.getElementById("cardScoreboardTitle");
  const scoreboardSubtitle = document.getElementById("cardScoreboardSubtitle");

  if (currentStep === 3 || currentStep === 4) {
    if (vrfSection) vrfSection.classList.remove("hidden");

    // Self VRF Score
    const selfScore = (nodeData.vrf_score !== undefined && nodeData.vrf_score !== null)
      ? Number(nodeData.vrf_score)
      : (STORYBOARD_10_VRF_SCORES[idNum] !== undefined ? STORYBOARD_10_VRF_SCORES[idNum] : null);

    if (vrfBadge) {
      vrfBadge.textContent = selfScore !== null ? `\u03c3_self = ${selfScore.toFixed(4)}` : "N/A";
    }

    if (currentStep === 3) {
      // Step 3: Only local score calculation. Keep Step 2 node info + local VRF score.
      // Remove Received Scores section (Issue #2)
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "VRF_COMPUTED";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-300";
      }
      if (electionBanner) electionBanner.classList.add("hidden");
      if (scoreboardContainer) scoreboardContainer.classList.add("hidden");
    } else if (currentStep === 4) {
      // Step 4: 1-Hop Neighbor Score Exchange & Election
      if (scoreboardContainer) scoreboardContainer.classList.remove("hidden");
      const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
      const winnerId = nodeData.winner_id || (idNum === 1 ? 4 : idNum === 2 ? 2 : idNum === 3 ? 2 : idNum === 4 ? 4 : idNum === 5 ? 4 : idNum === 6 ? 8 : idNum === 7 ? 4 : idNum === 8 ? 8 : idNum === 9 ? 8 : 8);
      const minScore = (nodeData.min_score !== undefined && nodeData.min_score !== null)
        ? Number(nodeData.min_score)
        : STORYBOARD_10_VRF_SCORES[winnerId];

      if (cardStatusBadge) {
        if (isInitiator) {
          cardStatusBadge.textContent = "👑 INITIATOR";
          cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-400 font-bold";
        } else {
          cardStatusBadge.textContent = "CANDIDATE";
          cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200";
        }
      }

      // Decision banner:
      // Nodes 2, 4, 8: 🏆 Self-Elected Initiator (Holds minimum score in 1-hop ball).
      // Others: Candidate Member (Minimum held by C{winner_id} with σ={min_score}).
      if (electionBanner) {
        electionBanner.classList.remove("hidden");
        if (isInitiator) {
          electionBanner.className = "mt-2 p-2 rounded-lg text-[10.5px] font-bold bg-amber-50 text-amber-900 border border-amber-300 flex items-center gap-1.5 shadow-xs";
          electionBanner.innerHTML = `<span>🏆</span><span>Self-Elected Initiator (Holds minimum score in 1-hop ball)</span>`;
        } else {
          electionBanner.className = "mt-2 p-2 rounded-lg text-[10px] font-semibold bg-slate-50 text-slate-700 border border-slate-200 leading-snug";
          electionBanner.innerHTML = `<div>Candidate Member</div><div class="text-[9.5px] text-slate-500 font-normal">Minimum held by <span class="font-bold font-mono text-amber-800">C${winnerId}</span> with &sigma;=<span class="font-bold font-mono text-amber-800">${minScore.toFixed(4)}</span></div>`;
        }
      }

      if (scoreboardTitle) scoreboardTitle.textContent = "1-Hop Comparison (Closed Ball):";
      if (scoreboardSubtitle) scoreboardSubtitle.textContent = "min(\u03c3_q, id_q)";

      // Build table with self + neighbor scores, highlighting winning minimum in bold gold
      if (scoreboardBody) {
        scoreboardBody.innerHTML = "";

        const participants = [];
        // Add self
        participants.push({
          id: idNum,
          label: `C${idNum} (Self)`,
          score: selfScore,
          is_min: (idNum === winnerId),
          is_self: true
        });

        // Add neighbors
        const scoreboard = nodeData.neighbor_scoreboard || [];
        if (scoreboard.length > 0) {
          scoreboard.forEach(item => {
            const nbId = item.neighbor_id || parseInt(String(item.label).replace("C", ""), 10);
            participants.push({
              id: nbId,
              label: `C${nbId}`,
              score: Number(item.vrf_score),
              is_min: (nbId === winnerId),
              is_self: false
            });
          });
        } else if (nodeData.neighbor_scores) {
          Object.entries(nodeData.neighbor_scores).forEach(([nbKey, score]) => {
            const nbId = parseInt(String(nbKey).replace("C", ""), 10);
            participants.push({
              id: nbId,
              label: `C${nbId}`,
              score: Number(score),
              is_min: (nbId === winnerId),
              is_self: false
            });
          });
        }

        participants.forEach(p => {
          const tr = document.createElement("tr");
          if (p.is_min) {
            tr.className = "bg-amber-100/80 text-amber-950 font-bold border-l-2 border-amber-500 transition-colors";
            tr.innerHTML = `
              <td class="py-1 px-2 font-mono flex items-center gap-1 text-amber-900">
                <span>🏆</span><span>${p.label}</span>
              </td>
              <td class="py-1 px-2 text-right font-mono text-amber-950">
                <span class="inline-block px-1.5 py-0.2 rounded bg-amber-200/80 border border-amber-400 font-bold">${p.score.toFixed(4)} (Min)</span>
              </td>
            `;
          } else {
            tr.className = "hover:bg-slate-50 transition-colors";
            tr.innerHTML = `
              <td class="py-1 px-2 font-mono ${p.is_self ? 'font-bold text-slate-800' : 'text-slate-600'}">${p.label}</td>
              <td class="py-1 px-2 text-right font-mono text-slate-800">
                <span class="inline-block px-1.5 py-0.2 rounded bg-slate-100 border border-slate-200">${p.score.toFixed(4)}</span>
              </td>
            `;
          }
          scoreboardBody.appendChild(tr);
        });
      }
    }
  } else {
    if (vrfSection) vrfSection.classList.add("hidden");
  }

  card.classList.remove("hidden");
}

function hideNodeModal() {
  const card = document.getElementById("nodeInfoCard");
  if (card) card.classList.add("hidden");
  activeSelectedNodeId = null;
  activeSelectedNodeData = null;
  if (cy) {
    cy.nodes().removeClass("selected-node");
    if (activeClassFilterId !== null) {
      highlightNodesByClass(activeClassFilterId, true);
    } else {
      cy.elements().removeClass("dimmed highlighted selected-node");
      cy.nodes().forEach(n => {
        n.removeStyle();
      });
      cy.edges().forEach(e => {
        e.removeStyle();
      });
    }
  }
}



// Focused Slow-Mo Packet Tracer for Clicked Node (Requirement 3 & 4)
function replaySlowMoNodeTrace(nodeData) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const nid = nodeData.node_id_num;
  const centerNode = cy.getElementById(`node_${nid}`);
  if (!centerNode || !centerNode.isNode()) return;

  const isInit = nodeData.is_initiator;
  const acc = nodeData.accepted_probe;
  const rejections = nodeData.rejected_probes || [];
  const forwards = nodeData.forwarded_to || [];
  const bndAlerts = nodeData.boundary_notifications_emitted || [];

  const totalDuration = 3800; // ms
  const startTime = performance.now();

  logToTerminal("ZONE", `[Slow-Mo Tracer] Focusing packet trace on C${nid} (${nodeData.class_title})...`);

  function runSlowMoFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / totalDuration, 1.0);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerPos = centerNode.renderedPosition();

    // -------------------------------------------------------------
    // Phase 1: Incoming Accepted Probe (0 to 1500ms)
    // -------------------------------------------------------------
    if (elapsed < 1500) {
      const p1Progress = Math.min(elapsed / 1200, 1.0);
      const ease1 = easeInOutQuad(p1Progress);

      if (isInit) {
        const pulseR = 20 + Math.sin(elapsed / 140) * 5;
        ctx.beginPath();
        ctx.arc(centerPos.x, centerPos.y, pulseR, 0, Math.PI * 2);
        ctx.strokeStyle = "#f59e0b";
        ctx.lineWidth = 3;
        ctx.stroke();

        drawCanvasFloatingBadge(
          ctx,
          "👑 Zone Initiator (Root Seed)",
          centerPos.x,
          centerPos.y - 30,
          "rgba(254, 243, 199, 0.98)",
          "#92400e",
          "#f59e0b"
        );
      } else if (acc && acc.sender_id) {
        const senderNode = cy.getElementById(`node_${acc.sender_id}`);
        if (senderNode && senderNode.isNode()) {
          const sPos = senderNode.renderedPosition();
          const curX = sPos.x + (centerPos.x - sPos.x) * ease1;
          const curY = sPos.y + (centerPos.y - sPos.y) * ease1;

          ctx.beginPath();
          ctx.moveTo(sPos.x, sPos.y);
          ctx.lineTo(curX, curY);
          ctx.strokeStyle = "rgba(16, 185, 129, 0.75)";
          ctx.lineWidth = 3;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(curX, curY, 8, 0, Math.PI * 2);
          ctx.fillStyle = "#10b981";
          ctx.shadowBlur = 12;
          ctx.shadowColor = "#10b981";
          ctx.fill();

          ctx.beginPath();
          ctx.arc(curX, curY, 4, 0, Math.PI * 2);
          ctx.fillStyle = "#ffffff";
          ctx.shadowBlur = 0;
          ctx.fill();

          if (p1Progress < 0.9) {
            drawCanvasFloatingBadge(
              ctx,
              `INCOMING PROBE (${acc.from_initiator})`,
              curX,
              curY - 18,
              "rgba(236, 253, 245, 0.98)",
              "#065f46",
              "#10b981"
            );
          } else {
            drawCanvasFloatingBadge(
              ctx,
              `✓ Accepted (First-Wins) from Zone ${acc.from_initiator}`,
              centerPos.x,
              centerPos.y - 30,
              "rgba(236, 253, 245, 0.98)",
              "#047857",
              "#10b981"
            );
          }
        }
      }
    }

    // -------------------------------------------------------------
    // Phase 2: Competing Probes Rejected (1200 to 2600ms)
    // -------------------------------------------------------------
    if (elapsed >= 1200 && elapsed < 2600 && rejections.length > 0) {
      const p2Progress = Math.min((elapsed - 1200) / 1100, 1.0);
      const ease2 = easeInOutQuad(p2Progress);

      rejections.forEach((rej, idx) => {
        const sndId = rej.sender_id || parseInt((rej.sender || "").replace("C", ""));
        const sndNode = cy.getElementById(`node_${sndId}`);
        if (!sndNode || !sndNode.isNode()) return;

        const sPos = sndNode.renderedPosition();
        const curX = sPos.x + (centerPos.x - sPos.x) * ease2;
        const curY = sPos.y + (centerPos.y - sPos.y) * ease2;

        ctx.save();
        ctx.beginPath();
        ctx.setLineDash([5, 4]);
        ctx.moveTo(sPos.x, sPos.y);
        ctx.lineTo(curX, curY);
        ctx.strokeStyle = "rgba(244, 63, 94, 0.85)";
        ctx.lineWidth = 2.5;
        ctx.stroke();
        ctx.restore();

        ctx.beginPath();
        ctx.arc(curX, curY, 7.5, 0, Math.PI * 2);
        ctx.fillStyle = "#f43f5e";
        ctx.shadowBlur = 10;
        ctx.shadowColor = "#f43f5e";
        ctx.fill();

        ctx.beginPath();
        ctx.arc(curX, curY, 3.5, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.shadowBlur = 0;
        ctx.fill();

        if (p2Progress < 0.9) {
          drawCanvasFloatingBadge(
            ctx,
            `COMPETING PROBE (${rej.competing_initiator})`,
            curX,
            curY - 18,
            "rgba(255, 241, 242, 0.98)",
            "#9f1239",
            "#f43f5e"
          );
        } else {
          drawCanvasFloatingBadge(
            ctx,
            `✕ Dropped Competing Probe from Zone ${rej.competing_initiator}`,
            centerPos.x,
            centerPos.y + 26 + idx * 20,
            "rgba(255, 241, 242, 0.98)",
            "#be123c",
            "#f43f5e"
          );
        }
      });
    }

    // -------------------------------------------------------------
    // Phase 3: Outgoing Forwards & Boundary Alerts (2400 to 3800ms)
    // -------------------------------------------------------------
    if (elapsed >= 2400) {
      const p3Progress = Math.min((elapsed - 2400) / 1200, 1.0);
      const ease3 = easeInOutQuad(p3Progress);

      forwards.forEach(f => {
        const tgtNode = cy.getElementById(`node_${f.target_id}`);
        if (!tgtNode || !tgtNode.isNode()) return;

        const tPos = tgtNode.renderedPosition();
        const curX = centerPos.x + (tPos.x - centerPos.x) * ease3;
        const curY = centerPos.y + (tPos.y - centerPos.y) * ease3;

        ctx.beginPath();
        ctx.moveTo(centerPos.x, centerPos.y);
        ctx.lineTo(curX, curY);
        ctx.strokeStyle = "rgba(59, 130, 246, 0.7)";
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(curX, curY, 6.5, 0, Math.PI * 2);
        ctx.fillStyle = "#3b82f6";
        ctx.shadowBlur = 8;
        ctx.shadowColor = "#3b82f6";
        ctx.fill();

        if (p3Progress < 0.85) {
          drawCanvasFloatingBadge(
            ctx,
            `➜ Forwarding PROBE(TTL=${3 - f.hop})`,
            curX,
            curY - 16,
            "rgba(239, 246, 255, 0.98)",
            "#1e40af",
            "#3b82f6"
          );
        }
      });

      // Algorithm 3 lines 18-19: Dual reverse alerts emitted in slow-mo
      const dualAlerts = nodeData.dual_neighbor_alerts || [];
      if (dualAlerts.length > 0) {
        dualAlerts.forEach(da => {
          const toId = da.to_initiator_id;
          const targetNode = cy.getElementById(`node_${toId}`);
          const tPos = targetNode && targetNode.isNode() ? targetNode.renderedPosition() : centerPos;

          const curX = centerPos.x + (tPos.x - centerPos.x) * ease3;
          const curY = centerPos.y + (tPos.y - centerPos.y) * ease3;
          const isOwn = (da.target_type === "OWN_INITIATOR");
          const pulseColor = isOwn ? "#f59e0b" : "#f43f5e";

          ctx.beginPath();
          ctx.arc(curX, curY, 6.5, 0, Math.PI * 2);
          ctx.fillStyle = pulseColor;
          ctx.shadowBlur = 10;
          ctx.shadowColor = pulseColor;
          ctx.fill();

          if (p3Progress < 0.88) {
            drawCanvasFloatingBadge(
              ctx,
              isOwn ? `⚡ Alert ➜ Own ${da.to_initiator}` : `⚡ Alert ➜ Competing ${da.to_initiator}`,
              curX,
              curY - 18,
              isOwn ? "rgba(254, 243, 199, 0.98)" : "rgba(255, 241, 242, 0.98)",
              isOwn ? "#92400e" : "#9f1239",
              pulseColor
            );
          }
        });
      } else {
        bndAlerts.forEach(b => {
          const parentId = acc?.sender_id || (isInit ? nid : null);
          if (!parentId) return;
          const parentNode = cy.getElementById(`node_${parentId}`);
          const pPos = parentNode && parentNode.isNode() ? parentNode.renderedPosition() : centerPos;

          const curX = centerPos.x + (pPos.x - centerPos.x) * ease3;
          const curY = centerPos.y + (pPos.y - centerPos.y) * ease3;

          ctx.beginPath();
          ctx.arc(curX, curY, 6, 0, Math.PI * 2);
          ctx.fillStyle = "#8b5cf6";
          ctx.shadowBlur = 10;
          ctx.shadowColor = "#8b5cf6";
          ctx.fill();

          if (p3Progress < 0.9) {
            drawCanvasFloatingBadge(
              ctx,
              `⚡ Reverse Alert to ${b.to_initiator}`,
              curX,
              curY - 18,
              "rgba(250, 245, 255, 0.98)",
              "#6b21a8",
              "#8b5cf6"
            );
          }
        });
      }
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runSlowMoFrame);
    } else {
      setTimeout(() => {
        if (activeSelectedNodeId === nid) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }, 1600);
      activeAnimationId = null;
    }
  }

  activeAnimationId = requestAnimationFrame(runSlowMoFrame);
}

// 11. Render KaTeX Math Formula in Sidebar HUD
function renderSidebarFormula(title, texStr, description, badgeText, isAmber = false, theme = null) {
  const cardEl = document.getElementById("sidebarFormulaCard");
  if (cardEl) {
    cardEl.classList.remove("formula-amber", "formula-purple");
    if (theme === "purple") {
      cardEl.classList.add("formula-purple");
    } else if (isAmber) {
      cardEl.classList.add("formula-amber");
    }
  }

  const titleEl = document.getElementById("formulaCardTitle");
  if (titleEl) titleEl.textContent = title;

  const badgeEl = document.getElementById("formulaCardBadge");
  if (badgeEl) {
    badgeEl.textContent = badgeText;
    if (theme === "purple") {
      badgeEl.className = "text-[9px] font-mono font-bold text-purple-800 bg-purple-100 px-1.5 py-0.5 rounded border border-purple-300";
    } else if (isAmber) {
      badgeEl.className = "text-[9px] font-mono font-bold text-amber-800 bg-amber-100 px-1.5 py-0.5 rounded border border-amber-300";
    } else {
      badgeEl.className = "text-[9px] font-mono font-bold text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded";
    }
  }

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

// 12. Stepper & Navigation Buttons
function updateStepper(step) {
  for (let s = 1; s <= 4; s++) {
    const item = document.getElementById(`stepNav${s}`);
    if (!item) continue;

    item.classList.remove("active", "completed", "step-amber", "step-purple");
    if (s < step) {
      item.classList.add("completed");
    } else if (s === step) {
      item.classList.add("active");
      if (step === 3 || step === 4) {
        item.classList.add("step-amber");
      }
    }
  }
}

function updateNavButtons(step) {
  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");
  const btnReset = document.getElementById("btnReset");

  if (btnReset) {
    btnReset.disabled = false;
  }

  if (btnPrev) {
    if (step > 1) {
      btnPrev.disabled = false;
      btnPrev.className = "btn-secondary px-3.5 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 hover:bg-slate-100 cursor-pointer transition-colors";
      btnPrev.innerHTML = `<span>◀️</span><span>Previous Step</span>`;
      btnPrev.title = `Return to Step ${step - 1}`;
    } else {
      btnPrev.disabled = true;
      btnPrev.className = "btn-secondary px-3.5 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 opacity-50 cursor-not-allowed";
      btnPrev.innerHTML = `<span>◀️</span><span>Previous Step</span>`;
      btnPrev.title = "Already at initial Step 1";
    }
  }

  if (btnNext) {
    if (step < 4) {
      btnNext.disabled = false;
      btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 hover:bg-blue-700 cursor-pointer transition-colors shadow-sm";
      btnNext.innerHTML = `<span>Next Step (Step ${step + 1})</span><span>▶️</span>`;
      btnNext.title = `Advance to Step ${step + 1}`;
    } else {
      btnNext.disabled = true;
      btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 opacity-50 cursor-not-allowed";
      btnNext.title = "Step 4 active (Initiator Election complete)";
      btnNext.innerHTML = `<span>Next Step</span><span>🔒</span>`;
    }
  }
}

function setNavButtonsDisabled(disabled) {
  const btnReset = document.getElementById("btnReset");
  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");

  if (btnReset) btnReset.disabled = disabled;
  if (btnPrev) btnPrev.disabled = disabled || (currentStep <= 1);
  if (btnNext) btnNext.disabled = disabled || (currentStep >= 4);
}

function bindActionButtons() {
  const btnReset = document.getElementById("btnReset");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      loadStep(1);
    });
  }

  const btnPrev = document.getElementById("btnPrev");
  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      if (currentStep > 1) {
        loadStep(currentStep - 1);
      }
    });
  }

  const btnNext = document.getElementById("btnNext");
  if (btnNext) {
    btnNext.addEventListener("click", (e) => {
      e.preventDefault();
      if (currentStep < 4) {
        loadStep(currentStep + 1);
      } else {
        logToTerminal("INFO", "Step 4 is active (Initiator Election complete).");
      }
    });
  }

  // Clickable Stepper tabs (Step 1, Step 2, Step 3, Step 4)
  for (let s = 1; s <= 4; s++) {
    const item = document.getElementById(`stepNav${s}`);
    if (item) {
      item.addEventListener("click", () => {
        loadStep(s);
      });
    }
  }

  const btnClearLogs = document.getElementById("btnClearLogs");
  if (btnClearLogs) {
    btnClearLogs.addEventListener("click", () => {
      const logs = document.getElementById("terminalLogs");
      if (logs) logs.innerHTML = '<div class="text-slate-400">[SYSTEM] Terminal logs cleared.</div>';
    });
  }

  const btnReplayNodePackets = document.getElementById("btnReplayNodePackets");
  if (btnReplayNodePackets) {
    btnReplayNodePackets.addEventListener("click", () => {
      if (activeSelectedNodeData && currentStep === 4) {
        replaySlowMoNodeTrace(activeSelectedNodeData);
      }
    });
  }
}

// 13. Terminal Console Logger
function logToTerminal(level, message) {
  const terminal = document.getElementById("terminalLogs");
  if (!terminal) return;

  const row = document.createElement("div");
  row.className = "flex items-start space-x-2 font-mono text-[11px] leading-tight";

  const timeStr = new Date().toLocaleTimeString("en-US", { hour12: false });
  let badgeColor = "text-blue-400";

  if (level === "ERROR") badgeColor = "text-rose-400";
  else if (level === "SUCCESS") badgeColor = "text-emerald-400";
  else if (level === "TRAINING") badgeColor = "text-cyan-400";
  else if (level === "WARN") badgeColor = "text-amber-400";
  else if (level === "ZONE") badgeColor = "text-purple-400";
  else if (level === "VRF") badgeColor = "text-amber-400";
  else if (level === "TOPOLOGY") badgeColor = "text-blue-400";

  row.innerHTML = `
    <span class="text-slate-500 select-none">[${timeStr}]</span>
    <span class="${badgeColor} font-bold select-none">[${level}]</span>
    <span class="text-slate-200">${message}</span>
  `;

  terminal.appendChild(row);
  terminal.scrollTop = terminal.scrollHeight;
}
