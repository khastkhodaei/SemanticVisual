// SemanticDFL Storyboard Simulator - Step 1: Physical Ad-Hoc Mesh & Non-IID Data Distribution

let currentSession = null;
let simulationData = {};
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
  // Automatically bootstrap Step 1
  initializeNetwork();
});

// Render the 10 Dataset Classes in the Sidebar
function renderClassLegend() {
  const container = document.getElementById("classList");
  if (!container) return;

  container.innerHTML = "";
  for (let cid = 0; cid < 10; cid++) {
    const cls = DATASET_CLASSES[cid];
    const item = document.createElement("div");
    item.className = "class-chip text-slate-300 hover:text-white";
    item.dataset.classId = cid;

    item.innerHTML = `
      <div class="flex items-center space-x-2">
        <span class="text-sm">${cls.icon}</span>
        <span class="font-bold text-xs">${cls.name}</span>
        <span class="text-[10px] text-slate-500 font-mono">(Class ${cid})</span>
      </div>
      <div class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700/60 text-cyan-400">
        Dims ${cls.slice[0]}-${cls.slice[1]}
      </div>
    `;

    // Interactive filter highlight on hover/click
    item.addEventListener("mouseenter", () => highlightClassNodes(cid));
    item.addEventListener("mouseleave", () => resetNodeHighlights());
    container.appendChild(item);
  }
}

// 1. Initialize Cytoscape Canvas for Pure Step 1
function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById("cy"),
    elements: [],
    style: [
      {
        selector: "node",
        style: {
          "label": "data(label)",
          "color": "#f8fafc",
          "font-size": "10px",
          "font-family": "ui-monospace, monospace",
          "font-weight": "bold",
          "text-valign": "bottom",
          "text-margin-y": 5,
          "text-background-color": "rgba(9, 13, 22, 0.75)",
          "text-background-opacity": 0.9,
          "text-background-padding": 2,
          "text-background-shape": "roundrectangle",
          "background-color": "#0284c7", // Uniform neutral blue/cyan
          "border-color": "#38bdf8",
          "border-width": 2,
          "width": 28,
          "height": 28,
          "transition-property": "background-color, border-color, width, height, border-width, opacity",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: "node.highlighted",
        style: {
          "background-color": "#06b6d4",
          "border-color": "#a5f3fc",
          "border-width": 3.5,
          "width": 34,
          "height": 34,
          "z-index": 99
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
          "line-color": "#38bdf8",
          "curve-style": "straight",
          "opacity": 0.45,
          "transition-property": "line-color, width, opacity",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: "edge.highlighted",
        style: {
          "line-color": "#06b6d4",
          "width": 2.8,
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

// Show Glassmorphic Tooltip Card
function showNodeTooltip(nodeData) {
  const card = document.getElementById("nodeInfoCard");
  if (!card) return;

  document.getElementById("cardNodeId").textContent = `NODE #C${nodeData.id}`;
  document.getElementById("cardStatusBadge").textContent = nodeData.status || "NOT_ASSIGNED";

  const classId = nodeData.class_id !== undefined ? nodeData.class_id : (nodeData.category_id || 0);
  const cls = DATASET_CLASSES[classId] || { name: "Class", icon: "📦", slice: [0, 4] };

  document.getElementById("cardClass").textContent = `${cls.name} ${cls.icon} (Class ${classId})`;
  document.getElementById("cardSlice").textContent = `Dims [${cls.slice[0]} - ${cls.slice[1]}]`;
  document.getElementById("cardDegree").textContent = `${nodeData.degree || 0} neighbors`;

  const x = nodeData.coords ? Math.round(nodeData.coords.x) : (nodeData.x ? Math.round(nodeData.x) : "-");
  const y = nodeData.coords ? Math.round(nodeData.coords.y) : (nodeData.y ? Math.round(nodeData.y) : "-");
  const cardCoords = document.getElementById("cardCoords");
  if (cardCoords) cardCoords.textContent = `(${x}, ${y})`;

  // Draw 50-dimensional parameter vector preview with active class spike
  renderTooltipVectorPreview(nodeData.weights || [], classId);

  card.classList.remove("hidden");
}

function hideNodeTooltip() {
  const card = document.getElementById("nodeInfoCard");
  if (card) card.classList.add("hidden");
}

// Render Mini 50-Dimension Vector Bar Chart Snapshot
function renderTooltipVectorPreview(weights, classId) {
  const canvas = document.getElementById("tooltipVectorCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  // Background grid line
  ctx.strokeStyle = "rgba(51, 65, 85, 0.4)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, height - 6);
  ctx.lineTo(width, height - 6);
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

    // Height scaled between 4px and 38px
    const barHeight = Math.max(3, Math.min(height - 8, val * (height - 8)));
    const y = (height - 6) - barHeight;

    if (isActive) {
      // Glowing active parameter slice
      const grad = ctx.createLinearGradient(0, y, 0, height);
      grad.addColorStop(0, "#38bdf8");
      grad.addColorStop(1, "#0284c7");
      ctx.fillStyle = grad;
      ctx.fillRect(x, y, totalBarWidth, barHeight);

      // Top cap highlight
      ctx.fillStyle = "#e0f2fe";
      ctx.fillRect(x, y, totalBarWidth, 1.5);
    } else {
      // Baseline small noise coordinates
      ctx.fillStyle = "rgba(71, 85, 105, 0.5)";
      ctx.fillRect(x, y, totalBarWidth, barHeight);
    }
  }
}

// Highlight all nodes belonging to a specific dataset class
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

// 2. Action Buttons & Events
function bindActionButtons() {
  const btnInit = document.getElementById("btnInit");
  if (btnInit) {
    btnInit.addEventListener("click", initializeNetwork);
  }

  const btnClearLogs = document.getElementById("btnClearLogs");
  if (btnClearLogs) {
    btnClearLogs.addEventListener("click", () => {
      const logs = document.getElementById("terminalLogs");
      if (logs) logs.innerHTML = '<div class="text-slate-500">[SYSTEM] Terminal logs cleared.</div>';
    });
  }
}

// 3. API Call: Initialize 50-Node Storyboard Network
async function initializeNetwork() {
  const btnInit = document.getElementById("btnInit");
  if (btnInit) {
    btnInit.disabled = true;
    btnInit.classList.add("opacity-60");
  }

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

    // Update Session Badge
    const sessionVal = document.getElementById("sessionVal");
    if (sessionVal) {
      sessionVal.textContent = currentSession.substring(0, 8) + "...";
    }

    // Update Quick Stats
    const statNodes = document.getElementById("statNodes");
    if (statNodes) statNodes.textContent = data.nodes ? data.nodes.length : 50;

    const statDegree = document.getElementById("statDegree");
    if (statDegree && data.metadata) {
      statDegree.textContent = `Avg ${data.metadata.avg_degree || 4.4} (3-6)`;
    }

    // Render Cytoscape elements
    renderMesh(data.nodes, data.edges);

    // Log received events
    if (data.logs && Array.isArray(data.logs)) {
      data.logs.forEach(l => logToTerminal(l.level, l.message));
    }

    logToTerminal("SUCCESS", `Step 1 Base Topology deployed: 50 nodes, ${data.edges.length} undirected physical links.`);
    logToTerminal("INFO", "Non-IID Class Allocation: Cat 🐱 (C1, C2, C20, C21, C22, C35 separated across network).");
    logToTerminal("INFO", "Pure overlay-free mesh: All nodes are in CLIENT role with status NOT_ASSIGNED.");

  } catch (err) {
    logToTerminal("ERROR", `Initialization failure: ${err.message}`);
    console.error("Initialization Error:", err);
  } finally {
    if (btnInit) {
      btnInit.disabled = false;
      btnInit.classList.remove("opacity-60");
    }
  }
}

// 4. Render Physical Ad-Hoc Mesh in Cytoscape
function renderMesh(nodes, edges) {
  if (!cy) return;

  const elements = [];

  // Build Nodes with uniform neutral blue/cyan
  nodes.forEach(n => {
    const classId = n.class_id !== undefined ? n.class_id : (n.category_id !== undefined ? n.category_id : (n.category || 0));
    const cls = DATASET_CLASSES[classId] || { name: "Node", icon: "📦" };
    const label = `C${n.id} ${cls.icon}`;

    elements.push({
      group: "nodes",
      data: {
        id: `node_${n.id}`,
        peer_id: n.id,
        label: label,
        status: n.status || "NOT_ASSIGNED",
        role: n.role || "CLIENT",
        class_id: classId,
        category_id: classId,
        class_name: cls.name,
        category_name: cls.name,
        emoji: cls.icon,
        class_icon: cls.icon,
        degree: n.degree || 0,
        vrf_score: null,
        coords: n.coords,
        weights: n.weights || []
      },
      position: {
        x: n.coords ? n.coords.x : 100,
        y: n.coords ? n.coords.y : 100
      }
    });
  });

  // Build Undirected Physical Edges
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

// 5. Console Terminal Logger Helper
function logToTerminal(level, message) {
  const terminal = document.getElementById("terminalLogs");
  if (!terminal) return;

  const row = document.createElement("div");
  row.className = "flex items-start space-x-2 font-mono text-[11px] leading-tight";

  const timeStr = new Date().toLocaleTimeString("en-US", { hour12: false });
  let badgeColor = "text-cyan-400";

  if (level === "ERROR") badgeColor = "text-rose-400";
  else if (level === "SUCCESS") badgeColor = "text-emerald-400";
  else if (level === "WARN") badgeColor = "text-amber-400";

  row.innerHTML = `
    <span class="text-slate-600 select-none">[${timeStr}]</span>
    <span class="${badgeColor} font-bold select-none">[${level}]</span>
    <span class="text-slate-300">${message}</span>
  `;

  terminal.appendChild(row);
  terminal.scrollTop = terminal.scrollHeight;
}
