// ==========================================================================
// SemanticDFL Storyboard Simulator - Decoupled Algorithm 2 & 3 Controller
// Precomputed Ground-Truth from 'semantic_dfl_simulation_data.xlsx'
// ACM 2026 Reference Implementation - Steps 1 to 4
// ==========================================================================

let currentStep = 1;
let currentConfig = null;
let currentStepData = null;
let cy = null;
let activeSelectedNodeId = null;
let activeSelectedNodeData = null;
let activeAnimationId = null;

// CIFAR-10 Fallback / Cache
const CIFAR10_CLASSES = {
  0: { name: "هواپیما (Airplane)", english: "Airplane", icon: "✈️" },
  1: { name: "اتومبیل (Automobile)", english: "Automobile", icon: "🚗" },
  2: { name: "پرنده (Bird)", english: "Bird", icon: "🐦" },
  3: { name: "گربه (Cat)", english: "Cat", icon: "🐱" },
  4: { name: "آهو (Deer)", english: "Deer", icon: "🦌" },
  5: { name: "سگ (Dog)", english: "Dog", icon: "🐶" },
  6: { name: "قورباغه (Frog)", english: "Frog", icon: "🐸" },
  7: { name: "اسب (Horse)", english: "Horse", icon: "🐎" },
  8: { name: "کشتی (Ship)", english: "Ship", icon: "🚢" },
  9: { name: "کامیون (Truck)", english: "Truck", icon: "🚚" },
};

// 10 Distinct Palettes for the 10 Proximity Zones (Sheet 3)
const ZONE_PALETTES = {
  "زون C1": { fill: "#3b82f6", border: "#1d4ed8", text: "#1e3a8a", name: "Zone C1 (Blue)" },
  "زون C6": { fill: "#10b981", border: "#047857", text: "#064e3b", name: "Zone C6 (Emerald)" },
  "زون C11": { fill: "#f59e0b", border: "#b45309", text: "#78350f", name: "Zone C11 (Amber)" },
  "زون C16": { fill: "#ef4444", border: "#b91c1c", text: "#7f1d1d", name: "Zone C16 (Red)" },
  "زون C21": { fill: "#8b5cf6", border: "#6d28d9", text: "#4c1d95", name: "Zone C21 (Purple)" },
  "زون C26": { fill: "#06b6d4", border: "#0e7490", text: "#164e63", name: "Zone C26 (Cyan)" },
  "زون C31": { fill: "#ec4899", border: "#be185d", text: "#831843", name: "Zone C31 (Pink)" },
  "زون C36": { fill: "#14b8a6", border: "#0f766e", text: "#134e4a", name: "Zone C36 (Teal)" },
  "زون C41": { fill: "#f97316", border: "#c2410c", text: "#7c2d12", name: "Zone C41 (Orange)" },
  "زون C46": { fill: "#6366f1", border: "#4338ca", text: "#312e81", name: "Zone C46 (Indigo)" },
};

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
          "label": "data(label)",
          "color": "#0f172a",
          "font-size": "9.5px",
          "font-family": "ui-monospace, monospace",
          "font-weight": "bold",
          "text-valign": "bottom",
          "text-margin-y": 4,
          "text-background-color": "rgba(255, 255, 255, 0.92)",
          "text-background-opacity": 0.95,
          "text-background-padding": 2,
          "text-background-shape": "roundrectangle",
          "background-color": "data(bg_color)",
          "border-color": "data(border_color)",
          "border-width": 2,
          "width": 26,
          "height": 26,
          "transition-property": "background-color, border-color, width, height, border-width, opacity, shadow-blur, shadow-opacity",
          "transition-duration": "0.25s"
        }
      },
      {
        selector: "node.initiator-node",
        style: {
          "border-color": "#b45309",
          "border-width": 4.5,
          "width": 36,
          "height": 36,
          "color": "#78350f",
          "font-size": "11px",
          "shadow-blur": 18,
          "shadow-color": "#f59e0b",
          "shadow-opacity": 0.85,
          "z-index": 90
        }
      },
      {
        selector: "node.selected-node",
        style: {
          "border-color": "#0284c7",
          "border-width": 5,
          "width": 38,
          "height": 38,
          "z-index": 100
        }
      },
      {
        selector: "node.initiator-node.selected-node",
        style: {
          "border-color": "#78350f",
          "border-width": 5,
          "width": 40,
          "height": 40,
          "z-index": 100
        }
      },
      {
        selector: "node.highlighted",
        style: {
          "background-color": "#0284c7",
          "border-color": "#0369a1",
          "border-width": 4,
          "width": 34,
          "height": 34,
          "z-index": 95
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
          "line-color": "#94a3b8", // High-contrast clean physical link
          "curve-style": "straight",
          "opacity": 0.65,
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
          "width": 2.4,
          "opacity": 0.95,
          "z-index": 60
        }
      },
      {
        selector: "edge.intra-zone-edge",
        style: {
          "line-style": "solid",
          "line-color": "#94a3b8",
          "width": 1.5,
          "opacity": 0.45
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
          "opacity": 0.15
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

  // Click-to-Toggle Node Modal Interaction & Slow-Mo Focus
  cy.on("tap", "node", (evt) => {
    const node = evt.target;
    const nid = node.data("node_id_num");

    if (activeSelectedNodeId === nid) {
      hideNodeModal();
    } else {
      activeSelectedNodeId = nid;
      activeSelectedNodeData = node.data();
      showNodeModal(node.data());

      // Darken/dim all unrelated nodes and edges on canvas (opacity 0.2)
      cy.elements().addClass("dimmed");
      node.removeClass("dimmed").addClass("selected-node");
      node.connectedEdges().removeClass("dimmed").addClass("highlighted");
      node.neighborhood().nodes().removeClass("dimmed");

      // In Step 4, automatically launch slow-mo packet tracer for this clicked node
      if (currentStep === 4) {
        replaySlowMoNodeTrace(node.data());
      }
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
    if (statNodes) statNodes.textContent = data.num_nodes || 50;
    const statDegree = document.getElementById("statDegree");
    if (statDegree) statDegree.textContent = `${data.avg_degree || 3.6} (${data.total_edges} edges)`;

    const sessionVal = document.getElementById("sessionVal");
    if (sessionVal) sessionVal.textContent = "Excel Ground-Truth";
  } catch (err) {
    console.error("Config Load Error:", err);
    logToTerminal("ERROR", `Failed to load network configuration: ${err.message}`);
  }
}

// Render Dataset Class Legend in Left Sidebar
function renderDatasetClassLegend(classes) {
  const container = document.getElementById("classList");
  if (!container) return;
  container.innerHTML = "";

  classes.forEach(c => {
    const item = document.createElement("div");
    item.className = "class-chip text-slate-700";
    item.dataset.classId = c.class_id;

    item.innerHTML = `
      <div class="flex items-center space-x-1.5">
        <span class="text-sm">${c.icon}</span>
        <span class="font-bold text-[11px] text-slate-800">${c.english_name || c.name}</span>
        <span class="text-[9px] text-slate-400 font-mono">(C${c.class_id})</span>
      </div>
      <div class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-blue-700 font-semibold">
        ${c.count} nodes
      </div>
    `;

    item.addEventListener("mouseenter", () => highlightClassNodes(c.class_id));
    item.addEventListener("mouseleave", () => resetNodeHighlights());
    container.appendChild(item);
  });
}

function highlightClassNodes(classId) {
  if (!cy) return;
  cy.nodes().forEach(n => {
    if (n.data("class_id") === classId) {
      n.removeClass("dimmed").addClass("highlighted");
    } else {
      n.removeClass("highlighted").addClass("dimmed");
    }
  });
}

function resetNodeHighlights() {
  if (!cy) return;
  cy.nodes().removeClass("highlighted dimmed");
}

// 4. Main Step Loading Function (Steps 1 to 4)
async function loadStep(stepNumber) {
  if (stepNumber < 1 || stepNumber > 4) return;
  setNavButtonsDisabled(true);
  hideNodeModal();
  stopCurrentPacketAnimation();

  try {
    const res = await fetch(`/api/v1/storyboard/step/${stepNumber}`);
    if (!res.ok) throw new Error(`Step ${stepNumber} fetch failed: ${res.statusText}`);
    const data = await res.json();
    currentStep = stepNumber;
    currentStepData = data;

    updateUIHeaders(data);
    updateStepper(stepNumber);
    updateNavButtons(stepNumber);

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
  const activeBadge = document.getElementById("activeStepBadge");
  if (activeBadge) {
    activeBadge.textContent = data.phase_badge || `Step ${data.step}`;
    if (data.step === 1) {
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200";
    } else if (data.step === 2) {
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-sky-50 text-sky-700 border border-sky-300";
    } else if (data.step === 3) {
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 border border-amber-300";
    } else if (data.step === 4) {
      activeBadge.className = "text-xs font-bold font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-purple-50 text-purple-800 border border-purple-300";
    }
  }

  const stepTag = document.getElementById("stepTag");
  if (stepTag) stepTag.textContent = `STEP ${data.step} / SHEET ${data.step === 1 ? '2' : '3'}`;
  const stepTitle = document.getElementById("stepTitle");
  if (stepTitle) stepTitle.textContent = data.title;
  const stepDesc = document.getElementById("stepDescription");
  if (stepDesc) stepDesc.textContent = data.description;
}

// 5. STEP 1: Base Physical Topology
function renderStep1(data) {
  renderSidebarFormula(
    "Physical Network Topology",
    "G = (V, E), \\quad |V|=50, \\quad |E|=90",
    "Base physical ad-hoc network loaded from Sheet 2. 50 mobile edge devices with 90 physical communication links. No overlays or zones.",
    "Topology",
    false
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Physical Ad-Hoc Topology (50 Nodes, 90 Edges)";

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

// 6. STEP 2: Local VRF Score Computation
function renderStep2(data) {
  renderSidebarFormula(
    "Local VRF Score Computation",
    "\\sigma_p = \\text{VRF}_{sk_p}(\\text{seed}_{e-1}) \\in [0, 1)",
    "Each peer computes a verifiable pseudorandom score using its private key sk and global seed_e0. Zero network communication.",
    "Local VRF",
    false
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Local VRF Evaluation (50 Peers, All Roles = CLIENT)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.add("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.textContent = "0 Initiators (Unexchanged)";
    statLeaders.className = "text-xs font-bold text-slate-500";
  }

  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: false,
    useZoneColors: false,
    showBoundaryEdges: false
  });
}

// 7. STEP 3: VRF Comparison & Local Initiator Deciding (Algorithm 2)
// - 10 Initiators receive their distinct assigned Zone Palette color seed with gold crown 👑
// - Non-initiators stay in neutral blue (#2563eb)
// - Clicking a node displays the 3-hop decision table and scoreboard
function renderStep3(data) {
  renderSidebarFormula(
    "VRF Initiator Election (Alg. 2)",
    "m_p = \\min_{q \\in \\mathcal{N}_3(p)} (\\sigma_q, id_q)",
    "Each node evaluates the minimum VRF score in its 3-hop physical neighborhood ball. The node holding the minimum score elects itself as Initiator.",
    "R = 3 Hops",
    true
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "VRF Comparison (10 Initiator Color Seeds 👑, 40 Candidates)";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.add("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.textContent = "10 Initiators 👑 (R=3)";
    statLeaders.className = "text-xs font-bold text-amber-600";
  }

  // Render nodes: 10 Initiators receive their distinct Zone Palette color seeds with crown, non-initiators in neutral blue
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    initiatorColorSeeds: true,
    useZoneColors: false,
    showBoundaryEdges: false
  });
}

// 8. STEP 4: Zone Formation, First-Wins & Probe Conflicts (Algorithm 3)
// - Start Step 4 with non-initiators in neutral blue (like Step 3), while Initiators have their distinct zone colors
// - Nodes morph dynamically upon probe arrival wave-by-wave
// - Delayed competing probes dropped, edges dashed red (#f87171), and reverse boundary alerts emitted
function renderStep4(data) {
  renderSidebarFormula(
    "Zone Formation (Alg. 3)",
    "\\text{PROBE}(p, \\text{TTL}=3) \\xrightarrow{\\text{first-wins}} \\text{ASSIGNED}(Z_I), \\quad \\text{delayed} \\rightarrow \\text{BOUNDARY}",
    "Initiators flood PROBE packets (TTL=3). Unassigned peers adopt the first arriving probe (First-Wins). Delayed competing probes are dropped, forming boundary bridges.",
    "TTL = 3, First-Wins",
    false,
    "purple"
  );

  const canvasLabel = document.getElementById("canvasViewLabel");
  if (canvasLabel) canvasLabel.textContent = "Zone PROBE Flooding & First-Wins Dynamic Color Morphing";

  const leaderLegend = document.getElementById("leaderLegendItem");
  if (leaderLegend) leaderLegend.classList.remove("hidden");
  const boundaryLegend = document.getElementById("boundaryLegendItem");
  if (boundaryLegend) boundaryLegend.classList.remove("hidden");

  const statLeaders = document.getElementById("statLeaders");
  if (statLeaders) {
    statLeaders.textContent = "10 Zones Forming...";
    statLeaders.className = "text-xs font-bold text-purple-700";
  }

  // Step 4 starts with non-initiators in neutral blue; morphing happens dynamically on packet impact
  renderCytoscapeGraph(data.nodes, data.edges, {
    showInitiators: true,
    initiatorColorSeeds: true,
    useZoneColors: false,
    showBoundaryEdges: false
  });

  // Launch the 3-wave PROBE packet animation with dynamic state-change morphing
  if (data.waves) {
    animateProbeFloodingWaves(data.waves, data.nodes);
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
      activePackets.forEach(pkt => {
        const tgtNode = cy.getElementById(`node_${pkt.target}`);
        const p2 = tgtNode && tgtNode.isNode() ? tgtNode.renderedPosition() : null;
        if (!p2) return;

        if (pkt.is_first_wins && !morphedNodes.has(pkt.target)) {
          morphedNodes.add(pkt.target);
          const pal = ZONE_PALETTES[`زون C${pkt.initiator}`];
          if (pal) {
            tgtNode.style({
              "background-color": pal.fill,
              "border-color": pal.border
            });
            ripples.push({
              x: p2.x,
              y: p2.y,
              radius: 10,
              maxRadius: 36,
              color: pal.fill,
              alpha: 0.95
            });
            logToTerminal("SUCCESS", `[FIRST-WINS] C${pkt.target} adopted Zone C${pkt.initiator} at Hop ${currentWaveIndex}. Color morphed!`);
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

            // Emit reverse boundary alert packet (Alg 3 L17-L19)
            const srcNode = cy.getElementById(`node_${pkt.source}`);
            const p1 = srcNode && srcNode.isNode() ? srcNode.renderedPosition() : null;
            if (p1) {
              reverseAlerts.push({
                startX: p2.x,
                startY: p2.y,
                endX: p1.x,
                endY: p1.y,
                startTime: now,
                duration: 650,
                color: "#8b5cf6"
              });
            }
            logToTerminal("WARN", `[CONFLICT/BOUNDARY] C${pkt.target} dropped delayed PROBE from Zone C${pkt.initiator}. Link dashed red. Reverse alert emitted!`);
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

    // Render reverse boundary alerts (Alg 3 L17-L19)
    for (let i = reverseAlerts.length - 1; i >= 0; i--) {
      const a = reverseAlerts[i];
      const aElapsed = now - a.startTime;
      const aProg = Math.min(aElapsed / a.duration, 1.0);
      const easeA = easeInOutQuad(aProg);
      const ax = a.startX + (a.endX - a.startX) * easeA;
      const ay = a.startY + (a.endY - a.startY) * easeA;

      ctx.save();
      ctx.beginPath();
      ctx.arc(ax, ay, 5.5, 0, Math.PI * 2);
      ctx.fillStyle = a.color;
      ctx.shadowBlur = 8;
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
        currentWaveIndex = 2;
        waveStartTime = performance.now();
        logWaveTransition(2);
        activeAnimationId = requestAnimationFrame(runWaveFrame);
      } else if (currentWaveIndex === 2 && wave3Packets.length > 0) {
        currentWaveIndex = 3;
        waveStartTime = performance.now();
        logWaveTransition(3);
        activeAnimationId = requestAnimationFrame(runWaveFrame);
      } else {
        // Animation finished
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        activeAnimationId = null;

        // Ensure all nodes and boundary edges reflect final state
        (allNodes || []).forEach(n => {
          const cyNode = cy.getElementById(`node_${n.id}`);
          if (cyNode && cyNode.isNode() && n.assigned_zone) {
            const pal = ZONE_PALETTES[n.assigned_zone];
            const isInit = n.is_initiator;
            if (pal) {
              cyNode.style({
                "background-color": pal.fill,
                "border-color": isInit ? "#b45309" : pal.border
              });
            }
          }
        });
        cy.edges().forEach(e => {
          if (e.data("is_inter_zone")) {
            e.addClass("boundary-edge");
          }
        });

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
    const label = isInit ? `👑 C${n.id} ${n.class_icon}` : `C${n.id} ${n.class_icon}`;

    let bgColor = "#2563eb";
    let borderColor = "#1d4ed8";

    if (options.useZoneColors && n.assigned_zone) {
      const pal = ZONE_PALETTES[n.assigned_zone];
      if (pal) {
        bgColor = pal.fill;
        borderColor = isInit ? "#b45309" : pal.border;
      } else if (n.zone_color) {
        bgColor = n.zone_color;
        borderColor = isInit ? "#b45309" : n.zone_color;
      }
    } else if (isInit && options.initiatorColorSeeds) {
      // Step 3 initiator seeds: 10 distinct hues for the 10 initiators
      const pal = ZONE_PALETTES[`زون C${n.id}`];
      bgColor = pal ? pal.fill : (n.initiator_color || n.zone_color || "#f59e0b");
      borderColor = "#b45309";
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
        role: isInit ? "👑 Initiator" : (n.role || "Member"),
        status: n.status || "NOT_ASSIGNED",
        bg_color: bgColor,
        border_color: borderColor,
        class_id: n.class_id,
        class_title: n.class_title,
        class_icon: n.class_icon,
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
        first_wins_text: n.first_wins_text,
        accepted_probe: n.accepted_probe,
        rejected_probes: n.rejected_probes || n.competing_probes_rejected || [],
        competing_probes_rejected: n.competing_probes_rejected || [],
        forwarded_to: n.forwarded_to || [],
        boundary_notifications_emitted: n.boundary_notifications_emitted || [],
        is_boundary: n.is_boundary,
        boundary_neighbors: n.boundary_neighbors || [],
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
}

// 10. Click-to-Toggle Node Details Modal
function showNodeModal(nodeData) {
  const card = document.getElementById("nodeInfoCard");
  if (!card) return;

  const isInitiator = nodeData.is_initiator;
  const cardNodeId = document.getElementById("cardNodeId");
  const cardStatusBadge = document.getElementById("cardStatusBadge");
  const cardRole = document.getElementById("cardRole");
  const cardClass = document.getElementById("cardClass");
  const cardVrfScore = document.getElementById("cardVrfScore");
  const cardVrfScoreRow = document.getElementById("cardVrfScoreRow");
  const cardVrfDetailsRow = document.getElementById("cardVrfDetailsRow");
  const cardSk = document.getElementById("cardSk");
  const cardFormula = document.getElementById("cardFormula");
  const cardDegree = document.getElementById("cardDegree");
  const cardNeighbors = document.getElementById("cardNeighbors");

  // Step 3 Scoreboard Elements
  const step3Sec = document.getElementById("cardStep3ScoreboardSection");
  const step3Badge = document.getElementById("cardStep3Badge");
  const decisionBanner = document.getElementById("cardDecisionBanner");
  const scoreboardCount = document.getElementById("cardScoreboardCount");
  const scoreboardList = document.getElementById("cardScoreboardList");

  // Step 4 Zone & Conflict Elements
  const step4Sec = document.getElementById("cardStep4ZoneSection");
  const zoneStatusTag = document.getElementById("cardZoneStatusTag");
  const cardZoneId = document.getElementById("cardZoneId");
  const cardZoneWinner = document.getElementById("cardZoneWinner");
  const cardFirstWinsText = document.getElementById("cardFirstWinsText");
  const cardRejectedCount = document.getElementById("cardRejectedCount");
  const cardRejectedProbesList = document.getElementById("cardRejectedProbesList");
  const cardBoundaryNeighborsRow = document.getElementById("cardBoundaryNeighborsRow");
  const cardBoundaryNeighborsList = document.getElementById("cardBoundaryNeighborsList");

  // Title: Node ID & Emoji
  if (cardNodeId) {
    if (isInitiator && currentStep >= 3) {
      cardNodeId.innerHTML = `<span class="text-amber-800">👑 C${nodeData.node_id_num} ${nodeData.class_icon}</span>`;
    } else {
      cardNodeId.innerHTML = `<span class="text-blue-700">C${nodeData.node_id_num} ${nodeData.class_icon}</span>`;
    }
  }

  // Status Badge
  if (cardStatusBadge) {
    if (currentStep === 4) {
      cardStatusBadge.textContent = isInitiator ? "👑 INITIATOR" : "ASSIGNED";
      cardStatusBadge.className = isInitiator
        ? "text-[9px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300"
        : "text-[9px] font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300";
    } else if (currentStep === 3) {
      cardStatusBadge.textContent = isInitiator ? "👑 INITIATOR" : "CANDIDATE";
      cardStatusBadge.className = isInitiator
        ? "text-[9px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300"
        : "text-[9px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-300";
    } else if (currentStep === 2) {
      cardStatusBadge.textContent = "VRF COMPUTED";
      cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-sky-100 text-sky-800 border border-sky-300";
    } else {
      cardStatusBadge.textContent = "NOT_ASSIGNED";
      cardStatusBadge.className = "text-[9px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200";
    }
  }

  // Role: 👑 Initiator or Member
  if (cardRole) {
    if (currentStep >= 3 && isInitiator) {
      cardRole.textContent = "👑 Initiator (Zone Root)";
      cardRole.className = "text-amber-800 font-mono font-bold";
    } else if (currentStep === 4) {
      cardRole.textContent = "Member";
      cardRole.className = "text-slate-800 font-mono font-bold";
    } else {
      cardRole.textContent = "CLIENT";
      cardRole.className = "text-slate-700 font-mono font-bold";
    }
  }

  // CIFAR-10 Class (Title + Emoji)
  if (cardClass) {
    cardClass.textContent = `${nodeData.class_title} ${nodeData.class_icon} (Class ${nodeData.class_id})`;
  }

  // Exact VRF Score (Step 2+)
  if (cardVrfScore && cardVrfScoreRow) {
    if (currentStep >= 2 && nodeData.vrf_score !== null && nodeData.vrf_score !== undefined) {
      cardVrfScoreRow.classList.remove("hidden");
      cardVrfScore.textContent = Number(nodeData.vrf_score).toFixed(4);
    } else {
      cardVrfScoreRow.classList.add("hidden");
    }
  }

  // VRF Formula & Key details (Step 2)
  if (cardVrfDetailsRow) {
    if (currentStep === 2 && nodeData.sk) {
      cardVrfDetailsRow.classList.remove("hidden");
      if (cardSk) cardSk.textContent = nodeData.sk;
      if (cardFormula) cardFormula.textContent = nodeData.vrf_formula || "((100+ID)*sk+1337)%10000";
    } else {
      cardVrfDetailsRow.classList.add("hidden");
    }
  }

  // STEP 3: 3-Hop VRF Scoreboard & Decision Table
  if (step3Sec) {
    if (currentStep === 3 && nodeData.scoreboard_3hop) {
      step3Sec.classList.remove("hidden");
      const sb = nodeData.scoreboard_3hop;

      if (step3Badge) {
        step3Badge.textContent = isInitiator ? "Self-Elected" : "Candidate";
        step3Badge.className = isInitiator
          ? "text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300"
          : "text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-300";
      }

      if (decisionBanner) {
        decisionBanner.textContent = sb.decision_result;
        decisionBanner.className = isInitiator
          ? "p-2 rounded font-mono text-[10px] font-bold border bg-amber-50 border-amber-300 text-amber-950 leading-snug"
          : "p-2 rounded font-mono text-[10px] font-bold border bg-slate-50 border-slate-300 text-slate-800 leading-snug";
      }

      if (scoreboardCount) {
        scoreboardCount.textContent = `${sb.total_coverage} peers covered`;
      }

      // Populate Hop 1, 2, 3 peers
      if (scoreboardList) {
        scoreboardList.innerHTML = "";

        const hopGroups = [
          { hop: 1, label: "Hop 1 (Direct Neighbors)", peers: sb.hop_1 },
          { hop: 2, label: "Hop 2 Reach", peers: sb.hop_2 },
          { hop: 3, label: "Hop 3 Reach", peers: sb.hop_3 },
        ];

        hopGroups.forEach(grp => {
          if (!grp.peers || grp.peers.length === 0) return;

          const grpHeader = document.createElement("div");
          grpHeader.className = "text-[9px] font-bold font-mono tracking-wider pt-1.5 pb-0.5 flex items-center justify-between text-slate-500 border-b border-slate-100";
          grpHeader.innerHTML = `
            <span class="flex items-center gap-1">
              <span class="px-1 py-0.2 rounded text-[8px] hop-badge-${grp.hop}">Hop ${grp.hop}</span>
              <span>${grp.label}</span>
            </span>
            <span class="text-[8px] text-slate-400">(${grp.peers.length} peers)</span>
          `;
          scoreboardList.appendChild(grpHeader);

          grp.peers.forEach(peer => {
            const row = document.createElement("div");
            const isWinner = peer.is_min;

            row.className = isWinner
              ? "winner-score-row px-2 py-1 flex items-center justify-between my-0.5"
              : "px-2 py-0.5 bg-slate-50 border border-slate-200/80 rounded flex items-center justify-between text-slate-700 my-0.5";

            row.innerHTML = `
              <span class="flex items-center gap-1 font-mono">
                ${isWinner ? "<span>👑</span>" : ""}
                <span class="${isWinner ? "font-bold text-amber-950" : "font-medium"}">C${peer.id}</span>
              </span>
              <span class="flex items-center gap-1 font-mono">
                <span class="${isWinner ? "text-amber-900 font-extrabold" : "text-slate-800"}">σ=${Number(peer.score).toFixed(4)}</span>
                ${isWinner ? '<span class="text-[8px] px-1 py-0.2 rounded bg-amber-200 text-amber-950 font-bold border border-amber-400">★ Winner (m_p)</span>' : ""}
              </span>
            `;
            scoreboardList.appendChild(row);
          });
        });
      }

    } else {
      step3Sec.classList.add("hidden");
    }
  }

  // STEP 4: Zone Formation, First-Wins & Conflict Resolution
  if (step4Sec) {
    if (currentStep === 4 && nodeData.assigned_zone) {
      step4Sec.classList.remove("hidden");

      if (zoneStatusTag) {
        zoneStatusTag.textContent = nodeData.status_tag || (nodeData.is_boundary ? "⚡ BOUNDARY" : "ASSIGNED");
        zoneStatusTag.className = nodeData.is_boundary
          ? "text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-300"
          : "text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-300";
      }

      if (cardZoneId) cardZoneId.textContent = nodeData.assigned_zone;
      if (cardZoneWinner) cardZoneWinner.textContent = nodeData.winner_initiator || "Unknown";
      if (cardFirstWinsText) cardFirstWinsText.textContent = nodeData.first_wins_text || "First-Wins";

      // 1. Accepted Probe Details
      const cardAcceptedWaveBadge = document.getElementById("cardAcceptedWaveBadge");
      const cardAcceptedProbeDetail = document.getElementById("cardAcceptedProbeDetail");
      const acc = nodeData.accepted_probe;
      if (cardAcceptedWaveBadge && cardAcceptedProbeDetail) {
        if (isInitiator) {
          cardAcceptedWaveBadge.textContent = "Root Seed";
          cardAcceptedWaveBadge.className = "px-1.5 py-0.2 rounded bg-amber-100 text-amber-900 border border-amber-300 font-bold";
          cardAcceptedProbeDetail.innerHTML = `👑 <strong>Zone Initiator:</strong> Self-elected root node. Floods PROBE(TTL=3) to physical neighbors.`;
        } else if (acc) {
          cardAcceptedWaveBadge.textContent = `Hop ${acc.hop} (Wave ${acc.arrival_wave})`;
          cardAcceptedWaveBadge.className = "px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold";
          cardAcceptedProbeDetail.innerHTML = `
            <div class="flex justify-between items-center">
              <span>Initiator: <strong class="text-amber-800">${acc.from_initiator} 👑</strong></span>
              <span>Sender: <strong class="text-blue-700">${acc.sender}</strong></span>
            </div>
            <div class="text-[8px] text-emerald-700 mt-0.5 font-sans">
              ✓ Adopted upon impact (First-Wins). Morphed to Initiator zone color.
            </div>
          `;
        }
      }

      // 2. Competing Probes Rejected
      const rejectedList = nodeData.rejected_probes || nodeData.competing_probes_rejected || [];
      if (cardRejectedCount) cardRejectedCount.textContent = `${rejectedList.length} probe(s) dropped`;
      if (cardRejectedProbesList) {
        if (rejectedList.length === 0) {
          cardRejectedProbesList.innerHTML = '<span class="text-slate-400 italic">None (Zone interior peer)</span>';
        } else {
          cardRejectedProbesList.innerHTML = rejectedList.map(r => `
            <div class="rejected-chip flex items-center justify-between my-0.5 w-full">
              <span>✕ ${r.competing_initiator || r.initiator} (${r.competing_zone || r.zone})</span>
              <span class="text-[8px] opacity-80">via ${r.sender || 'peer'} • Hop ${r.hop || r.arrived_hop}</span>
            </div>
          `).join("");
        }
      }

      // 3. Outgoing Forwarded Probes
      const fwdRow = document.getElementById("cardForwardedRow");
      const fwdCount = document.getElementById("cardForwardedCount");
      const fwdList = document.getElementById("cardForwardedList");
      const forwards = nodeData.forwarded_to || [];
      if (fwdRow && fwdList) {
        fwdRow.classList.remove("hidden");
        if (forwards.length > 0) {
          if (fwdCount) fwdCount.textContent = `${forwards.length} forwarded`;
          fwdList.innerHTML = forwards.map(f => `
            <span class="forwarded-chip mr-1 mb-0.5">
              ➜ ${f.target} (Hop ${f.hop})
            </span>
          `).join("");
        } else {
          if (fwdCount) fwdCount.textContent = "0 (Frontier/Leaf)";
          fwdList.innerHTML = '<span class="text-slate-400 italic">No further forwards (Zone frontier)</span>';
        }
      }

      // 4. Boundary Neighbors & Reverse Alerts (Alg 3 L17-L19)
      const bndRow = document.getElementById("cardBoundaryNeighborsRow");
      const bndAlertCount = document.getElementById("cardBoundaryAlertCount");
      const bndList = document.getElementById("cardBoundaryNeighborsList");
      const bndAlerts = nodeData.boundary_notifications_emitted || [];
      if (bndRow && bndList) {
        if (bndAlerts.length > 0) {
          bndRow.classList.remove("hidden");
          if (bndAlertCount) bndAlertCount.textContent = `${bndAlerts.length} alert(s)`;
          bndList.innerHTML = bndAlerts.map(b => `
            <div class="boundary-alert-chip flex items-center justify-between my-0.5 w-full">
              <span>⚡ Interface: ${b.frontier_peer} (${b.adjacent_zone})</span>
              <span class="text-[8px] text-purple-700">Alert ➜ ${b.to_initiator}</span>
            </div>
          `).join("");
        } else {
          bndRow.classList.add("hidden");
        }
      }

    } else {
      step4Sec.classList.add("hidden");
    }
  }

  // Direct Physical Neighbors (Sheet 2)
  if (cardDegree) {
    cardDegree.textContent = `${(nodeData.neighbors || []).length} neighbors`;
  }
  if (cardNeighbors) {
    const neighList = (nodeData.neighbors_str && nodeData.neighbors_str.length)
      ? nodeData.neighbors_str.join(", ")
      : (nodeData.neighbors || []).map(x => `C${x}`).join(", ");
    cardNeighbors.textContent = neighList || "None";
  }

  card.classList.remove("hidden");
}

function hideNodeModal() {
  const card = document.getElementById("nodeInfoCard");
  if (card) card.classList.add("hidden");
  if (cy) {
    cy.elements().removeClass("dimmed highlighted selected-node");
  }
  activeSelectedNodeId = null;
  activeSelectedNodeData = null;
  stopCurrentPacketAnimation();
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
      if (step === 3) {
        item.classList.add("step-amber");
      } else if (step === 4) {
        item.classList.add("step-purple");
      }
    }
  }
}

function updateNavButtons(step) {
  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");

  if (btnPrev) {
    btnPrev.disabled = (step === 1);
    if (step === 1) {
      btnPrev.innerHTML = `<span>◀️</span><span>Previous Step</span>`;
    } else {
      btnPrev.innerHTML = `<span>◀️</span><span>Previous Step (Step ${step - 1})</span>`;
    }
  }

  if (btnNext) {
    if (step === 4) {
      btnNext.disabled = true;
      btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 opacity-50 cursor-not-allowed";
      btnNext.innerHTML = `<span>Simulation Complete</span><span>✓</span>`;
    } else {
      btnNext.disabled = false;
      btnNext.className = "btn-primary px-4 py-1.5 rounded-lg text-xs font-bold font-mono flex items-center gap-1.5 shadow-sm transition-colors";
      const nextNames = {
        1: "Step 2: VRF Compute",
        2: "Step 3: VRF Comparison",
        3: "Step 4: Zone Flooding",
      };
      btnNext.innerHTML = `<span>Next Step (${nextNames[step]})</span><span>▶️</span>`;
    }
  }
}

function setNavButtonsDisabled(disabled) {
  const btnReset = document.getElementById("btnReset");
  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");

  if (btnReset) btnReset.disabled = disabled;
  if (btnPrev && currentStep > 1) btnPrev.disabled = disabled;
  if (btnNext && currentStep < 4) btnNext.disabled = disabled;
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
      if (currentStep > 1) loadStep(currentStep - 1);
    });
  }

  const btnNext = document.getElementById("btnNext");
  if (btnNext) {
    btnNext.addEventListener("click", () => {
      if (currentStep < 4) loadStep(currentStep + 1);
    });
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
