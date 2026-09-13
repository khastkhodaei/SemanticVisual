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
  if (typeof cytoscape === "undefined") {
    console.error("Cytoscape.js is not loaded! Please check script tags.");
    const cyContainer = document.getElementById("cy");
    if (cyContainer) {
      cyContainer.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full p-6 text-center text-slate-500">
          <p class="text-base font-bold text-red-600 mb-2">Cytoscape Library Not Loaded</p>
          <p class="text-xs">Failed to load Cytoscape.js. Please verify vendor scripts or internet connectivity.</p>
        </div>`;
    }
    return;
  }
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
            if (ele.hasClass("initiator-node")) {
              return "👑 C" + clean;
            }
            return "C" + clean;
          },
          "color": "#ffffff",
          "font-size": "11px",
          "font-family": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
          "font-weight": "bold",
          "text-valign": "center",
          "text-halign": "center",
          "background-color": "data(bg_color)",
          "border-color": "data(border_color)",
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
          "label": function(ele) {
            const raw = ele.data("node_id_num") || ele.data("id");
            const clean = String(raw).replace("node_", "").replace("C", "");
            return "👑 C" + clean;
          },
          "border-width": 4.5,
          "width": 44,
          "height": 44,
          "color": "#ffffff",
          "font-size": "12px",
          "shadow-blur": 22,
          "shadow-opacity": 0.9,
          "z-index": 90
        }
      },
      {
        selector: "node.top-initiator-node",
        style: {
          "label": function(ele) {
            const raw = ele.data("node_id_num") || ele.data("id");
            const clean = String(raw).replace("node_", "").replace("C", "");
            return "👑👑 C" + clean;
          },
          "border-color": "#eab308",
          "border-width": 5.5,
          "width": 50,
          "height": 50,
          "color": "#ffffff",
          "font-size": "12px",
          "shadow-blur": 30,
          "shadow-color": "#eab308",
          "shadow-opacity": 1.0,
          "z-index": 120
        }
      },
      {
        selector: "node.exemplar-node",
        style: {
          "label": function(ele) {
            const raw = ele.data("node_id_num") || ele.data("id");
            const clean = String(raw).replace("node_", "").replace("C", "");
            return "⭐ C" + clean;
          },
          "border-color": "#f59e0b",
          "border-width": 4.5,
          "width": 42,
          "height": 42,
          "color": "#ffffff",
          "font-size": "11.5px",
          "shadow-blur": 22,
          "shadow-color": "#f59e0b",
          "shadow-opacity": 0.9,
          "z-index": 100
        }
      },
      {
        selector: "node.super-peer-node",
        style: {
          "label": function(ele) {
            const raw = ele.data("node_id_num") || ele.data("id");
            const clean = String(raw).replace("node_", "").replace("C", "");
            return "🌟⭐ C" + clean;
          },
          "border-color": "#f59e0b",
          "border-width": 6.0,
          "width": 52,
          "height": 52,
          "color": "#ffffff",
          "font-size": "12px",
          "shadow-blur": 35,
          "shadow-color": "#f59e0b",
          "shadow-opacity": 1.0,
          "z-index": 130
        }
      },
      {
        selector: "edge.dimmed-physical",
        style: {
          "line-color": "rgba(148, 163, 184, 0.22)",
          "width": 1.5,
          "opacity": 0.35,
          "z-index": 1
        }
      },
      {
        selector: "node.super-cluster-sc1",
        style: {
          "border-color": "#38bdf8",
          "border-width": 4.5,
          "shadow-blur": 26,
          "shadow-color": "#38bdf8",
          "shadow-opacity": 0.95,
          "z-index": 110
        }
      },
      {
        selector: "node.super-cluster-sc2",
        style: {
          "border-color": "#fbbf24",
          "border-width": 4.5,
          "shadow-blur": 26,
          "shadow-color": "#fbbf24",
          "shadow-opacity": 0.95,
          "z-index": 110
        }
      },
      {
        selector: "node.super-cluster-sc3",
        style: {
          "border-color": "#c084fc",
          "border-width": 4.5,
          "shadow-blur": 26,
          "shadow-color": "#c084fc",
          "shadow-opacity": 0.95,
          "z-index": 110
        }
      },
      {
        selector: "node.winner-node-4",
        style: {
          "background-color": "#166534",
          "border-color": "#14532d",
          "shadow-color": "#166534",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.winner-node-2",
        style: {
          "background-color": "#991b1b",
          "border-color": "#7f1d1d",
          "shadow-color": "#991b1b",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.winner-node-8",
        style: {
          "background-color": "#a16207",
          "border-color": "#713f12",
          "shadow-color": "#a16207",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-node-2",
        style: {
          "background-color": "#059669",
          "border-color": "#047857",
          "shadow-color": "#059669",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-node-4",
        style: {
          "background-color": "#ea580c",
          "border-color": "#c2410c",
          "shadow-color": "#ea580c",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-node-8",
        style: {
          "background-color": "#7c3aed",
          "border-color": "#6d28d9",
          "shadow-color": "#7c3aed",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-pastel-2",
        style: {
          "background-color": "#34d399",
          "border-color": "#10b981",
          "shadow-color": "#34d399",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-pastel-4",
        style: {
          "background-color": "#fb923c",
          "border-color": "#f97316",
          "shadow-color": "#fb923c",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-pastel-8",
        style: {
          "background-color": "#a78bfa",
          "border-color": "#8b5cf6",
          "shadow-color": "#a78bfa",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-initiator-2",
        style: {
          "background-color": "#059669",
          "border-color": "#f59e0b",
          "shadow-color": "#059669",
          "border-width": 4.5,
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-initiator-4",
        style: {
          "background-color": "#ea580c",
          "border-color": "#f59e0b",
          "shadow-color": "#ea580c",
          "border-width": 4.5,
          "color": "#ffffff"
        }
      },
      {
        selector: "node.zone-initiator-8",
        style: {
          "background-color": "#7c3aed",
          "border-color": "#f59e0b",
          "shadow-color": "#7c3aed",
          "border-width": 4.5,
          "color": "#ffffff"
        }
      },
      {
        selector: "node.boundary-node-1",
        style: {
          "background-color": "#059669",
          "border-color": "#ea580c",
          "border-width": 4.5,
          "shadow-color": "#ea580c",
          "color": "#ffffff"
        }
      },
      {
        selector: "node.boundary-node-6",
        style: {
          "background-color": "#ea580c",
          "border-color": "#7c3aed",
          "border-width": 4.5,
          "shadow-color": "#7c3aed",
          "color": "#ffffff"
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
          "line-style": "solid",
          "opacity": 0.65,
          "curve-style": "straight",
          "target-arrow-shape": "none"
        }
      },
      {
        selector: "edge.boundary-edge",
        style: {
          "line-style": "solid",
          "line-color": "#64748b",
          "width": 2,
          "opacity": 0.65
        }
      },
      {
        selector: "edge.intra-zone-edge",
        style: {
          "line-style": "solid",
          "line-color": "#64748b",
          "width": 2,
          "opacity": 0.65
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
    autoungrabify: true,
    minZoom: 0.4,
    maxZoom: 2.5
  });

  // Track mousedown / mousemove to cleanly distinguish Click (open modal) from Drag (pan/move canvas)
  let startX = 0;
  let startY = 0;
  let isMouseDown = false;
  let isDragging = false;

  const cyContainer = cy.container();
  if (cyContainer) {
    cyContainer.addEventListener("mousedown", (e) => {
      startX = e.clientX;
      startY = e.clientY;
      isMouseDown = true;
      isDragging = false;
    });

    cyContainer.addEventListener("mousemove", (e) => {
      if (isMouseDown && Math.hypot(e.clientX - startX, e.clientY - startY) > 5) {
        isDragging = true;
      }
    });

    cyContainer.addEventListener("mouseup", (e) => {
      isMouseDown = false;
      // Allow slight window for tap to evaluate
      setTimeout(() => {
        isDragging = false;
      }, 50);
    });
  }

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

  function handleNodeClick(node) {
    console.log("Clicked node:", node);
    if (!node) return;

    if (node && typeof node.position === "function") {
      const pos = node.position();
      node.position({ x: pos.x, y: pos.y });
    }

    const nodeData = (typeof node.data === "function") ? node.data() : node;
    const rawId = nodeData.node_id_num ?? nodeData.id;
    const nid = typeof rawId === "string" ? parseInt(rawId.replace(/\D/g, ""), 10) : Number(rawId);

    if (activeSelectedNodeId === nid) {
      hideNodeModal();
    } else {
      activeSelectedNodeId = nid;
      activeSelectedNodeData = nodeData;
      renderNodeModal(nodeData, currentStepData);

      if (cy) {
        cy.nodes().removeClass("selected-node");
        const ele = cy.getElementById(`node_${nid}`) || cy.getElementById(nid);
        if (ele && ele.length > 0) {
          ele.addClass("selected-node");
        }
      }
    }
  }

  function openNodeModal(node) {
    handleNodeClick(node);
  }

  function selectNode(node) {
    handleNodeClick(node);
  }

  window.handleNodeClick = handleNodeClick;
  window.openNodeModal = openNodeModal;
  window.selectNode = selectNode;

  // Click-to-Toggle Node Modal Interaction
  cy.on("tap", "node", (evt) => {
    handleNodeClick(evt.target);
  });

  // Tap on background to dismiss modal and restore full canvas opacity
  cy.on("tap", (evt) => {
    if (isDragging) return;
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

// Helper to reliably find Cytoscape node element by number or ID string
function getNodeElement(id) {
  if (!cy) return null;
  const numId = parseInt(String(id).replace("node_", "").replace("C", ""), 10);
  let el = cy.getElementById(`node_${numId}`);
  if (!el || !el.length) el = cy.getElementById(String(numId));
  if (!el || !el.length) el = cy.getElementById(`C${numId}`);
  return (el && el.length && el.isNode && el.isNode()) ? el : null;
}

// 4. Main Step Loading Function (Steps 1 to 19)
async function loadStep(stepNumber) {
  if (stepNumber < 1 || stepNumber > 19) return;
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
    } else if (stepNumber === 5) {
      renderStep5(data);
    } else if (stepNumber === 6) {
      try {
        renderStep6(data);
      } catch (renderErr) {
        console.error("Step 6 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 6 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 7) {
      try {
        renderStep7(data);
      } catch (renderErr) {
        console.error("Step 7 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 7 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 8) {
      try {
        renderStep8(data);
      } catch (renderErr) {
        console.error("Step 8 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 8 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 9) {
      try {
        renderStep9(data);
      } catch (renderErr) {
        console.error("Step 9 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 9 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 10) {
      try {
        renderStep10(data);
      } catch (renderErr) {
        console.error("Step 10 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 10 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 11) {
      try {
        renderStep11(data);
      } catch (renderErr) {
        console.error("Step 11 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 11 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 12) {
      try {
        renderStep12(data);
      } catch (renderErr) {
        console.error("Step 12 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 12 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 13) {
      try {
        renderStep13(data);
      } catch (renderErr) {
        console.error("Step 13 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 13 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 14) {
      try {
        renderStep14(data);
      } catch (renderErr) {
        console.error("Step 14 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 14 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 15) {
      try {
        renderStep15(data);
      } catch (renderErr) {
        console.error("Step 15 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 15 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 16) {
      try {
        renderStep16(data);
      } catch (renderErr) {
        console.error("Step 16 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 16 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 17) {
      try {
        renderStep17(data);
      } catch (renderErr) {
        console.error("Step 17 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 17 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 18) {
      try {
        renderStep18(data);
      } catch (renderErr) {
        console.error("Step 18 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 18 Render Error: ${renderErr.message}`);
      }
    } else if (stepNumber === 19) {
      try {
        renderStep19(data);
      } catch (renderErr) {
        console.error("Step 19 Render Crash:", renderErr);
        logToTerminal("ERROR", `Step 19 Render Error: ${renderErr.message}`);
      }
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
        else if (log.startsWith("[PROBE") || log.startsWith("[Zone") || log.startsWith("[ZONE")) lvl = "ZONE";
        else if (log.startsWith("[BOUNDARY") || log.startsWith("[DISCOVERY")) lvl = "BOUNDARY";
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
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  const stepTag = document.getElementById("stepTag");
  const stepTitle = document.getElementById("stepTitle");
  const stepDesc = document.getElementById("stepDescription");

  if (step === 1) {
    activeBadges.forEach(badge => {
      badge.textContent = "Step 1: Network Creation";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200";
    });
    if (stepTag) stepTag.textContent = "STEP 1 / NETWORK CREATION";
    if (stepTitle) stepTitle.textContent = "Step 1: Network Creation & Non-IID Data Distribution";
    if (stepDesc) stepDesc.textContent = "10 decentralized edge clients connected via 18 physical ad-hoc links. Each node holds local CIFAR-10 data.";
  } else if (step === 2) {
    activeBadges.forEach(badge => {
      badge.textContent = "Step 2: Local Vectors";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-cyan-50 text-cyan-700 border border-cyan-200";
    });
    if (stepTag) stepTag.textContent = "STEP 2 / LOCAL TRAINING & VECTORS";
    if (stepTitle) stepTitle.textContent = "Step 2: Local Training & Normalized 10D Vector Generation";
    if (stepDesc) stepDesc.textContent = "Each client trains on local CIFAR-10 data, outputting a normalized 10-dimensional vector representing class proportions.";
  } else if (step === 3) {
    activeBadges.forEach(badge => {
      badge.textContent = "Step 3: Local VRF";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 border border-amber-200";
    });
    if (stepTag) stepTag.textContent = "STEP 3 / LOCAL VRF GENERATION";
    if (stepTitle) stepTitle.textContent = "Step 3: Local VRF Score Calculation";
    if (stepDesc) stepDesc.textContent = "Each peer independently calculates its local VRF score σ_p = VRF(seed_{e-1}) using its private key. Scores are not transmitted or received in this step.";
  } else if (step === 4) {
    activeBadges.forEach(badge => {
      badge.textContent = "Step 4: Initiator Election";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-300";
    });
    if (stepTag) stepTag.textContent = "STEP 4 / 1-HOP EXCHANGE & INITIATOR ELECTION";
    if (stepTitle) stepTitle.textContent = "Step 4: 1-Hop Neighbor Score Exchange & Initiator Election";
    if (stepDesc) stepDesc.textContent = "Clients exchange VRF scores with direct 1-hop physical neighbors and elect closed-ball minimums. Nodes 2, 4, and 8 are crowned as Initiators.";
  } else if (step === 5) {
    activeBadges.forEach(badge => {
      badge.textContent = "STEP 5: ZONE PROBE FLOODING (TTL=1)";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300";
    });
    if (stepTag) stepTag.textContent = "STEP 5 / ZONE PROBE FLOODING (TTL=1)";
    if (stepTitle) stepTitle.textContent = "Step 5: Zone Creation via PROBE Flooding (TTL = 1)";
    if (stepDesc) stepDesc.textContent = "Elected Initiators (Nodes 2, 4, and 8) broadcast a PROBE packet with TTL=1 strictly to their 1-hop physical neighbors.";
  } else if (step === 6) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 6: ZONE CREATION & BOUNDARY DISCOVERY";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-purple-50 text-purple-800 border border-purple-300";
    });
    if (stepTag) stepTag.textContent = "STEP 6 / ZONE FORMATION & BOUNDARY DISCOVERY";
    if (stepTitle) stepTitle.textContent = "Step 6: Official Zone Formation & Inter-Zone Boundary Discovery";
    if (stepDesc) stepDesc.textContent = "Clients morph into their initiator's zone color. Frontier peers send dual notifications so initiators learn adjacent zones.";
  } else if (step === 7) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 7: INITIATOR P_MIN QUERY";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-800 border border-blue-300";
    });
    if (stepTag) stepTag.textContent = "STEP 7 / INITIATOR P_MIN QUERY";
    if (stepTitle) stepTitle.textContent = "Step 7: Initiator P_min Query Request";
    if (stepDesc) stepDesc.textContent = "Zone Initiators prompt zone members to evaluate the minimum signature length P_min^i needed to retain 80% model quality.";
  } else if (step === 8) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 8: LOCAL BINARY SEARCH & P_MIN REPORTING";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-purple-50 text-purple-800 border border-purple-300";
    });
    if (stepTag) stepTag.textContent = "STEP 8 / LOCAL BINARY SEARCH & REPORTING";
    if (stepTitle) stepTitle.textContent = "Step 8: Local Binary Search & P_min^i Reporting";
    if (stepDesc) stepDesc.textContent = "Each client executes local binary search on interval p in [1, 10] on sorted absolute weights to find minimal P_min retaining 80% quality, then reports to zone initiator.";
  } else if (step === 9) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 9: INTER-INITIATOR CONSENSUS EXCHANGE";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-800 border border-indigo-300";
    });
    if (stepTag) stepTag.textContent = "STEP 9 / INTER-INITIATOR CONSENSUS";
    if (stepTitle) stepTitle.textContent = "Step 9: Inter-Initiator Exchange via Boundary Gateways & Global Consensus";
    if (stepDesc) stepDesc.textContent = "Initiators relay their zone proposals through boundary nodes C1 and C6 to agree on a unified global P=3.";
  } else if (step === 10) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 10: EXTRACTION ORDER BROADCAST (P=3)";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300";
    });
    if (stepTag) stepTag.textContent = "STEP 10 / EXTRACTION ORDER BROADCAST";
    if (stepTitle) stepTitle.textContent = "Step 10: Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3)";
    if (stepDesc) stepDesc.textContent = "Initiators broadcast the agreed global length P=3 down to all zone peers.";
  } else if (step === 11) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 11: SIGNATURE EXTRACTION & DISPATCH";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-cyan-50 text-cyan-800 border border-cyan-300";
    });
    if (stepTag) stepTag.textContent = "STEP 11 / SIGNATURE EXTRACTION & DISPATCH";
    if (stepTitle) stepTitle.textContent = "Step 11: Top-P Signature Extraction with Dual Representation";
    if (stepDesc) stepDesc.textContent = "Peers extract compact unweighted 3-index sets (3 Bytes) to eliminate parameter leakage, while the dashboard renders 10D binary indicator masks.";
  } else if (step === 12) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 12: INTRA-ZONE SEMANTIC CLUSTERING (AP)";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-violet-50 text-violet-800 border border-violet-300";
    });
    if (stepTag) stepTag.textContent = "STEP 12 / INTRA-ZONE SEMANTIC CLUSTERING";
    if (stepTitle) stepTitle.textContent = "Step 12: Intra-Zone Semantic Clustering (Affinity Propagation)";
    if (stepDesc) stepDesc.textContent = "Initiators evaluate pairwise Cosine Similarities across member Top-P signatures and run Affinity Propagation to partition peers into semantic clusters.";
  } else if (step === 13) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 13: CLUSTER EXEMPLAR DESIGNATION";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 border border-amber-400";
    });
    if (stepTag) stepTag.textContent = "STEP 13 / CLUSTER EXEMPLAR DESIGNATION";
    if (stepTitle) stepTitle.textContent = "Step 13: Intra-Zone Cluster Exemplar Designation & Profile Assignment";
    if (stepDesc) stepDesc.textContent = "Zone initiators assign official cluster exemplars and dispatch representative profile signatures via ORDER_SET_EXEMPLAR.";
  } else if (step === 14) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 14: TOP-LEVEL INITIATOR ELECTION & SUPER-ZONE (C4 👑👑)";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 border border-amber-400";
    });
    if (stepTag) stepTag.textContent = "STEP 14 / TOP-LEVEL INITIATOR ELECTION & SUPER-ZONE (C4 👑👑)";
    if (stepTitle) stepTitle.textContent = "Step 14: Top-Level Initiator Election & Super-Zone Creation (Figure 3(e))";
    if (stepDesc) stepDesc.textContent = "Base initiators form a higher-level overlay graph. Initiator C4 wins election and broadcasts symmetrical TOP_PROBE to form the global Super-Zone Z_TOP.";
  } else if (step === 15) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 15: TOP-LEVEL CATALOG QUERY DISPATCH (REQ_CLUSTER_CATALOG)";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-cyan-50 text-cyan-900 border border-cyan-400";
    });
    if (stepTag) stepTag.textContent = "STEP 15 / TOP-LEVEL CATALOG QUERY DISPATCH";
    if (stepTitle) stepTitle.textContent = "Step 15: Top-Level Catalog Query Dispatch (REQ_CLUSTER_CATALOG)";
    if (stepDesc) stepDesc.textContent = "Super-Initiator C4 broadcasts REQ_CLUSTER_CATALOG across the super-zone overlay to retrieve cluster metadata from base initiators C2 and C8.";
  } else if (step === 16) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 16: ZONE CATALOG RESPONSE & SIGNATURE INGESTION";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-400";
    });
    if (stepTag) stepTag.textContent = "STEP 16 / ZONE CATALOG RESPONSE & SIGNATURE INGESTION";
    if (stepTitle) stepTitle.textContent = "Step 16: Zone Catalog Response & Signature Ingestion at C4";
    if (stepDesc) stepDesc.textContent = "Base initiators transmit exemplar profiles and binary masks inward to Super-Initiator C4, assembling the 7-cluster Global Semantic Registry.";
  } else if (step === 17) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 17: GLOBAL SUPER-CLUSTER FORMATION";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-sky-50 text-sky-900 border border-sky-400";
    });
    if (stepTag) stepTag.textContent = "STEP 17 / GLOBAL SUPER-CLUSTER FORMATION";
    if (stepTitle) stepTitle.textContent = "Step 17: Inter-Zone Meta-Clustering & Global Super-Cluster Formation";
    if (stepDesc) stepDesc.textContent = "C4 evaluates pairwise Cosine Similarities across cluster masks to form a 7x7 matrix, partitioning the network into 3 cross-zone Super-Clusters.";
  } else if (step === 18) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 18: SUPER-PEER DESIGNATION & HIERARCHICAL BINDING";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 border border-amber-400";
    });
    if (stepTag) stepTag.textContent = "STEP 18 / SUPER-PEER DESIGNATION & HIERARCHICAL BINDING";
    if (stepTitle) stepTitle.textContent = "Step 18: Super-Peer Designation & Hierarchical Overlay Binding";
    if (stepDesc) stepDesc.textContent = "Super-Initiator C4 designates Super-Peers (1, 5, 10) and binds local exemplars to coordinate cross-zone federations.";
  } else if (step === 19) {
    activeBadges.forEach(badge => {
      badge.textContent = "ACTIVE PHASE: STEP 19: SEMANTIC OVERLAY NETWORK (SON) FORMATION";
      badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-400";
    });
    if (stepTag) stepTag.textContent = "STEP 19 / SEMANTIC OVERLAY NETWORK (SON) FORMATION";
    if (stepTitle) stepTitle.textContent = "Step 19: Semantic Overlay Network (SON) Logical Topology Formation";
    if (stepDesc) stepDesc.textContent = "Active logical edges connect members to exemplars, and exemplars to super-peers across physical zones.";
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
      e.style({
        "line-style": "solid",
        "line-color": "#64748b",
        "width": 2,
        "opacity": 0.65
      });
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
  if (canvasLabel) canvasLabel.textContent = "Step 4: 1-Hop Neighbor Score Exchange & Initiator Election";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Initiators (<span class="text-emerald-700 font-bold">C4: Dark Green</span>, <span class="text-rose-700 font-bold">C2: Dark Red</span>, <span class="text-amber-700 font-bold">C8: Dark Yellow</span>)</span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes: All 3 selected Initiators (Node 4: dark green, Node 2: dark red, Node 8: dark yellow) recognized and displayed as winners
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useZoneColors: false,
    showBoundaryEdges: false
  });

  logToTerminal("VRF_TX", "[1/4 SCORE TRANSMISSION] Broadcasting local VRF scores to direct 1-hop physical neighbors...");
  logToTerminal("VRF_RX", "[2/4 SCORE RECEPTION] 1-hop neighbor scores received across all 18 physical links.");
  logToTerminal("ELECTION", "[3/4 WINNER SELECTION] Evaluating closed-ball minimums: m_p = min_{q in N_1(p) U {p}} (sigma_q, id_q).");
  logToTerminal("INITIATOR", "[4/4 INITIATOR IDENTIFIED] Node 4 (0.0412) elected Winner -> Dark Green");
  logToTerminal("INITIATOR", "[4/4 INITIATOR IDENTIFIED] Node 2 (0.0837) elected Winner -> Dark Red");
  logToTerminal("INITIATOR", "[4/4 INITIATOR IDENTIFIED] Node 8 (0.0275) elected Winner -> Dark Yellow");

  // Animate 1-hop score packet exchanges along edges exclusively in Step 4
  if (data.packet_exchanges && data.packet_exchanges.length > 0) {
    animateVrfScoreExchangePackets(data.packet_exchanges, data.nodes, null);
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

// Animate 1-hop VRF score exchange packets along the 18 physical links in Step 4
function animateVrfScoreExchangePackets(packets, allNodes, onArrival) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 2200; // ms
  const startTime = performance.now();
  const activeList = packets || [];
  let arrivalTriggered = false;

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

    if (progress >= 1.0 && !arrivalTriggered) {
      arrivalTriggered = true;
      if (typeof onArrival === "function") {
        onArrival();
      }
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      // Loop smoothly after a brief pause if still on Step 4
      setTimeout(() => {
        if (currentStep === 4) {
          animateVrfScoreExchangePackets(packets, allNodes, null);
        }
      }, 2000);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8b. Storyboard Step 5: Zone Creation via PROBE Flooding (TTL = 1)
function renderStep5(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "STEP 5: ZONE PROBE FLOODING (TTL=1)";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300";
  });

  renderSidebarFormula(
    "Zone Creation via PROBE Flooding",
    "\\text{PROBE}(p, \\text{TTL}=1), \\quad p \\in \\{2, 4, 8\\}",
    "Elected Initiators broadcast a PROBE packet with TTL=1 to discover and claim their 1-hop physical neighbors.",
    "Step 5: Zone Creation",
    false,
    "emerald"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 5: Zone Creation via PROBE Flooding (TTL = 1)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Initiators (<span class="text-rose-700 font-bold">C2</span>, <span class="text-emerald-700 font-bold">C4</span>, <span class="text-amber-700 font-bold">C8</span>) | <span class="text-blue-700 font-bold">7 Neutral Clients (Probing)</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Prevent Premature Zone Coloring:
  // Initiators (C2, C4, C8) retain distinct initiator/winner styling & crown badge (👑).
  // All non-initiator clients (C1, C3, C5, C6, C7, C9, C10) remain solid neutral blue (#2563eb).
  // Zone color morphing happens only in the subsequent zone joining step.
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useZoneColors: false,
    showBoundaryEdges: false
  });

  logToTerminal("ZONE", "[PROBE FLOODING] Initiators broadcast PROBE(TTL=1) to 1-hop physical neighbors.");
  logToTerminal("ZONE", "Initiator C2 (Zone 2 - Emerald Green) dispatches PROBE to: [C1, C3]");
  logToTerminal("ZONE", "Initiator C4 (Zone 4 - Coral/Orange) dispatches PROBE to: [C1, C5, C6, C7]");
  logToTerminal("ZONE", "Initiator C8 (Zone 8 - Violet/Purple) dispatches PROBE to: [C6, C9, C10]");
  logToTerminal("ZONE", "[PROBE ARRIVAL] C1: C2 arrived at t=10.4ms (First-Wins Winner) vs C4 at t=16.8ms (Delayed).");
  logToTerminal("ZONE", "[PROBE ARRIVAL] C6: C4 arrived at t=11.2ms (First-Wins Winner) vs C8 at t=18.5ms (Delayed).");
  logToTerminal("NOTICE", "[FIRST-WINS ARBITRATION] Competing probes resolved. Nodes retain neutral blue until formal zone joining in next step.");

  const packets = data.packet_events || data.packet_exchanges || [];
  if (packets.length > 0) {
    animateStep5ProbePackets(packets, data.nodes);
  }
}

// Directional PROBE packet animation along physical links in Step 5
function animateStep5ProbePackets(packets, allNodes) {
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
      const srcId = pkt.source_num || pkt.source;
      const tgtId = pkt.target_num || pkt.target;
      const srcNode = getNodeElement(srcId);
      const tgtNode = getNodeElement(tgtId);
      if (!srcNode || !tgtNode) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      const curX = p1.x + (p2.x - p1.x) * ease;
      const curY = p1.y + (p2.y - p1.y) * ease;

      const initId = pkt.initiator_id || (typeof srcId === "number" ? srcId : parseInt(String(srcId).replace("C", "").replace("node_", ""), 10));
      let badgeBg = "rgba(209, 250, 229, 0.98)";
      let badgeText = "#065f46";
      let badgeBorder = "#059669";
      if (initId === 4) {
        badgeBg = "rgba(255, 237, 213, 0.98)";
        badgeText = "#9a3412";
        badgeBorder = "#ea580c";
      } else if (initId === 8) {
        badgeBg = "rgba(237, 233, 254, 0.98)";
        badgeText = "#5b21b6";
        badgeBorder = "#7c3aed";
      }

      ctx.save();
      ctx.beginPath();
      ctx.arc(curX, curY, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = badgeBorder;
      ctx.shadowBlur = 8;
      ctx.shadowColor = badgeBorder;
      ctx.fill();
      ctx.restore();

      drawCanvasFloatingBadge(
        ctx,
        `PROBE(TTL=1)`,
        curX,
        curY - 14,
        badgeBg,
        badgeText,
        badgeBorder
      );
    });

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      setTimeout(() => {
        if (currentStep === 5) {
          animateStep5ProbePackets(packets, allNodes);
        }
      }, 2000);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8c. Storyboard Step 6: Official Zone Formation & Inter-Zone Boundary Discovery
function renderStep6(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 6: ZONE CREATION & BOUNDARY DISCOVERY";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-purple-50 text-purple-800 border border-purple-300";
  });

  renderSidebarFormula(
    "Zone Formation & Boundary Discovery",
    "\\text{First-Wins} \\rightarrow \\text{ASSIGNED}(Z_I), \\quad \\text{NEIGHBOR}(p, q) \\rightarrow I_p \\text{ learns } I_q",
    "Clients morph into their initiator's zone color. Frontier peers send dual notifications so initiators learn adjacent zones.",
    "Step 6: Boundary Discovery",
    false,
    "purple"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 6: Official Zone Formation & Inter-Zone Boundary Discovery (Algorithm 3)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.remove("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Assigned Zones (<span class="text-emerald-700 font-bold">Z2: C1-C3</span>, <span class="text-orange-700 font-bold">Z4: C4-C7</span>, <span class="text-purple-700 font-bold">Z8: C8-C10</span>) | <span class="text-rose-700 font-bold">Boundary Discovery Active</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Color Morphing & Dashed Boundary Edges
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: true
  });

  logToTerminal("ZONE", "[OFFICIAL ZONE FORMATION] All 10 peers officially assigned (First-Wins adopted).");
  logToTerminal("ZONE", "Zone 2 (Leader C2 👑): C1, C3 adopt pastel emerald tone (#34d399).");
  logToTerminal("ZONE", "Zone 4 (Leader C4 👑): C5, C6, C7 adopt pastel coral tone (#fb923c).");
  logToTerminal("ZONE", "Zone 8 (Leader C8 👑): C9, C10 adopt pastel violet tone (#a78bfa).");
  logToTerminal("BOUNDARY", "[DUAL NOTIFICATIONS] Frontier peers dispatch reverse boundary announcements (Algorithm 3, L17-L20):");
  logToTerminal("BOUNDARY", "[DISCOVERY NOTICE] Frontier C1 dispatched NEIGHBOR(C4) to Initiator C2.");
  logToTerminal("BOUNDARY", "[DISCOVERY NOTICE] Frontier C1 dispatched NEIGHBOR(C2) to Initiator C4.");
  logToTerminal("BOUNDARY", "[DISCOVERY NOTICE] Frontier C6 dispatched NEIGHBOR(C8) to Initiator C4.");
  logToTerminal("BOUNDARY", "[DISCOVERY NOTICE] Frontier C6 dispatched NEIGHBOR(C4) to Initiator C8.");
  logToTerminal("SUCCESS", "[INITIATOR DISCOVERY] Initiator C2 learned: [C4]. Initiator C4 learned: [C2, C8]. Initiator C8 learned: [C4].");

  const packets = data.packet_events || data.packet_exchanges || [];
  if (packets.length > 0) {
    animateStep6BoundaryPackets(packets, data.nodes);
  }
}

// Directional Reverse Boundary NEIGHBOR Announcement packet animation in Step 6
function animateStep6BoundaryPackets(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 2600; // ms
  const startTime = performance.now();
  const activeList = packets || [];
  let arrivalPulseTriggered = false;

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);
    const ease = easeInOutQuad(progress);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate fade multiplier as packet nears destination (fades out completely between 88% and 100%)
    let badgeAlpha = 1.0;
    if (progress < 0.1) {
      badgeAlpha = progress / 0.1;
    } else if (progress > 0.85) {
      badgeAlpha = Math.max(0, (1.0 - progress) / 0.15);
    }

    activeList.forEach(pkt => {
      const srcId = pkt.source_num || pkt.source;
      const tgtId = pkt.target_num || pkt.target;
      const srcNode = getNodeElement(srcId);
      const tgtNode = getNodeElement(tgtId);
      if (!srcNode || !tgtNode) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      const curX = p1.x + (p2.x - p1.x) * ease;
      const curY = p1.y + (p2.y - p1.y) * ease;

      const pktColor = pkt.color || "#8b5cf6";

      // Animated traveling packet particle
      ctx.save();
      ctx.globalAlpha = Math.min(1.0, badgeAlpha + 0.2);
      ctx.beginPath();
      ctx.arc(curX, curY, 5.0, 0, Math.PI * 2);
      ctx.fillStyle = pktColor;
      ctx.shadowBlur = 9;
      ctx.shadowColor = pktColor;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(curX, curY, 2.0, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.restore();

      // Explicit floating pill badge moving synchronously with the particle dot
      if (badgeAlpha > 0.05) {
        const introNbr = pkt.introduced_neighbor || (pkt.label ? pkt.label.replace(/[^0-9C]/g, "") : "");
        const badgeLabel = `NEIGHBOR (${introNbr})`;
        const badgeBg = `rgba(15, 23, 42, ${0.88 * badgeAlpha})`;
        const textColor = "#fbbf24"; // Amber/gold for high contrast
        const borderColor = `rgba(245, 158, 11, ${0.75 * badgeAlpha})`;

        ctx.save();
        ctx.globalAlpha = badgeAlpha;
        drawCanvasFloatingBadge(
          ctx,
          badgeLabel,
          curX,
          curY - 15,
          badgeBg,
          textColor,
          borderColor
        );
        ctx.restore();
      }
    });

    // When packets arrive (progress near 1.0), briefly pulse target initiator nodes in golden yellow
    if (progress >= 0.92) {
      const pulseProg = (progress - 0.92) / 0.08;
      const pulseAlpha = Math.sin(pulseProg * Math.PI) * 0.85;
      const targetInitiatorIds = [2, 4, 8];

      ctx.save();
      targetInitiatorIds.forEach(id => {
        const nodeEl = getNodeElement(id);
        if (nodeEl) {
          const pos = nodeEl.renderedPosition();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 26 + pulseProg * 10, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(245, 158, 11, ${pulseAlpha})`;
          ctx.lineWidth = 3.5;
          ctx.shadowColor = "#f59e0b";
          ctx.shadowBlur = 12;
          ctx.stroke();
        }
      });
      ctx.restore();

      if (!arrivalPulseTriggered) {
        arrivalPulseTriggered = true;
      }
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setTimeout(() => {
        if (currentStep === 6) {
          animateStep6BoundaryPackets(packets, allNodes);
        }
      }, 2000);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8d. Storyboard Step 7: Initiator P_min Query Request
function renderStep7(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 7: INITIATOR P_MIN QUERY";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-800 border border-blue-300";
  });

  renderSidebarFormula(
    "Step 7: Initiator P_min Query Request",
    "\\text{REQ\\_P\\_MIN}(\\tau = 0.80) \\quad \\forall i \\in Z_I",
    "Zone Initiators prompt zone members to evaluate the minimum signature length P_min^i needed to retain 80% model quality.",
    "Step 7: P_min Query",
    false,
    "blue"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 7: Initiator P_min Query Broadcast (REQ_P_MIN, τ = 80%)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Active Initiators (<span class="text-emerald-700 font-bold">C2</span>, <span class="text-orange-700 font-bold">C4</span>, <span class="text-purple-700 font-bold">C8</span>) | <span class="text-blue-700 font-bold">REQ_P_MIN Broadcast Active (τ = 80%)</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Colors and solid slate physical links
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false
  });

  logToTerminal("ZONE", "[STEP 7] Initiator P_min Query Request initialized (tau = 0.80).");
  logToTerminal("INFO", "Initiator C2 (Zone 2) dispatched REQ_P_MIN(tau=0.80) to zone members [C1, C3].");
  logToTerminal("INFO", "Initiator C4 (Zone 4) dispatched REQ_P_MIN(tau=0.80) to zone members [C5, C6, C7].");
  logToTerminal("INFO", "Initiator C8 (Zone 8) dispatched REQ_P_MIN(tau=0.80) to zone members [C9, C10].");
  logToTerminal("SUCCESS", "All zone members received REQ_P_MIN and set pending_query = 'REQ_P_MIN (tau=0.80)'.");

  const packets = data.packet_events || data.packet_exchanges || [];
  if (packets.length > 0) {
    animateStep7PminPackets(packets, data.nodes);
  }
}

// Traveling REQ_P_MIN packet animation in Step 7
function animateStep7PminPackets(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 2400; // ms
  const startTime = performance.now();
  const activeList = packets || [];
  let arrivalPulseTriggered = false;

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);
    const ease = easeInOutQuad(progress);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate fade multiplier as packet nears destination (fades out completely between 85% and 100%)
    let badgeAlpha = 1.0;
    if (progress < 0.1) {
      badgeAlpha = progress / 0.1;
    } else if (progress > 0.85) {
      badgeAlpha = Math.max(0, (1.0 - progress) / 0.15);
    }

    activeList.forEach(pkt => {
      const srcId = pkt.source_num || pkt.source;
      const tgtId = pkt.target_num || pkt.target;
      const srcNode = getNodeElement(srcId);
      const tgtNode = getNodeElement(tgtId);
      if (!srcNode || !tgtNode) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      const curX = p1.x + (p2.x - p1.x) * ease;
      const curY = p1.y + (p2.y - p1.y) * ease;

      const pktColor = pkt.color || "#2563eb";

      // Animated traveling packet particle
      ctx.save();
      ctx.globalAlpha = Math.min(1.0, badgeAlpha + 0.2);
      ctx.beginPath();
      ctx.arc(curX, curY, 5.0, 0, Math.PI * 2);
      ctx.fillStyle = pktColor;
      ctx.shadowBlur = 9;
      ctx.shadowColor = pktColor;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(curX, curY, 2.0, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.restore();

      // Floating pill badge moving synchronously above particle dot
      if (badgeAlpha > 0.05) {
        const badgeLabel = pkt.label || "REQ(τ=80%)";
        const badgeBg = `rgba(15, 23, 42, ${0.88 * badgeAlpha})`;
        const textColor = "#38bdf8"; // Light sky-blue for clear visibility
        const borderColor = `rgba(56, 189, 248, ${0.75 * badgeAlpha})`;

        ctx.save();
        ctx.globalAlpha = badgeAlpha;
        drawCanvasFloatingBadge(
          ctx,
          badgeLabel,
          curX,
          curY - 16,
          badgeBg,
          textColor,
          borderColor
        );
        ctx.restore();
      }
    });

    // When packets arrive (progress near 0.92-1.0), briefly pulse the member nodes receiving the query
    if (progress >= 0.92) {
      const pulseProg = (progress - 0.92) / 0.08;
      const pulseAlpha = Math.sin(pulseProg * Math.PI) * 0.85;
      const memberIds = [1, 3, 5, 6, 7, 9, 10];

      ctx.save();
      memberIds.forEach(id => {
        const nodeEl = getNodeElement(id);
        if (nodeEl) {
          const pos = nodeEl.renderedPosition();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 22 + pulseProg * 8, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(59, 130, 246, ${pulseAlpha})`;
          ctx.lineWidth = 3.0;
          ctx.shadowColor = "#3b82f6";
          ctx.shadowBlur = 10;
          ctx.stroke();
        }
      });
      ctx.restore();

      if (!arrivalPulseTriggered) {
        arrivalPulseTriggered = true;
      }
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setTimeout(() => {
        if (currentStep === 7) {
          animateStep7PminPackets(packets, allNodes);
        }
      }, 1800);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8e. Storyboard Step 8: Local Binary Search & P_min Reporting
function renderStep8(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 8: LOCAL BINARY SEARCH & P_MIN REPORTING";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-purple-50 text-purple-800 border border-purple-300";
  });

  renderSidebarFormula(
    "Step 8: Local Binary Search & P_min^i Reporting",
    "\\text{BinarySearch}(p \\in [1, 10]) \\rightarrow P_{\\min}^i, \\quad \\text{REPORT}(P_{\\min}^i) \\rightarrow I_{Z}",
    "Each client executes local binary search on interval p in [1, 10] on sorted absolute weights to find minimal P_min retaining 80% quality.",
    "Step 8: Binary Search",
    false,
    "purple"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 8: Reverse P_min Reporting to Zone Initiators (τ = 80%)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Initiators Receiving Reports (<span class="text-emerald-700 font-bold">C2</span>, <span class="text-orange-700 font-bold">C4</span>, <span class="text-purple-700 font-bold">C8</span>) | <span class="text-purple-700 font-bold">Reverse P_min Reports In-Flight</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Colors and solid slate physical links
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false
  });

  logToTerminal("ZONE", "[STEP 8] Local Binary Search & P_min Reporting initialized (tau = 0.80).");
  logToTerminal("INFO", "Zone 2: C1 (P_min=2), C3 (P_min=2) reporting to Initiator C2 👑.");
  logToTerminal("INFO", "Zone 4: C5 (P_min=1 [cos] / 2 [energy]), C6 (P_min=2 [cos] / 3 [energy]), C7 (P_min=2 [cos] / 3 [energy]) reporting to Initiator C4 👑.");
  logToTerminal("INFO", "Zone 8: C9 (P_min=2 [cos] / 3 [energy]), C10 (P_min=2 [cos] / 3 [energy]) reporting to Initiator C8 👑.");
  logToTerminal("SUCCESS", "All 10 nodes finalized local binary search and dispatched P_min reports.");

  const packets = data.packet_events || data.packet_exchanges || [];
  if (packets.length > 0) {
    animateStep8ReportPackets(packets, data.nodes);
  }
}

// Traveling Reverse P_min REPORT packet animation in Step 8
function animateStep8ReportPackets(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 2500; // ms
  const startTime = performance.now();
  const activeList = packets || [];
  let arrivalPulseTriggered = false;

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);
    const ease = easeInOutQuad(progress);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate fade multiplier as packet nears destination (fades out completely between 85% and 100%)
    let badgeAlpha = 1.0;
    if (progress < 0.1) {
      badgeAlpha = progress / 0.1;
    } else if (progress > 0.85) {
      badgeAlpha = Math.max(0, (1.0 - progress) / 0.15);
    }

    activeList.forEach(pkt => {
      const srcId = pkt.source_num || pkt.source;
      const tgtId = pkt.target_num || pkt.target;
      const srcNode = getNodeElement(srcId);
      const tgtNode = getNodeElement(tgtId);
      if (!srcNode || !tgtNode) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      const curX = p1.x + (p2.x - p1.x) * ease;
      const curY = p1.y + (p2.y - p1.y) * ease;

      const pktColor = pkt.color || "#8b5cf6";

      // Animated traveling packet particle
      ctx.save();
      ctx.globalAlpha = Math.min(1.0, badgeAlpha + 0.2);
      ctx.beginPath();
      ctx.arc(curX, curY, 5.0, 0, Math.PI * 2);
      ctx.fillStyle = pktColor;
      ctx.shadowBlur = 9;
      ctx.shadowColor = pktColor;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(curX, curY, 2.0, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.restore();

      // Floating pill badge moving synchronously above particle dot
      if (badgeAlpha > 0.05) {
        const badgeLabel = pkt.label || `P_min = ${pkt.p_min || 2}`;
        const badgeBg = `rgba(15, 23, 42, ${0.88 * badgeAlpha})`;
        const textColor = "#a78bfa"; // Soft purple text
        const borderColor = `rgba(167, 139, 250, ${0.75 * badgeAlpha})`;

        ctx.save();
        ctx.globalAlpha = badgeAlpha;
        drawCanvasFloatingBadge(
          ctx,
          badgeLabel,
          curX,
          curY - 16,
          badgeBg,
          textColor,
          borderColor
        );
        ctx.restore();
      }
    });

    // When packets arrive (progress near 0.92-1.0), pulse receiving zone initiator nodes
    if (progress >= 0.92) {
      const pulseProg = (progress - 0.92) / 0.08;
      const pulseAlpha = Math.sin(pulseProg * Math.PI) * 0.85;
      const targetInitiatorIds = [2, 4, 8];

      ctx.save();
      targetInitiatorIds.forEach(id => {
        const nodeEl = getNodeElement(id);
        if (nodeEl) {
          const pos = nodeEl.renderedPosition();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 25 + pulseProg * 10, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(245, 158, 11, ${pulseAlpha})`;
          ctx.lineWidth = 3.5;
          ctx.shadowColor = "#f59e0b";
          ctx.shadowBlur = 12;
          ctx.stroke();
        }
      });
      ctx.restore();

      if (!arrivalPulseTriggered) {
        arrivalPulseTriggered = true;
      }
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setTimeout(() => {
        if (currentStep === 8) {
          animateStep8ReportPackets(packets, allNodes);
        }
      }, 1900);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8f. Storyboard Step 9: Inter-Initiator Exchange via Boundary Peers & Global Consensus
function renderStep9(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 9: INTER-INITIATOR CONSENSUS EXCHANGE";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-800 border border-indigo-300";
  });

  renderSidebarFormula(
    "Step 9: Inter-Initiator Exchange & Global Consensus",
    "P = \\min(\\text{Quantile}_{0.8}(\\{P_{\\min}^i\\}), P_{\\max}) = 3, \\quad I_p \\xleftrightarrow{\\text{Frontier}} I_q",
    "Initiators relay their zone proposals through boundary nodes C1 and C6 to agree on a unified global P=3.",
    "Step 9: Consensus",
    false,
    "indigo"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 9: Multi-Hop Inter-Initiator Exchange via Boundary Peers (Agreed P = 3)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.remove("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Initiators in Consensus (<span class="text-emerald-700 font-bold">C2: P=2</span>, <span class="text-orange-700 font-bold">C4: P=3</span>, <span class="text-purple-700 font-bold">C8: P=3</span>) → <span class="text-indigo-700 font-bold">Global P = 3</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Zone colors and clean solid slate physical links
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false
  });

  logToTerminal("ZONE", "[STEP 9] Inter-Initiator P_min Exchange & Global Consensus initialized (q = 0.80).");
  logToTerminal("INFO", "Route C2 <-> C4: Relayed through Boundary Gateway Node C1 (P=2 from C2, P=3 from C4).");
  logToTerminal("INFO", "Route C4 <-> C8: Relayed through Boundary Gateway Node C6 (P=3 from C4, P=3 from C8).");
  logToTerminal("SUCCESS", "Initiators computed max(2, 3, 3) = 3 (80th quantile across network).");
  logToTerminal("SUCCESS", "All 3 Zone Initiators (C2, C4, C8) reached unanimous agreement on Global P = 3.");

  const packets = data.packet_events || data.packet_exchanges || [];
  if (packets.length > 0) {
    animateStep9ConsensusRelays(packets, data.nodes);
  }
}

// Traveling Multi-Hop Reverse Inter-Initiator Relay animation in Step 9
function animateStep9ConsensusRelays(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 3200; // ms for full 2-hop round trip
  const startTime = performance.now();
  const activeList = packets || [];

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Subtle gateway glow on C1 and C6 when relaying (active around progress 0.35 to 0.65)
    if (progress >= 0.35 && progress <= 0.65) {
      const midProg = (progress - 0.35) / 0.30;
      const glowAlpha = Math.sin(midProg * Math.PI) * 0.9;
      [1, 6].forEach(gwId => {
        const gwEl = getNodeElement(gwId);
        if (gwEl) {
          const pos = gwEl.renderedPosition();
          ctx.save();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 24 + midProg * 8, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(59, 130, 246, ${glowAlpha})`;
          ctx.lineWidth = 3.0;
          ctx.shadowColor = "#3b82f6";
          ctx.shadowBlur = 14;
          ctx.stroke();

          // Inner gateway pulse dot
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 6.0, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(147, 197, 253, ${glowAlpha * 0.8})`;
          ctx.fill();
          ctx.restore();
        }
      });
    }

    // Destination arrival pulse on initiators near the end
    if (progress >= 0.88) {
      const arrProg = (progress - 0.88) / 0.12;
      const arrAlpha = Math.sin(arrProg * Math.PI) * 0.85;
      [2, 4, 8].forEach(initId => {
        const initEl = getNodeElement(initId);
        if (initEl) {
          const pos = initEl.renderedPosition();
          ctx.save();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 26 + arrProg * 10, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(99, 102, 241, ${arrAlpha})`;
          ctx.lineWidth = 3.5;
          ctx.shadowColor = "#6366f1";
          ctx.shadowBlur = 12;
          ctx.stroke();
          ctx.restore();
        }
      });
    }

    // Animate multi-hop packets
    let badgeAlpha = 1.0;
    if (progress < 0.08) {
      badgeAlpha = progress / 0.08;
    } else if (progress > 0.88) {
      badgeAlpha = Math.max(0, (1.0 - progress) / 0.12);
    }

    activeList.forEach(pkt => {
      const pathNums = pkt.path_nums || [pkt.source_num, pkt.relay_num, pkt.target_num];
      if (!pathNums || pathNums.length < 3) return;

      const n0 = getNodeElement(pathNums[0]);
      const n1 = getNodeElement(pathNums[1]); // Relay Gateway
      const n2 = getNodeElement(pathNums[2]); // Destination
      if (!n0 || !n1 || !n2) return;

      const p0 = n0.renderedPosition();
      const p1 = n1.renderedPosition();
      const p2 = n2.renderedPosition();

      let curX, curY;
      if (progress < 0.5) {
        // Hop 1: n0 -> n1
        const subProgress = progress / 0.5;
        const subEase = easeInOutQuad(subProgress);
        curX = p0.x + (p1.x - p0.x) * subEase;
        curY = p0.y + (p1.y - p0.y) * subEase;
      } else {
        // Hop 2: n1 -> n2
        const subProgress = (progress - 0.5) / 0.5;
        const subEase = easeInOutQuad(subProgress);
        curX = p1.x + (p2.x - p1.x) * subEase;
        curY = p1.y + (p2.y - p1.y) * subEase;
      }

      const pktColor = pkt.color || "#4f46e5";

      // Animated traveling packet particle
      ctx.save();
      ctx.globalAlpha = Math.min(1.0, badgeAlpha + 0.2);
      ctx.beginPath();
      ctx.arc(curX, curY, 5.5, 0, Math.PI * 2);
      ctx.fillStyle = pktColor;
      ctx.shadowBlur = 10;
      ctx.shadowColor = pktColor;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(curX, curY, 2.2, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.restore();

      // Synchronized floating pill badge above particle
      if (badgeAlpha > 0.05) {
        const badgeLabel = pkt.label || `P=${pkt.p_val || 3}`;
        const badgeBg = `rgba(15, 23, 42, ${0.90 * badgeAlpha})`;
        const textColor = pkt.p_val === 2 ? "#34d399" : "#fdba74";
        const borderColor = pkt.p_val === 2 ? `rgba(52, 211, 153, ${0.8 * badgeAlpha})` : `rgba(251, 146, 60, ${0.8 * badgeAlpha})`;

        ctx.save();
        ctx.globalAlpha = badgeAlpha;
        drawCanvasFloatingBadge(
          ctx,
          badgeLabel,
          curX,
          curY - 17,
          badgeBg,
          textColor,
          borderColor
        );
        ctx.restore();
      }
    });

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setTimeout(() => {
        if (currentStep === 9) {
          animateStep9ConsensusRelays(packets, allNodes);
        }
      }, 1900);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8g. Storyboard Step 10: Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3)
function renderStep10(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 10: EXTRACTION ORDER BROADCAST (P=3)";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300";
  });

  renderSidebarFormula(
    "Step 10: Extraction Order Broadcast (P = 3)",
    "\\text{ORDER\\_EXTRACT}(P = 3) \\quad \\forall i \\in Z_I",
    "Initiators broadcast the agreed global length P=3 down to all zone peers.",
    "Step 10: Order Extract",
    false,
    "emerald"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 10: Intra-Zone Extraction Order Broadcast (Locked P = 3)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Initiators Broadcasting Directive (<span class="text-emerald-700 font-bold">C2</span>, <span class="text-orange-700 font-bold">C4</span>, <span class="text-purple-700 font-bold">C8</span>) → <span class="text-emerald-700 font-bold font-mono">ORDER_EXTRACT(P=3)</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Zone colors and clean solid slate physical links
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false
  });

  logToTerminal("ZONE", "[STEP 10] Initiator Extraction Order Broadcast initialized (Global P = 3).");
  logToTerminal("INFO", "Zone 2 Initiator C2 dispatched ORDER_EXTRACT(P=3) to members [C1, C3].");
  logToTerminal("INFO", "Zone 4 Initiator C4 dispatched ORDER_EXTRACT(P=3) to members [C5, C6, C7].");
  logToTerminal("INFO", "Zone 8 Initiator C8 dispatched ORDER_EXTRACT(P=3) to members [C9, C10].");
  logToTerminal("SUCCESS", "All 10 edge nodes locked target signature length to P = 3.");
  logToTerminal("SUCCESS", "All 10 nodes status updated to READY_TO_EXTRACT.");

  const packets = data.packet_events || data.packet_exchanges || [];
  if (packets.length > 0) {
    animateStep10OrderPackets(packets, data.nodes);
  }
}

// Traveling Intra-Zone Extraction Order Broadcast animation in Step 10
function animateStep10OrderPackets(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 2500; // ms
  const startTime = performance.now();
  const activeList = packets || [];

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);
    const ease = easeInOutQuad(progress);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate fade multiplier as packet nears destination
    let badgeAlpha = 1.0;
    if (progress < 0.1) {
      badgeAlpha = progress / 0.1;
    } else if (progress > 0.85) {
      badgeAlpha = Math.max(0, (1.0 - progress) / 0.15);
    }

    activeList.forEach(pkt => {
      const srcId = pkt.source_num || pkt.source;
      const tgtId = pkt.target_num || pkt.target;
      const srcNode = getNodeElement(srcId);
      const tgtNode = getNodeElement(tgtId);
      if (!srcNode || !tgtNode) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      const curX = p1.x + (p2.x - p1.x) * ease;
      const curY = p1.y + (p2.y - p1.y) * ease;

      const pktColor = pkt.color || "#059669";

      // Animated traveling packet particle
      ctx.save();
      ctx.globalAlpha = Math.min(1.0, badgeAlpha + 0.2);
      ctx.beginPath();
      ctx.arc(curX, curY, 5.0, 0, Math.PI * 2);
      ctx.fillStyle = pktColor;
      ctx.shadowBlur = 9;
      ctx.shadowColor = pktColor;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(curX, curY, 2.0, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.restore();

      // Floating pill badge moving synchronously above particle dot
      if (badgeAlpha > 0.05) {
        const badgeLabel = pkt.label || "ORDER: P=3";
        const badgeBg = `rgba(15, 23, 42, ${0.90 * badgeAlpha})`;
        const textColor = "#34d399"; // Bright emerald
        const borderColor = `rgba(52, 211, 153, ${0.8 * badgeAlpha})`;

        ctx.save();
        ctx.globalAlpha = badgeAlpha;
        drawCanvasFloatingBadge(
          ctx,
          badgeLabel,
          curX,
          curY - 16,
          badgeBg,
          textColor,
          borderColor
        );
        ctx.restore();
      }
    });

    // When packets arrive (progress near 0.90-1.0), pulse receiving member nodes
    if (progress >= 0.90) {
      const pulseProg = (progress - 0.90) / 0.10;
      const pulseAlpha = Math.sin(pulseProg * Math.PI) * 0.85;
      const memberIds = [1, 3, 5, 6, 7, 9, 10];

      ctx.save();
      memberIds.forEach(id => {
        const nodeEl = getNodeElement(id);
        if (nodeEl) {
          const pos = nodeEl.renderedPosition();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 22 + pulseProg * 8, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(16, 185, 129, ${pulseAlpha})`;
          ctx.lineWidth = 3.0;
          ctx.shadowColor = "#10b981";
          ctx.shadowBlur = 10;
          ctx.stroke();
        }
      });
      ctx.restore();
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setTimeout(() => {
        if (currentStep === 10) {
          animateStep10OrderPackets(packets, allNodes);
        }
      }, 1900);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8h. Storyboard Step 11: Top-P Signature Extraction with Dual Representation
function renderStep11(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 11: SIGNATURE EXTRACTION & DISPATCH";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-cyan-50 text-cyan-800 border border-cyan-300";
  });

  renderSidebarFormula(
    "Step 11: Top-P Signature Extraction",
    "S_i = \\text{Top-}3(\\text{indices of } |\\mathbf{w}_i|) \\subset \\{1, \\dots, 10\\}, \\quad \\mathbf{m}_i \\in \\{0, 1\\}^{10}",
    "Network layer transmits raw index sets (zero weights attached). Dashboard renders 10D binary indicators for visual clarity.",
    "Step 11: Signatures",
    false,
    "cyan"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 11: Top-P Signature Extraction & Wire Dispatch (P = 3)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Initiator Registries (<span class="text-emerald-700 font-bold">C2</span>: 3, <span class="text-orange-700 font-bold">C4</span>: 4, <span class="text-purple-700 font-bold">C8</span>: 3) ← <span class="text-cyan-700 font-bold font-mono">3-Byte Index Sets</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Zone colors and clean solid slate physical links
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false
  });

  logToTerminal("ZONE", "[STEP 11] Top-P Signature Extraction initialized (Consensus P = 3).");
  logToTerminal("INFO", "All 10 edge peers extracted top-3 unweighted coordinate indices.");
  logToTerminal("INFO", "Transmitted payloads contain zero floating-point weights (zero parameter leakage).");
  logToTerminal("INFO", "Wire payload size: 3 Bytes (3 × uint8) vs. 40 Bytes raw vector (92.5% reduction).");
  logToTerminal("SUCCESS", "Zone 2 members [C1, C3] dispatched signatures to Initiator C2.");
  logToTerminal("SUCCESS", "Zone 4 members [C5, C6, C7] dispatched signatures to Initiator C4.");
  logToTerminal("SUCCESS", "Zone 8 members [C9, C10] dispatched signatures to Initiator C8.");
  logToTerminal("SUCCESS", "Initiators C2, C4, C8 successfully aggregated all zone signatures.");

  const packets = data.packet_events || data.packet_exchanges || [];
  if (packets.length > 0) {
    animateStep11SignaturePackets(packets, data.nodes);
  }
}

// Traveling Intra-Zone Signature Packets animation in Step 11
function animateStep11SignaturePackets(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 2500; // ms
  const startTime = performance.now();
  const activeList = packets || [];

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);
    const ease = easeInOutQuad(progress);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let badgeAlpha = 1.0;
    if (progress < 0.1) {
      badgeAlpha = progress / 0.1;
    } else if (progress > 0.85) {
      badgeAlpha = Math.max(0, (1.0 - progress) / 0.15);
    }

    activeList.forEach(pkt => {
      const srcId = pkt.source_num || pkt.source;
      const tgtId = pkt.target_num || pkt.target;
      const srcNode = getNodeElement(srcId);
      const tgtNode = getNodeElement(tgtId);
      if (!srcNode || !tgtNode) return;

      const p1 = srcNode.renderedPosition();
      const p2 = tgtNode.renderedPosition();

      const curX = p1.x + (p2.x - p1.x) * ease;
      const curY = p1.y + (p2.y - p1.y) * ease;

      const pktColor = pkt.color || "#0891b2";

      // Animated traveling packet particle
      ctx.save();
      ctx.globalAlpha = Math.min(1.0, badgeAlpha + 0.2);
      ctx.beginPath();
      ctx.arc(curX, curY, 5.0, 0, Math.PI * 2);
      ctx.fillStyle = pktColor;
      ctx.shadowBlur = 10;
      ctx.shadowColor = pktColor;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(curX, curY, 2.0, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.restore();

      // Floating pill badge moving synchronously above particle dot
      if (badgeAlpha > 0.05) {
        const badgeLabel = pkt.label || "SIG: {...}";
        const badgeBg = `rgba(15, 23, 42, ${0.90 * badgeAlpha})`;
        const textColor = "#22d3ee"; // Bright cyan
        const borderColor = `rgba(34, 211, 238, ${0.8 * badgeAlpha})`;

        ctx.save();
        ctx.globalAlpha = badgeAlpha;
        drawCanvasFloatingBadge(
          ctx,
          badgeLabel,
          curX,
          curY - 16,
          badgeBg,
          textColor,
          borderColor
        );
        ctx.restore();
      }
    });

    // When packets arrive (progress near 0.90-1.0), pulse receiving initiator nodes
    if (progress >= 0.90) {
      const pulseProg = (progress - 0.90) / 0.10;
      const pulseAlpha = Math.sin(pulseProg * Math.PI) * 0.9;
      const initiatorIds = [2, 4, 8];

      ctx.save();
      initiatorIds.forEach(id => {
        const nodeEl = getNodeElement(id);
        if (nodeEl) {
          const pos = nodeEl.renderedPosition();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 24 + pulseProg * 10, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(6, 182, 212, ${pulseAlpha})`;
          ctx.lineWidth = 3.5;
          ctx.shadowColor = "#06b6d4";
          ctx.shadowBlur = 12;
          ctx.stroke();
        }
      });
      ctx.restore();
    }

    if (progress < 1.0) {
      activeAnimationId = requestAnimationFrame(runFrame);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setTimeout(() => {
        if (currentStep === 11) {
          animateStep11SignaturePackets(packets, allNodes);
        }
      }, 1900);
    }
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 8i. Storyboard Step 12: Intra-Zone Semantic Clustering (Affinity Propagation)
function renderStep12(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 12: INTRA-ZONE SEMANTIC CLUSTERING (AP)";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-violet-50 text-violet-800 border border-violet-300";
  });

  renderSidebarFormula(
    "Step 12: Intra-Zone Semantic Clustering",
    "\\text{Sim}(i, j) = \\frac{|\\mathbf{m}_i \\cap \\mathbf{m}_j|}{3}, \\quad \\text{AP}(S) \\to \\mathcal{C}_k",
    "Initiators run Affinity Propagation on intra-zone cosine similarities to partition peers into semantic clusters.",
    "Step 12: AP Clustering",
    false,
    "violet"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 12: Intra-Zone Semantic Clustering (Cosine Similarity & AP)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>3 Initiators Formed Clusters (<span class="text-emerald-700 font-bold">Zone 2</span>: 2, <span class="text-orange-700 font-bold">Zone 4</span>: 2, <span class="text-purple-700 font-bold">Zone 8</span>: 3) → <span class="text-violet-700 font-bold font-mono">AP Partitioning</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Zone colors and luminous cluster halos
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false,
    clusterHalos: true
  });

  logToTerminal("ZONE", "[STEP 12] Intra-Zone Semantic Clustering initialized via Affinity Propagation (AP).");
  logToTerminal("INFO", "Zone 2 Initiator C2 computed 3x3 Cosine Similarity matrix: Sim(1,2)=1.0, Sim(1,3)=0.0, Sim(2,3)=0.0.");
  logToTerminal("SUCCESS", "Zone 2 partitioned into 2 clusters: Cluster 2-A {C1, C2} (Exemplar C2) & Cluster 2-B {C3} (Exemplar C3).");
  logToTerminal("INFO", "Zone 4 Initiator C4 computed 4x4 Cosine Similarity matrix: Sim(4,5)=1.0, Sim(6,7)=0.67, cross-pairs=0.0.");
  logToTerminal("SUCCESS", "Zone 4 partitioned into 2 clusters: Cluster 4-A {C4, C5} (Exemplar C4) & Cluster 4-B {C6, C7} (Exemplar C6).");
  logToTerminal("INFO", "Zone 8 Initiator C8 computed 3x3 Cosine Similarity matrix: All non-diagonal similarities = 0.0.");
  logToTerminal("SUCCESS", "Zone 8 partitioned into 3 orthogonal clusters: Cluster 8-A {C8}, Cluster 8-B {C9}, Cluster 8-C {C10}.");
  logToTerminal("INFO", "Orthogonal distribution in Zone 8 highlights necessity for inter-zone Semantic Overlay links in Step 13.");
}

// 8j. Storyboard Step 13: Intra-Zone Cluster Exemplar Designation & Profile Assignment
function renderStep13(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 13: CLUSTER EXEMPLAR DESIGNATION";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 border border-amber-400";
  });

  renderSidebarFormula(
    "Step 13: Intra-Zone Cluster Exemplar Designation & Profile Assignment",
    "\\mathcal{C}_k \\xrightarrow{\\text{AP}} e_k \\in \\mathcal{V}_k, \\quad \\text{ORDER\\_SET\\_EXEMPLAR}(e_k, \\mathbf{s}_{\\mathcal{C}_k})",
    "Zone initiators assign official cluster exemplars and dispatch representative profile signatures.",
    "Step 13: Exemplars",
    false,
    "gold"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 13: Intra-Zone Cluster Exemplar Designation & Profile Assignment";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>7 Cluster Exemplars Designated (<span class="text-emerald-700 font-bold">C1, C3</span>, <span class="text-orange-700 font-bold">C5, C7</span>, <span class="text-purple-700 font-bold">C8, C9, C10</span>) → <span class="text-amber-700 font-bold font-mono">ORDER_SET_EXEMPLAR Active</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Zone colors, cluster halos, and star exemplar badges
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false,
    clusterHalos: true,
    isStep13Exemplars: true
  });
  if (cy) {
    cy.autoungrabify(true);
    cy.nodes().lock();
  }

  logToTerminal("ZONE", "[STEP 13] Intra-Zone Cluster Exemplar Designation & Profile Assignment initiated.");
  logToTerminal("INFO", "Zone 2 Initiator C2 designated Exemplar C1 (Cluster 2-A: {C1, C2}) and Exemplar C3 (Cluster 2-B: {C3}).");
  logToTerminal("INFO", "Zone 4 Initiator C4 designated Exemplar C5 (Cluster 4-A: {C4, C5}) and Exemplar C7 (Cluster 4-B: {C6, C7}).");
  logToTerminal("INFO", "Zone 8 Initiator C8 designated Exemplars C8 (Cluster 8-A: {C8}), C9 (Cluster 8-B: {C9}), C10 (Cluster 8-C: {C10}).");
  logToTerminal("SUCCESS", "Zone initiators transmitted ORDER_SET_EXEMPLAR control packets containing representative cluster profile signatures.");

  const packets = data.order_set_exemplar_events || data.packet_events || [];
  animateStep13Exemplars(packets, data.nodes);
}

// Animate Step 13: Transmission of ORDER_SET_EXEMPLAR from Initiators to Exemplars + Golden Star Badges
function animateStep13Exemplars(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 4000; // ms per cycle
  const startTime = performance.now();

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = (elapsed % duration) / duration;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get rendered coordinates for all 10 nodes
    const nodeCoords = {};
    for (let i = 1; i <= 10; i++) {
      const el = getNodeElement(i);
      if (el) nodeCoords[i] = el.renderedPosition();
    }

    if (!nodeCoords[2] || !nodeCoords[4] || !nodeCoords[8]) {
      activeAnimationId = requestAnimationFrame(runFrame);
      return;
    }

    // Exemplar definitions (strictly direct 1-hop physical links)
    const exemplarDefs = [
      { id: 1, cluster: "2-A", init: 2, path: [2, 1] },
      { id: 3, cluster: "2-B", init: 2, path: [2, 3] },
      { id: 5, cluster: "4-A", init: 4, path: [4, 5] },
      { id: 7, cluster: "4-B", init: 4, path: [4, 7] },
      { id: 8, cluster: "8-A", init: 8, path: [8, 8] },
      { id: 9, cluster: "8-B", init: 8, path: [8, 9] },
      { id: 10, cluster: "8-C", init: 8, path: [8, 10] }
    ];

    // Status Banner at top center of canvas
    ctx.save();
    const midX = (nodeCoords[2].x + nodeCoords[8].x) / 2;
    const midY = nodeCoords[4].y - 50;
    ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
    const statusTxt = progress < 0.65
      ? "DISPATCHING ORDER_SET_EXEMPLAR CONTROL PACKETS"
      : "⭐ 7 CLUSTER EXEMPLARS DESIGNATED & PROFILES ASSIGNED";
    const sW = ctx.measureText(statusTxt).width;
    ctx.fillStyle = progress < 0.65 ? "rgba(30, 41, 59, 0.92)" : "rgba(120, 53, 15, 0.95)";
    ctx.strokeStyle = progress < 0.65 ? "#f59e0b" : "#fbbf24";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.roundRect(midX - sW / 2 - 10, midY - 11, sW + 20, 22, 5);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = progress < 0.65 ? "#fef08a" : "#fef3c7";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(statusTxt, midX, midY);
    ctx.restore();

    // Packet Transit Phase (progress < 0.65)
    if (progress < 0.65) {
      const transitProg = progress / 0.65;
      const easeT = easeInOutQuad(transitProg);

      exemplarDefs.forEach(ex => {
        if (ex.id === ex.init) {
          // Local designation (Node 8): Pulsing circle around C8
          const p = nodeCoords[8];
          if (p) {
            ctx.save();
            const pulseR = 24 + easeT * 18;
            ctx.beginPath();
            ctx.arc(p.x, p.y, pulseR, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(245, 158, 11, 0.85)";
            ctx.lineWidth = 2.5;
            ctx.stroke();
            ctx.restore();
          }
        } else {
          // Multi-hop or single hop path
          const path = ex.path;
          let curX, curY;
          if (path.length === 2) {
            const pFrom = nodeCoords[path[0]];
            const pTo = nodeCoords[path[1]];
            if (pFrom && pTo) {
              curX = pFrom.x + (pTo.x - pFrom.x) * easeT;
              curY = pFrom.y + (pTo.y - pFrom.y) * easeT;
            }
          } else if (path.length === 3) {
            const pFrom = nodeCoords[path[0]];
            const pMid = nodeCoords[path[1]];
            const pTo = nodeCoords[path[2]];
            if (pFrom && pMid && pTo) {
              if (easeT < 0.5) {
                const subE = easeT / 0.5;
                curX = pFrom.x + (pMid.x - pFrom.x) * subE;
                curY = pFrom.y + (pMid.y - pFrom.y) * subE;
              } else {
                const subE = (easeT - 0.5) / 0.5;
                curX = pMid.x + (pTo.x - pMid.x) * subE;
                curY = pMid.y + (pTo.y - pMid.y) * subE;
              }
            }
          }

          if (curX !== undefined && curY !== undefined) {
            drawOrderPacket(ctx, curX, curY, "#f59e0b", `ORDER_SET_EXEMPLAR (C${ex.id})`);
          }
        }
      });
    }

    // Exemplar Established Phase: Draw star badge ⭐ and golden aura on all 7 exemplar nodes
    exemplarDefs.forEach(ex => {
      const p = nodeCoords[ex.id];
      if (!p) return;

      // Halo ring
      ctx.save();
      const pulseProg = (now % 1800) / 1800;
      const r = 24 + pulseProg * 10;
      const a = (1.0 - pulseProg) * 0.8;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(245, 158, 11, ${a})`;
      ctx.lineWidth = 2.2;
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 12;
      ctx.stroke();
      ctx.restore();

      // ⭐ Floating Exemplar Badge
      ctx.save();
      const badgeY = p.y - 32;
      const bTxt = `⭐ EXEMPLAR (${ex.cluster})`;
      ctx.font = "bold 8.5px ui-monospace, SFMono-Regular, monospace";
      const bW = ctx.measureText(bTxt).width;
      ctx.fillStyle = "rgba(254, 243, 199, 0.95)";
      ctx.strokeStyle = "#d97706";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(p.x - bW / 2 - 6, badgeY - 9, bW + 12, 18, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#78350f";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(bTxt, p.x, badgeY);
      ctx.restore();
    });

    activeAnimationId = requestAnimationFrame(runFrame);
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// Helper: Draw ORDER_SET_EXEMPLAR packet
function drawOrderPacket(ctx, x, y, color, label) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, 6, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.shadowBlur = 12;
  ctx.shadowColor = color;
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, 2.5, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.fill();

  if (label) {
    ctx.font = "bold 8px ui-monospace, SFMono-Regular, monospace";
    const lW = ctx.measureText(label).width;
    const boxW = lW + 10;
    const boxH = 15;
    const boxX = x - boxW / 2;
    const boxY = y + 9;

    ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(boxX, boxY, boxW, boxH, 3);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#fef08a";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, boxX + boxW / 2, boxY + boxH / 2);
  }
  ctx.restore();
}

// 8k. Storyboard Step 14: Top-Level Initiator Election & Super-Zone Creation (Figure 3(e))
function renderStep14(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 14: TOP-LEVEL INITIATOR ELECTION & SUPER-ZONE (C4 👑👑)";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 border border-amber-400";
  });

  renderSidebarFormula(
    "Step 14: Top-Level Initiator Election & Super-Zone",
    "\\mathcal{G}_{\\text{init}} = \\{I_2 \\leftrightarrow I_4 \\leftrightarrow I_8\\}, \\quad I_{\\text{top}} = C_4, \\quad \\text{TOP\\_PROBE}(C_4, \\text{TTL}=1) \\to \\mathcal{Z}_{\\text{Top}}",
    "Initiators exchange VRF scores across overlay links. Central bridge C4 is elected Top-Level Initiator and symmetrically floods TOP_PROBE to C2 and C8.",
    "Step 14: Super-Zone",
    false,
    "gold"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 14: Top-Level Initiator Election & Super-Zone Creation (Root: C4 👑👑)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>Top-Level Super-Zone (<span class="text-amber-600 font-bold">👑👑 Root: C4</span>, Members: C2, C4, C8) → <span class="text-amber-700 font-bold font-mono">Z_TOP Control Plane</span></span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render nodes with Tonal Zone colors, cluster halos, and special Top-Initiator styling for C4
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false,
    clusterHalos: true,
    isStep14: true
  });

  logToTerminal("ZONE", "[STEP 14] Hierarchical Top-Level Zone Creation initialized (Figure 3(e)).");
  logToTerminal("INFO", "Base zone initiators form higher-level overlay graph: V_init={C2, C4, C8}, E_init={(C2, C4), (C4, C8)}.");
  logToTerminal("VRF", "Phase 1 (1-Hop VRF Exchange): C2 <-> C4 (scores 0.0837 <-> 0.0412 via C1) and C4 <-> C8 (scores 0.0412 <-> 0.0275 via C6).");
  logToTerminal("SUCCESS", "Phase 2 (Election): Node C4 elected as central Top-Level Super-Initiator 👑👑 (Bridge hub connecting West & East).");
  logToTerminal("ZONE", "Phase 3 (Symmetrical Probing): Initiator C4 broadcasts TOP_PROBE(TTL=1) symmetrically to C2 (via C1) and C8 (via C6).");
  logToTerminal("SUCCESS", "Phase 4 (Super-Zone Formed): Top-Level Super-Zone Z_TOP established (Root: C4, Members: [C2, C4, C8]).");
  logToTerminal("TOPOLOGY", "Hierarchical control plane active for global cluster catalog exchange across the 14-step storyboard.");

  const packets = data.packet_events || data.packet_exchanges || [];
  animateStep14TopProbe(packets, data.nodes);
}

// Animate Step 14: Phase A (1-Hop VRF Score Exchange), Election Flash, and Phase B (Symmetrical TOP_PROBE)
function animateStep14TopProbe(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 6600; // ms per complete two-phase cycle
  const startTime = performance.now();

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = (elapsed % duration) / duration;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const n8 = getNodeElement(8);
    const n6 = getNodeElement(6);
    const n4 = getNodeElement(4);
    const n1 = getNodeElement(1);
    const n2 = getNodeElement(2);

    if (!n4 || !n2 || !n8) {
      activeAnimationId = requestAnimationFrame(runFrame);
      return;
    }

    const p4 = n4.renderedPosition();
    const p1 = n1 ? n1.renderedPosition() : null;
    const p2 = n2.renderedPosition();
    const p6 = n6 ? n6.renderedPosition() : null;
    const p8 = n8.renderedPosition();

    // 1. High-Level Super-Zone Envelope encompassing C2, C4, C8
    ctx.save();
    ctx.beginPath();
    const topPad = 46;
    const sidePad = 48;
    const botPad = 44;

    ctx.moveTo(p4.x, p4.y - topPad - 8);
    ctx.bezierCurveTo(p4.x + 140, p4.y - topPad + 4, p8.x + sidePad, p8.y - topPad + 10, p8.x + sidePad, p8.y);
    ctx.bezierCurveTo(p8.x + sidePad, p8.y + botPad, p8.x - 30, p8.y + botPad, (p8.x + p2.x) / 2, p8.y + botPad - 8);
    ctx.bezierCurveTo(p2.x + 30, p2.y + botPad, p2.x - sidePad, p2.y + botPad, p2.x - sidePad, p2.y);
    ctx.bezierCurveTo(p2.x - sidePad, p2.y - topPad + 10, p4.x - sidePad - 10, p4.y - topPad + 4, p4.x, p4.y - topPad - 8);
    ctx.closePath();

    const envGrad = ctx.createLinearGradient(p2.x, p4.y, p8.x, p8.y);
    envGrad.addColorStop(0, "rgba(234, 179, 8, 0.05)");
    envGrad.addColorStop(0.5, "rgba(245, 158, 11, 0.08)");
    envGrad.addColorStop(1, "rgba(234, 179, 8, 0.07)");
    ctx.fillStyle = envGrad;
    ctx.fill();

    ctx.strokeStyle = "rgba(234, 179, 8, 0.45)";
    ctx.lineWidth = 2.0;
    ctx.setLineDash([8, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // Floating Badge Pill for Super-Zone Envelope
    ctx.save();
    const badgeX = p4.x;
    const badgeY = p4.y - 56;
    ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, Menlo, Monaco, monospace";
    const badgeText = "👑👑 SUPER-ZONE Z_TOP (ROOT: C4)";
    const textW = ctx.measureText(badgeText).width;
    ctx.fillStyle = "rgba(254, 243, 199, 0.96)";
    ctx.strokeStyle = "#eab308";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.roundRect(badgeX - textW / 2 - 8, badgeY - 12, textW + 16, 20, 6);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#92400e";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(badgeText, badgeX, badgeY - 2);
    ctx.restore();

    // 2. Distinct Golden Connecting Backbone along C2 ↔ C1 ↔ C4 ↔ C6 ↔ C8
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(p2.x, p2.y);
    if (p1) ctx.lineTo(p1.x, p1.y);
    ctx.lineTo(p4.x, p4.y);
    if (p6) ctx.lineTo(p6.x, p6.y);
    ctx.lineTo(p8.x, p8.y);
    ctx.strokeStyle = "rgba(234, 179, 8, 0.70)";
    ctx.lineWidth = 2.8;
    ctx.shadowColor = "#eab308";
    ctx.shadowBlur = 14;
    ctx.setLineDash([7, 5]);
    ctx.lineDashOffset = -(now / 35); // Animated forward marching dash
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 3. Glowing Gold Aura & Floating Double-Crown around Elected Root Initiator Node 4
    ctx.save();
    const auraProg = (now % 1600) / 1600;
    const auraR = 28 + auraProg * 22;
    const auraA = (1.0 - auraProg) * 0.90;
    ctx.beginPath();
    ctx.arc(p4.x, p4.y, auraR, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(234, 179, 8, ${auraA})`;
    ctx.lineWidth = 3.2;
    ctx.shadowColor = "#eab308";
    ctx.shadowBlur = 20;
    ctx.stroke();

    // Floating 👑👑 crown icon above C4
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("👑👑", p4.x, p4.y - 32);
    ctx.restore();

    // 4. Subtle Super-Zone Member Aura on Node 2 and Node 8
    [p2, p8].forEach(p => {
      ctx.save();
      const mProg = ((now + 400) % 2000) / 2000;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 25 + mProg * 12, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(245, 158, 11, ${(1.0 - mProg) * 0.65})`;
      ctx.lineWidth = 2.2;
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 10;
      ctx.stroke();
      ctx.restore();
    });

    // 4-Step Canvas Animation Sequence for Step 13:
    // Step A (progress < 0.28): Inward reporting C2 -> C4 (VRF: 0.0837) & C8 -> C4 (VRF: 0.0275)
    // Step B (0.28 <= progress < 0.56): Outward relay C4 -> C2 ({C4:0.0412, C8:0.0275}) & C4 -> C8 ({C4:0.0412, C2:0.0837})
    // Step C (0.56 <= progress < 0.72): Node 4 flashes golden halo and receives 👑👑 TOP INITIATOR badge
    // Step D (0.72 <= progress <= 1.0): Golden TOP_PROBE pulses spread simultaneously C4 -> C2 and C4 -> C8

    if (progress < 0.28) {
      // ===== STEP A: INWARD VRF SCORE REPORTING (C2 & C8 ➔ C4) =====
      const subA = progress / 0.28;
      const easeA = easeInOutQuad(subA);

      // Step A Status Banner
      ctx.save();
      const statusX = (p2.x + p8.x) / 2;
      const statusY = p4.y + 42;
      ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
      const statTxt = "STEP A: INWARD VRF REPORTING (C2 & C8 ➔ C4)";
      const sW = ctx.measureText(statTxt).width;
      ctx.fillStyle = "rgba(30, 41, 59, 0.92)";
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(statusX - sW / 2 - 8, statusY - 10, sW + 16, 18, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#38bdf8";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(statTxt, statusX, statusY);
      ctx.restore();

      // Exchange 1: C2 -> C4 via C1 (carrying VRF: 0.0837)
      let x2_4, y2_4;
      const tgt1 = p1 || p4;
      if (subA < 0.5) {
        const seg = subA / 0.5;
        const e = easeInOutQuad(seg);
        x2_4 = p2.x + (tgt1.x - p2.x) * e;
        y2_4 = p2.y + (tgt1.y - p2.y) * e;
      } else {
        const seg = (subA - 0.5) / 0.5;
        const e = easeInOutQuad(seg);
        x2_4 = tgt1.x + (p4.x - tgt1.x) * e;
        y2_4 = tgt1.y + (p4.y - tgt1.y) * e;
      }

      // Exchange 2: C8 -> C4 via C6 (carrying VRF: 0.0275)
      let x8_4, y8_4;
      const tgt6 = p6 || p4;
      if (subA < 0.5) {
        const seg = subA / 0.5;
        const e = easeInOutQuad(seg);
        x8_4 = p8.x + (tgt6.x - p8.x) * e;
        y8_4 = p8.y + (tgt6.y - p8.y) * e;
      } else {
        const seg = (subA - 0.5) / 0.5;
        const e = easeInOutQuad(seg);
        x8_4 = tgt6.x + (p4.x - tgt6.x) * e;
        y8_4 = tgt6.y + (p4.y - tgt6.y) * e;
      }

      // Render inward packets
      drawVrfPacket(ctx, x2_4, y2_4, "#3b82f6", "VRF: 0.0837");
      drawVrfPacket(ctx, x8_4, y8_4, "#8b5cf6", "VRF: 0.0275");

    } else if (progress < 0.56) {
      // ===== STEP B: OUTWARD RELAY OF DISSEMINATED SCORES FROM C4 =====
      const subB = (progress - 0.28) / 0.28;
      const easeB = easeInOutQuad(subB);

      // Step B Status Banner
      ctx.save();
      const statusX = (p2.x + p8.x) / 2;
      const statusY = p4.y + 42;
      ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
      const statTxt = "STEP B: C4 OUTWARD RELAY OF DISSEMINATED SCORES";
      const sW = ctx.measureText(statTxt).width;
      ctx.fillStyle = "rgba(30, 41, 59, 0.92)";
      ctx.strokeStyle = "#f97316";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(statusX - sW / 2 - 8, statusY - 10, sW + 16, 18, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#fdba74";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(statTxt, statusX, statusY);
      ctx.restore();

      // Relay 1: C4 -> C2 via C1 (carrying SCORES: {C4:0.0412, C8:0.0275})
      let x4_2, y4_2;
      const tgt1 = p1 || p2;
      if (subB < 0.5) {
        const seg = subB / 0.5;
        const e = easeInOutQuad(seg);
        x4_2 = p4.x + (tgt1.x - p4.x) * e;
        y4_2 = p4.y + (tgt1.y - p4.y) * e;
      } else {
        const seg = (subB - 0.5) / 0.5;
        const e = easeInOutQuad(seg);
        x4_2 = tgt1.x + (p2.x - tgt1.x) * e;
        y4_2 = tgt1.y + (p2.y - tgt1.y) * e;
      }

      // Relay 2: C4 -> C8 via C6 (carrying SCORES: {C4:0.0412, C2:0.0837})
      let x4_8, y4_8;
      const tgt6 = p6 || p8;
      if (subB < 0.5) {
        const seg = subB / 0.5;
        const e = easeInOutQuad(seg);
        x4_8 = p4.x + (tgt6.x - p4.x) * e;
        y4_8 = p4.y + (tgt6.y - p4.y) * e;
      } else {
        const seg = (subB - 0.5) / 0.5;
        const e = easeInOutQuad(seg);
        x4_8 = tgt6.x + (p8.x - tgt6.x) * e;
        y4_8 = tgt6.y + (p8.y - tgt6.y) * e;
      }

      // Render outward relay packets
      drawVrfPacket(ctx, x4_2, y4_2, "#f97316", "SCORES: {C4:0.0412, C8:0.0275}", true);
      drawVrfPacket(ctx, x4_8, y4_8, "#f97316", "SCORES: {C4:0.0412, C2:0.0837}", false);

    } else if (progress < 0.72) {
      // ===== STEP C: NODE 4 FLASHES GOLDEN HALO & RECEIVES TOP INITIATOR BADGE =====
      const subC = (progress - 0.56) / 0.16;
      const easeC = easeInOutQuad(subC);
      const eRing1 = 28 + easeC * 44;
      const eRing2 = 18 + easeC * 28;
      const eA = Math.sin(subC * Math.PI) * 0.98;

      ctx.save();
      // Outer flashing golden halo
      ctx.beginPath();
      ctx.arc(p4.x, p4.y, eRing1, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(234, 179, 8, ${eA})`;
      ctx.lineWidth = 4;
      ctx.shadowColor = "#eab308";
      ctx.shadowBlur = 28;
      ctx.stroke();

      // Inner pulsating halo
      ctx.beginPath();
      ctx.arc(p4.x, p4.y, eRing2, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(251, 191, 36, ${eA * 0.85})`;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // 👑👑 TOP INITIATOR badge above C4
      const badgeY = p4.y - 36;
      const badgeTxt = "👑👑 TOP INITIATOR";
      ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
      const bW = ctx.measureText(badgeTxt).width;
      ctx.fillStyle = "rgba(120, 53, 15, 0.96)";
      ctx.strokeStyle = "#fbbf24";
      ctx.lineWidth = 1.3;
      ctx.beginPath();
      ctx.roundRect(p4.x - bW / 2 - 8, badgeY - 10, bW + 16, 20, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#fef3c7";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(badgeTxt, p4.x, badgeY);

      // Announcement Banner
      const aX = (p2.x + p8.x) / 2;
      const aY = p4.y + 42;
      ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
      const aText = "STEP C: NODE C4 ELECTED TOP-LEVEL INITIATOR (CENTRAL BRIDGE)";
      const aW = ctx.measureText(aText).width;
      ctx.fillStyle = "rgba(120, 53, 15, 0.95)";
      ctx.strokeStyle = "#fbbf24";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(aX - aW / 2 - 8, aY - 10, aW + 16, 20, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#fef3c7";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(aText, aX, aY);
      ctx.restore();

    } else {
      // ===== STEP D: GOLDEN TOP_PROBE PULSES SPREAD SIMULTANEOUSLY (C4 ➔ C2 & C8) =====
      const subD = (progress - 0.72) / 0.28;
      const easeD = easeInOutQuad(subD);

      // Step D Status Banner
      ctx.save();
      const statusX = (p2.x + p8.x) / 2;
      const statusY = p4.y + 42;
      ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
      const statTxt = "STEP D: SYMMETRICAL TOP_PROBE BROADCAST (C4 ➔ C2 & C8)";
      const sW = ctx.measureText(statTxt).width;
      ctx.fillStyle = "rgba(30, 41, 59, 0.90)";
      ctx.strokeStyle = "#eab308";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(statusX - sW / 2 - 8, statusY - 10, sW + 16, 18, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#fef08a";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(statTxt, statusX, statusY);

      // Retain 👑👑 TOP INITIATOR badge above C4
      const badgeY = p4.y - 36;
      const badgeTxt = "👑👑 TOP INITIATOR";
      ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
      const bW = ctx.measureText(badgeTxt).width;
      ctx.fillStyle = "rgba(120, 53, 15, 0.96)";
      ctx.strokeStyle = "#fbbf24";
      ctx.lineWidth = 1.3;
      ctx.beginPath();
      ctx.roundRect(p4.x - bW / 2 - 8, badgeY - 10, bW + 16, 20, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#fef3c7";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(badgeTxt, p4.x, badgeY);
      ctx.restore();

      // 1. Symmetrical Outward West Branch: C4 -> C1 -> C2
      let westX, westY;
      const tgt1 = p1 || p2;
      if (subD < 0.5) {
        const seg = subD / 0.5;
        const e = easeInOutQuad(seg);
        westX = p4.x + (tgt1.x - p4.x) * e;
        westY = p4.y + (tgt1.y - p4.y) * e;
      } else {
        const seg = (subD - 0.5) / 0.5;
        const e = easeInOutQuad(seg);
        westX = tgt1.x + (p2.x - tgt1.x) * e;
        westY = tgt1.y + (p2.y - tgt1.y) * e;
      }

      // 2. Symmetrical Outward East Branch: C4 -> C6 -> C8
      let eastX, eastY;
      const tgt6 = p6 || p8;
      if (subD < 0.5) {
        const seg = subD / 0.5;
        const e = easeInOutQuad(seg);
        eastX = p4.x + (tgt6.x - p4.x) * e;
        eastY = p4.y + (tgt6.y - p4.y) * e;
      } else {
        const seg = (subD - 0.5) / 0.5;
        const e = easeInOutQuad(seg);
        eastX = tgt6.x + (p8.x - tgt6.x) * e;
        eastY = tgt6.y + (p8.y - tgt6.y) * e;
      }

      // Gateway Relay Glow on C1 and C6 when traversed
      if (subD >= 0.42 && subD <= 0.58) {
        const gProg = (subD - 0.42) / 0.16;
        const gA = Math.sin(gProg * Math.PI) * 0.95;
        [p1, p6].filter(Boolean).forEach(p => {
          ctx.save();
          ctx.beginPath();
          ctx.arc(p.x, p.y, 25 + gProg * 8, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(234, 179, 8, ${gA})`;
          ctx.lineWidth = 3.0;
          ctx.shadowColor = "#eab308";
          ctx.shadowBlur = 18;
          ctx.stroke();
          ctx.restore();
        });
      }

      // Render traveling golden TOP_PROBE packets
      drawTopProbePacket(ctx, westX, westY, "TOP_PROBE(TTL=1) ➔ C2");
      drawTopProbePacket(ctx, eastX, eastY, "TOP_PROBE(TTL=1) ➔ C8");

      // Simultaneous Arrival flash at C2 and C8 (subD >= 0.88)
      if (subD >= 0.88) {
        const arrProg = (subD - 0.88) / 0.12;
        const arrA = (1.0 - arrProg) * 0.92;
        [p2, p8].forEach(p => {
          ctx.save();
          ctx.beginPath();
          ctx.arc(p.x, p.y, 25 + arrProg * 16, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(234, 179, 8, ${arrA})`;
          ctx.lineWidth = 3.2;
          ctx.shadowColor = "#eab308";
          ctx.shadowBlur = 18;
          ctx.stroke();
          ctx.restore();
        });
      }
    }

    activeAnimationId = requestAnimationFrame(runFrame);
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// Helper: Draw VRF exchange traveling particle
function drawVrfPacket(ctx, x, y, color, label, alignLeft = false) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, 6, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.shadowBlur = 12;
  ctx.shadowColor = color;
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, 2.5, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.fill();

  if (label) {
    ctx.font = "bold 8.5px ui-monospace, SFMono-Regular, monospace";
    const lW = ctx.measureText(label).width;
    const boxW = lW + 10;
    const boxH = 16;
    const canvasW = ctx.canvas ? ctx.canvas.width : 1000;
    const placeLeft = alignLeft || (x + 8 + boxW > canvasW - 15);
    const boxX = placeLeft ? (x - boxW - 8) : (x + 8);
    const boxY = y - boxH / 2;

    ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(boxX, boxY, boxW, boxH, 3);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, boxX + boxW / 2, boxY + boxH / 2);
  }
  ctx.restore();
}

// Helper: Draw TOP_PROBE golden traveling particle
function drawTopProbePacket(ctx, x, y, label) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, 7, 0, Math.PI * 2);
  ctx.fillStyle = "#eab308";
  ctx.shadowBlur = 16;
  ctx.shadowColor = "#eab308";
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, 3, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.fill();

  ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
  const lW = ctx.measureText(label).width;
  ctx.fillStyle = "rgba(120, 53, 15, 0.94)";
  ctx.strokeStyle = "#fbbf24";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(x + 9, y - 13, lW + 10, 16, 4);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#fef3c7";
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(label, x + 14, y - 5);
  ctx.restore();
}

// Helper: Draw REQ_CLUSTER_CATALOG cyan/golden traveling particle
function drawCatalogQueryPacket(ctx, x, y, label) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, 7.5, 0, Math.PI * 2);
  ctx.fillStyle = "#06b6d4";
  ctx.shadowBlur = 18;
  ctx.shadowColor = "#06b6d4";
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, 3.5, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.fill();

  ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
  const lW = ctx.measureText(label).width;
  ctx.fillStyle = "rgba(8, 51, 68, 0.95)";
  ctx.strokeStyle = "#22d3ee";
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.roundRect(x + 9, y - 13, lW + 10, 16, 4);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#cffafe";
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(label, x + 14, y - 5);
  ctx.restore();
}

function renderStep15(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 15: TOP-LEVEL CATALOG QUERY DISPATCH";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-cyan-50 text-cyan-900 border border-cyan-400";
  });

  renderSidebarFormula(
    "Step 15: Top-Level Catalog Query Dispatch",
    "\\text{REQ\\_CLUSTER\\_CATALOG}(C_4) \\xrightarrow{\\text{overlay}} \\{C_2, C_8\\}",
    "Super-Initiator C4 requests intra-zone cluster metadata from base initiators across boundary routes.",
    "Step 15: Catalog Query",
    false,
    "cyan"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 15: Top-Level Catalog Query Dispatch (REQ_CLUSTER_CATALOG from C4 👑👑)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.remove("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>Super-Initiator <span class="text-amber-600 font-bold">👑👑 C4</span> dispatches <span class="text-cyan-700 font-bold font-mono">REQ_CLUSTER_CATALOG</span> ➔ C2 & C8</span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render Cytoscape network maintaining super-zone, exemplars, and zones
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false,
    clusterHalos: true,
    isStep15: true,
    isStep13Exemplars: true
  });

  logToTerminal("ZONE", "[STEP 15] Top-Level Catalog Query Dispatch initialized (REQ_CLUSTER_CATALOG).");
  logToTerminal("INFO", "Super-Initiator C4 initiates global cluster catalog discovery across Super-Zone Z_TOP.");
  logToTerminal("QUERY", "Westbound Query: C4 ➔ C1 (relay gateway) ➔ C2 [path: 4-1-2] with payload REQ_CLUSTER_CATALOG.");
  logToTerminal("QUERY", "Eastbound Query: C4 ➔ C6 (relay gateway) ➔ C8 [path: 4-6-8] with payload REQ_CLUSTER_CATALOG.");
  logToTerminal("SUCCESS", "Initiator C2 received REQ_CLUSTER_CATALOG: Status set to RECEIVED_PENDING_RESPONSE.");
  logToTerminal("SUCCESS", "Initiator C8 received REQ_CLUSTER_CATALOG: Status set to RECEIVED_PENDING_RESPONSE.");
  logToTerminal("INFO", "Cluster catalog response transmission and global alignment scheduled for Step 16.");

  const packets = data.packet_events || data.packet_traces || [];
  animateStep15CatalogQuery(packets, data.nodes);
}

// Animate Step 15: Outward golden/cyan packet traces C4 -> C1 -> C2 and C4 -> C6 -> C8
function animateStep15CatalogQuery(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 4800; // ms per complete query dispatch cycle
  const startTime = performance.now();

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = (elapsed % duration) / duration;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const n8 = getNodeElement(8);
    const n6 = getNodeElement(6);
    const n4 = getNodeElement(4);
    const n1 = getNodeElement(1);
    const n2 = getNodeElement(2);

    if (!n4 || !n2 || !n8) {
      activeAnimationId = requestAnimationFrame(runFrame);
      return;
    }

    const p4 = n4.renderedPosition();
    const p1 = n1 ? n1.renderedPosition() : null;
    const p2 = n2.renderedPosition();
    const p6 = n6 ? n6.renderedPosition() : null;
    const p8 = n8.renderedPosition();

    // 1. Static Super-Zone Envelope encompassing C2, C4, C8
    ctx.save();
    ctx.beginPath();
    const topPad = 46;
    const sidePad = 48;
    const botPad = 44;

    ctx.moveTo(p4.x, p4.y - topPad - 8);
    ctx.bezierCurveTo(p4.x + 140, p4.y - topPad + 4, p8.x + sidePad, p8.y - topPad + 10, p8.x + sidePad, p8.y);
    ctx.bezierCurveTo(p8.x + sidePad, p8.y + botPad, p8.x - 30, p8.y + botPad, (p8.x + p2.x) / 2, p8.y + botPad - 8);
    ctx.bezierCurveTo(p2.x + 30, p2.y + botPad, p2.x - sidePad, p2.y + botPad, p2.x - sidePad, p2.y);
    ctx.bezierCurveTo(p2.x - sidePad, p2.y - topPad + 10, p4.x - sidePad - 10, p4.y - topPad + 4, p4.x, p4.y - topPad - 8);
    ctx.closePath();

    const envGrad = ctx.createLinearGradient(p2.x, p4.y, p8.x, p8.y);
    envGrad.addColorStop(0, "rgba(6, 182, 212, 0.05)");
    envGrad.addColorStop(0.5, "rgba(234, 179, 8, 0.06)");
    envGrad.addColorStop(1, "rgba(6, 182, 212, 0.05)");
    ctx.fillStyle = envGrad;
    ctx.fill();

    ctx.strokeStyle = "rgba(6, 182, 212, 0.40)";
    ctx.lineWidth = 1.8;
    ctx.setLineDash([8, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 2. Connecting Backbone C2 <-> C1 <-> C4 <-> C6 <-> C8
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(p2.x, p2.y);
    if (p1) ctx.lineTo(p1.x, p1.y);
    ctx.lineTo(p4.x, p4.y);
    if (p6) ctx.lineTo(p6.x, p6.y);
    ctx.lineTo(p8.x, p8.y);
    ctx.strokeStyle = "rgba(6, 182, 212, 0.65)";
    ctx.lineWidth = 2.4;
    ctx.shadowColor = "#06b6d4";
    ctx.shadowBlur = 12;
    ctx.setLineDash([6, 5]);
    ctx.lineDashOffset = -(now / 30);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 3. Super-Initiator C4 Golden Pulsing Aura
    ctx.save();
    const auraProg = (now % 1500) / 1500;
    const auraR = 26 + auraProg * 18;
    const auraA = (1.0 - auraProg) * 0.85;
    ctx.beginPath();
    ctx.arc(p4.x, p4.y, auraR, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(234, 179, 8, ${auraA})`;
    ctx.lineWidth = 3.0;
    ctx.shadowColor = "#eab308";
    ctx.shadowBlur = 16;
    ctx.stroke();

    ctx.font = "bold 13px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("👑👑", p4.x, p4.y - 30);
    ctx.restore();

    // 4. Status Announcement Banner
    ctx.save();
    const aX = (p2.x + p8.x) / 2;
    const aY = p4.y + 44;
    ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
    const aText = "REQ_CLUSTER_CATALOG: C4 DISPATCHES QUERY TO C2 AND C8";
    const aW = ctx.measureText(aText).width;
    ctx.fillStyle = "rgba(8, 51, 68, 0.95)";
    ctx.strokeStyle = "#22d3ee";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.roundRect(aX - aW / 2 - 8, aY - 10, aW + 16, 20, 4);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#cffafe";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(aText, aX, aY);
    ctx.restore();

    // 5. Directional Multi-Hop Traveling Packets C4 -> C1 -> C2 & C4 -> C6 -> C8
    const ease = easeInOutQuad(progress);

    // West Branch: C4 -> C1 -> C2
    let westX, westY;
    const tgt1 = p1 || p2;
    if (progress < 0.5) {
      const seg = progress / 0.5;
      const e = easeInOutQuad(seg);
      westX = p4.x + (tgt1.x - p4.x) * e;
      westY = p4.y + (tgt1.y - p4.y) * e;
    } else {
      const seg = (progress - 0.5) / 0.5;
      const e = easeInOutQuad(seg);
      westX = tgt1.x + (p2.x - tgt1.x) * e;
      westY = tgt1.y + (p2.y - tgt1.y) * e;
    }

    // East Branch: C4 -> C6 -> C8
    let eastX, eastY;
    const tgt6 = p6 || p8;
    if (progress < 0.5) {
      const seg = progress / 0.5;
      const e = easeInOutQuad(seg);
      eastX = p4.x + (tgt6.x - p4.x) * e;
      eastY = p4.y + (tgt6.y - p4.y) * e;
    } else {
      const seg = (progress - 0.5) / 0.5;
      const e = easeInOutQuad(seg);
      eastX = tgt6.x + (p8.x - tgt6.x) * e;
      eastY = tgt6.y + (p8.y - tgt6.y) * e;
    }

    // Gateway Relay Glow on C1 and C6 when traversed
    if (progress >= 0.42 && progress <= 0.58) {
      const gProg = (progress - 0.42) / 0.16;
      const gA = Math.sin(gProg * Math.PI) * 0.95;
      [p1, p6].filter(Boolean).forEach(p => {
        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, 25 + gProg * 8, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${gA})`;
        ctx.lineWidth = 3.0;
        ctx.shadowColor = "#06b6d4";
        ctx.shadowBlur = 18;
        ctx.stroke();
        ctx.restore();
      });
    }

    // Render traveling packets with floating labels
    drawCatalogQueryPacket(ctx, westX, westY, "REQ_CATALOG ➔ C2");
    drawCatalogQueryPacket(ctx, eastX, eastY, "REQ_CATALOG ➔ C8");

    // Flash subtle reception rings on Node 2 and Node 8 upon arrival
    if (progress >= 0.82) {
      const arrProg = (progress - 0.82) / 0.18;
      const arrA = (1.0 - arrProg) * 0.95;
      [p2, p8].forEach(p => {
        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, 24 + arrProg * 22, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${arrA})`;
        ctx.lineWidth = 3.5;
        ctx.shadowColor = "#06b6d4";
        ctx.shadowBlur = 20;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(p.x, p.y, 16 + arrProg * 12, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(234, 179, 8, ${arrA * 0.8})`;
        ctx.lineWidth = 2.0;
        ctx.shadowColor = "#eab308";
        ctx.shadowBlur = 12;
        ctx.stroke();
        ctx.restore();
      });
    }

    activeAnimationId = requestAnimationFrame(runFrame);
  }

}

// Helper: Draw REP_CLUSTER_CATALOG emerald/golden traveling particle
function drawCatalogResponsePacket(ctx, x, y, label, color = "#10b981") {
  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, 7.5, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.shadowBlur = 18;
  ctx.shadowColor = color;
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, 3.5, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.fill();

  ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
  const lW = ctx.measureText(label).width;
  ctx.fillStyle = "rgba(6, 78, 59, 0.95)";
  ctx.strokeStyle = "#34d399";
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.roundRect(x + 9, y - 13, lW + 10, 16, 4);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#d1fae5";
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(label, x + 14, y - 5);
  ctx.restore();
}

// 5.16 STEP 16: Zone Catalog Response & Signature Ingestion at C4
function renderStep16(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 16: ZONE CATALOG RESPONSE & SIGNATURE INGESTION";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-400";
  });

  renderSidebarFormula(
    "Step 16: Zone Catalog Response & Signature Ingestion",
    "\\text{REP\\_CATALOG}(Z_2, Z_8) \\xrightarrow{\\text{boundary routes}} C_4 \\quad (\\text{Ingests 7 Cluster Masks})",
    "Base initiators transmit exemplar profiles and binary masks inward to Super-Initiator C4.",
    "Step 16: Global Catalog",
    false,
    "emerald"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 16: Zone Catalog Response & Signature Ingestion at C4 (7 Cluster Masks Ingested)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.remove("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>Super-Initiator <span class="text-amber-600 font-bold">👑👑 C4</span> ingested <span class="text-emerald-700 font-bold font-mono">7 Cluster Masks</span> from Zones 2, 4, 8</span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render Cytoscape network maintaining super-zone, exemplars, and zones
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false,
    clusterHalos: true,
    isStep16: true,
    isStep15: true,
    isStep13Exemplars: true
  });

  logToTerminal("ZONE", "[STEP 16] Zone Catalog Response & Signature Ingestion initialized (REP_CLUSTER_CATALOG).");
  logToTerminal("INFO", "Base initiators compile local intra-zone cluster profiles and respond to Super-Initiator C4.");
  logToTerminal("SUCCESS", "Inbound Response 1: C2 ➔ C1 (gateway) ➔ C4 [path: 2-1-4] with REP_CLUSTER_CATALOG (Clusters: 2-A, 2-B).");
  logToTerminal("SUCCESS", "Inbound Response 2: C8 ➔ C6 (gateway) ➔ C4 [path: 8-6-4] with REP_CLUSTER_CATALOG (Clusters: 8-A, 8-B, 8-C).");
  logToTerminal("INFO", "Local Consolidation: Super-Initiator C4 integrates local Zone 4 clusters (4-A, 4-B).");
  logToTerminal("SUCCESS", "Global Registry Assembled: 7 unique semantic clusters registered under C4's global supervision.");
  logToTerminal("SUCCESS", "Super-Initiator C4 pulses with vibrant cyan/gold glow across Super-Zone Z_TOP.");

  const packets = data.packet_events || data.packet_traces || [];
  animateStep16CatalogResponse(packets, data.nodes);
}

// Animate Step 16: Inward response packets C2 -> C1 -> C4 and C8 -> C6 -> C4 + Cyan/Gold Glow at C4
function animateStep16CatalogResponse(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 5000; // ms per complete catalog response cycle
  const startTime = performance.now();

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = (elapsed % duration) / duration;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const n8 = getNodeElement(8);
    const n6 = getNodeElement(6);
    const n4 = getNodeElement(4);
    const n1 = getNodeElement(1);
    const n2 = getNodeElement(2);

    if (!n4 || !n2 || !n8) {
      activeAnimationId = requestAnimationFrame(runFrame);
      return;
    }

    const p4 = n4.renderedPosition();
    const p1 = n1 ? n1.renderedPosition() : null;
    const p2 = n2.renderedPosition();
    const p6 = n6 ? n6.renderedPosition() : null;
    const p8 = n8.renderedPosition();

    // 1. Static Super-Zone Envelope encompassing C2, C4, C8
    ctx.save();
    ctx.beginPath();
    const topPad = 46;
    const sidePad = 48;
    const botPad = 44;

    ctx.moveTo(p4.x, p4.y - topPad - 8);
    ctx.bezierCurveTo(p4.x + 140, p4.y - topPad + 4, p8.x + sidePad, p8.y - topPad + 10, p8.x + sidePad, p8.y);
    ctx.bezierCurveTo(p8.x + sidePad, p8.y + botPad, p8.x - 30, p8.y + botPad, (p8.x + p2.x) / 2, p8.y + botPad - 8);
    ctx.bezierCurveTo(p2.x + 30, p2.y + botPad, p2.x - sidePad, p2.y + botPad, p2.x - sidePad, p2.y);
    ctx.bezierCurveTo(p2.x - sidePad, p2.y - topPad + 10, p4.x - sidePad - 10, p4.y - topPad + 4, p4.x, p4.y - topPad - 8);
    ctx.closePath();

    const envGrad = ctx.createLinearGradient(p2.x, p4.y, p8.x, p8.y);
    envGrad.addColorStop(0, "rgba(16, 185, 129, 0.05)");
    envGrad.addColorStop(0.5, "rgba(234, 179, 8, 0.08)");
    envGrad.addColorStop(1, "rgba(16, 185, 129, 0.05)");
    ctx.fillStyle = envGrad;
    ctx.fill();

    ctx.strokeStyle = "rgba(16, 185, 129, 0.45)";
    ctx.lineWidth = 1.8;
    ctx.setLineDash([8, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 2. Connecting Inward Backbone C2 <-> C1 <-> C4 <-> C6 <-> C8
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(p2.x, p2.y);
    if (p1) ctx.lineTo(p1.x, p1.y);
    ctx.lineTo(p4.x, p4.y);
    if (p6) ctx.lineTo(p6.x, p6.y);
    ctx.lineTo(p8.x, p8.y);
    ctx.strokeStyle = "rgba(16, 185, 129, 0.70)";
    ctx.lineWidth = 2.4;
    ctx.shadowColor = "#10b981";
    ctx.shadowBlur = 12;
    ctx.setLineDash([6, 5]);
    ctx.lineDashOffset = now / 30; // inward dash animation toward C4
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 3. Status Announcement Banner
    ctx.save();
    const aX = (p2.x + p8.x) / 2;
    const aY = p4.y + 44;
    ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
    const aText = "REP_CLUSTER_CATALOG: C2 & C8 TRANSMIT CATALOGS ➔ C4 (7 CLUSTERS TOTAL)";
    const aW = ctx.measureText(aText).width;
    ctx.fillStyle = "rgba(6, 78, 59, 0.95)";
    ctx.strokeStyle = "#34d399";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.roundRect(aX - aW / 2 - 8, aY - 10, aW + 16, 20, 4);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#d1fae5";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(aText, aX, aY);
    ctx.restore();

    // 4. Directional Inward Multi-Hop Packets:
    // West Branch: C2 -> C1 -> C4
    let westX, westY;
    const tgt1 = p1 || p4;
    if (progress < 0.5) {
      const seg = progress / 0.5;
      const e = easeInOutQuad(seg);
      westX = p2.x + (tgt1.x - p2.x) * e;
      westY = p2.y + (tgt1.y - p2.y) * e;
    } else {
      const seg = (progress - 0.5) / 0.5;
      const e = easeInOutQuad(seg);
      westX = tgt1.x + (p4.x - tgt1.x) * e;
      westY = tgt1.y + (p4.y - tgt1.y) * e;
    }

    // East Branch: C8 -> C6 -> C4
    let eastX, eastY;
    const tgt6 = p6 || p4;
    if (progress < 0.5) {
      const seg = progress / 0.5;
      const e = easeInOutQuad(seg);
      eastX = p8.x + (tgt6.x - p8.x) * e;
      eastY = p8.y + (tgt6.y - p8.y) * e;
    } else {
      const seg = (progress - 0.5) / 0.5;
      const e = easeInOutQuad(seg);
      eastX = tgt6.x + (p4.x - tgt6.x) * e;
      eastY = tgt6.y + (p4.y - tgt6.y) * e;
    }

    // Gateway Relay Glow on C1 and C6 when traversed (around progress 0.42 to 0.58)
    if (progress >= 0.42 && progress <= 0.58) {
      const gProg = (progress - 0.42) / 0.16;
      const gA = Math.sin(gProg * Math.PI) * 0.95;
      [p1, p6].filter(Boolean).forEach(p => {
        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, 25 + gProg * 8, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(16, 185, 129, ${gA})`;
        ctx.lineWidth = 3.0;
        ctx.shadowColor = "#10b981";
        ctx.shadowBlur = 18;
        ctx.stroke();
        ctx.restore();
      });
    }

    // Render traveling packets with floating labels
    drawCatalogResponsePacket(ctx, westX, westY, "REP_CATALOG (Z2)", "#10b981");
    drawCatalogResponsePacket(ctx, eastX, eastY, "REP_CATALOG (Z8)", "#10b981");

    // 5. Energetic Cyan/Gold Glow & Supervisory Beacon on C4
    ctx.save();
    // Continuous cyan/gold pulse
    const auraProg = (now % 1400) / 1400;
    const auraR = 26 + auraProg * 22;
    const auraA = (1.0 - auraProg) * 0.9;
    ctx.beginPath();
    ctx.arc(p4.x, p4.y, auraR, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(34, 211, 238, ${auraA * 0.9})`;
    ctx.lineWidth = 3.2;
    ctx.shadowColor = "#06b6d4";
    ctx.shadowBlur = 18;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(p4.x, p4.y, auraR * 0.85, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(234, 179, 8, ${auraA * 0.8})`;
    ctx.lineWidth = 2.4;
    ctx.shadowColor = "#eab308";
    ctx.shadowBlur = 14;
    ctx.stroke();

    // Arrival energetic cyan/gold flash upon payload reception (progress >= 0.82)
    if (progress >= 0.82) {
      const arrProg = (progress - 0.82) / 0.18;
      const arrA = (1.0 - arrProg);

      // Expanding cyan & gold shockwaves
      [0, 14, 28].forEach(offset => {
        // Cyan outer wave
        ctx.beginPath();
        ctx.arc(p4.x, p4.y, 26 + arrProg * 42 + offset, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(34, 211, 238, ${arrA * 0.9})`;
        ctx.lineWidth = 3.5;
        ctx.shadowColor = "#22d3ee";
        ctx.shadowBlur = 24;
        ctx.stroke();

        // Golden inner wave
        ctx.beginPath();
        ctx.arc(p4.x, p4.y, 22 + arrProg * 32 + offset, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(245, 158, 11, ${arrA * 0.95})`;
        ctx.lineWidth = 3.0;
        ctx.shadowColor = "#f59e0b";
        ctx.shadowBlur = 20;
        ctx.stroke();
      });

      // Bright white/cyan/gold radial core
      const coreGrad = ctx.createRadialGradient(p4.x, p4.y, 4, p4.x, p4.y, 42);
      coreGrad.addColorStop(0, `rgba(255, 255, 255, ${arrA * 0.95})`);
      coreGrad.addColorStop(0.35, `rgba(34, 211, 238, ${arrA * 0.65})`);
      coreGrad.addColorStop(0.7, `rgba(251, 191, 36, ${arrA * 0.5})`);
      coreGrad.addColorStop(1, `rgba(245, 158, 11, 0)`);
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(p4.x, p4.y, 42, 0, Math.PI * 2);
      ctx.fill();

      // Floating celebratory aggregation badge above C4
      ctx.font = "bold 10px ui-monospace, SFMono-Regular, monospace";
      const bText = "👑👑 7 CLUSTERS INGESTED";
      const bW = ctx.measureText(bText).width;
      ctx.fillStyle = `rgba(12, 74, 96, ${arrA * 0.95})`;
      ctx.strokeStyle = `rgba(34, 211, 238, ${arrA})`;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(p4.x - bW / 2 - 8, p4.y - 48, bW + 16, 18, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#cffafe";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(bText, p4.x, p4.y - 39);
    } else {
      ctx.font = "bold 13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("👑👑", p4.x, p4.y - 30);
    }
    ctx.restore();

    activeAnimationId = requestAnimationFrame(runFrame);
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}

// 5.17 STEP 17: Inter-Zone Meta-Clustering & Global Super-Cluster Formation
function renderStep17(data) {
  stopCurrentPacketAnimation();

  // Explicitly sync header active step badge
  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 17: GLOBAL SUPER-CLUSTER FORMATION";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-sky-50 text-sky-900 border border-sky-400";
  });

  renderSidebarFormula(
    "Step 17: Global Super-Cluster Formation",
    "S_{7 \\times 7} = \\frac{|\\mathbf{m}_a \\cap \\mathbf{m}_b|}{3} \\longrightarrow \\{\\mathcal{SC}_1, \\mathcal{SC}_2, \\mathcal{SC}_3\\}",
    "C4 executes meta-clustering over cluster profile masks, partitioning the network into 3 cross-zone Super-Clusters.",
    "Step 17: Super-Clusters",
    false,
    "sky"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 17: Inter-Zone Meta-Clustering & 3 Global Super-Clusters Formed";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const zoneLegend = document.getElementById("zoneLegendItem");
  if (zoneLegend) zoneLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.remove("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>Super-Initiator <span class="text-amber-600 font-bold">👑👑 C4</span> formed <span class="text-sky-700 font-bold font-mono">3 Global Super-Clusters</span>: SC-1 (Sky Blue), SC-2 (Amber), SC-3 (Violet)</span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  // Render Cytoscape network with isStep17: true
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    showBoundaryEdges: false,
    clusterHalos: true,
    isStep17: true,
    isStep16: true,
    isStep15: true,
    isStep13Exemplars: true
  });

  logToTerminal("ZONE", "[STEP 17] Inter-Zone Meta-Clustering & Super-Cluster Formation initialized.");
  logToTerminal("INFO", "Super-Initiator C4 computes pairwise Cosine Similarity over 7 ingested cluster profile masks.");
  logToTerminal("SUCCESS", "Evaluated 7x7 Inter-Cluster Similarity Matrix S_{7x7} (threshold τ >= 0.85).");
  logToTerminal("SUCCESS", "Super-Cluster 1 (SC-1) formed: Clusters {2-A, 8-B} -> Nodes {C1, C2, C9} (Aviation & Vehicles).");
  logToTerminal("SUCCESS", "Super-Cluster 2 (SC-2) formed: Clusters {2-B, 4-A, 8-A} -> Nodes {C3, C4, C5, C8} (Animals).");
  logToTerminal("SUCCESS", "Super-Cluster 3 (SC-3) formed: Clusters {4-B, 8-C} -> Nodes {C6, C7, C10} (Heavy Transport & Amphibians).");
  logToTerminal("INFO", "Network topology partitioned into 3 cross-zone semantic federations while preserving physical 1-hop mesh.");

  animateStep17SuperClusters(data.nodes);
}

// Animate Step 17: Glowing colored hulls, node halos, and floating badge overlays for SC-1, SC-2, SC-3
function animateStep17SuperClusters(allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 4000;
  const startTime = performance.now();

  function runFrame(now) {
    const elapsed = now - startTime;
    const pulse = (Math.sin((elapsed / 1000) * Math.PI) + 1) / 2; // 0..1 smooth breathing pulse

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scGroups = [
      { id: "SC-1", name: "Aviation & Vehicles", nodes: [1, 2, 9], color: "#38bdf8", rgb: "56, 189, 248" },
      { id: "SC-2", name: "Animals", nodes: [3, 4, 5, 8], color: "#fbbf24", rgb: "251, 191, 36" },
      { id: "SC-3", name: "Heavy Transport & Amphibians", nodes: [6, 7, 10], color: "#c084fc", rgb: "192, 132, 252" },
    ];

    scGroups.forEach(sc => {
      const positions = sc.nodes.map(id => {
        const ele = getNodeElement(id);
        return ele ? ele.renderedPosition() : null;
      }).filter(Boolean);

      if (positions.length === 0) return;

      // 1. Draw glowing aura rings around each node in this Super-Cluster
      positions.forEach(p => {
        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, 28 + pulse * 6, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${sc.rgb}, ${0.35 + pulse * 0.45})`;
        ctx.lineWidth = 2.5;
        ctx.shadowColor = sc.color;
        ctx.shadowBlur = 18 + pulse * 10;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(p.x, p.y, 34 + pulse * 4, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${sc.rgb}, ${0.15 + pulse * 0.25})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.restore();
      });

      // 2. Draw subtle hull connecting nodes of this SC
      if (positions.length >= 2) {
        ctx.save();
        const cx = positions.reduce((sum, p) => sum + p.x, 0) / positions.length;
        const cy_pos = positions.reduce((sum, p) => sum + p.y, 0) / positions.length;

        const sorted = [...positions].sort((a, b) => {
          return Math.atan2(a.y - cy_pos, a.x - cx) - Math.atan2(b.y - cy_pos, b.x - cx);
        });

        ctx.beginPath();
        sorted.forEach((p, idx) => {
          const dx = p.x - cx;
          const dy = p.y - cy_pos;
          const dist = Math.hypot(dx, dy);
          const push = dist > 0 ? 32 : 0;
          const px = p.x + (dx / dist) * push;
          const py = p.y + (dy / dist) * push;
          if (idx === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.closePath();

        ctx.fillStyle = `rgba(${sc.rgb}, 0.05)`;
        ctx.fill();
        ctx.strokeStyle = `rgba(${sc.rgb}, ${0.4 + pulse * 0.3})`;
        ctx.lineWidth = 1.6;
        ctx.setLineDash([6, 5]);
        ctx.lineDashOffset = -now / 40;
        ctx.stroke();
        ctx.setLineDash([]);

        // 3. Floating Super-Cluster identifier badge
        ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
        const tagText = `🌌 ${sc.id}: ${sc.name}`;
        const tW = ctx.measureText(tagText).width;
        const tagY = cy_pos - 12;

        ctx.fillStyle = `rgba(15, 23, 42, 0.88)`;
        ctx.strokeStyle = sc.color;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.roundRect(cx - tW / 2 - 7, tagY - 9, tW + 14, 18, 4);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = sc.color;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(tagText, cx, tagY);
        ctx.restore();
      }
    });

    activeAnimationId = requestAnimationFrame(runFrame);
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}


// 5.18 STEP 18: Super-Peer Designation & Hierarchical Overlay Binding
function renderStep18(data) {
  stopCurrentPacketAnimation();

  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 18: SUPER-PEER DESIGNATION & HIERARCHICAL BINDING";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 border border-amber-400";
  });

  renderSidebarFormula(
    "Step 18: Super-Peer Designation & Hierarchical Binding",
    "\\mathcal{SC}_m \\longrightarrow SP_m \\in \\{C_1, C_5, C_{10}\\}, \\quad e_k \\xrightarrow{\\text{bind}} SP_m",
    "Super-Initiator C4 designates Super-Peers (1, 5, 10) to coordinate local exemplars across zones.",
    "Step 18: Super-Peers",
    false,
    "amber"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 18: Super-Peer Designation & Hierarchical Overlay Binding";

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>Super-Peers Designated: <span class="text-sky-700 font-bold font-mono">🌟 C1</span> (SC-1), <span class="text-amber-700 font-bold font-mono">🌟 C5</span> (SC-2), <span class="text-purple-700 font-bold font-mono">🌟 C10</span> (SC-3)</span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    clusterHalos: true,
    isStep18: true,
    isStep17: true,
    isStep16: true,
    isStep15: true,
    isStep13Exemplars: true
  });

  logToTerminal("ZONE", "[STEP 18] Super-Peer Designation & Hierarchical Overlay Binding initialized.");
  logToTerminal("SUCCESS", "Super-Initiator C4 designates Super-Peers: C1 (SC-1), C5 (SC-2), C10 (SC-3).");
  logToTerminal("INFO", "Dispatched ORDER_SET_SUPER_PEER downstream along super-zone paths [4 -> 1 -> 2] and [4 -> 6 -> 8].");
  logToTerminal("SUCCESS", "Exemplar bindings established: C1->SP1, C9->SP1 | C3->SP5, C5->SP5, C8->SP5 | C7->SP10, C10->SP10.");
  logToTerminal("INFO", "3-tier hierarchy established: Regular Members -> Intra-Zone Exemplars -> Global Super-Peers.");

  animateStep18SuperPeerDirectives(data.packet_traces || [], data.nodes);
}

// Animate Step 18: Downstream directive dispatches along super-zone paths and Super-Peer halos
function animateStep18SuperPeerDirectives(packets, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 4500;
  const startTime = performance.now();

  function runFrame(now) {
    const elapsed = now - startTime;
    const progress = (elapsed % duration) / duration;
    const pulse = (Math.sin((elapsed / 800) * Math.PI) + 1) / 2;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const n4 = getNodeElement(4);
    const n1 = getNodeElement(1);
    const n2 = getNodeElement(2);
    const n6 = getNodeElement(6);
    const n8 = getNodeElement(8);
    const n5 = getNodeElement(5);
    const n10 = getNodeElement(10);

    if (!n4 || !n2 || !n8) {
      activeAnimationId = requestAnimationFrame(runFrame);
      return;
    }

    const p4 = n4.renderedPosition();
    const p1 = n1 ? n1.renderedPosition() : null;
    const p2 = n2.renderedPosition();
    const p6 = n6 ? n6.renderedPosition() : null;
    const p8 = n8.renderedPosition();
    const p5 = n5 ? n5.renderedPosition() : null;
    const p10 = n10 ? n10.renderedPosition() : null;

    // 1. Downstream Directive Paths: C4 -> C1 -> C2 and C4 -> C6 -> C8
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(p4.x, p4.y);
    if (p1) ctx.lineTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.strokeStyle = "rgba(245, 158, 11, 0.75)";
    ctx.lineWidth = 2.4;
    ctx.shadowColor = "#f59e0b";
    ctx.shadowBlur = 12;
    ctx.setLineDash([7, 5]);
    ctx.lineDashOffset = -now / 30; // outward flow from C4
    ctx.stroke();
    ctx.closePath();

    ctx.beginPath();
    ctx.moveTo(p4.x, p4.y);
    if (p6) ctx.lineTo(p6.x, p6.y);
    ctx.lineTo(p8.x, p8.y);
    ctx.strokeStyle = "rgba(245, 158, 11, 0.75)";
    ctx.lineWidth = 2.4;
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 2. Status Banner
    ctx.save();
    const aX = (p2.x + p8.x) / 2;
    const aY = p4.y - 48;
    ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
    const aText = "ORDER_SET_SUPER_PEER: C4 ➔ C2 & C8 (DOWNSTREAM HIERARCHICAL BINDINGS)";
    const aW = ctx.measureText(aText).width;
    ctx.fillStyle = "rgba(120, 53, 15, 0.92)";
    ctx.strokeStyle = "#f59e0b";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.roundRect(aX - aW / 2 - 8, aY - 10, aW + 16, 20, 4);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#fef3c7";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(aText, aX, aY);
    ctx.restore();

    // 3. Downstream Moving Packets
    // West Branch: C4 -> C1 -> C2
    let westX, westY;
    const tgt1 = p1 || p2;
    if (progress < 0.5) {
      const seg = progress / 0.5;
      const e = easeInOutQuad(seg);
      westX = p4.x + (tgt1.x - p4.x) * e;
      westY = p4.y + (tgt1.y - p4.y) * e;
    } else {
      const seg = (progress - 0.5) / 0.5;
      const e = easeInOutQuad(seg);
      westX = tgt1.x + (p2.x - tgt1.x) * e;
      westY = tgt1.y + (p2.y - tgt1.y) * e;
    }

    // East Branch: C4 -> C6 -> C8
    let eastX, eastY;
    const tgt6 = p6 || p8;
    if (progress < 0.5) {
      const seg = progress / 0.5;
      const e = easeInOutQuad(seg);
      eastX = p4.x + (tgt6.x - p4.x) * e;
      eastY = p4.y + (tgt6.y - p4.y) * e;
    } else {
      const seg = (progress - 0.5) / 0.5;
      const e = easeInOutQuad(seg);
      eastX = tgt6.x + (p8.x - tgt6.x) * e;
      eastY = tgt6.y + (p8.y - tgt6.y) * e;
    }

    [ { x: westX, y: westY, lbl: "ORDER [SP1, C3->SP5]" }, { x: eastX, y: eastY, lbl: "ORDER [SP10, C9->SP1, C8->SP5]" } ].forEach(pkt => {
      ctx.save();
      ctx.beginPath();
      ctx.arc(pkt.x, pkt.y, 7, 0, Math.PI * 2);
      ctx.fillStyle = "#f59e0b";
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 14;
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.font = "bold 8.5px ui-monospace, SFMono-Regular, monospace";
      const w = ctx.measureText(pkt.lbl).width;
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
      ctx.beginPath();
      ctx.roundRect(pkt.x - w / 2 - 4, pkt.y - 18, w + 8, 13, 3);
      ctx.fill();
      ctx.fillStyle = "#fef3c7";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(pkt.lbl, pkt.x, pkt.y - 12);
      ctx.restore();
    });

    // 4. Glowing Super-Peer Badges and Halos on C1, C5, C10
    const superPeers = [
      { id: 1, pos: p1, sc: "SC-1", color: "#38bdf8", rgb: "56, 189, 248" },
      { id: 5, pos: p5, sc: "SC-2", color: "#fbbf24", rgb: "251, 191, 36" },
      { id: 10, pos: p10, sc: "SC-3", color: "#c084fc", rgb: "192, 132, 252" },
    ];

    superPeers.forEach(sp => {
      if (!sp.pos) return;
      ctx.save();
      // Glowing golden outer aura
      ctx.beginPath();
      ctx.arc(sp.pos.x, sp.pos.y, 32 + pulse * 6, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(245, 158, 11, ${0.4 + pulse * 0.4})`;
      ctx.lineWidth = 3.0;
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 22 + pulse * 10;
      ctx.stroke();

      // Floating Badge
      ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
      const bText = `🌟 SUPER-PEER (${sp.sc})`;
      const bW = ctx.measureText(bText).width;
      const bY = sp.pos.y + 36;
      ctx.fillStyle = "rgba(15, 23, 42, 0.90)";
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(sp.pos.x - bW / 2 - 6, bY - 8, bW + 12, 16, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#fef3c7";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(bText, sp.pos.x, bY);
      ctx.restore();
    });

    activeAnimationId = requestAnimationFrame(runFrame);
  }

  activeAnimationId = requestAnimationFrame(runFrame);
}


// 5.19 STEP 19: Semantic Overlay Network (SON) Logical Topology Formation
function renderStep19(data) {
  stopCurrentPacketAnimation();

  const activeBadges = [
    document.getElementById("activePhaseBadge"),
    document.getElementById("activeStepBadge")
  ].filter(Boolean);
  activeBadges.forEach(badge => {
    badge.textContent = "ACTIVE PHASE: STEP 19: SEMANTIC OVERLAY NETWORK (SON) FORMATION";
    badge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-400";
  });

  renderSidebarFormula(
    "Step 19: Semantic Overlay Network (SON) Formation",
    "\\mathcal{E}_{\\text{SON}} = \\mathcal{E}_{\\text{intra}} \\cup \\mathcal{E}_{\\text{inter}} \\subset \\mathcal{V} \\times \\mathcal{V}, \\quad \\mathcal{G}_{\\text{SON}} = (\\mathcal{V}, \\mathcal{E}_{\\text{SON}})",
    "Active logical edges connect members to exemplars, and exemplars to super-peers across physical zones.",
    "Step 19: Semantic Overlay",
    false,
    "emerald"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Step 19: 2-Tier Semantic Overlay Network (SON) Activated (7 Logical Edges)";

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.innerHTML = '<span>SON Topology Active: <span class="text-emerald-700 font-bold font-mono">7 Logical Edges</span> (3 Intra-Zone Tier-1, 4 Inter-Zone Tier-2)</span>';
    statLeaders.className = "text-xs font-bold text-slate-800";
  }

  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    useTonalZoneColors: true,
    clusterHalos: true,
    dimPhysicalEdges: true,
    isStep19: true,
    isStep18: true,
    isStep17: true,
    isStep16: true,
    isStep15: true,
    isStep13Exemplars: true
  });

  logToTerminal("ZONE", "[STEP 19] Semantic Overlay Network (SON) activated.");
  logToTerminal("SUCCESS", "Tier-1 Intra-Zone links active: (C2 <-> C1), (C4 <-> C5), (C6 <-> C7).");
  logToTerminal("SUCCESS", "Tier-2 Inter-Zone links active: SC-1 (C9 <-> C1), SC-2 (C3 <-> C5, C8 <-> C5), SC-3 (C7 <-> C10).");
  logToTerminal("INFO", "Physical 18-edge topology serves as transport underlay for 7 vibrant semantic overlay links.");

  animateStep19SemanticOverlay(data.semantic_overlay_edges || [], data.nodes);
}

// Animate Step 19: 7 vibrant neon overlay edges (Tier 1 dashed, Tier 2 solid glowing)
function animateStep19SemanticOverlay(overlayEdges, allNodes) {
  stopCurrentPacketAnimation();
  syncPacketCanvasSize();

  const canvas = document.getElementById("packetCanvas");
  if (!canvas || !cy) return;
  const ctx = canvas.getContext("2d");

  const duration = 3600;
  const startTime = performance.now();

  const scColors = {
    "SC-1": { hex: "#38bdf8", rgb: "56, 189, 248" },
    "SC-2": { hex: "#fbbf24", rgb: "251, 191, 36" },
    "SC-3": { hex: "#c084fc", rgb: "192, 132, 252" },
  };

  function runFrame(now) {
    const elapsed = now - startTime;
    const pulse = (Math.sin((elapsed / 700) * Math.PI) + 1) / 2;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Status Banner
    ctx.save();
    ctx.font = "bold 9.5px ui-monospace, SFMono-Regular, monospace";
    const bannerText = "2-TIER SEMANTIC OVERLAY (SON): 3 TIER-1 (DASHED) | 4 TIER-2 (SOLID NEON GLOW)";
    const bW = ctx.measureText(bannerText).width;
    const bX = canvas.width / 2;
    const bY = 24;
    ctx.fillStyle = "rgba(6, 78, 59, 0.92)";
    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.roundRect(bX - bW / 2 - 8, bY - 10, bW + 16, 20, 4);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#d1fae5";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(bannerText, bX, bY);
    ctx.restore();

    // 2. Draw each of the 7 Semantic Overlay Edges
    overlayEdges.forEach((edge, idx) => {
      const srcEle = getNodeElement(edge.source);
      const tgtEle = getNodeElement(edge.target);
      if (!srcEle || !tgtEle) return;

      const pSrc = srcEle.renderedPosition();
      const pTgt = tgtEle.renderedPosition();
      const sc = scColors[edge.super_cluster] || { hex: "#38bdf8", rgb: "56, 189, 248" };

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(pSrc.x, pSrc.y);
      ctx.lineTo(pTgt.x, pTgt.y);

      if (edge.tier === 1) {
        // Tier 1: Intra-zone Member <-> Exemplar (Dashed neon stroke, 2px)
        ctx.strokeStyle = `rgba(${sc.rgb}, ${0.75 + pulse * 0.25})`;
        ctx.lineWidth = 2.2;
        ctx.shadowColor = sc.hex;
        ctx.shadowBlur = 10;
        ctx.setLineDash([8, 6]);
        ctx.lineDashOffset = -now / 35;
        ctx.stroke();
        ctx.setLineDash([]);
      } else {
        // Tier 2: Inter-zone Exemplar <-> Super-Peer (Solid neon stroke, 3.5px with pulsing glow)
        ctx.strokeStyle = `rgba(${sc.rgb}, ${0.85 + pulse * 0.15})`;
        ctx.lineWidth = 3.5;
        ctx.shadowColor = sc.hex;
        ctx.shadowBlur = 20 + pulse * 10;
        ctx.stroke();

        // Traveling pulse particle along Tier 2 edge
        const tProgress = ((elapsed + idx * 800) % 2400) / 2400;
        const pX = pSrc.x + (pTgt.x - pSrc.x) * tProgress;
        const pY = pSrc.y + (pTgt.y - pSrc.y) * tProgress;

        ctx.beginPath();
        ctx.arc(pX, pY, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.shadowColor = sc.hex;
        ctx.shadowBlur = 14;
        ctx.fill();
      }

      // Small middle pill badge denoting link tier
      const midX = (pSrc.x + pTgt.x) / 2;
      const midY = (pSrc.y + pTgt.y) / 2;
      const tag = edge.tier === 1 ? `T1: C${edge.source}⇄C${edge.target}` : `T2: C${edge.source}⇄SP${edge.target}`;
      ctx.font = "bold 8px ui-monospace, SFMono-Regular, monospace";
      const tagW = ctx.measureText(tag).width;

      ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
      ctx.strokeStyle = sc.hex;
      ctx.lineWidth = 1.0;
      ctx.beginPath();
      ctx.roundRect(midX - tagW / 2 - 4, midY - 6, tagW + 8, 12, 3);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = sc.hex;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(tag, midX, midY);

      ctx.restore();
    });

    // 3. Draw Halos on Super-Peers (1, 5, 10) and Exemplars
    [1, 5, 10].forEach(spId => {
      const ele = getNodeElement(spId);
      if (!ele) return;
      const p = ele.renderedPosition();
      ctx.save();
      ctx.beginPath();
      ctx.arc(p.x, p.y, 30 + pulse * 5, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(245, 158, 11, ${0.45 + pulse * 0.4})`;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 18;
      ctx.stroke();
      ctx.restore();
    });

    activeAnimationId = requestAnimationFrame(runFrame);
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
    const isInit = Boolean(options.showInitiators && (n.is_initiator || [2, 4, 8].includes(n.id)));
    const domName = n.dominant_class_name || n.class_title || "CIFAR-10";
    const domIcon = n.dominant_class_icon || n.class_icon || "";
    const isTopInit = Boolean((options.isStep15 || options.isStep14 || options.isStep13TopZone) && (n.id === 4 || n.is_top_initiator));
    const isExemplar = Boolean(options.isStep13Exemplars && (n.is_exemplar !== undefined ? n.is_exemplar : [1, 3, 5, 7, 8, 9, 10].includes(n.id)));
    const isSuperPeer = Boolean((options.isStep18 || options.isStep19) && (n.is_super_peer !== undefined ? n.is_super_peer : [1, 5, 10].includes(n.id)));
    let label = isSuperPeer ? `🌟⭐ C${n.id}` : (isTopInit ? `👑👑 C${n.id}` : (isExemplar ? `⭐ C${n.id}` : (isInit ? `👑 C${n.id}` : `C${n.id}`)));

    let bgColor = "#2563eb";
    let borderColor = "#1d4ed8";

    let nodeClasses = "";
    if (isExemplar) {
      nodeClasses += "exemplar-node ";
    }
    if (isSuperPeer) {
      nodeClasses += "super-peer-node ";
    }
    if (options.isStep17 || options.isStep18 || options.isStep19) {
      const scId = n.assigned_super_cluster || ([1, 2, 9].includes(n.id) ? "SC-1" : ([3, 4, 5, 8].includes(n.id) ? "SC-2" : "SC-3"));
      if (scId === "SC-1") {
        nodeClasses += "super-cluster-sc1 ";
      } else if (scId === "SC-2") {
        nodeClasses += "super-cluster-sc2 ";
      } else if (scId === "SC-3") {
        nodeClasses += "super-cluster-sc3 ";
      }
    }

    if (options.useTonalZoneColors && (n.assigned_zone || n.zone_id)) {
      const zid = n.assigned_zone || n.zone_id;
      if (isInit) {
        if (isTopInit) {
          nodeClasses += `top-initiator-node zone-initiator-${zid} `;
          bgColor = "#ea580c";
          borderColor = "#eab308";
        } else {
          nodeClasses += `initiator-node zone-initiator-${zid} `;
          if (zid === 2) {
            bgColor = "#059669";
            borderColor = isExemplar ? "#f59e0b" : "#f59e0b";
          } else if (zid === 4) {
            bgColor = "#ea580c";
            borderColor = isExemplar ? "#f59e0b" : "#f59e0b";
          } else if (zid === 8) {
            bgColor = "#7c3aed";
            borderColor = isExemplar ? "#f59e0b" : "#f59e0b";
          }
        }
      } else {
        nodeClasses += `zone-pastel-${zid} `;
        if (zid === 2) {
          bgColor = "#34d399";
          borderColor = isExemplar ? "#f59e0b" : "#10b981";
        } else if (zid === 4) {
          bgColor = "#fb923c";
          borderColor = isExemplar ? "#f59e0b" : "#f97316";
        } else if (zid === 8) {
          bgColor = "#a78bfa";
          borderColor = isExemplar ? "#f59e0b" : "#8b5cf6";
        }
      }
    } else if (options.useZoneColors && (n.assigned_zone || n.zone_id)) {
      const zid = n.assigned_zone || n.zone_id;
      if (zid === 2) {
        bgColor = "#059669";
        borderColor = isInit ? "#047857" : (n.is_boundary ? "#ea580c" : "#047857");
      } else if (zid === 4) {
        bgColor = "#ea580c";
        borderColor = isInit ? "#c2410c" : (n.is_boundary ? "#7c3aed" : "#c2410c");
      } else if (zid === 8) {
        bgColor = "#7c3aed";
        borderColor = isInit ? "#6d28d9" : "#6d28d9";
      }

      if (n.is_boundary) {
        if (n.id === 1) {
          bgColor = "#059669";
          borderColor = "#ea580c";
          nodeClasses += "boundary-node-1 ";
        } else if (n.id === 6) {
          bgColor = "#ea580c";
          borderColor = "#7c3aed";
          nodeClasses += "boundary-node-6 ";
        }
      } else {
        nodeClasses += `zone-node-${zid} `;
      }
      if (isInit) {
        nodeClasses += "initiator-node ";
      }
    } else if (isInit) {
      nodeClasses += `initiator-node winner-node-${n.id} `;
      if (n.id === 4 || n.winner_color === "dark green") {
        bgColor = "#166534";
        borderColor = "#14532d";
      } else if (n.id === 2 || n.winner_color === "dark red") {
        bgColor = "#991b1b";
        borderColor = "#7f1d1d";
      } else if (n.id === 8 || n.winner_color === "dark yellow") {
        bgColor = "#a16207";
        borderColor = "#713f12";
      } else {
        bgColor = n.winner_bg || "#f59e0b";
        borderColor = n.winner_border || "#b45309";
      }
    }

    elements.push({
      group: "nodes",
      classes: nodeClasses.trim(),
      data: {
        id: `node_${n.id}`,
        node_id_num: n.id,
        node_id_str: n.node_id || `C${n.id}`,
        label: label,
        role: isInit ? "👑 Initiator" : (n.role || "CLIENT"),
        status: isInit ? "INITIATOR" : (n.status || "NOT_ASSIGNED"),
        bg_color: bgColor,
        border_color: borderColor,
        neighbor_scoreboard: n.neighbor_scoreboard || [],
        neighbor_scores: n.neighbor_scores || {},
        neighbor_scores_str: n.neighbor_scores_str || {},
        winner_color: n.winner_color,
        winner_bg: n.winner_bg,
        winner_border: n.winner_border,
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
        zone_id: n.zone_id || n.assigned_zone,
        zone_label: n.zone_label,
        zone_color: n.zone_color || bgColor,
        zone_probes_received: n.zone_probes_received || [],
        probes_sent: n.probes_sent || [],
        boundary_zones: n.boundary_zones || [],
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
        assigned_cluster_id: n.assigned_cluster_id,
        cluster_id: n.cluster_id || n.assigned_cluster_id,
        cluster_exemplar: n.cluster_exemplar,
        cluster_peers: n.cluster_peers || [],
        cluster_peers_str: n.cluster_peers_str || [],
        cluster_color: n.cluster_color,
        cluster_status: n.cluster_status,
        clustering_role: n.clustering_role,
        intra_zone_similarity_matrix: n.intra_zone_similarity_matrix,
        clusters: n.clusters,
        zone_clusters: n.zone_clusters,
        top_p_indices: n.top_p_indices,
        binary_mask_10d: n.binary_mask_10d,
        top_level_role: n.top_level_role,
        top_level_status: n.top_level_status,
        is_top_initiator: n.is_top_initiator,
        super_zone_role: n.super_zone_role,
        governing_initiators: n.governing_initiators,
        top_level_zone: n.top_level_zone,
        is_exemplar: n.is_exemplar,
        exemplar_for: n.exemplar_for,
        exemplar_node_id: n.exemplar_node_id,
        profile_signature: n.profile_signature,
        is_super_peer: n.is_super_peer,
        bound_super_peer: n.bound_super_peer,
        governed_exemplars: n.governed_exemplars,
        active_overlay_neighbors: n.active_overlay_neighbors,
      },
      position: {
        x: n.x,
        y: n.y
      }
    });
  });

  edges.forEach((e, idx) => {
    // All 18 physical links in the entire network remain uniform, solid, clean slate/neutral lines at all times.
    let edgeClass = "network-physical-edge";
    if (options.dimPhysicalEdges) {
      edgeClass += " dimmed-physical";
    }
    elements.push({
      group: "edges",
      classes: edgeClass,
      data: {
        id: e.id || `edge_${idx}`,
        source: `node_${e.source_num || parseInt(String(e.source).replace('C', '').replace('node_', ''), 10)}`,
        target: `node_${e.target_num || parseInt(String(e.target).replace('C', '').replace('node_', ''), 10)}`,
        is_inter_zone: false,
      }
    });
  });

  cy.elements().remove();
  cy.add(elements);
  cy.resize();
  cy.layout({ name: "preset" }).run();
  cy.fit(undefined, 35);
  cy.autoungrabify(true);
  cy.nodes().lock();

  if (options.clusterHalos) {
    nodes.forEach(n => {
      const cColor = n.cluster_color || "#8b5cf6";
      const ele = cy.getElementById(`node_${n.id}`);
      if (ele && ele.length > 0) {
        ele.style({
          "underlay-color": cColor,
          "underlay-padding": 5.5,
          "underlay-opacity": 0.5,
          "shadow-blur": 14,
          "shadow-color": cColor,
          "shadow-opacity": 0.85
        });
      }
    });
  }

  if (options.useZoneColors && !options.useTonalZoneColors) {
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

// Render dedicated 4-column Overlay VRF Scoreboard (Super-Initiator Election) Table for Step 13
function renderOverlayVrfScoreboardHtml(idNum, scoreboard) {
  // Initiator order: C2, C4, C8
  let rows = [];
  if (idNum === 2) {
    rows = [
      { id: 2, origin: "Self", score: 0.0837, status: "Base Zone Initiator", isWinner: false },
      { id: 4, origin: "Direct Neighbor", score: 0.0412, status: "🏆 Elected Top-Level Initiator", isWinner: true },
      { id: 8, origin: "Relayed via C4", score: 0.0275, status: "Base Zone Initiator", isWinner: false }
    ];
  } else if (idNum === 8) {
    rows = [
      { id: 2, origin: "Relayed via C4", score: 0.0837, status: "Base Zone Initiator", isWinner: false },
      { id: 4, origin: "Direct Neighbor", score: 0.0412, status: "🏆 Elected Top-Level Initiator", isWinner: true },
      { id: 8, origin: "Self", score: 0.0275, status: "Base Zone Initiator", isWinner: false }
    ];
  } else {
    // Node 4 (Central Bridge Hub / Elected Super-Initiator)
    rows = [
      { id: 2, origin: "Direct Neighbor", score: 0.0837, status: "Base Zone Initiator", isWinner: false },
      { id: 4, origin: "Self", score: 0.0412, status: "🏆 Elected Top-Level Initiator", isWinner: true },
      { id: 8, origin: "Direct Neighbor", score: 0.0275, status: "Base Zone Initiator", isWinner: false }
    ];
  }

  // If scoreboard has backend provided rows, overlay their exact scores and origins
  if (scoreboard && Array.isArray(scoreboard.rows) && scoreboard.rows.length > 0) {
    rows = scoreboard.rows.map(r => ({
      id: r.id,
      origin: r.origin || (r.id === idNum ? "Self" : (r.via === "relayed_by_C4" || r.relayed ? "Relayed via C4" : "Direct Neighbor")),
      score: r.score,
      status: r.is_winner || r.id === 4 ? "🏆 Elected Top-Level Initiator" : "Base Zone Initiator",
      isWinner: Boolean(r.is_winner || r.id === 4)
    }));
  }

  const rowsHtml = rows.map(r => {
    const isWinner = Boolean(r.isWinner || r.id === 4);
    const trClass = isWinner
      ? "bg-amber-100/90 font-bold border-y-2 border-amber-400 text-amber-950"
      : "hover:bg-slate-50 border-b border-slate-200 text-slate-700";

    const originBadgeClass = r.origin.includes("Self")
      ? "bg-blue-100 text-blue-800 border-blue-200"
      : r.origin.includes("Direct")
        ? "bg-emerald-100 text-emerald-800 border-emerald-200"
        : "bg-purple-100 text-purple-800 border-purple-200";

    return `
      <tr class="${trClass}">
        <td class="py-1.5 px-2.5 font-bold font-mono ${isWinner ? 'text-amber-950' : 'text-slate-800'}">
          ${isWinner ? '👑 ' : ''}C${r.id}
        </td>
        <td class="py-1.5 px-2.5">
          <span class="inline-block px-1.5 py-0.5 rounded text-[8.5px] font-semibold border ${originBadgeClass}">
            ${r.origin}
          </span>
        </td>
        <td class="py-1.5 px-2.5 font-mono font-bold ${isWinner ? 'text-amber-950 text-[10px]' : 'text-slate-800'}">
          ${typeof r.score === 'number' ? r.score.toFixed(4) : r.score}
        </td>
        <td class="py-1.5 px-2.5">
          ${isWinner
            ? '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-200 text-amber-950 border border-amber-400 font-extrabold text-[9px] shadow-xs">🏆 Elected Top-Level Initiator</span>'
            : '<span class="text-[9px] text-slate-600 font-medium">Base Zone Initiator</span>'
          }
        </td>
      </tr>
    `;
  }).join("");

  return `
    <div class="space-y-1.5 font-mono text-[10px] mt-1">
      <div class="font-bold text-amber-950 flex items-center justify-between">
        <span class="flex items-center gap-1">
          <span>📊</span>
          <span>Overlay VRF Scoreboard (Super-Initiator Election):</span>
        </span>
        <span class="text-[8.5px] px-1.5 py-0.2 rounded bg-amber-200 text-amber-900 border border-amber-300 font-bold">
          Elected: Node C4 🏆
        </span>
      </div>
      <div class="overflow-x-auto border border-amber-300 rounded shadow-xs">
        <table class="w-full text-left border-collapse bg-white">
          <thead>
            <tr class="bg-amber-50 text-amber-900 text-[8.5px] border-b border-amber-200 font-bold uppercase tracking-wider">
              <th class="py-1.5 px-2.5">Initiator ID</th>
              <th class="py-1.5 px-2.5">Role / Origin</th>
              <th class="py-1.5 px-2.5">Exact VRF Value</th>
              <th class="py-1.5 px-2.5">Election Status</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
      <div class="text-[8.5px] text-slate-500 font-sans italic flex items-center justify-between px-0.5">
        <span>Multi-way VRF dissemination across C2 ↔ C4 ↔ C8 overlay.</span>
        <span class="font-semibold text-amber-900 font-mono">Consensus: C4 (0.0412)</span>
      </div>
    </div>
  `;
}

// 10. Click-to-Toggle Node Details Modal (Strict Step 1 Scope)
function renderNodeModal(node, stepData = currentStepData) {
  try {
    if (!node) return;
    const nodeData = (typeof node.data === "function") ? node.data() : node;
    const rawId = nodeData.node_id_num ?? nodeData.id;
    const idNum = typeof rawId === "string" ? parseInt(rawId.replace(/\D/g, ""), 10) : Number(rawId);

    // Merge with backend step data if available for safe fallbacks
    const backendNode = (stepData?.nodes || []).find(n => n.id === idNum) || {};
    const mergedNode = Object.assign({}, backendNode, nodeData);

    const card = document.getElementById("nodeInfoCard");
    if (!card) return;

  const cardNodeId = document.getElementById("cardNodeId");
  const cardStatusBadge = document.getElementById("cardStatusBadge");
  const cardDegree = document.getElementById("cardDegree");
  const cardNeighbors = document.getElementById("cardNeighbors");
  const distTableBody = document.getElementById("cardDataDistributionTableBody");

  // Header: Node C{id} | Role: INITIATOR / CLIENT | Zone: {assigned_zone} in Step 5 & 6
  if (cardNodeId) {
    if (currentStep === 19) {
      const sonTier = mergedNode?.son_tier ?? ([1, 5, 10].includes(idNum) ? 3 : ([3, 7, 8, 9].includes(idNum) ? 2 : 1));
      const tierStr = sonTier === 3 ? "🌟 TIER-3 SUPER-PEER" : (sonTier === 2 ? "⭐ TIER-2 EXEMPLAR" : "TIER-1 MEMBER");
      const scStr = mergedNode?.assigned_super_cluster || ([1, 2, 9].includes(idNum) ? "SC-1" : ([3, 4, 5, 8].includes(idNum) ? "SC-2" : "SC-3"));
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">SON Role: <span class="${sonTier === 3 ? 'text-amber-800 font-bold' : (sonTier === 2 ? 'text-blue-800 font-bold' : 'text-slate-800')}">${tierStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Super-Cluster: <span class="font-bold text-sky-800">${scStr}</span></span>`;
    } else if (currentStep === 18) {
      const isSP = Boolean(mergedNode?.is_super_peer || [1, 5, 10].includes(idNum));
      const roleStr = isSP ? "🌟 GLOBAL SUPER-PEER" : (mergedNode?.is_exemplar ? "⭐ INTRA-ZONE EXEMPLAR" : "REGULAR MEMBER");
      const scStr = mergedNode?.assigned_super_cluster || ([1, 2, 9].includes(idNum) ? "SC-1" : ([3, 4, 5, 8].includes(idNum) ? "SC-2" : "SC-3"));
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Role: <span class="${isSP ? 'text-amber-800 font-bold' : 'text-slate-800'}">${roleStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Super-Cluster: <span class="font-bold text-sky-800">${scStr}</span></span>`;
    } else if (currentStep === 17) {
      const isTopInit = Boolean(idNum === 4 || mergedNode?.is_top_initiator);
      const isInit = Boolean([2, 4, 8].includes(idNum) || mergedNode?.is_initiator);
      const roleStr = isTopInit ? "👑👑 SUPER-INITIATOR" : (isInit ? "👑 BASE INITIATOR" : "CLIENT");
      const scStr = mergedNode?.assigned_super_cluster || ([1, 2, 9].includes(idNum) ? "SC-1" : ([3, 4, 5, 8].includes(idNum) ? "SC-2" : "SC-3"));
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Role: <span class="${isTopInit ? 'text-amber-800 font-bold' : (isInit ? 'text-amber-700 font-bold' : 'text-slate-800')}">${roleStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Super-Cluster: <span class="font-bold text-sky-800">${scStr}</span></span>`;
    } else if (currentStep === 16) {
      const isTopInit = Boolean(idNum === 4 || mergedNode.is_top_initiator);
      const isInit = Boolean([2, 4, 8].includes(idNum) || mergedNode.is_initiator);
      const roleStr = isTopInit ? "👑👑 SUPER-INITIATOR" : (isInit ? "👑 BASE INITIATOR" : "CLIENT");
      const cStatus = idNum === 4 ? "7 CLUSTERS ASSEMBLED" : ([2, 8].includes(idNum) ? "CATALOG DISPATCHED" : "CLUSTER MEMBER");
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Role: <span class="${isTopInit ? 'text-amber-800 font-bold' : (isInit ? 'text-amber-700 font-bold' : 'text-slate-800')}">${roleStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Catalog: <span class="font-bold text-emerald-800">${cStatus}</span></span>`;
    } else if (currentStep === 15) {
      const isTopInit = Boolean(idNum === 4 || mergedNode.is_top_initiator);
      const isInit = Boolean([2, 4, 8].includes(idNum) || mergedNode.is_initiator);
      const roleStr = isTopInit ? "👑👑 SUPER-INITIATOR" : (isInit ? "👑 BASE INITIATOR" : "CLIENT");
      const qStatus = idNum === 4 ? "DISPATCHED" : ([2, 8].includes(idNum) ? "QUERY RECEIVED" : "INACTIVE");
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Role: <span class="${isTopInit ? 'text-amber-800 font-bold' : (isInit ? 'text-amber-700 font-bold' : 'text-slate-800')}">${roleStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Query: <span class="font-bold text-cyan-800">${qStatus}</span></span>`;
    } else if (currentStep === 14) {
      const isTopInit = Boolean(idNum === 4 || mergedNode.is_top_initiator);
      const isInit = Boolean([2, 4, 8].includes(idNum) || mergedNode.is_initiator);
      const roleStr = isTopInit ? "👑👑 TOP INITIATOR" : (isInit ? "👑 BASE INITIATOR" : "CLIENT");
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Role: <span class="${isTopInit ? 'text-amber-800 font-bold' : (isInit ? 'text-amber-700 font-bold' : 'text-slate-800')}">${roleStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Super-Zone: <span class="font-bold text-amber-900">Z_TOP</span></span>`;
    } else if (currentStep === 13) {
      const isEx = Boolean(mergedNode.is_exemplar);
      const roleStr = isEx ? "⭐ CLUSTER EXEMPLAR" : "CLUSTER MEMBER";
      const cId = mergedNode.cluster_id || 'N/A';
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Role: <span class="${isEx ? 'text-amber-600 font-bold' : 'text-slate-800 font-semibold'}">${roleStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Cluster: <span class="font-bold text-violet-900">${cId}</span></span>`;
    } else if (currentStep === 5 || currentStep === 6) {
      const isInit = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
      const roleStr = isInit ? "INITIATOR" : "CLIENT";
      let zStr = "Zone " + (nodeData.assigned_zone || (idNum in {1:1,2:1,3:1} ? 2 : idNum in {4:1,5:1,6:1,7:1} ? 4 : 8));
      if (nodeData.zone_label) zStr = nodeData.zone_label;
      cardNodeId.innerHTML = `<span class="text-blue-700 font-bold font-mono text-sm">Node C${idNum}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Role: <span class="${isInit ? 'text-amber-700 font-bold' : 'text-slate-800'}">${roleStr}</span></span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Zone: <span class="font-bold text-slate-900">${zStr}</span></span>`;
    } else {
      cardNodeId.innerHTML = `<span class="text-blue-700 font-bold font-mono text-sm">Node C${idNum}</span>`;
    }
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

  // Client dataset classes directly below connected neighbors (Issue #4 & Step 5)
  // Shows Local percentage breakdown (e.g., Airplane: 46%, Automobile: 17%, Bird: 37%)
  const cardClientClasses = document.getElementById("cardClientClasses");
  if (cardClientClasses) {
    let activeClasses = [];
    const dist = nodeData.data_distribution || nodeData.distribution || STORYBOARD_10_DISTRIBUTION[idNum] || {};
    const entries = Object.entries(dist).filter(([_, pct]) => Number(pct) > 0);
    if (entries.length > 0) {
      activeClasses = entries.map(([clsKey, pct]) => `${getCifarClass(clsKey).name}: ${pct}%`);
    } else {
      const vec = nodeData.vector_10d || nodeData.normalized_vector || nodeData.vector || STORYBOARD_10_VECTORS[idNum] || [];
      vec.forEach((val, idx) => {
        if (Number(val) > 0) {
          activeClasses.push(`${getCifarClass(idx + 1).name}: ${(Number(val) * 100).toFixed(0)}%`);
        }
      });
    }
    cardClientClasses.textContent = activeClasses.length > 0 ? activeClasses.join(", ") : "None";
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

  // Step 2, Step 3, Step 4+: Normalized 10D Semantic Vector (w_i) - Kept in Step 4+ per Issue #4
  const vectorSection = document.getElementById("cardVectorSection");
  const vectorArrayEl = document.getElementById("cardVectorArray");
  const vectorBreakdownContainer = document.getElementById("cardVectorBreakdownContainer");
  const vectorBreakdownBody = document.getElementById("cardVectorBreakdownBody");

  if (currentStep >= 2) {
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

    // Mini bar profile for Step 5, 6, 7, 8, 9, 10, 11, 12 & 13
    const vectorBarsContainer = document.getElementById("cardVectorBarsContainer");
    const vectorBars = document.getElementById("cardVectorBars");
    if ((currentStep >= 5 && currentStep <= 13) && vectorBarsContainer && vectorBars) {
      vectorBarsContainer.classList.remove("hidden");
      vectorBars.innerHTML = "";
      vec.forEach((val, idx) => {
        const numVal = Number(val);
        if (numVal > 0) {
          const cls = getCifarClass(idx + 1);
          const pct = (numVal * 100).toFixed(0);
          const row = document.createElement("div");
          row.className = "flex items-center gap-2 text-[10px] font-mono";
          row.innerHTML = `
            <span class="w-20 truncate font-sans text-slate-700 font-medium">${cls.name}</span>
            <div class="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
              <div class="bg-cyan-600 h-2 rounded-full" style="width: ${pct}%"></div>
            </div>
            <span class="w-10 text-right font-bold text-slate-800">${numVal.toFixed(2)}</span>
          `;
          vectorBars.appendChild(row);
        }
      });
    } else if (vectorBarsContainer) {
      vectorBarsContainer.classList.add("hidden");
    }

    // In Step 4 and subsequent steps, remove the breakdown table below the vector per Issue #4
    if (currentStep >= 4) {
      if (vectorBreakdownContainer) vectorBreakdownContainer.classList.add("hidden");
    } else {
      if (vectorBreakdownContainer) vectorBreakdownContainer.classList.remove("hidden");
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
    }
  } else {
    if (vectorSection) vectorSection.classList.add("hidden");
  }

  // Step 3, 4, 5: Local VRF Score & 1-Hop Neighborhood Scoreboard / Election / Probe
  const vrfSection = document.getElementById("cardVrfSection");
  const vrfBadge = document.getElementById("cardVrfScoreBadge");
  const scoreboardContainer = document.getElementById("cardNeighborhoodScoreboardContainer");
  const scoreboardBody = document.getElementById("cardNeighborhoodScoreboardBody");
  const electionBanner = document.getElementById("cardElectionBanner");
  const scoreboardTitle = document.getElementById("cardScoreboardTitle");
  const scoreboardSubtitle = document.getElementById("cardScoreboardSubtitle");

  if (currentStep === 3 || currentStep === 4 || currentStep === 5) {
    if (vrfSection) vrfSection.classList.remove("hidden");

    // Self VRF Score
    const selfScore = (nodeData.vrf_score !== undefined && nodeData.vrf_score !== null)
      ? Number(nodeData.vrf_score)
      : (STORYBOARD_10_VRF_SCORES[idNum] !== undefined ? STORYBOARD_10_VRF_SCORES[idNum] : null);

    if (vrfBadge) {
      vrfBadge.textContent = selfScore !== null ? `\u03c3_self = ${selfScore.toFixed(4)}` : "N/A";
    }

    if (currentStep === 5) {
      if (scoreboardContainer) scoreboardContainer.classList.add("hidden");
      if (electionBanner) electionBanner.classList.add("hidden");
    } else if (currentStep === 3) {
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
          let badgeColorClass = "bg-amber-100 text-amber-900 border-amber-400";
          let winnerLabel = "👑 WINNER (INITIATOR)";
          if (idNum === 4) {
            badgeColorClass = "bg-emerald-100 text-emerald-900 border-emerald-500";
            winnerLabel = "👑 WINNER (Dark Green)";
          } else if (idNum === 2) {
            badgeColorClass = "bg-rose-100 text-rose-900 border-rose-500";
            winnerLabel = "👑 WINNER (Dark Red)";
          } else if (idNum === 8) {
            badgeColorClass = "bg-amber-100 text-amber-900 border-amber-500";
            winnerLabel = "👑 WINNER (Dark Yellow)";
          }
          cardStatusBadge.textContent = winnerLabel;
          cardStatusBadge.className = `text-[9px] font-semibold px-2 py-0.5 rounded border font-bold ${badgeColorClass}`;
        } else {
          cardStatusBadge.textContent = "CANDIDATE";
          cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200";
        }
      }

      // Decision banner:
      // Initiators (Nodes 2, 4, 8): 🏆 Winner — Self-Elected Initiator with distinct color indication.
      // Candidate members: Candidate Member (minimum score listed).
      if (electionBanner) {
        electionBanner.classList.remove("hidden");
        if (isInitiator) {
          let bannerClass = "bg-amber-50 text-amber-900 border-amber-300";
          let colorTag = "Dark Yellow";
          if (idNum === 4) {
            bannerClass = "bg-emerald-50 text-emerald-950 border-emerald-400";
            colorTag = "Dark Green";
          } else if (idNum === 2) {
            bannerClass = "bg-rose-50 text-rose-950 border-rose-400";
            colorTag = "Dark Red";
          } else if (idNum === 8) {
            bannerClass = "bg-amber-50 text-amber-950 border-amber-400";
            colorTag = "Dark Yellow";
          }
          electionBanner.className = `mt-2 p-2 rounded-lg text-[10.5px] font-bold border flex items-center gap-1.5 shadow-xs ${bannerClass}`;
          electionBanner.innerHTML = `<span>🏆</span><span>Winner (${colorTag}) — Self-Elected Initiator (Holds minimum score in 1-hop ball)</span>`;
        } else {
          electionBanner.className = "mt-2 p-2 rounded-lg text-[10px] font-semibold bg-slate-50 text-slate-700 border border-slate-200 leading-snug";
          electionBanner.innerHTML = `<div>Candidate Member</div><div class="text-[9.5px] text-slate-500 font-normal">Minimum held by <span class="font-bold font-mono text-slate-700">C${winnerId}</span> with &sigma;=<span class="font-bold font-mono text-slate-700">${minScore.toFixed(4)}</span></div>`;
        }
      }

      if (scoreboardTitle) scoreboardTitle.textContent = "1-Hop Comparison (Closed Ball):";
      if (scoreboardSubtitle) scoreboardSubtitle.textContent = "min(\u03c3_q, id_q)";

      // Build complete table with VRF scores of selected node itself and all connected neighbors:
      // Regular nodes: show all scores cleanly without highlighting any winner.
      // Initiator nodes: highlight winning score in gold and clearly label node as Winner.
      if (scoreboardBody) {
        scoreboardBody.innerHTML = "";

        const participants = [];
        // Add selected node itself
        const selfScoreVal = (selfScore !== null && selfScore !== undefined)
          ? selfScore
          : (STORYBOARD_10_VRF_SCORES[idNum] !== undefined ? STORYBOARD_10_VRF_SCORES[idNum] : 0.0);

        participants.push({
          id: idNum,
          label: `C${idNum} (Self)`,
          score: selfScoreVal,
          is_self: true
        });

        // Add all connected neighbors
        let neighborList = [];
        if (Array.isArray(nodeData.neighbor_scoreboard) && nodeData.neighbor_scoreboard.length > 0) {
          neighborList = nodeData.neighbor_scoreboard.map(item => ({
            id: item.neighbor_id || parseInt(String(item.label).replace("C", ""), 10),
            score: Number(item.vrf_score !== undefined ? item.vrf_score : STORYBOARD_10_VRF_SCORES[item.neighbor_id])
          }));
        } else if (nodeData.neighbor_scores && Object.keys(nodeData.neighbor_scores).length > 0) {
          neighborList = Object.entries(nodeData.neighbor_scores).map(([nbKey, score]) => ({
            id: parseInt(String(nbKey).replace("C", ""), 10),
            score: Number(score)
          }));
        } else {
          // Fallback using neighbors list or physical topology adjacency
          const nbrIds = (Array.isArray(nodeData.neighbors) && nodeData.neighbors.length > 0)
            ? nodeData.neighbors
            : (STORYBOARD_10_ADJACENCY[idNum] || []);
          neighborList = nbrIds.map(nbId => ({
            id: nbId,
            score: STORYBOARD_10_VRF_SCORES[nbId]
          }));
        }

        // Sort neighbors by ID for clean deterministic display
        neighborList.sort((a, b) => a.id - b.id);

        neighborList.forEach(nb => {
          participants.push({
            id: nb.id,
            label: `C${nb.id}`,
            score: nb.score,
            is_self: false
          });
        });

        participants.forEach(p => {
          const tr = document.createElement("tr");
          if (isInitiator && p.is_self) {
            // Selected node is an Initiator: highlight its own row in gold and clearly mark as Winner
            tr.className = "bg-amber-100/90 text-amber-950 font-bold border-l-4 border-amber-500 shadow-xs transition-colors";
            tr.innerHTML = `
              <td class="py-1.5 px-2 font-mono flex items-center gap-1.5 text-amber-950">
                <span class="inline-flex items-center px-1.5 py-0.2 rounded text-[9.5px] bg-amber-200 border border-amber-400 font-bold text-amber-950">👑 Winner</span>
                <span>${p.label}</span>
              </td>
              <td class="py-1.5 px-2 text-right font-mono text-amber-950">
                <span class="inline-block px-1.5 py-0.2 rounded bg-amber-200/90 border border-amber-400 font-bold">${p.score.toFixed(4)}</span>
              </td>
            `;
          } else {
            // Regular candidate nodes and neighbors: clean unhighlighted display
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

  // Step 5: Zone Creation & Probe Status
  const probeSection = document.getElementById("cardProbeSection");
  const probeContent = document.getElementById("cardProbeContent");
  const zoneBadge = document.getElementById("cardZoneBadge");

  if (currentStep === 5) {
    if (probeSection) probeSection.classList.remove("hidden");
    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const isBoundary = Boolean(nodeData.is_boundary || [1, 6].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    if (zoneBadge) {
      if (isBoundary) {
        zoneBadge.textContent = idNum === 1 ? "Zone 2 (First-Wins) ∩ Zone 4" : "Zone 4 (First-Wins) ∩ Zone 8";
        zoneBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-800 border border-amber-300";
      } else if (isInitiator) {
        zoneBadge.textContent = `Zone ${assignedZ} (Initiator)`;
        zoneBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-800 border border-amber-300";
      } else {
        zoneBadge.textContent = `Zone ${assignedZ} (Pending Join)`;
        zoneBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-blue-100 text-blue-800 border border-blue-300";
      }
    }

    if (cardStatusBadge) {
      if (isInitiator) {
        cardStatusBadge.textContent = "👑 INITIATOR";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      } else {
        cardStatusBadge.textContent = "CLIENT";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-blue-50 text-blue-800 border-blue-200";
      }
    }

    if (probeContent) {
      probeContent.innerHTML = "";
      if (isInitiator) {
        const tgtList = (nodeData.probes_sent && nodeData.probes_sent.length)
          ? nodeData.probes_sent.map(p => `C${p.target_id || p.target}`)
          : (idNum === 2 ? ["C1", "C3"] : idNum === 4 ? ["C1", "C5", "C6", "C7"] : ["C6", "C9", "C10"]);
        probeContent.innerHTML = `
          <div class="p-2.5 bg-amber-50 rounded-lg border border-amber-200 text-amber-950">
            <div class="font-bold flex items-center gap-1.5 text-xs text-amber-900">
              <span>👑</span>
              <span>Elected Initiator for Zone ${assignedZ}</span>
            </div>
            <div class="text-slate-600 mt-1.5 text-xs">Dispatched <span class="font-bold font-mono text-slate-800">PROBE(TTL=1)</span> to 1-hop physical neighbors:</div>
            <div class="font-mono font-bold text-amber-900 mt-1 text-xs">${tgtList.join(", ")}</div>
          </div>
        `;
      } else if (isBoundary || idNum === 1 || idNum === 6) {
        const isNode6 = (idNum === 6);
        const winInit = isNode6 ? "C4" : "C2";
        const winTime = isNode6 ? "t = 11.2 ms" : "t = 10.4 ms";
        const winZone = isNode6 ? "4" : "2";
        const delInit = isNode6 ? "C8" : "C4";
        const delTime = isNode6 ? "t = 18.5 ms" : "t = 16.8 ms";

        probeContent.innerHTML = `
          <div class="p-3 bg-amber-50/80 rounded-lg border border-amber-200 text-slate-800">
            <div class="font-bold flex items-center gap-1.5 text-xs text-amber-900">
              <span>⚠️</span>
              <span>Overlapping Probes Detected (First-Wins Arbitration)</span>
            </div>
            <div class="text-slate-600 mt-1 text-xs">Received competing 1-hop PROBE messages:</div>
            <ul class="mt-2 space-y-1.5 text-xs font-mono">
              <li class="flex items-center gap-1.5 text-emerald-800 font-semibold">
                <span>-</span>
                <span>Initiator ${winInit}: Arrived at ${winTime} (<span class="font-bold text-emerald-700">✓ FIRST-WINS WINNER</span>)</span>
              </li>
              <li class="flex items-center gap-1.5 text-slate-600">
                <span>-</span>
                <span>Initiator ${delInit}: Arrived at ${delTime} (<span class="font-semibold text-rose-600">✕ Delayed / Will be dropped</span>)</span>
              </li>
            </ul>
            <div class="mt-2.5 pt-2 border-t border-amber-200/70 text-[11px] text-slate-700 font-sans leading-relaxed">
              <span class="font-bold text-slate-900">Notice:</span> Per Algorithm 3 (First-Wins rule), this node will formally join Zone ${winZone} in the next step.
            </div>
          </div>
        `;
      } else {
        const fromInit = idNum === 3 ? 2 : (idNum === 5 || idNum === 7) ? 4 : 8;
        const arrivalTime = idNum === 3 ? "t = 9.8 ms" : idNum === 5 ? "t = 12.1 ms" : idNum === 7 ? "t = 13.5 ms" : idNum === 9 ? "t = 10.9 ms" : "t = 14.2 ms";
        probeContent.innerHTML = `
          <div class="p-3 bg-blue-50/80 rounded-lg border border-blue-200 text-slate-800">
            <div class="font-bold flex items-center gap-1.5 text-xs text-blue-900">
              <span>✓</span>
              <span>Accepted PROBE(TTL=1) from Initiator C${fromInit}</span>
            </div>
            <div class="text-xs font-mono text-blue-800 mt-1.5">
              - Initiator C${fromInit}: Arrived at ${arrivalTime} (<span class="font-bold text-emerald-700">✓ FIRST-WINS WINNER</span>)
            </div>
            <div class="mt-2.5 pt-2 border-t border-blue-200/70 text-[11px] text-slate-700 font-sans leading-relaxed">
              <span class="font-bold text-slate-900">Notice:</span> Per Algorithm 3 (First-Wins rule), this node will formally join Zone ${fromInit} in the next step.
            </div>
          </div>
        `;
      }
    }
  } else {
    if (probeSection) probeSection.classList.add("hidden");
  }

  // Step 6: Zone Creation & Inter-Zone Boundary Discovery
  const bndSection = document.getElementById("cardBoundaryDiscoverySection");
  const bndBadge = document.getElementById("cardBoundaryDiscoveryBadge");
  const bndContent = document.getElementById("cardBoundaryDiscoveryContent");

  if (currentStep === 6) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.remove("hidden");

    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const isBoundary = Boolean(nodeData.is_boundary || [1, 6].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    if (cardStatusBadge) {
      cardStatusBadge.textContent = "ASSIGNED";
      cardStatusBadge.className = isInitiator
        ? "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400"
        : "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-purple-50 text-purple-800 border-purple-200";
    }

    if (bndBadge) {
      if (isInitiator) {
        bndBadge.textContent = `Zone ${assignedZ} (Initiator Leader 👑)`;
        bndBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      } else if (isBoundary) {
        bndBadge.textContent = `Zone ${assignedZ} (Frontier Client)`;
        bndBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-purple-100 text-purple-900 border border-purple-300";
      } else {
        bndBadge.textContent = `Zone ${assignedZ} (Member Client)`;
        bndBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-slate-100 text-slate-800 border border-slate-300";
      }
    }

    if (bndContent) {
      bndContent.innerHTML = "";
      if (isInitiator) {
        // Initiators: Dedicated highlighted section "Neighbor Zone Initiators Discovered:"
        const discovered = nodeData.discovered_neighbor_zones || (idNum === 2 ? ["C4"] : idNum === 4 ? ["C2", "C8"] : ["C4"]);
        const listItems = discovered.map(nbr => `
          <li class="flex items-center gap-2 text-xs font-mono font-bold text-amber-900 bg-amber-100/70 px-2.5 py-1.5 rounded border border-amber-300/80">
            <span class="text-amber-600">👑</span>
            <span>Zone Initiator ${nbr}</span>
          </li>
        `).join("");

        bndContent.innerHTML = `
          <div class="p-3 bg-amber-50/90 rounded-lg border border-amber-300 shadow-xs">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-amber-950 flex items-center gap-1.5">
                <span>👑</span>
                <span>Zone ${assignedZ} Initiator Discovery</span>
              </span>
              <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-200 text-amber-900 border border-amber-300">
                ${discovered.length} Adjacent Zone${discovered.length > 1 ? 's' : ''}
              </span>
            </div>
            <div class="mt-2.5 text-xs text-slate-700 font-semibold">
              Neighbor Zone Initiators Discovered:
            </div>
            <ul class="mt-1.5 space-y-1.5">
              ${listItems}
            </ul>
            <div class="mt-2.5 pt-2 border-t border-amber-200 text-[11px] text-slate-600 font-sans leading-relaxed">
              Learned via reverse boundary announcements dispatched by frontier peer${idNum === 4 ? 's C1 and C6' : idNum === 2 ? ' C1' : ' C6'}.
            </div>
          </div>
        `;
      } else if (isBoundary || idNum === 1 || idNum === 6) {
        // Frontier member: Explicit "Dispatched Boundary Notifications Table"
        const isNode1 = (idNum === 1);
        const ownInit = isNode1 ? "C2" : "C4";
        const adjInit = isNode1 ? "C4" : "C8";

        bndContent.innerHTML = `
          <div class="p-3 bg-purple-50/80 rounded-lg border border-purple-200">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-purple-950 flex items-center gap-1.5">
                <span>⚡</span>
                <span>Frontier Boundary Client</span>
              </span>
              <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-300">
                L17-L20 NEIGHBOR
              </span>
            </div>
            <div class="mt-2 text-xs text-slate-700">
              <span class="font-semibold text-slate-900">Assigned Zone:</span> Zone ${assignedZ} &nbsp;|&nbsp; <span class="font-semibold text-slate-900">Status:</span> <span class="font-bold text-emerald-700">ASSIGNED</span>
            </div>

            <div class="mt-3 text-xs font-bold text-purple-950 flex items-center gap-1">
              <span>📬</span>
              <span>Dispatched Boundary Notifications Table:</span>
            </div>

            <div class="mt-1.5 overflow-x-auto rounded border border-purple-200">
              <table class="w-full text-left text-xs font-mono">
                <thead class="bg-purple-100/70 text-[10px] uppercase text-purple-900">
                  <tr>
                    <th class="py-1 px-2">Target Initiator</th>
                    <th class="py-1 px-2">Introduced Neighbor</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-purple-100 bg-white">
                  <tr>
                    <td class="py-1.5 px-2 font-semibold text-amber-900">
                      To Own Initiator ${ownInit} 👑
                    </td>
                    <td class="py-1.5 px-2 text-slate-800">
                      Introduced adjacent Initiator <span class="font-bold text-amber-800">${adjInit}</span>
                    </td>
                  </tr>
                  <tr>
                    <td class="py-1.5 px-2 font-semibold text-purple-900">
                      To Neighbor Initiator ${adjInit} 👑
                    </td>
                    <td class="py-1.5 px-2 text-slate-800">
                      Introduced adjacent Initiator <span class="font-bold text-purple-800">${ownInit}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="mt-2.5 pt-2 border-t border-purple-200 text-[11px] text-slate-600 font-sans leading-relaxed">
              Dispatched reverse boundary announcements over physical links per Algorithm 3 lines 17-20.
            </div>
          </div>
        `;
      } else {
        // Regular non-initiator members (C3, C5, C7, C9, C10)
        bndContent.innerHTML = `
          <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-slate-900 flex items-center gap-1.5">
                <span>✓</span>
                <span>Official Zone Member</span>
              </span>
              <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                ASSIGNED
              </span>
            </div>
            <div class="mt-2 text-xs text-slate-700 space-y-1">
              <div><span class="font-semibold text-slate-900">Assigned Zone:</span> Zone C${assignedZ}</div>
              <div><span class="font-semibold text-slate-900">Status:</span> <span class="font-bold text-emerald-700">ASSIGNED</span></div>
              <div><span class="font-semibold text-slate-900">Zone Leader:</span> Initiator C${assignedZ} 👑</div>
            </div>
            <div class="mt-2.5 pt-2 border-t border-slate-200 text-[11px] text-slate-600 font-sans leading-relaxed">
              Node has fully joined Zone ${assignedZ} with tonal color morphing applied.
            </div>
          </div>
        `;
      }
    }
  } else {
    if (bndSection) bndSection.classList.add("hidden");
  }

  // Step 7: Initiator P_min Query Request
  const pminSection = document.getElementById("cardPminQuerySection");
  const pminBadge = document.getElementById("cardPminQueryBadge");
  const pminContent = document.getElementById("cardPminQueryContent");

  if (currentStep === 7) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.remove("hidden");

    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    if (cardStatusBadge) {
      cardStatusBadge.textContent = isInitiator ? "👑 INITIATOR" : "CLIENT";
      cardStatusBadge.className = isInitiator
        ? "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400"
        : "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-blue-50 text-blue-800 border-blue-200";
    }

    if (pminBadge) {
      if (isInitiator) {
        pminBadge.textContent = `Zone ${assignedZ} (Initiator Leader 👑)`;
        pminBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      } else {
        pminBadge.textContent = `Zone ${assignedZ} (Member Client)`;
        pminBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-blue-100 text-blue-900 border border-blue-300";
      }
    }

    if (pminContent) {
      pminContent.innerHTML = "";
      if (isInitiator) {
        const zoneMembersMap = {
          2: ["C1", "C3"],
          4: ["C5", "C6", "C7"],
          8: ["C9", "C10"]
        };
        const membersList = zoneMembersMap[idNum] || (nodeData.target_members ? nodeData.target_members.map(m => `C${m}`) : []);
        pminContent.innerHTML = `
          <div class="p-3 bg-blue-50/90 rounded-lg border border-blue-300 shadow-xs">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-blue-950 flex items-center gap-1.5">
                <span>👑</span>
                <span>Active Dispatched Query:</span>
              </span>
              <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-300">
                REQ_P_MIN
              </span>
            </div>
            <div class="mt-2 text-xs font-bold text-slate-800">
              Broadcasted REQ_P_MIN (τ=0.80) to zone members
            </div>
            <div class="mt-2 text-xs text-slate-700">
              <span class="font-semibold text-slate-900">Target Members:</span> <span class="font-bold font-mono text-blue-900">${membersList.join(", ")}</span>
            </div>
            <div class="mt-2 text-xs font-mono text-slate-600 bg-white/70 p-1.5 rounded border border-blue-100">
              Payload: {"msg": "REQ_P_MIN", "tau": 0.80}
            </div>
            <div class="mt-2.5 pt-2 border-t border-blue-200 text-[11px] text-slate-600 font-sans leading-relaxed">
              Initiator prompts zone members to evaluate the minimum signature length P_min^i needed to retain 80% model quality.
            </div>
          </div>
        `;
      } else {
        const initId = assignedZ;
        pminContent.innerHTML = `
          <div class="p-3 bg-blue-50/90 rounded-lg border border-blue-300 shadow-xs">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-blue-950 flex items-center gap-1.5">
                <span>📥</span>
                <span>Query Notification Banner:</span>
              </span>
              <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                PENDING
              </span>
            </div>
            <div class="mt-2 text-xs font-bold text-blue-900">
              📥 Received REQ_P_MIN from Initiator C${initId} (Target τ=80%)
            </div>
            <div class="mt-2 text-xs font-mono text-slate-700 bg-white/80 p-2 rounded border border-blue-100 space-y-1">
              <div><span class="font-semibold text-slate-900">Pending Query:</span> <span class="font-bold text-blue-700">REQ_P_MIN (tau=0.80)</span></div>
              <div><span class="font-semibold text-slate-900">Quality Retention:</span> &tau; = 0.80 (80%)</div>
              <div><span class="font-semibold text-slate-900">Status:</span> Prepared for Step 8 Local Binary Search</div>
            </div>
            <div class="mt-2.5 pt-2 border-t border-blue-200 text-[11px] text-slate-600 font-sans leading-relaxed">
              Peers receive the query and prepare to execute the local binary search in the next step.
            </div>
          </div>
        `;
      }
    }
  } else {
    if (pminSection) pminSection.classList.add("hidden");
  }

  // Step 8: Local Binary Search & P_min Reporting
  const bsSection = document.getElementById("cardBinarySearchSection");
  const bsBadge = document.getElementById("cardBinarySearchBadge");
  const bsContent = document.getElementById("cardBinarySearchContent");

  if (currentStep === 8) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.remove("hidden");

    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    if (cardStatusBadge) {
      cardStatusBadge.textContent = isInitiator ? "👑 INITIATOR" : "CLIENT";
      cardStatusBadge.className = isInitiator
        ? "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400"
        : "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-purple-50 text-purple-800 border-purple-200";
    }

    if (bsBadge) {
      if (isInitiator) {
        bsBadge.textContent = `Zone ${assignedZ} Leader 👑 (P_min=${nodeData.p_min_cosine || 1})`;
        bsBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      } else {
        bsBadge.textContent = `Zone ${assignedZ} Member (Reported P_min=${nodeData.p_min_cosine || 2})`;
        bsBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-purple-100 text-purple-900 border border-purple-300";
      }
    }

    if (bsContent) {
      bsContent.innerHTML = "";
      const trace = nodeData.binary_search_steps || nodeData.binary_search_trace || [];
      const traceRows = trace.map(t => `
        <tr class="hover:bg-purple-50/50">
          <td class="py-1 px-2 font-bold text-slate-700">Step ${t.step}</td>
          <td class="py-1 px-2 font-mono text-purple-900 font-semibold">mid = ${t.mid}</td>
          <td class="py-1 px-2 font-mono">${t.ratio_pct}</td>
          <td class="py-1 px-2 text-right">
            <span class="inline-block px-1.5 py-0.2 rounded text-[9px] font-mono font-bold ${t.meets ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
              ${t.meets ? '✓ ≥ 80%' : '✕ < 80%'}
            </span>
          </td>
        </tr>
      `).join("");

      const rCos = nodeData.ratios_cosine || {};
      const rEn = nodeData.ratios_energy || {};
      const pMinCos = nodeData.p_min_cosine || nodeData.p_min || 2;
      const pMinEn = nodeData.p_min_energy || 2;

      let reportDetailsHtml = "";
      if (isInitiator) {
        const receivedMap = nodeData.received_reports || (idNum === 2 ? {1: 2, 3: 2} : idNum === 4 ? {5: 1, 6: 2, 7: 2} : {9: 2, 10: 2});
        const reportEntries = Object.entries(receivedMap).map(([mId, pVal]) => `
          <li class="flex items-center justify-between text-[10px] font-mono bg-white p-1.5 rounded border border-amber-200">
            <span class="font-bold text-slate-800">Node C${mId}:</span>
            <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-bold border border-amber-300">P_min = ${pVal}</span>
          </li>
        `).join("");

        reportDetailsHtml = `
          <div class="mt-2.5 p-2.5 bg-amber-50 rounded border border-amber-300 space-y-1.5">
            <div class="text-[10px] font-bold text-amber-900 flex items-center justify-between">
              <span>📥 Received Member Reports:</span>
              <span class="font-mono text-slate-600 font-normal">Self P_min = ${pMinCos}</span>
            </div>
            <ul class="space-y-1">
              ${reportEntries}
            </ul>
          </div>
        `;
      } else {
        reportDetailsHtml = `
          <div class="mt-2.5 p-2 bg-purple-50 rounded border border-purple-200 flex items-center justify-between text-[10.5px]">
            <span class="text-slate-700 font-medium">📬 Reverse Report Destination:</span>
            <span class="font-mono font-bold text-purple-900 px-2 py-0.5 rounded bg-purple-100 border border-purple-300">Initiator C${assignedZ} 👑</span>
          </div>
        `;
      }

      bsContent.innerHTML = `
        <div class="p-3 bg-white rounded-lg border border-purple-200 shadow-xs space-y-2.5">
          <!-- Trace Steps -->
          <div>
            <div class="font-bold text-[10.5px] text-purple-950 flex items-center gap-1 mb-1">
              <span>⚡</span>
              <span>Local Binary Search Execution (Interval p ∈ [1, 10]):</span>
            </div>
            <div class="overflow-x-auto rounded border border-purple-100">
              <table class="w-full text-left text-[10px] font-mono">
                <thead class="bg-purple-100/60 text-purple-900">
                  <tr>
                    <th class="py-1 px-2">Iteration</th>
                    <th class="py-1 px-2">Pivot</th>
                    <th class="py-1 px-2">Cosine Ratio</th>
                    <th class="py-1 px-2 text-right">Evaluation</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-purple-100 bg-white">
                  ${traceRows}
                </tbody>
              </table>
            </div>
          </div>

          <!-- Quality Retention Table -->
          <div>
            <div class="font-bold text-[10.5px] text-slate-900 flex items-center gap-1 mb-1">
              <span>📊</span>
              <span>Quality Retention Ratio Profile:</span>
            </div>
            <div class="overflow-x-auto rounded border border-slate-200">
              <table class="w-full text-left text-[10px] font-mono">
                <thead class="bg-slate-100 text-slate-800">
                  <tr>
                    <th class="py-1 px-2">Dimension (p)</th>
                    <th class="py-1 px-2">Cosine Quality</th>
                    <th class="py-1 px-2">Energy Quality</th>
                    <th class="py-1 px-2 text-right">Meets τ=80%</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 bg-white">
                  <tr>
                    <td class="py-1 px-2 font-bold text-slate-700">p = 1</td>
                    <td class="py-1 px-2 text-slate-800">${(Number(rCos[1] || 0)*100).toFixed(1)}%</td>
                    <td class="py-1 px-2 text-slate-600">${(Number(rEn[1] || 0)*100).toFixed(1)}%</td>
                    <td class="py-1 px-2 text-right font-bold ${rCos[1] >= 0.8 ? 'text-emerald-700' : 'text-slate-400'}">${rCos[1] >= 0.8 ? '✓ Yes' : '✕ No'}</td>
                  </tr>
                  <tr>
                    <td class="py-1 px-2 font-bold text-slate-700">p = 2</td>
                    <td class="py-1 px-2 text-slate-800">${(Number(rCos[2] || 0)*100).toFixed(1)}%</td>
                    <td class="py-1 px-2 text-slate-600">${(Number(rEn[2] || 0)*100).toFixed(1)}%</td>
                    <td class="py-1 px-2 text-right font-bold ${rCos[2] >= 0.8 ? 'text-emerald-700' : 'text-slate-400'}">${rCos[2] >= 0.8 ? '✓ Yes' : '✕ No'}</td>
                  </tr>
                  <tr>
                    <td class="py-1 px-2 font-bold text-slate-700">p = 3</td>
                    <td class="py-1 px-2 text-slate-800">${(Number(rCos[3] || 0)*100).toFixed(1)}%</td>
                    <td class="py-1 px-2 text-slate-600">${(Number(rEn[3] || 0)*100).toFixed(1)}%</td>
                    <td class="py-1 px-2 text-right font-bold ${rCos[3] >= 0.8 ? 'text-emerald-700' : 'text-slate-400'}">${rCos[3] >= 0.8 ? '✓ Yes' : '✕ No'}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Final Result Card -->
          <div class="p-2 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200 flex items-center justify-between">
            <div class="text-[10px] text-purple-950 font-sans">
              <span class="font-bold">Minimal Cardinality:</span>
              <span class="font-mono text-purple-700 font-bold ml-1">P_min (Cosine) = ${pMinCos}</span>
              <span class="text-slate-500 font-mono ml-2">| Energy = ${pMinEn}</span>
            </div>
            <span class="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-600 text-white shadow-xs">
              P_min = ${pMinCos}
            </span>
          </div>

          ${reportDetailsHtml}
        </div>
      `;
    }
  } else {
    if (bsSection) bsSection.classList.add("hidden");
  }

  // Step 9: Inter-Initiator P_min Exchange & Global Consensus
  const consensusSection = document.getElementById("cardConsensusSection");
  const consensusBadge = document.getElementById("cardConsensusBadge");
  const consensusContent = document.getElementById("cardConsensusContent");

  if (currentStep === 9) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.remove("hidden");

    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const isBoundary = Boolean(nodeData.is_boundary || [1, 6].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    if (cardStatusBadge) {
      if (isInitiator) {
        cardStatusBadge.textContent = "👑 INITIATOR (CONSENSUS REACHED)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      } else if (isBoundary) {
        cardStatusBadge.textContent = "🌐 BOUNDARY GATEWAY (ACTIVE RELAY)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-blue-100 text-blue-900 border-blue-400";
      } else {
        cardStatusBadge.textContent = "CLIENT (ZONE MEMBER)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-purple-50 text-purple-800 border-purple-200";
      }
    }

    if (consensusBadge) {
      if (isInitiator) {
        consensusBadge.textContent = `Zone ${assignedZ} Initiator (Agreed P = 3)`;
        consensusBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      } else if (isBoundary) {
        consensusBadge.textContent = `Boundary Relay Gateway (C${idNum})`;
        consensusBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-blue-100 text-blue-900 border border-blue-300";
      } else {
        consensusBadge.textContent = `Zone ${assignedZ} Member`;
        consensusBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-slate-100 text-slate-800 border border-slate-300";
      }
    }

    if (consensusContent) {
      consensusContent.innerHTML = "";

      if (isInitiator) {
        const localP = nodeData.local_zone_p || (idNum === 2 ? 2 : 3);
        const receivedMap = nodeData.received_neighbor_p || (idNum === 2 ? {"C4": 3} : idNum === 4 ? {"C2": 2, "C8": 3} : {"C4": 3});
        const receivedEntries = Object.entries(receivedMap).map(([nbr, pVal]) => `
          <tr class="hover:bg-amber-50/50">
            <td class="py-1 px-2 font-bold text-amber-950 font-mono">${nbr}</td>
            <td class="py-1 px-2 text-slate-600 font-mono">${nbr === 'C2' || (idNum === 2 && nbr === 'C4') ? 'Node C1' : 'Node C6'}</td>
            <td class="py-1 px-2 text-right">
              <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-bold border border-amber-300 text-[10px] font-mono">
                P = ${pVal}
              </span>
            </td>
          </tr>
        `).join("");

        consensusContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-amber-200 shadow-xs space-y-2.5">
            <div>
              <div class="font-bold text-[10.5px] text-amber-950 flex items-center gap-1 mb-1">
                <span>🤝</span>
                <span>Inter-Zone Negotiation Table:</span>
              </div>
              <div class="overflow-x-auto rounded border border-amber-100">
                <table class="w-full text-left text-[10px] font-mono">
                  <thead class="bg-amber-100/70 text-amber-900">
                    <tr>
                      <th class="py-1 px-2">Source Initiator</th>
                      <th class="py-1 px-2">Relay Gateway</th>
                      <th class="py-1 px-2 text-right">Proposed P</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-amber-100 bg-white">
                    <tr class="bg-amber-50/40">
                      <td class="py-1 px-2 font-bold text-emerald-800 font-mono">C${idNum} (Local Zone)</td>
                      <td class="py-1 px-2 text-slate-500 font-mono">Direct Self</td>
                      <td class="py-1 px-2 text-right">
                        <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 font-bold border border-emerald-300 text-[10px] font-mono">
                          P = ${localP}
                        </span>
                      </td>
                    </tr>
                    ${receivedEntries}
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Consensus Computation Box -->
            <div class="p-2.5 bg-gradient-to-r from-amber-50 to-indigo-50 rounded-lg border border-indigo-200 space-y-1">
              <div class="text-[10.5px] font-bold text-indigo-950 flex items-center justify-between">
                <span>🎯 Quantile Consensus Formula:</span>
                <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold border border-emerald-300 text-[10px] font-mono">✓ Consensus Reached</span>
              </div>
              <div class="text-[10px] font-mono text-slate-700 bg-white/80 p-1.5 rounded border border-indigo-100">
                P = min(Quantile_0.8({P_min^i}), P_max) = max(2, 3, 3) = 3
              </div>
              <div class="flex items-center justify-between pt-1">
                <span class="text-[10px] font-bold text-slate-700">Agreed Global Dimension:</span>
                <span class="px-3 py-0.5 rounded-md bg-indigo-600 text-white font-bold text-xs font-mono shadow-xs">
                  Global P = 3
                </span>
              </div>
            </div>
          </div>
        `;
      } else if (isBoundary) {
        const relayPackets = nodeData.relayed_packets || (idNum === 1 ? [
          {packet: "P_Z2=2", from: "C2", to: "C4", p_val: 2, route: "C2 -> C1 -> C4"},
          {packet: "P_Z4=3", from: "C4", to: "C2", p_val: 3, route: "C4 -> C1 -> C2"}
        ] : [
          {packet: "P_Z4=3", from: "C4", to: "C8", p_val: 3, route: "C4 -> C6 -> C8"},
          {packet: "P_Z8=3", from: "C8", to: "C4", p_val: 3, route: "C8 -> C6 -> C4"}
        ]);

        const relayRows = relayPackets.map(r => `
          <tr class="hover:bg-blue-50/50">
            <td class="py-1 px-2 font-mono font-bold text-blue-900">${r.from} → ${r.to}</td>
            <td class="py-1 px-2 font-mono text-slate-600">${r.route}</td>
            <td class="py-1 px-2 text-right">
              <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-bold border border-blue-300 text-[10px] font-mono">
                P = ${r.p_val}
              </span>
            </td>
          </tr>
        `).join("");

        consensusContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-blue-200 shadow-xs space-y-2.5">
            <div>
              <div class="font-bold text-[10.5px] text-blue-950 flex items-center gap-1 mb-1">
                <span>🌐</span>
                <span>Active Gateway Relay Log:</span>
              </div>
              <div class="overflow-x-auto rounded border border-blue-100">
                <table class="w-full text-left text-[10px] font-mono">
                  <thead class="bg-blue-100/70 text-blue-900">
                    <tr>
                      <th class="py-1 px-2">Initiator Exchange</th>
                      <th class="py-1 px-2">Physical Route</th>
                      <th class="py-1 px-2 text-right">Payload</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-blue-100 bg-white">
                    ${relayRows}
                  </tbody>
                </table>
              </div>
            </div>

            <div class="p-2 bg-blue-50/90 rounded border border-blue-200 text-[10px] text-slate-700 leading-relaxed font-sans">
              <span class="font-bold text-blue-950">Gateway Role:</span> Peer C${idNum} is the critical inter-zone boundary bridge forwarding proposal packets between neighboring initiators.
            </div>

            <div class="flex items-center justify-between p-2 bg-indigo-50 rounded border border-indigo-200">
              <span class="text-[10px] font-bold text-indigo-950">Network Consensus Result:</span>
              <span class="px-2.5 py-0.5 rounded bg-indigo-600 text-white font-bold text-xs font-mono">
                Global P = 3
              </span>
            </div>
          </div>
        `;
      } else {
        consensusContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-xs space-y-2">
            <div class="text-[10.5px] font-bold text-slate-900 flex items-center gap-1">
              <span>⏳</span>
              <span>Member Status:</span>
            </div>
            <div class="p-2.5 bg-slate-50 rounded border border-slate-200 text-[10.5px] text-slate-700 space-y-1">
              <div>Zone: <span class="font-bold text-slate-900">Zone ${assignedZ}</span></div>
              <div>Reported in Step 8: <span class="font-mono font-bold text-purple-700">P_min = ${nodeData.p_min_reported || 2}</span></div>
              <div>Initiators Status: <span class="text-emerald-700 font-bold">Unanimously Agreed on P = 3</span></div>
              <div class="text-slate-500 pt-1 text-[9.5px]">Awaiting Step 10 Global-P Broadcast from Zone Initiator.</div>
            </div>
          </div>
        `;
      }
    }
  } else {
    if (consensusSection) consensusSection.classList.add("hidden");
  }

  // Step 10: Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3)
  const orderSection = document.getElementById("cardOrderExtractSection");
  const orderBadge = document.getElementById("cardOrderExtractBadge");
  const orderContent = document.getElementById("cardOrderExtractContent");

  if (currentStep === 10) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.remove("hidden");

    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    if (cardStatusBadge) {
      if (isInitiator) {
        cardStatusBadge.textContent = "👑 INITIATOR (DIRECTIVE ISSUER)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      } else {
        cardStatusBadge.textContent = "CLIENT (ORDER RECEIVED)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-emerald-50 text-emerald-800 border-emerald-300";
      }
    }

    if (orderBadge) {
      if (isInitiator) {
        orderBadge.textContent = `Zone ${assignedZ} Initiator (P=3 Directive)`;
        orderBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      } else {
        orderBadge.textContent = `Zone ${assignedZ} Member (Locked P=3)`;
        orderBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-300";
      }
    }

    if (orderContent) {
      orderContent.innerHTML = "";

      if (isInitiator) {
        const zoneMembersMap = {
          2: ["C1", "C3"],
          4: ["C5", "C6", "C7"],
          8: ["C9", "C10"]
        };
        const membersList = zoneMembersMap[idNum] || (nodeData.target_members ? nodeData.target_members.map(m => `C${m}`) : []);

        orderContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-amber-200 shadow-xs space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-[10.5px] text-amber-950 flex items-center gap-1.5">
                <span>👑</span>
                <span>Broadcast Extraction Order:</span>
              </span>
              <span class="text-[9.5px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                ORDER_EXTRACT
              </span>
            </div>

            <div class="p-2.5 bg-amber-50 rounded border border-amber-300 space-y-1.5 text-[10px] font-mono">
              <div class="font-bold text-slate-800 flex items-center justify-between">
                <span>Directive Command:</span>
                <span class="text-amber-900 font-bold">ORDER_EXTRACT(P = 3)</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Target Members:</span>
                <span class="font-bold text-amber-900">${membersList.join(", ")}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Target Dimensionality:</span>
                <span class="font-bold text-emerald-700 bg-white px-2 py-0.2 rounded border border-emerald-200">P = 3 (Locked)</span>
              </div>
            </div>

            <div class="p-2 bg-emerald-50 rounded border border-emerald-200 flex items-center justify-between text-[10.5px]">
              <span class="text-slate-700 font-medium">Local Initiator State:</span>
              <span class="font-mono font-bold text-emerald-800 px-2 py-0.5 rounded bg-emerald-100 border border-emerald-300">
                READY_TO_EXTRACT
              </span>
            </div>

            <div class="text-[10px] text-slate-600 font-sans leading-relaxed">
              Following global consensus agreement on P=3 in Step 9, Initiator C${idNum} commands all zone peers to lock their signature truncation dimension to exactly P = 3.
            </div>
          </div>
        `;
      } else {
        const fromInit = nodeData.order_received_from || `C${assignedZ}`;

        orderContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-emerald-200 shadow-xs space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-[10.5px] text-emerald-950 flex items-center gap-1.5">
                <span>📥</span>
                <span>Directive Notice:</span>
              </span>
              <span class="text-[9.5px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                RECEIVED ORDER
              </span>
            </div>

            <div class="p-2.5 bg-emerald-50 rounded border border-emerald-300 space-y-1.5 text-[10px] font-mono">
              <div class="font-bold text-slate-800 flex items-center justify-between">
                <span>Received From:</span>
                <span class="text-emerald-900 font-bold">Initiator ${fromInit} 👑</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Protocol Payload:</span>
                <span class="text-slate-800 bg-white px-1.5 py-0.2 rounded border border-emerald-200">{"cmd": "ORDER_EXTRACT", "target_p": 3}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Target Signature Dimensionality:</span>
                <span class="font-bold text-emerald-700 bg-white px-2 py-0.2 rounded border border-emerald-200">P = 3 (Locked)</span>
              </div>
            </div>

            <div class="p-2 bg-emerald-50/90 rounded border border-emerald-200 flex items-center justify-between text-[10.5px]">
              <span class="text-slate-700 font-medium">Peer Extraction Readiness:</span>
              <span class="font-mono font-bold text-emerald-800 px-2 py-0.5 rounded bg-emerald-100 border border-emerald-300">
                READY_TO_EXTRACT
              </span>
            </div>

            <div class="text-[10px] text-slate-600 font-sans leading-relaxed">
              Peer C${idNum} has locked its parameter extraction target to P = 3 and is fully primed to extract its top-3 compact signature in Step 11.
            </div>
          </div>
        `;
      }
    }
  } else {
    if (orderSection) orderSection.classList.add("hidden");
  }

  // Step 11: Top-P Signature Extraction with Dual Representation
  const sigSection = document.getElementById("cardSignatureSection");
  const sigBadge = document.getElementById("cardSignatureBadge");
  const sigContent = document.getElementById("cardSignatureContent");

  if (currentStep === 11) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.remove("hidden");

    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    // Fallback top_p_indices and binary_mask_10d if not directly on nodeData
    const defaultIndicesMap = {
      1: [1, 2, 3], 2: [1, 2, 3], 3: [4, 5, 6],
      4: [4, 5, 6], 5: [4, 5, 6], 6: [7, 9, 10],
      7: [8, 9, 10], 8: [4, 5, 6], 9: [1, 2, 3],
      10: [8, 9, 10]
    };
    const topPIndices = nodeData.top_p_indices || defaultIndicesMap[idNum] || [1, 2, 3];
    const binaryMask = nodeData.binary_mask_10d || Array.from({ length: 10 }, (_, i) => topPIndices.includes(i + 1) ? 1 : 0);

    if (cardStatusBadge) {
      if (isInitiator) {
        cardStatusBadge.textContent = "👑 INITIATOR (ZONE REGISTRY)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      } else {
        cardStatusBadge.textContent = "CLIENT (SIGNATURE DISPATCHED)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-cyan-50 text-cyan-800 border-cyan-300";
      }
    }

    if (sigBadge) {
      if (isInitiator) {
        sigBadge.textContent = `Zone ${assignedZ} Initiator (Registry Ready)`;
        sigBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      } else {
        sigBadge.textContent = `Zone ${assignedZ} Member (Wire Dispatched)`;
        sigBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-cyan-100 text-cyan-800 border border-cyan-300";
      }
    }

    if (sigContent) {
      sigContent.innerHTML = "";

      // 1. 10-Cell Interactive Binary Strip
      let stripCells = "";
      for (let c = 1; c <= 10; c++) {
        const isBitActive = binaryMask[c - 1] === 1;
        const cl = CIFAR10_CLASSES[c] || { code: `C${c}`, icon: "", name: "" };
        if (isBitActive) {
          stripCells += `
            <div class="flex flex-col items-center justify-center py-1 px-0.5 rounded border border-emerald-400 bg-emerald-500 text-white font-bold shadow-xs transition-all hover:scale-105" title="${cl.code}: ${cl.name} (Active bit = 1)">
              <span class="text-[8px] font-mono leading-tight">${cl.code}</span>
              <span class="text-xs font-mono font-black">1</span>
            </div>
          `;
        } else {
          stripCells += `
            <div class="flex flex-col items-center justify-center py-1 px-0.5 rounded border border-slate-200 bg-slate-100 text-slate-400 font-mono opacity-80" title="${cl.code}: ${cl.name} (Inactive bit = 0)">
              <span class="text-[8px] font-mono leading-tight text-slate-400">${cl.code}</span>
              <span class="text-xs font-mono font-medium">0</span>
            </div>
          `;
        }
      }

      // Active Class Tag Badges
      const activeTags = topPIndices.map(cid => {
        const cl = CIFAR10_CLASSES[cid] || { code: `C${cid}`, icon: "📦", name: `Class ${cid}` };
        return `
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 font-bold font-mono text-[9.5px]">
            <span>${cl.icon}</span>
            <span>${cl.code}: ${cl.name}</span>
          </span>
        `;
      }).join("");

      // Initiator Zone Signature Registry Table
      let registrySectionHtml = "";
      if (isInitiator) {
        const fallbackRegistries = {
          2: { 1: [1, 2, 3], 2: [1, 2, 3], 3: [4, 5, 6] },
          4: { 4: [4, 5, 6], 5: [4, 5, 6], 6: [7, 9, 10], 7: [8, 9, 10] },
          8: { 8: [4, 5, 6], 9: [1, 2, 3], 10: [8, 9, 10] }
        };
        const registryData = nodeData.zone_collected_signatures && Object.keys(nodeData.zone_collected_signatures).length > 0
          ? nodeData.zone_collected_signatures
          : (fallbackRegistries[idNum] || {});

        registrySectionHtml = `
          <div class="pt-2 border-t border-cyan-200 space-y-1.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-[10px] text-cyan-950 flex items-center gap-1">
                <span>📚</span>
                <span>Zone ${assignedZ} Signature Registry:</span>
              </span>
              <span class="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 border border-amber-300">
                Ready for Step 12
              </span>
            </div>
            <div class="overflow-hidden border border-cyan-200 rounded-md bg-white shadow-xs">
              <table class="w-full text-[9.5px] font-mono">
                <thead>
                  <tr class="bg-cyan-50/80 text-cyan-900 border-b border-cyan-200 text-left">
                    <th class="py-1 px-2 font-bold">Node</th>
                    <th class="py-1 px-2 font-bold">Role</th>
                    <th class="py-1 px-2 font-bold">Received Indices</th>
                    <th class="py-1 px-2 font-bold text-right">Wire Size</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  ${Object.entries(registryData).map(([peerId, idxs]) => {
                    const isSelf = parseInt(peerId) === idNum;
                    const idxStr = idxs.map(c => `C${c}`).join(", ");
                    return `
                      <tr class="${isSelf ? 'bg-amber-50/60 font-semibold' : 'hover:bg-slate-50'}">
                        <td class="py-1 px-2 font-bold text-slate-800">C${peerId}</td>
                        <td class="py-1 px-2 text-slate-600">${isSelf ? '👑 Initiator' : 'Member'}</td>
                        <td class="py-1 px-2 text-emerald-700 font-bold">{${idxStr}}</td>
                        <td class="py-1 px-2 text-right text-slate-500">3 Bytes</td>
                      </tr>
                    `;
                  }).join("")}
                </tbody>
              </table>
            </div>
          </div>
        `;
      }

      sigContent.innerHTML = `
        <div class="p-3 bg-white rounded-lg border border-cyan-200 shadow-xs space-y-2.5">
          <!-- 1. Wire Transmission (Paper Specification) -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-[10.5px] text-cyan-950 flex items-center gap-1.5">
                <span>📡</span>
                <span>Wire Transmission (Paper Spec):</span>
              </span>
              <span class="text-[9.5px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-100 text-cyan-800 border border-cyan-300">
                INDEX SET
              </span>
            </div>
            <div class="p-2.5 bg-slate-50 rounded border border-cyan-300 space-y-1.5 text-[10px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Transmitted Payload:</span>
                <span class="font-bold text-cyan-900 bg-white px-2 py-0.5 rounded border border-cyan-200">
                  Unweighted Index Set {${topPIndices.map(c => `C${c}`).join(", ")}}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Bandwidth Footprint:</span>
                <span class="font-bold text-emerald-700">3 integers (100% weight-free, zero parameter leakage)</span>
              </div>
              <div class="flex items-center justify-between text-[9px] pt-1 border-t border-slate-200 text-slate-500">
                <span>Payload Comparison:</span>
                <span class="text-slate-700 font-semibold font-mono">3 Bytes (uint8[3]) vs. 40 Bytes (float32[10]) → <strong class="text-emerald-700">92.5% savings</strong></span>
              </div>
            </div>
          </div>

          <!-- 2. Visual Bitmask Representation (Simulator View) -->
          <div class="space-y-1.5 pt-2 border-t border-slate-200">
            <div class="flex items-center justify-between">
              <span class="font-bold text-[10.5px] text-slate-800 flex items-center gap-1.5">
                <span>👁️</span>
                <span>Visual Bitmask (Simulator View):</span>
              </span>
              <span class="text-[9px] font-mono font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200">
                10-Cell Indicator
              </span>
            </div>
            <div class="grid grid-cols-10 gap-1 my-1.5">
              ${stripCells}
            </div>
            <div class="flex flex-wrap gap-1 mt-1">
              ${activeTags}
            </div>
          </div>

          <!-- 3. Initiator Registry (if Initiator) -->
          ${registrySectionHtml}
        </div>
      `;
    }
  } else {
    if (sigSection) sigSection.classList.add("hidden");
  }

  // Step 12: Intra-Zone Semantic Clustering (Affinity Propagation)
  const clSection = document.getElementById("cardClusteringSection");
  const clBadge = document.getElementById("cardClusteringBadge");
  const clContent = document.getElementById("cardClusteringContent");

  if (currentStep === 12) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.remove("hidden");

    const isInitiator = Boolean(nodeData.is_initiator || [2, 4, 8].includes(idNum));
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    const defaultClusterMap = {
      1: { cluster_id: "2-A", exemplar: 2, peers: [1, 2], color: "#059669" },
      2: { cluster_id: "2-A", exemplar: 2, peers: [1, 2], color: "#059669" },
      3: { cluster_id: "2-B", exemplar: 3, peers: [3], color: "#0d9488" },
      4: { cluster_id: "4-A", exemplar: 4, peers: [4, 5], color: "#ea580c" },
      5: { cluster_id: "4-A", exemplar: 4, peers: [4, 5], color: "#ea580c" },
      6: { cluster_id: "4-B", exemplar: 6, peers: [6, 7], color: "#d97706" },
      7: { cluster_id: "4-B", exemplar: 6, peers: [6, 7], color: "#d97706" },
      8: { cluster_id: "8-A", exemplar: 8, peers: [8], color: "#7c3aed" },
      9: { cluster_id: "8-B", exemplar: 9, peers: [9], color: "#6366f1" },
      10: { cluster_id: "8-C", exemplar: 10, peers: [10], color: "#8b5cf6" },
    };

    const clusterInfo = defaultClusterMap[idNum] || { cluster_id: "2-A", exemplar: 2, peers: [idNum], color: "#059669" };
    const assignedClusterId = nodeData.assigned_cluster_id || nodeData.cluster_id || clusterInfo.cluster_id;
    const clusterExemplar = nodeData.cluster_exemplar || clusterInfo.exemplar;
    const clusterPeers = nodeData.cluster_peers || clusterInfo.peers;
    const clusterColor = nodeData.cluster_color || clusterInfo.color;

    if (cardStatusBadge) {
      if (isInitiator) {
        cardStatusBadge.textContent = "👑 INITIATOR (AP CLUSTER ENGINE)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      } else {
        cardStatusBadge.textContent = "CLIENT (SEMANTICALLY CLUSTERED)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-violet-50 text-violet-800 border-violet-300";
      }
    }

    if (clBadge) {
      if (isInitiator) {
        clBadge.textContent = `Zone ${assignedZ} Initiator (AP Partitioning)`;
        clBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      } else {
        clBadge.textContent = `Cluster ${assignedClusterId} (Zone ${assignedZ})`;
        clBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-violet-100 text-violet-800 border border-violet-300";
      }
    }

    if (clContent) {
      clContent.innerHTML = "";

      if (isInitiator) {
        // Initiator View:
        // 1. Intra-Zone Cosine Similarity Heatmap/Matrix Table
        // 2. Identified Semantic Clusters Card
        const fallbackSim = {
          2: {
            peers: ["C1", "C2", "C3"],
            matrix: [[1.0, 1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
          },
          4: {
            peers: ["C4", "C5", "C6", "C7"],
            matrix: [[1.0, 1.0, 0.0, 0.0], [1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.67], [0.0, 0.0, 0.67, 1.0]]
          },
          8: {
            peers: ["C8", "C9", "C10"],
            matrix: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
          }
        }[idNum] || { peers: [], matrix: [] };

        const simData = (nodeData.intra_zone_similarity_matrix && nodeData.intra_zone_similarity_matrix.matrix)
          ? nodeData.intra_zone_similarity_matrix
          : fallbackSim;

        const peers = simData.peers || [];
        const matrix = simData.matrix || [];

        function getHeatmapStyle(val) {
          if (val >= 0.99) return "background-color: #059669; color: #ffffff; font-weight: bold;";
          if (val >= 0.6) return "background-color: #0d9488; color: #ffffff; font-weight: bold;";
          if (val > 0) return "background-color: #0284c7; color: #ffffff;";
          return "background-color: #1e293b; color: #94a3b8;";
        }

        const headerCells = peers.map(p => `<th class="py-1 px-1.5 text-center text-slate-700 bg-slate-100 border border-slate-200">${p}</th>`).join("");
        const matrixRows = matrix.map((row, rIdx) => {
          const rowPeer = peers[rIdx] || `C${rIdx}`;
          const cells = row.map(val => {
            const num = Number(val);
            const style = getHeatmapStyle(num);
            return `<td class="py-1 px-1.5 text-center text-[10px] font-mono border border-slate-200" style="${style}">${num.toFixed(2)}</td>`;
          }).join("");
          return `
            <tr>
              <th class="py-1 px-1.5 text-center font-bold text-slate-700 bg-slate-100 border border-slate-200">${rowPeer}</th>
              ${cells}
            </tr>
          `;
        }).join("");

        const fallbackClusters = {
          2: {
            "2-A": { cluster_id: "2-A", exemplar: 2, members_str: ["C1", "C2"], shared_classes: ["Airplane (C1)", "Automobile (C2)", "Bird (C3)"], overlap_pct: 100.0, color: "#059669" },
            "2-B": { cluster_id: "2-B", exemplar: 3, members_str: ["C3"], shared_classes: ["Cat (C4)", "Deer (C5)", "Dog (C6)"], overlap_pct: 100.0, color: "#0d9488" }
          },
          4: {
            "4-A": { cluster_id: "4-A", exemplar: 4, members_str: ["C4", "C5"], shared_classes: ["Cat (C4)", "Deer (C5)", "Dog (C6)"], overlap_pct: 100.0, color: "#ea580c" },
            "4-B": { cluster_id: "4-B", exemplar: 6, members_str: ["C6", "C7"], shared_classes: ["Ship (C9)", "Truck (C10)"], overlap_pct: 66.7, color: "#d97706" }
          },
          8: {
            "8-A": { cluster_id: "8-A", exemplar: 8, members_str: ["C8"], shared_classes: ["Cat (C4)", "Deer (C5)", "Dog (C6)"], overlap_pct: 100.0, color: "#7c3aed" },
            "8-B": { cluster_id: "8-B", exemplar: 9, members_str: ["C9"], shared_classes: ["Airplane (C1)", "Automobile (C2)", "Bird (C3)"], overlap_pct: 100.0, color: "#6366f1" },
            "8-C": { cluster_id: "8-C", exemplar: 10, members_str: ["C10"], shared_classes: ["Horse (C8)", "Ship (C9)", "Truck (C10)"], overlap_pct: 100.0, color: "#8b5cf6" }
          }
        }[idNum] || {};

        const clustersMap = (nodeData.clusters && Object.keys(nodeData.clusters).length > 0)
          ? nodeData.clusters
          : ((nodeData.zone_clusters && Object.keys(nodeData.zone_clusters).length > 0) ? nodeData.zone_clusters : fallbackClusters);

        const clusterCards = Object.values(clustersMap).map(c => `
          <div class="p-2 rounded-lg border text-[10px] space-y-1" style="border-color: ${c.color}66; background-color: ${c.color}10;">
            <div class="flex items-center justify-between font-bold">
              <span class="flex items-center gap-1.5" style="color: ${c.color};">
                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${c.color};"></span>
                <span>Cluster ${c.cluster_id}</span>
              </span>
              <span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-white border" style="border-color: ${c.color}55; color: ${c.color};">
                👑 Exemplar: C${c.exemplar}
              </span>
            </div>
            <div class="flex items-center justify-between text-slate-700">
              <span class="font-semibold">Member Nodes:</span>
              <span class="font-mono font-bold text-slate-900">{${(c.members_str || (c.members || []).map(m => `C${m}`)).join(", ")}}</span>
            </div>
            <div class="text-[9.5px] text-slate-600">
              <span class="font-semibold text-slate-700">Shared Classes:</span> ${(c.shared_classes || []).join(", ")}
              <span class="font-bold ml-1" style="color: ${c.color};">(${c.overlap_pct || 100}% Overlap)</span>
            </div>
          </div>
        `).join("");

        clContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-violet-200 shadow-xs space-y-3">
            <!-- Heatmap Table -->
            <div>
              <div class="flex items-center justify-between mb-1.5">
                <span class="font-bold text-[10.5px] text-violet-950 flex items-center gap-1.5">
                  <span>🔥</span>
                  <span>Intra-Zone Cosine Similarity Heatmap:</span>
                </span>
                <span class="text-[9px] font-mono text-slate-500">
                  Sim(i,j) = |m_i ∩ m_j| / 3
                </span>
              </div>
              <div class="overflow-x-auto rounded border border-slate-200">
                <table class="w-full text-left text-[10px] font-mono border-collapse">
                  <thead>
                    <tr>
                      <th class="py-1 px-1.5 text-center bg-slate-50 border border-slate-200 text-slate-500">Peer</th>
                      ${headerCells}
                    </tr>
                  </thead>
                  <tbody>
                    ${matrixRows}
                  </tbody>
                </table>
              </div>
              <div class="flex items-center justify-between mt-1 text-[9px] text-slate-500">
                <span class="flex items-center gap-1"><span class="w-2.5 h-2 rounded bg-slate-800 inline-block"></span> 0.0 (Orthogonal)</span>
                <span class="flex items-center gap-1"><span class="w-2.5 h-2 rounded bg-teal-600 inline-block"></span> 0.67 (Partial)</span>
                <span class="flex items-center gap-1"><span class="w-2.5 h-2 rounded bg-emerald-600 inline-block"></span> 1.0 (Identical)</span>
              </div>
            </div>

            <!-- Identified Semantic Clusters Card -->
            <div class="space-y-1.5 pt-2 border-t border-slate-200">
              <div class="flex items-center justify-between">
                <span class="font-bold text-[10.5px] text-violet-950 flex items-center gap-1.5">
                  <span>🧩</span>
                  <span>Identified Semantic Clusters (AP Partitioning):</span>
                </span>
                <span class="text-[9.5px] font-mono font-bold px-2 py-0.5 rounded bg-violet-100 text-violet-800 border border-violet-300">
                  ${Object.keys(clustersMap).length} Clusters
                </span>
              </div>
              <div class="space-y-2">
                ${clusterCards}
              </div>
            </div>

            <div class="p-2 bg-violet-50/80 rounded border border-violet-200 text-[10px] text-slate-700 leading-relaxed font-sans">
              <span class="font-bold text-violet-950">AP Clustering Notice:</span> Initiator C${idNum} grouped zone members by preference-driven message passing (median similarity preference), creating tight semantic consensus cells for model aggregation.
            </div>
          </div>
        `;
      } else {
        // Regular Member View
        const sharedClassesMap = {
          "2-A": "Airplane (C1), Automobile (C2), Bird (C3)",
          "2-B": "Cat (C4), Deer (C5), Dog (C6)",
          "4-A": "Cat (C4), Deer (C5), Dog (C6)",
          "4-B": "Ship (C9), Truck (C10)",
          "8-A": "Cat (C4), Deer (C5), Dog (C6)",
          "8-B": "Airplane (C1), Automobile (C2), Bird (C3)",
          "8-C": "Horse (C8), Ship (C9), Truck (C10)"
        };

        const sharedClasses = sharedClassesMap[assignedClusterId] || "Top-P Dominant Classes";
        const peerListStr = (clusterPeers || []).map(p => `C${p}`).join(", ");

        clContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-violet-200 shadow-xs space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-[10.5px] text-violet-950 flex items-center gap-1.5">
                <span>🧩</span>
                <span>Semantic Cluster Profile:</span>
              </span>
              <span class="text-[9.5px] font-mono font-bold px-2 py-0.5 rounded text-white shadow-xs" style="background-color: ${clusterColor};">
                Cluster ${assignedClusterId}
              </span>
            </div>

            <div class="p-2.5 bg-slate-50 rounded border border-violet-200 space-y-1.5 text-[10px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Assigned Semantic Cluster:</span>
                <span class="font-bold text-violet-900 bg-white px-2 py-0.5 rounded border border-violet-200">
                  Cluster ${assignedClusterId}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Cluster Exemplar:</span>
                <span class="font-bold text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  👑 Node C${clusterExemplar}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Semantic Peers in Zone:</span>
                <span class="font-bold text-emerald-800 bg-white px-2 py-0.5 rounded border border-emerald-200">
                  [${peerListStr}]
                </span>
              </div>
              <div class="pt-1 border-t border-slate-200 text-[9.5px]">
                <span class="text-slate-600 font-semibold">Cluster Focus:</span>
                <span class="text-slate-800 font-sans font-medium ml-1">${sharedClasses}</span>
              </div>
            </div>

            <div class="p-2 bg-violet-50 rounded border border-violet-200 flex items-center justify-between text-[10.5px]">
              <span class="text-slate-700 font-medium">Clustering State:</span>
              <span class="font-mono font-bold text-violet-800 px-2 py-0.5 rounded bg-violet-100 border border-violet-300">
                CLUSTERED_IN_ZONE_${assignedZ}
              </span>
            </div>

            <div class="text-[10px] text-slate-600 font-sans leading-relaxed">
              Assigned to Cluster ${assignedClusterId} by Initiator C${assignedZ} based on high intra-zone cosine similarity. Node C${idNum} shares federated weight updates primarily within this semantic cluster.
            </div>
          </div>
        `;
      }
    }
  } else {
    if (clSection) clSection.classList.add("hidden");
  }

  // Step 13: Intra-Zone Cluster Exemplar Designation & Profile Assignment
  const exemplarSection = document.getElementById("cardExemplarSection");
  const exemplarBadge = document.getElementById("cardExemplarBadge");
  const exemplarContent = document.getElementById("cardExemplarContent");
  const topZoneSection = document.getElementById("cardTopZoneSection");

  if (currentStep === 13) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.add("hidden");
    if (topZoneSection) topZoneSection.classList.add("hidden");
    if (exemplarSection) exemplarSection.classList.remove("hidden");

    // Defensive Exemplar Fields per specification
    const isExemplar = Boolean(mergedNode.is_exemplar);
    const clusterId = mergedNode.cluster_id || 'N/A';
    const exemplarFor = Array.isArray(mergedNode.exemplar_for) ? mergedNode.exemplar_for : [];
    const profileSig = Array.isArray(mergedNode.profile_signature) ? mergedNode.profile_signature : [];
    const exemplarNodeId = mergedNode.exemplar_node_id ?? (isExemplar ? (idNum || mergedNode.id) : 'N/A');

    const assignedZ = mergedNode.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    const defaultClusterColors = {
      "2-A": "#059669", "2-B": "#0d9488",
      "4-A": "#ea580c", "4-B": "#d97706",
      "8-A": "#7c3aed", "8-B": "#6d28d9"
    };
    const cColor = defaultClusterColors[clusterId] || "#2563eb";

    if (cardStatusBadge) {
      if (isExemplar) {
        cardStatusBadge.textContent = "⭐ DESIGNATED CLUSTER EXEMPLAR";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      } else {
        cardStatusBadge.textContent = "REGULAR CLUSTER MEMBER";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-slate-100 text-slate-700 border-slate-300";
      }
    }

    if (exemplarBadge) {
      if (isExemplar) {
        exemplarBadge.textContent = `EXEMPLAR (${clusterId})`;
        exemplarBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-400";
      } else {
        exemplarBadge.textContent = `MEMBER (${clusterId})`;
        exemplarBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-slate-100 text-slate-800 border border-slate-300";
      }
    }

    if (exemplarContent) {
      const peerListStr = exemplarFor.length > 0 ? exemplarFor.map(id => `C${id}`).join(", ") : `C${idNum}`;
      const sigListStr = profileSig.length > 0 
        ? profileSig.map(c => `<span class="px-1 py-0.5 rounded bg-slate-100 border border-slate-300 text-slate-800 font-bold font-mono text-[9px]">${c} (${getCifarClass(c).name})</span>`).join(" ")
        : '<span class="text-slate-400 italic">None</span>';

      if (isExemplar) {
        exemplarContent.innerHTML = `
          <div class="bg-amber-50/70 border border-amber-200 rounded-lg p-2.5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-bold text-amber-950 flex items-center gap-1.5 text-xs">
                <span>⭐</span>
                <span>DESIGNATED CLUSTER EXEMPLAR</span>
              </span>
              <span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold text-white shadow-xs" style="background-color: ${cColor};">
                Cluster ${clusterId}
              </span>
            </div>

            <div class="space-y-1 text-[10px] text-slate-700 bg-white/80 p-2 rounded border border-amber-100">
              <div class="flex justify-between items-center py-0.5">
                <span class="text-slate-500 font-semibold">Exemplar Status:</span>
                <span class="font-mono font-bold text-amber-900 bg-amber-100/80 px-1.5 py-0.2 rounded border border-amber-300">
                  TRUE (DESIGNATED CLUSTER EXEMPLAR)
                </span>
              </div>
              <div class="flex justify-between items-center py-0.5">
                <span class="text-slate-500 font-semibold">Cluster ID:</span>
                <span class="font-mono font-bold text-slate-900">${clusterId}</span>
              </div>
              <div class="flex justify-between items-center py-0.5">
                <span class="text-slate-500 font-semibold">Assigned Cluster Members:</span>
                <span class="font-mono font-bold text-slate-900 bg-slate-100 px-1.5 py-0.2 rounded">
                  [${peerListStr}]
                </span>
              </div>
              <div class="pt-1 border-t border-slate-100">
                <div class="text-slate-500 font-semibold mb-1">Cluster Profile Signature:</div>
                <div class="flex flex-wrap gap-1">${sigListStr}</div>
              </div>
            </div>

            <div class="text-[9.5px] text-amber-900/90 font-sans leading-relaxed italic bg-amber-100/50 p-1.5 rounded">
              Node C${idNum} acts as cluster representative for Zone ${assignedZ}, maintaining representative feature alignment.
            </div>
          </div>
        `;
      } else {
        exemplarContent.innerHTML = `
          <div class="bg-slate-50 border border-slate-200 rounded-lg p-2.5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-800 flex items-center gap-1.5 text-xs">
                <span>🔗</span>
                <span>Regular Cluster Member</span>
              </span>
              <span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold text-white shadow-xs" style="background-color: ${cColor};">
                Cluster ${clusterId}
              </span>
            </div>

            <div class="space-y-1 text-[10px] text-slate-700 bg-white p-2 rounded border border-slate-200">
              <div class="flex justify-between items-center py-0.5">
                <span class="text-slate-500 font-semibold">Role / Exemplar Status:</span>
                <span class="font-mono font-medium text-slate-600 bg-slate-100 px-1.5 py-0.2 rounded">
                  FALSE (Regular Cluster Member)
                </span>
              </div>
              <div class="flex justify-between items-center py-0.5">
                <span class="text-slate-500 font-semibold">Cluster ID:</span>
                <span class="font-mono font-bold text-slate-900">${clusterId}</span>
              </div>
              <div class="flex justify-between items-center py-0.5">
                <span class="text-slate-500 font-semibold">Designated Cluster Exemplar:</span>
                <span class="font-mono font-bold text-amber-800 bg-amber-50 border border-amber-200 px-1.5 py-0.2 rounded">
                  Node C${exemplarNodeId}
                </span>
              </div>
              <div class="flex justify-between items-center py-0.5">
                <span class="text-slate-500 font-semibold">Cluster Peer Group:</span>
                <span class="font-mono font-bold text-slate-800 bg-slate-100 px-1.5 py-0.2 rounded">
                  [${peerListStr}]
                </span>
              </div>
              <div class="pt-1.5 border-t border-slate-200 text-[9.5px] text-slate-600 font-sans leading-relaxed">
                Node C${idNum} delegates exemplar coordination to designated leader Node C${exemplarNodeId} and participates in intra-cluster aggregation.
              </div>
            </div>
          </div>
        `;
      }
    }
  } else {
    if (exemplarSection) exemplarSection.classList.add("hidden");
  }

  // Step 14: Hierarchical Top-Level Zone Creation (Figure 3(e))
  // topZoneSection declared above
  const topZoneBadge = document.getElementById("cardTopZoneBadge");
  const topZoneContent = document.getElementById("cardTopZoneContent");

  if (currentStep === 14) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.add("hidden");
    if (exemplarSection) exemplarSection.classList.add("hidden");
    if (topZoneSection) topZoneSection.classList.remove("hidden");

    const isTopInit = Boolean(idNum === 4 || nodeData.is_top_initiator);
    const isInit = Boolean([2, 4, 8].includes(idNum) || nodeData.is_initiator);
    const assignedZ = nodeData.assigned_zone || (idNum in {1:1, 2:1, 3:1} ? 2 : idNum in {4:1, 5:1, 6:1, 7:1} ? 4 : 8);

    const defaultClusterMap = {
      1: { cluster_id: "2-A", exemplar: 2, peers: [1, 2], color: "#059669" },
      2: { cluster_id: "2-A", exemplar: 2, peers: [1, 2], color: "#059669" },
      3: { cluster_id: "2-B", exemplar: 3, peers: [3], color: "#0d9488" },
      4: { cluster_id: "4-A", exemplar: 4, peers: [4, 5], color: "#ea580c" },
      5: { cluster_id: "4-A", exemplar: 4, peers: [4, 5], color: "#ea580c" },
      6: { cluster_id: "4-B", exemplar: 6, peers: [6, 7], color: "#d97706" },
      7: { cluster_id: "4-B", exemplar: 6, peers: [6, 7], color: "#d97706" },
      8: { cluster_id: "8-A", exemplar: 8, peers: [8], color: "#7c3aed" },
      9: { cluster_id: "8-B", exemplar: 9, peers: [9], color: "#6366f1" },
      10: { cluster_id: "8-C", exemplar: 10, peers: [10], color: "#8b5cf6" },
    };
    const clusterInfo = defaultClusterMap[idNum] || { cluster_id: "2-A", exemplar: 2, peers: [idNum], color: "#059669" };
    const assignedClusterId = nodeData.assigned_cluster_id || nodeData.cluster_id || clusterInfo.cluster_id;
    const clusterExemplar = nodeData.cluster_exemplar || clusterInfo.exemplar;
    const clusterPeers = nodeData.cluster_peers || clusterInfo.peers;
    const clusterColor = nodeData.cluster_color || clusterInfo.color;
    const peerListStr = (clusterPeers || []).map(p => `C${p}`).join(", ");

    const sharedClassesMap = {
      "2-A": "Airplane (C1), Automobile (C2), Bird (C3)",
      "2-B": "Cat (C4), Deer (C5), Dog (C6)",
      "4-A": "Cat (C4), Deer (C5), Dog (C6)",
      "4-B": "Ship (C9), Truck (C10)",
      "8-A": "Cat (C4), Deer (C5), Dog (C6)",
      "8-B": "Airplane (C1), Automobile (C2), Bird (C3)",
      "8-C": "Horse (C8), Ship (C9), Truck (C10)"
    };
    const sharedClasses = sharedClassesMap[assignedClusterId] || "Dominant Classes";

    if (isTopInit) {
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "👑👑 ELECTED TOP-LEVEL SUPER-INITIATOR (Central Hub of Z_TOP)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      }
      if (topZoneBadge) {
        topZoneBadge.textContent = "Z_TOP Root Initiator (C4 👑👑)";
        topZoneBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      }
      if (topZoneContent) {
        topZoneContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-amber-300 shadow-xs space-y-3">
            <!-- 1. Hero Elected Banner -->
            <div class="super-zone-banner p-2.5 rounded-lg border border-amber-400 text-center space-y-1">
              <div class="text-[11.5px] font-extrabold text-amber-950 flex items-center justify-center gap-1.5">
                <span>👑👑</span>
                <span>ELECTED TOP-LEVEL SUPER-INITIATOR</span>
                <span>👑👑</span>
              </div>
              <div class="text-[9.5px] font-mono text-amber-800 font-semibold">
                Central Hub of Z_TOP | Governing Initiators: C2 (West) & C8 (East)
              </div>
            </div>

            <!-- 2. Overlay VRF Scoreboard (Super-Initiator Election) Table -->
            ${renderOverlayVrfScoreboardHtml(4, nodeData.overlay_scoreboard)}

            <!-- 3. Symmetrical TOP_PROBE Broadcast Pipeline -->
            <div class="p-2.5 bg-slate-50 rounded border border-amber-200 space-y-1.5 text-[10px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-slate-700 font-bold flex items-center gap-1"><span>🚀</span><span>Symmetrical TOP_PROBE Broadcast:</span></span>
                <span class="text-amber-800 font-bold">TTL_top = 1</span>
              </div>
              <div class="text-[9.5px] text-slate-700 space-y-1">
                <div class="flex items-center gap-1">
                  <span class="text-amber-600 font-bold">• Westward Branch:</span> C4 ➔ via C1 (gateway) ➔ C2 (Accepted)
                </div>
                <div class="flex items-center gap-1">
                  <span class="text-amber-600 font-bold">• Eastward Branch:</span> C4 ➔ via C6 (gateway) ➔ C8 (Accepted)
                </div>
              </div>
              <div class="text-[9px] text-emerald-800 font-semibold pt-1 border-t border-slate-200">
                Top-Level Super-Zone Z_TOP formed: Root C4 encompasses base initiators {C2, C4, C8}.
              </div>
            </div>

            <!-- 4. Preserved Base Zone Authority -->
            <div class="p-2 bg-slate-50 rounded border border-slate-200 text-[9.5px] font-mono flex items-center justify-between">
              <span class="text-slate-600">Base Zone Authority:</span>
              <span class="font-bold text-orange-900">Zone 4 (Clusters 4-A & 4-B, Exemplar C4)</span>
            </div>
          </div>
        `;
      }
    } else if (isInit) {
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "👑 BASE INITIATOR (SUPER-ZONE MEMBER)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-50 text-amber-900 border-amber-300";
      }
      if (topZoneBadge) {
        topZoneBadge.textContent = "Member of Z_TOP (Root: C4)";
        topZoneBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      }
      const myVrf = idNum === 8 ? 0.0275 : 0.0837;
      const myHop = idNum === 8 ? "Received TOP_PROBE(TTL=1) from C4 via gateway C6" : "Received TOP_PROBE(TTL=1) from C4 via gateway C1";
      const myZoneDesc = idNum === 8 ? "Zone 8 {C8, C9, C10} (Clusters 8-A, 8-B, 8-C)" : "Zone 2 {C1, C2, C3} (Clusters 2-A & 2-B)";

      if (topZoneContent) {
        topZoneContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-amber-200 shadow-xs space-y-3">
            <div class="p-2 bg-amber-50/80 rounded border border-amber-200 text-[10.5px] font-mono text-amber-950">
              <span class="font-bold">Status:</span> Base Zone Initiator | Member of Top-Level Super-Zone (Root: C4)
            </div>

            <!-- Dedicated Overlay VRF Scoreboard (Super-Initiator Election) Table -->
            ${renderOverlayVrfScoreboardHtml(idNum, nodeData.overlay_scoreboard)}

            <!-- Membership & VRF Details -->
            <div class="p-2.5 bg-slate-50 rounded border border-amber-200 space-y-1.5 text-[10px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Super-Zone Root Initiator:</span>
                <span class="font-bold text-amber-900">👑👑 Node C4 (Central Bridge)</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Local Initiator VRF:</span>
                <span class="font-bold text-slate-800">σ_${idNum} = ${myVrf} (Overlay Peer)</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">TOP_PROBE Ingress:</span>
                <span class="font-bold text-emerald-800">${myHop}</span>
              </div>
              <div class="pt-1 border-t border-slate-200 text-[9.5px]">
                <span class="text-slate-600 font-semibold">Super-Zone Scope:</span>
                <span class="text-slate-800 ml-1">Enrolled in Z_TOP control plane (Root: C4) for hierarchical multi-level coordination.</span>
              </div>
            </div>

            <!-- Preserved Base Zone Authority -->
            <div class="p-2.5 bg-slate-50 rounded border border-slate-200 space-y-1 text-[9.5px] font-mono">
              <div class="text-slate-700 font-bold">Governed Base Zone:</div>
              <div class="text-slate-800">${myZoneDesc}</div>
              <div class="text-slate-500 text-[8.5px]">Intra-zone clustering assignments and exemplars remain fully preserved.</div>
            </div>
          </div>
        `;
      }
    } else {
      // Regular client
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "CLIENT (SUPERVISED BY CONTROL PLANE)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-slate-100 text-slate-700 border-slate-300";
      }
      if (topZoneBadge) {
        topZoneBadge.textContent = "Supervised by Z_TOP (Root: C4)";
        topZoneBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300";
      }
      if (topZoneContent) {
        topZoneContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-xs space-y-2.5">
            <div class="p-2 bg-amber-50/60 rounded border border-amber-200 text-[10px] text-amber-950 font-sans leading-relaxed">
              <span class="font-bold">Supervisory Plane Notice:</span> The Top-Level Super-Zone (Z_TOP, Root: C4) operates as a supervisory control plane above base clients. Node C${idNum}'s semantic cluster assignments remain active and unchanged.
            </div>

            <!-- Preserved Cluster Profile -->
            <div class="p-2.5 bg-slate-50 rounded border border-slate-200 space-y-1.5 text-[10px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Assigned Cluster:</span>
                <span class="font-bold text-white px-2 py-0.5 rounded shadow-xs" style="background-color: ${clusterColor};">
                  Cluster ${assignedClusterId}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Cluster Exemplar:</span>
                <span class="font-bold text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  👑 Node C${clusterExemplar}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Semantic Peers in Zone:</span>
                <span class="font-bold text-emerald-800 bg-white px-2 py-0.5 rounded border border-emerald-200">
                  [${peerListStr}]
                </span>
              </div>
              <div class="pt-1 border-t border-slate-200 text-[9.5px]">
                <span class="text-slate-600 font-semibold">Shared Classes:</span>
                <span class="text-slate-800 font-sans font-medium ml-1">${sharedClasses}</span>
              </div>
            </div>
          </div>
        `;
      }
    }
  } else {
    if (topZoneSection) topZoneSection.classList.add("hidden");
  }

  // Step 15: Top-Level Catalog Query Dispatch (REQ_CLUSTER_CATALOG)
  const catalogReqSection = document.getElementById("cardCatalogReqSection");
  const catalogReqBadge = document.getElementById("cardCatalogReqBadge");
  const catalogReqContent = document.getElementById("cardCatalogReqContent");

  if (currentStep === 15) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.add("hidden");
    if (exemplarSection) exemplarSection.classList.add("hidden");
    if (topZoneSection) topZoneSection.classList.add("hidden");
    if (catalogReqSection) catalogReqSection.classList.remove("hidden");

    if (idNum === 4) {
      // Node 4: Super-Initiator C4
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "👑👑 SUPER-INITIATOR (REQ_CATALOG DISPATCHER)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-cyan-100 text-cyan-900 border-cyan-400";
      }
      if (catalogReqBadge) {
        catalogReqBadge.textContent = "DISPATCHED (C2 & C8)";
        catalogReqBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-cyan-100 text-cyan-900 border border-cyan-300";
      }
      if (catalogReqContent) {
        catalogReqContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-cyan-300 shadow-xs space-y-3">
            <!-- 1. Outbound Query Status Banner -->
            <div class="p-2.5 rounded-lg border border-cyan-400 bg-cyan-50/90 text-center space-y-1">
              <div class="text-[11.5px] font-extrabold text-cyan-950 flex items-center justify-center gap-1.5">
                <span>📡</span>
                <span>Outbound Query: REQ_CLUSTER_CATALOG dispatched to C2 and C8</span>
                <span>📡</span>
              </div>
              <div class="text-[9.5px] font-mono text-cyan-800 font-semibold">
                Super-Initiator C4 | Status: DISPATCHED_TO_ALL_INITIATORS
              </div>
            </div>

            <!-- 2. Dispatched Route Details -->
            <div class="p-2.5 bg-slate-50 rounded border border-cyan-200 space-y-2 text-[10px] font-mono">
              <div class="text-slate-700 font-bold flex items-center gap-1">
                <span>🚀</span>
                <span>Dispatched Query Traces (Overlay Routes):</span>
              </div>
              <div class="space-y-1.5 text-[9.5px]">
                <div class="p-1.5 bg-white rounded border border-cyan-100 flex items-center justify-between">
                  <span class="text-cyan-900 font-bold">• West Branch:</span>
                  <span class="font-mono text-slate-800">C4 ➔ C1 (gateway) ➔ C2 [Path: 4-1-2]</span>
                </div>
                <div class="p-1.5 bg-white rounded border border-cyan-100 flex items-center justify-between">
                  <span class="text-cyan-900 font-bold">• East Branch:</span>
                  <span class="font-mono text-slate-800">C4 ➔ C6 (gateway) ➔ C8 [Path: 4-6-8]</span>
                </div>
              </div>
              <div class="pt-1 border-t border-slate-200 text-[9px] text-slate-600">
                <span class="font-semibold text-slate-800">Directive:</span> Collects intra-zone cluster IDs, exemplars, and profile signatures from base initiators.
              </div>
            </div>

            <!-- 3. Local Base Zone Authority -->
            <div class="p-2 bg-slate-50 rounded border border-slate-200 text-[9.5px] font-mono flex items-center justify-between">
              <span class="text-slate-600">Governed Zone 4 Clusters:</span>
              <span class="font-bold text-orange-900">4-A (Exemplar: C5) & 4-B (Exemplar: C7)</span>
            </div>
          </div>
        `;
      }
    } else if ([2, 8].includes(idNum)) {
      // Base Initiators C2 & C8
      const zoneNum = idNum;
      const gatewayNum = idNum === 2 ? 1 : 6;
      const pathStr = idNum === 2 ? "[4, 1, 2]" : "[4, 6, 8]";
      const myClusters = idNum === 2 ? "2-A (Exemplar: C1) & 2-B (Exemplar: C3)" : "8-A (Exemplar: C8), 8-B (Exemplar: C9), 8-C (Exemplar: C10)";

      if (cardStatusBadge) {
        cardStatusBadge.textContent = "👑 BASE INITIATOR (QUERY RECEIVED)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-50 text-amber-900 border-amber-300";
      }
      if (catalogReqBadge) {
        catalogReqBadge.textContent = "QUERY RECEIVED";
        catalogReqBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-cyan-100 text-cyan-900 border border-cyan-300";
      }
      if (catalogReqContent) {
        catalogReqContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-cyan-200 shadow-xs space-y-3">
            <!-- 1. Inbound Query Status Banner -->
            <div class="p-2.5 rounded-lg border border-cyan-300 bg-cyan-50 text-center space-y-1">
              <div class="text-[11px] font-extrabold text-cyan-950 flex items-center justify-center gap-1.5">
                <span>📥</span>
                <span>Inbound Query Received: Preparing intra-zone cluster catalog response</span>
              </div>
              <div class="text-[9.5px] font-mono text-cyan-800 font-semibold">
                Initiator C${idNum} | Status: RECEIVED_PENDING_RESPONSE
              </div>
            </div>

            <!-- 2. Query Ingress Details -->
            <div class="p-2.5 bg-slate-50 rounded border border-slate-200 space-y-1.5 text-[10px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Query Origin:</span>
                <span class="font-bold text-amber-900">👑👑 Super-Initiator C4 (Root)</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Traversed Path:</span>
                <span class="font-bold text-slate-800 font-mono">C4 ➔ C${gatewayNum} (gateway) ➔ C${idNum} ${pathStr}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">Requested Metadata:</span>
                <span class="font-bold text-cyan-900">INTRA_ZONE_CLUSTERS</span>
              </div>
              <div class="pt-1.5 border-t border-slate-200 text-[9.5px] text-slate-600 leading-relaxed">
                Node C${idNum} compiles local cluster profiles for transmission in Step 16.
              </div>
            </div>

            <!-- 3. Prepared Catalog Preview -->
            <div class="p-2 bg-slate-50 rounded border border-slate-200 text-[9.5px] font-mono space-y-1">
              <div class="text-slate-700 font-bold">Catalog Response Payload (Preview):</div>
              <div class="text-slate-800 font-medium">${myClusters}</div>
            </div>
          </div>
        `;
      }
    } else {
      // Member Node
      const isGateway = [1, 6].includes(idNum);
      if (cardStatusBadge) {
        cardStatusBadge.textContent = isGateway ? "GATEWAY BRIDGE (PACKET FORWARDER)" : "CLUSTER MEMBER";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-slate-100 text-slate-700 border-slate-300";
      }
      if (catalogReqBadge) {
        catalogReqBadge.textContent = isGateway ? "FORWARDING RELAY" : "INACTIVE";
        catalogReqBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300";
      }
      if (catalogReqContent) {
        catalogReqContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-xs space-y-2">
            <div class="text-[10.5px] text-slate-700 font-sans leading-relaxed">
              ${isGateway
                ? `<span class="font-bold text-cyan-800">Boundary Gateway Role:</span> Node C${idNum} transparently forwards the supervisory control packet <code>REQ_CLUSTER_CATALOG</code> from Super-Initiator C4 to its zone initiator.`
                : `Node C${idNum} remains in active cluster coordination within its assigned cluster while the supervisory control plane executes catalog query dispatch.`
              }
            </div>
          </div>
        `;
      }
    }
  } else {
    if (catalogReqSection) catalogReqSection.classList.add("hidden");
  }

  // Step 16: Zone Catalog Response & Global Catalog Aggregation at C4
  const globalCatalogSection = document.getElementById("cardGlobalCatalogSection");
  const globalCatalogBadge = document.getElementById("cardGlobalCatalogBadge");
  const globalCatalogContent = document.getElementById("cardGlobalCatalogContent");

  if (currentStep === 16) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.add("hidden");
    if (exemplarSection) exemplarSection.classList.add("hidden");
    if (topZoneSection) topZoneSection.classList.add("hidden");
    if (catalogReqSection) catalogReqSection.classList.add("hidden");
    if (globalCatalogSection) globalCatalogSection.classList.remove("hidden");

    if (idNum === 4) {
      // Node 4: Super-Initiator C4 - Assembled Global Cluster Registry (7 clusters)
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "👑👑 SUPER-INITIATOR (GLOBAL REGISTRY ASSEMBLED)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-emerald-100 text-emerald-900 border-emerald-400";
      }
      if (globalCatalogBadge) {
        globalCatalogBadge.textContent = "7 CLUSTERS REGISTERED";
        globalCatalogBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-emerald-100 text-emerald-900 border border-emerald-300";
      }
      if (globalCatalogContent) {
        const catalog = mergedNode?.global_cluster_catalog || stepData?.global_cluster_catalog || [];
        let rowsHtml = "";
        catalog.forEach(c => {
          const rawMask = c?.mask || c?.binary_mask || c?.signature;
          const maskStr = Array.isArray(rawMask) ? `[${rawMask.join(", ")}]` : JSON.stringify(rawMask || []);
          const membersStr = Array.isArray(c?.members) ? c.members.map(m => `C${m}`).join(", ") : (c?.members_str ? c.members_str.join(", ") : "");
          rowsHtml += `
            <tr class="hover:bg-slate-50 transition-colors border-b border-slate-100">
              <td class="py-1 px-2 font-bold text-emerald-700 font-mono">${c?.cluster_id || "N/A"}</td>
              <td class="py-1 px-2 font-mono text-slate-600">Zone ${c?.zone ?? "N/A"}</td>
              <td class="py-1 px-2 font-bold text-amber-700 font-mono">C${c?.exemplar ?? "N/A"}</td>
              <td class="py-1 px-2 font-mono text-slate-700">${membersStr}</td>
              <td class="py-1 px-2 text-right font-mono text-cyan-800 font-semibold">${maskStr}</td>
            </tr>
          `;
        });

        globalCatalogContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-emerald-300 shadow-xs space-y-3">
            <!-- 1. Header Aggregation Status Banner -->
            <div class="p-2.5 rounded-lg border border-emerald-400 bg-emerald-50/90 text-center space-y-1">
              <div class="text-[11.5px] font-extrabold text-emerald-950 flex items-center justify-center gap-1.5">
                <span>🌐</span>
                <span>Global Cluster Catalog Registry: 7 Clusters Ingested</span>
                <span>🌐</span>
              </div>
              <div class="text-[9.5px] font-mono text-emerald-800 font-semibold">
                Super-Initiator C4 | Status: GLOBAL_CATALOG_REGISTRY_ASSEMBLED
              </div>
            </div>

            <!-- 2. Full 7-Cluster Table -->
            <div class="rounded border border-emerald-200 overflow-hidden">
              <table class="w-full text-[9px] font-mono text-left">
                <thead class="bg-emerald-50 text-emerald-900 uppercase font-bold border-b border-emerald-200">
                  <tr>
                    <th class="py-1 px-2">Cluster ID</th>
                    <th class="py-1 px-2">Zone</th>
                    <th class="py-1 px-2">Exemplar</th>
                    <th class="py-1 px-2">Members</th>
                    <th class="py-1 px-2 text-right">10D Binary Mask</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 bg-white">
                  ${rowsHtml}
                </tbody>
              </table>
            </div>

            <!-- 3. Summary Footer -->
            <div class="p-2 bg-slate-50 rounded border border-slate-200 text-[9px] font-mono flex items-center justify-between text-slate-600">
              <span>Coverage: <strong class="text-slate-800">100% of network clients (10 Nodes)</strong></span>
              <span>Total Registry: <strong class="text-emerald-700">7 Global Clusters</strong></span>
            </div>
          </div>
        `;
      }
    } else if ([2, 8].includes(idNum)) {
      // Base Initiators C2 & C8 - Dispatched Catalog
      const reported = mergedNode?.reported_clusters || [];
      const relayGw = idNum === 2 ? "C1" : "C6";
      const pathStr = idNum === 2 ? "[2, 1, 4]" : "[8, 6, 4]";
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "👑 BASE INITIATOR (REP_CATALOG DISPATCHED)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-50 text-amber-900 border-amber-300";
      }
      if (globalCatalogBadge) {
        globalCatalogBadge.textContent = "DISPATCHED TO C4";
        globalCatalogBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-emerald-100 text-emerald-900 border border-emerald-300";
      }
      if (globalCatalogContent) {
        let repRowsHtml = "";
        reported.forEach(c => {
          const rawMask = c?.mask || c?.binary_mask || c?.signature;
          const maskStr = Array.isArray(rawMask) ? `[${rawMask.join(", ")}]` : JSON.stringify(rawMask || []);
          const membersStr = Array.isArray(c?.members) ? c.members.map(m => `C${m}`).join(", ") : "";
          repRowsHtml += `
            <div class="p-2 bg-white rounded border border-emerald-100 flex items-center justify-between text-[9.5px]">
              <div>
                <span class="font-bold text-emerald-800 font-mono">• Cluster ${c?.cluster_id || "N/A"}</span>
                <span class="text-slate-500 ml-1">(Exemplar: C${c?.exemplar ?? "N/A"}, Members: ${membersStr})</span>
              </div>
              <span class="font-mono text-cyan-800 font-semibold">${maskStr}</span>
            </div>
          `;
        });

        globalCatalogContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-emerald-300 shadow-xs space-y-3">
            <div class="p-2 rounded bg-emerald-50 border border-emerald-300 text-[10px] font-mono text-emerald-900 space-y-1">
              <div class="font-bold flex items-center justify-between">
                <span>Dispatched Cluster Catalog (REP_CLUSTER_CATALOG):</span>
                <span class="px-1.5 py-0.2 bg-emerald-200 text-emerald-900 rounded text-[9px]">SENT</span>
              </div>
              <div class="text-[9px] text-emerald-700">
                Route: C${idNum} ➔ ${relayGw} (gateway) ➔ C4 [Path: ${pathStr}]
              </div>
            </div>
            <div class="space-y-1.5">
              ${repRowsHtml}
            </div>
          </div>
        `;
      }
    } else {
      // Member nodes or relay gateways
      if (cardStatusBadge) {
        if ([1, 6].includes(idNum)) {
          cardStatusBadge.textContent = "BOUNDARY GATEWAY (FORWARDED RESPONSE)";
          cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-indigo-50 text-indigo-900 border-indigo-300";
        } else {
          cardStatusBadge.textContent = "CLUSTER MEMBER";
          cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-slate-100 text-slate-700 border-slate-300";
        }
      }
      if (globalCatalogBadge) {
        globalCatalogBadge.textContent = "INTRA-ZONE MEMBER";
        globalCatalogBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-slate-100 text-slate-600 border border-slate-300";
      }
      if (globalCatalogContent) {
        const cId = mergedNode?.cluster_id || 'N/A';
        const exId = mergedNode?.exemplar_node_id || 'N/A';
        globalCatalogContent.innerHTML = `
          <div class="p-2.5 bg-slate-50 rounded border border-slate-200 text-[9.5px] font-mono space-y-1 text-slate-700">
            <div><strong>Registered Cluster:</strong> <span class="text-emerald-700 font-bold">${cId}</span></div>
            <div><strong>Cluster Exemplar:</strong> <span class="text-amber-700 font-bold">C${exId}</span></div>
            <div class="text-[9px] text-slate-500">Represented in Global Semantic Catalog assembled at Super-Initiator C4.</div>
          </div>
        `;
      }
    }
  } else {
    if (globalCatalogSection) globalCatalogSection.classList.add("hidden");
  }

  // Step 17: Inter-Zone Meta-Clustering & Super-Clusters
  const superClusterSection = document.getElementById("cardSuperClusterSection");
  const superClusterBadge = document.getElementById("cardSuperClusterBadge");
  const superClusterContent = document.getElementById("cardSuperClusterContent");

  if (currentStep === 17) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.add("hidden");
    if (exemplarSection) exemplarSection.classList.add("hidden");
    if (topZoneSection) topZoneSection.classList.add("hidden");
    if (catalogReqSection) catalogReqSection.classList.add("hidden");
    if (globalCatalogSection) globalCatalogSection.classList.add("hidden");
    if (superClusterSection) superClusterSection.classList.remove("hidden");

    if (idNum === 4) {
      // Node 4: Super-Initiator C4 - 7x7 Similarity Matrix & 3 Global Super-Clusters
      if (cardStatusBadge) {
        cardStatusBadge.textContent = "👑👑 SUPER-INITIATOR (META-CLUSTERING COMPLETE)";
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-sky-100 text-sky-900 border-sky-400";
      }
      if (superClusterBadge) {
        superClusterBadge.textContent = "7x7 MATRIX & 3 SCs";
        superClusterBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-sky-100 text-sky-900 border border-sky-300";
      }
      if (superClusterContent) {
        const matrixData = mergedNode?.similarity_matrix_7x7 || stepData?.similarity_matrix_7x7 || {};
        const clusterIds = matrixData?.cluster_ids || ["2-A", "2-B", "4-A", "4-B", "8-A", "8-B", "8-C"];
        const matrix = matrixData?.matrix || [];

        // Build 7x7 Heatmap table
        let tableHeaderHtml = `<th class="py-1 px-1.5 bg-slate-100 text-slate-600 border-r border-slate-200"></th>`;
        clusterIds.forEach(cid => {
          tableHeaderHtml += `<th class="py-1 px-1 text-center font-bold text-slate-700">${cid}</th>`;
        });

        let tableRowsHtml = "";
        matrix.forEach((row, rIdx) => {
          const rowCid = clusterIds[rIdx] || `C${rIdx}`;
          let cellsHtml = `<td class="py-1 px-1 font-bold text-slate-700 bg-slate-50 border-r border-slate-200 font-mono">${rowCid}</td>`;
          row.forEach(val => {
            let cellClass = "bg-slate-50 text-slate-400";
            if (val === 1.0) {
              cellClass = "bg-emerald-600 text-white font-bold";
            } else if (val >= 0.8) {
              cellClass = "bg-emerald-500 text-white font-bold";
            } else if (val > 0) {
              cellClass = "bg-emerald-100 text-emerald-800 font-semibold";
            }
            cellsHtml += `<td class="py-1 px-0.5 text-center font-mono ${cellClass}">${Number(val).toFixed(2)}</td>`;
          });
          tableRowsHtml += `<tr class="border-b border-slate-100">${cellsHtml}</tr>`;
        });

        // Build 3 Global Super-Clusters Cards
        const superClusters = mergedNode?.super_clusters || stepData?.super_clusters || [];
        let scCardsHtml = "";
        superClusters.forEach(sc => {
          const clusterTags = (sc?.clusters || []).map(c => `<span class="px-1.5 py-0.2 bg-white rounded border border-slate-200 font-mono text-[9px] font-bold text-slate-700">${c}</span>`).join(" ");
          const peerTags = (sc?.peers || []).map(p => `<span class="px-1.5 py-0.2 bg-white rounded border border-slate-200 font-mono text-[9px] font-bold text-slate-800">C${p}</span>`).join(" ");
          const exemplarTags = (sc?.exemplars || []).map(e => `<span class="px-1.5 py-0.2 bg-amber-100 text-amber-900 rounded border border-amber-300 font-mono text-[9px] font-bold">⭐ C${e}</span>`).join(" ");
          const classNames = (sc?.class_names || []).join(", ");

          let badgeColor = sc?.id === "SC-1" ? "border-sky-300 bg-sky-50/80" : (sc?.id === "SC-2" ? "border-amber-300 bg-amber-50/80" : "border-violet-300 bg-violet-50/80");
          let headerColor = sc?.id === "SC-1" ? "text-sky-900" : (sc?.id === "SC-2" ? "text-amber-900" : "text-violet-900");

          scCardsHtml += `
            <div class="p-2.5 rounded-lg border ${badgeColor} space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="font-extrabold ${headerColor} text-[10.5px]">🌌 ${sc?.id}: ${sc?.name}</span>
                <span class="text-[8.5px] font-mono font-bold px-1.5 py-0.2 rounded bg-white border border-slate-200">${sc?.clusters?.length || 0} Clusters</span>
              </div>
              <div class="text-[9px] text-slate-600">
                <strong>Clusters:</strong> ${clusterTags}
              </div>
              <div class="text-[9px] text-slate-600">
                <strong>Member Peers:</strong> ${peerTags}
              </div>
              <div class="text-[9px] text-slate-600 flex items-center gap-1">
                <strong>Exemplars:</strong> ${exemplarTags}
              </div>
              <div class="text-[8.5px] text-slate-500 italic">
                Dominant Classes: ${classNames}
              </div>
            </div>
          `;
        });

        superClusterContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-sky-300 shadow-xs space-y-3">
            <!-- Header Banner -->
            <div class="p-2 rounded-lg border border-sky-400 bg-sky-50/90 text-center space-y-0.5">
              <div class="text-[11px] font-extrabold text-sky-950 flex items-center justify-center gap-1.5">
                <span>🌌</span>
                <span>Inter-Zone Meta-Clustering & Super-Clusters</span>
                <span>🌌</span>
              </div>
              <div class="text-[9px] font-mono text-sky-800 font-semibold">
                7x7 Pairwise Cosine Similarity Matrix (Threshold τ >= 0.85)
              </div>
            </div>

            <!-- 7x7 Similarity Matrix Heatmap -->
            <div class="space-y-1">
              <div class="text-[9.5px] font-bold text-slate-700 flex items-center justify-between">
                <span>7x7 Inter-Cluster Cosine Similarity Heatmap:</span>
                <span class="text-[8.5px] font-normal text-slate-500">Green = High Affinity</span>
              </div>
              <div class="rounded border border-slate-200 overflow-x-auto">
                <table class="w-full text-[8px] font-mono text-left">
                  <thead class="bg-slate-100 text-slate-800 uppercase font-bold border-b border-slate-200">
                    <tr>${tableHeaderHtml}</tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100 bg-white">
                    ${tableRowsHtml}
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 3 Global Super-Clusters List -->
            <div class="space-y-1.5">
              <div class="text-[9.5px] font-bold text-slate-700">
                Formed 3 Global Super-Clusters:
              </div>
              <div class="space-y-2">
                ${scCardsHtml}
              </div>
            </div>
          </div>
        `;
      }
    } else {
      // Other Nodes (1, 2, 3, 5, 6, 7, 8, 9, 10)
      const scId = mergedNode?.assigned_super_cluster || ([1, 2, 9].includes(idNum) ? "SC-1" : ([3, 4, 5, 8].includes(idNum) ? "SC-2" : "SC-3"));
      const scName = mergedNode?.super_cluster_name || (scId === "SC-1" ? "Aviation & Vehicles (C1-C3)" : (scId === "SC-2" ? "Animals (C4-C6)" : "Heavy Transport & Amphibians (C7-C10)"));
      const peers = mergedNode?.cross_zone_semantic_peers || [];
      const allPeers = mergedNode?.super_cluster_peers || (scId === "SC-1" ? [1, 2, 9] : (scId === "SC-2" ? [3, 4, 5, 8] : [6, 7, 10]));
      const exemplars = mergedNode?.super_cluster_exemplars || (scId === "SC-1" ? [1, 9] : (scId === "SC-2" ? [3, 5, 8] : [7, 10]));

      const scBadgeBg = scId === "SC-1" ? "bg-sky-100 text-sky-900 border-sky-300" : (scId === "SC-2" ? "bg-amber-100 text-amber-900 border-amber-300" : "bg-violet-100 text-violet-900 border-violet-300");
      const scCardBg = scId === "SC-1" ? "bg-sky-50 border-sky-300" : (scId === "SC-2" ? "bg-amber-50 border-amber-300" : "bg-violet-50 border-violet-300");

      if (cardStatusBadge) {
        cardStatusBadge.textContent = `SUPER-CLUSTER MEMBER (${scId})`;
        cardStatusBadge.className = `text-[9px] font-semibold px-2 py-0.5 rounded border font-bold ${scBadgeBg}`;
      }
      if (superClusterBadge) {
        superClusterBadge.textContent = scId;
        superClusterBadge.className = `text-[9px] px-1.5 py-0.2 rounded font-mono font-bold ${scBadgeBg}`;
      }
      if (superClusterContent) {
        const peerTags = peers.map(p => `<span class="px-1.5 py-0.5 bg-white rounded border border-slate-300 font-mono font-bold text-slate-800">C${p}</span>`).join(" ");
        const allPeerTags = allPeers.map(p => `<span class="px-1.5 py-0.5 bg-white rounded border border-slate-300 font-mono font-bold text-slate-800 ${p === idNum ? 'ring-1 ring-emerald-500 text-emerald-800' : ''}">C${p}${p === idNum ? ' (You)' : ''}</span>`).join(" ");
        const exemplarTags = exemplars.map(e => `<span class="px-1.5 py-0.5 bg-amber-100 text-amber-900 rounded border border-amber-300 font-mono font-bold">⭐ C${e}</span>`).join(" ");

        superClusterContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-xs space-y-2.5">
            <div class="p-2.5 rounded-lg border ${scCardBg} space-y-1">
              <div class="flex items-center justify-between">
                <span class="text-[11px] font-extrabold text-slate-900">Assigned Super-Cluster:</span>
                <span class="px-2 py-0.5 rounded font-mono font-extrabold text-[10px] ${scBadgeBg}">${scId}</span>
              </div>
              <div class="text-[9.5px] font-mono text-slate-700 font-semibold">
                ${scName}
              </div>
            </div>

            <div class="space-y-1.5 text-[9.5px] font-mono text-slate-700">
              <div class="p-2 bg-slate-50 rounded border border-slate-200 space-y-1">
                <div class="font-bold text-slate-800">Cross-Zone Semantic Peers:</div>
                <div class="flex flex-wrap gap-1">
                  ${peers.length > 0 ? peerTags : '<span class="text-slate-400">None</span>'}
                </div>
              </div>

              <div class="p-2 bg-slate-50 rounded border border-slate-200 space-y-1">
                <div class="font-bold text-slate-800">All Super-Cluster Members:</div>
                <div class="flex flex-wrap gap-1">
                  ${allPeerTags}
                </div>
              </div>

              <div class="p-2 bg-slate-50 rounded border border-slate-200 space-y-1">
                <div class="font-bold text-slate-800">Cluster Exemplars:</div>
                <div class="flex flex-wrap gap-1">
                  ${exemplarTags}
                </div>
              </div>
            </div>
          </div>
        `;
      }
    }
  } else {
    if (superClusterSection) superClusterSection.classList.add("hidden");
  }

  // Step 18: Super-Peer Designation & Hierarchical Overlay Binding
  const superPeerSection = document.getElementById("cardSuperPeerSection");
  const superPeerBadge = document.getElementById("cardSuperPeerBadge");
  const superPeerContent = document.getElementById("cardSuperPeerContent");

  if (currentStep === 18) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.add("hidden");
    if (exemplarSection) exemplarSection.classList.add("hidden");
    if (topZoneSection) topZoneSection.classList.add("hidden");
    if (catalogReqSection) catalogReqSection.classList.add("hidden");
    if (globalCatalogSection) globalCatalogSection.classList.add("hidden");
    if (superClusterSection) superClusterSection.classList.add("hidden");
    if (superPeerSection) superPeerSection.classList.remove("hidden");

    const isSP = [1, 5, 10].includes(idNum) || Boolean(mergedNode?.is_super_peer);
    const isEx = [1, 3, 5, 7, 8, 9, 10].includes(idNum) || Boolean(mergedNode?.is_exemplar);
    const boundSP = mergedNode?.bound_super_peer ?? (idNum === 1 || idNum === 9 ? 1 : ([3, 5, 8].includes(idNum) ? 5 : ([7, 10].includes(idNum) ? 10 : null)));
    const governed = mergedNode?.governed_exemplars || (idNum === 1 ? [1, 9] : (idNum === 5 ? [3, 5, 8] : (idNum === 10 ? [7, 10] : [])));
    const repExemplar = mergedNode?.exemplar_node_id ?? (idNum === 2 ? 1 : (idNum === 4 ? 5 : (idNum === 6 ? 7 : null)));
    const scId = mergedNode?.assigned_super_cluster || ([1, 2, 9].includes(idNum) ? "SC-1" : ([3, 4, 5, 8].includes(idNum) ? "SC-2" : "SC-3"));

    if (isSP) {
      if (cardStatusBadge) {
        cardStatusBadge.textContent = `🌟 GLOBAL SUPER-PEER (${scId})`;
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-100 text-amber-900 border-amber-400";
      }
      if (superPeerBadge) {
        superPeerBadge.textContent = "GLOBAL SUPER-PEER";
        superPeerBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300";
      }
      if (superPeerContent) {
        const govTags = governed.map(e => `<span class="px-2 py-0.5 bg-amber-50 text-amber-900 rounded border border-amber-300 font-mono font-bold">⭐ Node C${e}</span>`).join(" ");
        superPeerContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-amber-300 shadow-xs space-y-2.5">
            <div class="p-2.5 rounded-lg border border-amber-400 bg-amber-50/80 space-y-1">
              <div class="flex items-center justify-between">
                <span class="text-[11px] font-extrabold text-amber-950 flex items-center gap-1.5">
                  <span>🌟</span>
                  <span>Appointed Global Super-Peer</span>
                </span>
                <span class="px-2 py-0.5 rounded font-mono font-bold text-[9px] bg-white border border-amber-300 text-amber-900">${scId}</span>
              </div>
              <div class="text-[9px] text-amber-800">
                Officially designated by Super-Initiator C4 via ORDER_SET_SUPER_PEER.
              </div>
            </div>
            <div class="p-2.5 bg-slate-50 rounded border border-slate-200 text-[9.5px] font-mono space-y-1.5">
              <div class="font-bold text-slate-800">Governed Intra-Zone Exemplars:</div>
              <div class="flex flex-wrap gap-1.5">
                ${govTags}
              </div>
              <div class="text-[8.5px] text-slate-500 pt-1">Coordinates cross-zone model aggregation for ${scId}.</div>
            </div>
          </div>
        `;
      }
    } else if (isEx) {
      if (cardStatusBadge) {
        cardStatusBadge.textContent = `⭐ BOUND EXEMPLAR (${scId})`;
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-amber-50 text-amber-900 border-amber-300";
      }
      if (superPeerBadge) {
        superPeerBadge.textContent = "BOUND TO SP " + boundSP;
        superPeerBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-50 text-amber-900 border border-amber-300";
      }
      if (superPeerContent) {
        superPeerContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-xs space-y-2.5">
            <div class="p-2.5 rounded-lg border border-amber-200 bg-amber-50/50 space-y-1">
              <div class="flex items-center justify-between">
                <span class="text-[10.5px] font-bold text-slate-800">Hierarchical Overlay Binding:</span>
                <span class="px-1.5 py-0.2 rounded font-mono font-bold text-[9px] bg-amber-100 text-amber-900 border border-amber-300">TIER 2</span>
              </div>
              <div class="text-[10px] font-mono font-bold text-amber-900">
                Bound Global Super-Peer: Node C${boundSP}
              </div>
            </div>
            <div class="text-[9px] text-slate-600 font-mono">
              Directly federates local cluster updates to Super-Peer C${boundSP} for inter-zone coordination.
            </div>
          </div>
        `;
      }
    } else {
      if (cardStatusBadge) {
        cardStatusBadge.textContent = `CLIENT (LOCAL MEMBER)`;
        cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded border font-bold bg-slate-100 text-slate-800 border-slate-300";
      }
      if (superPeerBadge) {
        superPeerBadge.textContent = "REGULAR MEMBER";
        superPeerBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300";
      }
      if (superPeerContent) {
        superPeerContent.innerHTML = `
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-xs space-y-2.5">
            <div class="p-2.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1">
              <div class="flex items-center justify-between">
                <span class="text-[10.5px] font-bold text-slate-800">Tier 1 Regular Client:</span>
                <span class="px-1.5 py-0.2 rounded font-mono font-bold text-[9px] bg-slate-200 text-slate-700">TIER 1</span>
              </div>
              <div class="text-[10px] font-mono font-bold text-slate-900">
                Represented by Local Exemplar: Node C${repExemplar}
              </div>
            </div>
            <div class="text-[9px] text-slate-600 font-mono">
              Participates in local cluster training; updates are aggregated through intra-zone exemplar C${repExemplar}.
            </div>
          </div>
        `;
      }
    }
  } else {
    if (superPeerSection) superPeerSection.classList.add("hidden");
  }

  // Step 19: Semantic Overlay Network (SON) Connections
  const overlaySection = document.getElementById("cardOverlaySection");
  const overlayBadge = document.getElementById("cardOverlayBadge");
  const overlayContent = document.getElementById("cardOverlayContent");

  if (currentStep === 19) {
    if (probeSection) probeSection.classList.add("hidden");
    if (bndSection) bndSection.classList.add("hidden");
    if (pminSection) pminSection.classList.add("hidden");
    if (bsSection) bsSection.classList.add("hidden");
    if (consensusSection) consensusSection.classList.add("hidden");
    if (orderSection) orderSection.classList.add("hidden");
    if (sigSection) sigSection.classList.add("hidden");
    if (clSection) clSection.classList.add("hidden");
    if (exemplarSection) exemplarSection.classList.add("hidden");
    if (topZoneSection) topZoneSection.classList.add("hidden");
    if (catalogReqSection) catalogReqSection.classList.add("hidden");
    if (globalCatalogSection) globalCatalogSection.classList.add("hidden");
    if (superClusterSection) superClusterSection.classList.add("hidden");
    if (superPeerSection) superPeerSection.classList.add("hidden");
    if (overlaySection) overlaySection.classList.remove("hidden");

    const overlayNeighbors = mergedNode?.active_overlay_neighbors || [];
    const sonTier = mergedNode?.son_tier ?? ([1, 5, 10].includes(idNum) ? 3 : ([3, 7, 8, 9].includes(idNum) ? 2 : 1));
    const scId = mergedNode?.assigned_super_cluster || ([1, 2, 9].includes(idNum) ? "SC-1" : ([3, 4, 5, 8].includes(idNum) ? "SC-2" : "SC-3"));

    const tierLabel = sonTier === 3 ? "TIER 3 (SUPER-PEER)" : (sonTier === 2 ? "TIER 2 (EXEMPLAR)" : "TIER 1 (MEMBER)");
    const tierBadgeBg = sonTier === 3 ? "bg-amber-100 text-amber-900 border-amber-300" : (sonTier === 2 ? "bg-blue-100 text-blue-900 border-blue-300" : "bg-slate-100 text-slate-800 border-slate-300");

    if (cardStatusBadge) {
      cardStatusBadge.textContent = `SON ACTIVE: ${tierLabel}`;
      cardStatusBadge.className = `text-[9px] font-semibold px-2 py-0.5 rounded border font-bold ${tierBadgeBg}`;
    }
    if (overlayBadge) {
      overlayBadge.textContent = `${overlayNeighbors.length} OVERLAY LINKS`;
      overlayBadge.className = "text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-emerald-100 text-emerald-900 border border-emerald-300";
    }
    if (overlayContent) {
      const neighborTags = overlayNeighbors.map(nbr => `<span class="px-2 py-0.5 bg-emerald-50 text-emerald-900 rounded border border-emerald-300 font-mono font-bold">⚡ C${nbr}</span>`).join(" ");

      overlayContent.innerHTML = `
        <div class="p-3 bg-white rounded-lg border border-emerald-300 shadow-xs space-y-2.5">
          <div class="p-2.5 rounded-lg border border-emerald-300 bg-emerald-50/70 space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-[10.5px] font-bold text-emerald-950">Semantic Overlay Hierarchy:</span>
              <span class="px-2 py-0.5 rounded font-mono font-bold text-[9px] ${tierBadgeBg}">${tierLabel}</span>
            </div>
            <div class="text-[9.5px] font-mono text-emerald-900">
              Super-Cluster: <strong>${scId}</strong>
            </div>
          </div>

          <div class="p-2.5 bg-slate-50 rounded border border-slate-200 text-[9.5px] font-mono space-y-1.5">
            <div class="font-bold text-slate-800">Active Overlay Neighbors (SON Links):</div>
            <div class="flex flex-wrap gap-1.5">
              ${neighborTags || '<span class="text-slate-400">None</span>'}
            </div>
            <div class="text-[8.5px] text-slate-500 pt-1">
              Active bidirectional model exchange channel routed through the Semantic Overlay Network.
            </div>
          </div>
        </div>
      `;
    }
  } else {
    if (overlaySection) overlaySection.classList.add("hidden");
  }

    card.classList.remove("hidden");
    card.style.display = "block";
    card.style.zIndex = "9999";
  } catch (err) {
    console.error("Modal render error:", err);
    showFallbackModal(node, err);
  }
}

function showFallbackModal(node, err) {
  try {
    const card = document.getElementById("nodeInfoCard");
    if (!card) return;
    const nodeData = (typeof node?.data === "function") ? node.data() : (node || {});
    const rawId = nodeData.node_id_num ?? nodeData.id ?? "?";
    const idNum = typeof rawId === "string" ? parseInt(rawId.replace(/\D/g, ""), 10) : Number(rawId);

    const cardNodeId = document.getElementById("cardNodeId");
    if (cardNodeId) {
      cardNodeId.innerHTML = `<span class="text-amber-800 font-bold font-mono text-sm">Node C${idNum || rawId}</span> <span class="text-slate-300">|</span> <span class="text-slate-600 text-xs font-semibold">Inspector Mode</span>`;
    }

    const cardStatusBadge = document.getElementById("cardStatusBadge");
    if (cardStatusBadge) {
      cardStatusBadge.textContent = "INSPECTOR ACTIVE";
      cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-300";
    }

    card.classList.remove("hidden");
    card.style.display = "block";
    card.style.zIndex = "9999";
  } catch (e) {
    console.error("Fallback modal error:", e);
  }
}

function showNodeModal(nodeData) {
  return renderNodeModal(nodeData, currentStepData);
}

window.renderNodeModal = renderNodeModal;
window.showNodeModal = showNodeModal;
window.showFallbackModal = showFallbackModal;

function hideNodeModal() {
  const card = document.getElementById("nodeInfoCard");
  if (card) {
    card.classList.add("hidden");
    card.style.display = "none";
  }
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
    cardEl.classList.remove("formula-amber", "formula-purple", "formula-blue", "formula-violet");
    if (theme === "purple") {
      cardEl.classList.add("formula-purple");
    } else if (theme === "blue") {
      cardEl.classList.add("formula-blue");
    } else if (theme === "violet") {
      cardEl.classList.add("formula-violet");
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
    } else if (theme === "violet") {
      badgeEl.className = "text-[9px] font-mono font-bold text-violet-800 bg-violet-100 px-1.5 py-0.5 rounded border border-violet-300";
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
  for (let s = 1; s <= 19; s++) {
    const item = document.getElementById(`stepNav${s}`);
    if (!item) continue;

    item.classList.remove("active", "completed", "step-amber", "step-purple", "step-emerald", "step-blue", "step-indigo", "step-cyan", "step-violet", "step-gold");
    if (s < step) {
      item.classList.add("completed");
    } else if (s === step) {
      item.classList.add("active");
      if (step === 3 || step === 4) {
        item.classList.add("step-amber");
      } else if (step === 5 || step === 10 || step === 16) {
        item.classList.add("step-emerald");
      } else if (step === 6 || step === 8) {
        item.classList.add("step-purple");
      } else if (step === 7 || step === 17) {
        item.classList.add("step-blue");
      } else if (step === 9) {
        item.classList.add("step-indigo");
      } else if (step === 11 || step === 15) {
        item.classList.add("step-cyan");
      } else if (step === 12) {
        item.classList.add("step-violet");
      } else if (step === 13 || step === 18) {
        item.classList.add("step-amber");
      } else if (step === 14) {
        item.classList.add("step-gold");
      } else if (step === 19) {
        item.classList.add("step-emerald");
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
    if (step < 19) {
      btnNext.disabled = false;
      btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 hover:bg-blue-700 cursor-pointer transition-colors shadow-sm";
      btnNext.innerHTML = `<span>Next Step (Step ${step + 1})</span><span>▶️</span>`;
      btnNext.title = `Advance to Step ${step + 1}`;
    } else {
      btnNext.disabled = true;
      btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 opacity-50 cursor-not-allowed";
      btnNext.title = "Step 19 active (Semantic Overlay Network Formation complete)";
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
  if (btnNext) btnNext.disabled = disabled || (currentStep >= 19);
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
      if (currentStep < 19) {
        loadStep(currentStep + 1);
      } else {
        logToTerminal("INFO", "Step 19 is active (Semantic Overlay Network Formation complete).");
      }
    });
  }

  // Clickable Stepper tabs (Step 1 to Step 19)
  for (let s = 1; s <= 19; s++) {
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
