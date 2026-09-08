// SemanticDFL Protocol Simulator - Cyberpunk Interactive Dashboard Logic

let currentSession = null;
let currentPhase = 0;
let simulationData = {};
let cy = null;
let viewMode = 'mesh'; // 'mesh' | 'tree'
let autoPlayTimer = null;
let chartSignatures = null;
let chartConvergence = null;

// Zone color palette
const ZONE_COLORS = [
  '#06b6d4', '#10b981', '#a855f7', '#f59e0b', '#ec4899', 
  '#3b82f6', '#14b8a6', '#8b5cf6', '#f97316', '#84cc16'
];

document.addEventListener('DOMContentLoaded', () => {
  initCytoscape();
  initCharts();
  bindSliderInputs();
  bindActionButtons();
});

// 1. Parameter Sliders Sync
function bindSliderInputs() {
  const sliders = [
    { id: 'param_n', valId: 'val_n' },
    { id: 'param_dlimit', valId: 'val_dlimit' },
    { id: 'param_rhops', valId: 'val_rhops' },
    { id: 'param_sz', valId: 'val_sz' },
    { id: 'param_q', valId: 'val_q' },
    { id: 'param_theta', valId: 'val_theta' },
    { id: 'param_kappa', valId: 'val_kappa' },
  ];

  sliders.forEach(s => {
    const el = document.getElementById(s.id);
    const val = document.getElementById(s.valId);
    if (el && val) {
      el.addEventListener('input', (e) => {
        val.textContent = e.target.value;
      });
    }
  });
}

// 2. Cytoscape Canvas Initialization
function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById('cy'),
    elements: [],
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'color': '#f8fafc',
          'font-size': '9px',
          'font-family': 'monospace',
          'text-valign': 'bottom',
          'text-margin-y': 4,
          'background-color': 'data(color)',
          'width': 22,
          'height': 22,
          'border-width': 1.5,
          'border-color': '#06b6d4',
          'transition-property': 'background-color, border-color, width, height',
          'transition-duration': '0.3s'
        }
      },
      {
        selector: 'node[type = "initiator"]',
        style: {
          'shape': 'hexagon',
          'background-color': '#f59e0b',
          'border-color': '#fef08a',
          'border-width': 2.5,
          'width': 28,
          'height': 28
        }
      },
      {
        selector: 'node[type = "super_peer"]',
        style: {
          'shape': 'diamond',
          'background-color': '#a855f7',
          'border-color': '#e9d5ff',
          'border-width': 3,
          'width': 30,
          'height': 30
        }
      },
      {
        selector: 'node[type = "replica"]',
        style: {
          'shape': 'round-diamond',
          'background-color': '#10b981',
          'border-color': '#a7f3d0',
          'border-width': 2,
          'width': 24,
          'height': 24
        }
      },
      {
        selector: 'node[type = "root"]',
        style: {
          'shape': 'star',
          'background-color': '#f43f5e',
          'border-color': '#ffe4e6',
          'border-width': 3,
          'width': 36,
          'height': 36
        }
      },
      {
        selector: 'node[?isDead]',
        style: {
          'background-color': '#450a0a',
          'border-color': '#ef4444',
          'border-width': 2,
          'opacity': 0.45,
          'label': 'DEAD'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 1,
          'line-color': '#1e293b',
          'curve-style': 'straight',
          'opacity': 0.6
        }
      },
      {
        selector: 'edge[type = "hierarchy"]',
        style: {
          'width': 1.8,
          'line-color': '#a855f7',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#a855f7',
          'curve-style': 'bezier',
          'opacity': 0.75
        }
      }
    ],
    layout: { name: 'preset' }
  });

  // Hover Tooltip Interactions
  cy.on('mouseover', 'node', (evt) => {
    const n = evt.target.data();
    const card = document.getElementById('nodeInfoCard');
    if (!card) return;

    document.getElementById('cardNodeId').textContent = `NODE #${n.peer_id ?? n.id}`;
    document.getElementById('cardRole').textContent = n.role || n.type || 'CLIENT';
    document.getElementById('cardZone').textContent = n.zone !== undefined ? `Zone ${n.zone}` : 'None';
    document.getElementById('cardVRF').textContent = n.vrf !== undefined ? Number(n.vrf).toFixed(4) : '-';
    document.getElementById('cardClass').textContent = n.category || 'Non-IID Partition';
    document.getElementById('cardStatus').textContent = n.isDead ? 'OFFLINE (CHURN)' : 'ONLINE';
    card.classList.remove('hidden');
  });


  cy.on('mouseout', 'node', () => {
    const card = document.getElementById('nodeInfoCard');
    if (card) card.classList.add('hidden');
  });

  // Click-to-Kill Handler (Active in Phase 7)
  cy.on('tap', 'node', async (evt) => {
    if (currentPhase < 7) return;
    const n = evt.target.data();
    const nodeId = n.peer_id !== undefined ? n.peer_id : parseInt(n.id.replace(/\D/g, ''));
    if (isNaN(nodeId) || n.isDead) return;

    logToTerminal('CHURN', `User clicked node ${nodeId} to inject churn failure.`);
    await triggerChurn(nodeId);
  });
}

// 3. Chart.js Initialization
function initCharts() {
  // Dual Bar Chart for Signatures
  const ctxSig = document.getElementById('chartSignatures').getContext('2d');
  chartSignatures = new Chart(ctxSig, {
    type: 'bar',
    data: {
      labels: Array.from({ length: 50 }, (_, i) => `${i}`),
      datasets: [
        { label: 'Node A', data: [], backgroundColor: 'rgba(6, 182, 212, 0.7)' },
        { label: 'Node B', data: [], backgroundColor: 'rgba(168, 85, 247, 0.7)' }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { display: false },
        y: { display: true, ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: '#1e293b' } }
      },
      plugins: {
        legend: { labels: { color: '#94a3b8', font: { size: 10 } } }
      }
    }
  });

  // FL Convergence Line Chart
  const ctxConv = document.getElementById('chartConvergence').getContext('2d');
  chartConvergence = new Chart(ctxConv, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'SemanticDFL',
          data: [],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.3,
          borderWidth: 2,
          fill: true
        },
        {
          label: 'FedAvg (Non-IID)',
          data: [],
          borderColor: '#f43f5e',
          backgroundColor: 'rgba(244, 63, 94, 0.05)',
          tension: 0.3,
          borderWidth: 2,
          borderDash: [4, 4]
        },
        {
          label: 'Solo Local',
          data: [],
          borderColor: '#64748b',
          tension: 0.3,
          borderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: 'Rounds', color: '#64748b', font: { size: 10 } },
          ticks: { color: '#64748b', font: { size: 9 } },
          grid: { color: '#1e293b' }
        },
        y: {
          min: 0.3,
          max: 1.0,
          title: { display: true, text: 'Accuracy', color: '#64748b', font: { size: 10 } },
          ticks: { color: '#64748b', font: { size: 9 }, callback: v => `${Math.round(v * 100)}%` },
          grid: { color: '#1e293b' }
        }
      },
      plugins: {
        legend: { labels: { color: '#94a3b8', font: { size: 10 } } }
      }
    }
  });
}

// 4. Action Buttons Binding
function bindActionButtons() {
  document.getElementById('btnInit').addEventListener('click', bootstrapSimulation);
  document.getElementById('btnStep').addEventListener('click', advanceStep);
  document.getElementById('btnAuto').addEventListener('click', toggleAutoPlay);
  document.getElementById('btnReset').addEventListener('click', resetSimulation);
  document.getElementById('btnClearLogs').addEventListener('click', () => {
    document.getElementById('terminalLogs').innerHTML = '';
  });

  // View Switchers
  document.getElementById('btnViewMesh').addEventListener('click', () => {
    viewMode = 'mesh';
    document.getElementById('btnViewMesh').className = 'px-3 py-1 text-xs font-semibold rounded bg-cyan-600 text-white shadow';
    document.getElementById('btnViewTree').className = 'px-3 py-1 text-xs font-semibold rounded bg-slate-800 text-slate-400 hover:text-white';
    renderCytoscapeMesh();
  });

  document.getElementById('btnViewTree').addEventListener('click', () => {
    viewMode = 'tree';
    document.getElementById('btnViewTree').className = 'px-3 py-1 text-xs font-semibold rounded bg-purple-600 text-white shadow';
    document.getElementById('btnViewMesh').className = 'px-3 py-1 text-xs font-semibold rounded bg-slate-800 text-slate-400 hover:text-white';
    renderCytoscapeTree();
  });

  // Sandbox Node Selectors
  document.getElementById('selectNodeA').addEventListener('change', updateSignatureSandbox);
  document.getElementById('selectNodeB').addEventListener('change', updateSignatureSandbox);
}

// 5. Simulation Lifecycle Orchestration
async function bootstrapSimulation() {
  const payload = {
    benchmark: document.getElementById('param_benchmark')?.value || 'FMNIST (CNN)',
    num_nodes: parseInt(document.getElementById('param_n').value),
    d_limit: parseFloat(document.getElementById('param_dlimit').value),
    r_hops: parseInt(document.getElementById('param_rhops').value),
    max_zone_size: parseInt(document.getElementById('param_sz').value),
    theta: parseFloat(document.getElementById('param_theta').value),
    q: parseFloat(document.getElementById('param_q').value),
  };

  logToTerminal('INIT', `Bootstrapping Benchmark: ${payload.benchmark} | Model Family: Homogeneous | N=${payload.num_nodes}, D_limit=${payload.d_limit}...`);


  try {
    const res = await fetch('/api/v1/init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    currentSession = data.session_id;
    simulationData = data;

    document.getElementById('sessionBadge').classList.remove('hidden');
    document.getElementById('sessionVal').textContent = currentSession.substring(0, 8);
    document.getElementById('btnStep').disabled = false;
    document.getElementById('btnAuto').disabled = false;

    setPhase(1, 'Phase 1: Physical Topology (RGG) & 50D Heterogeneous Weights');
    renderCytoscapeMesh();
    populateSandboxSelects(data.nodes);
    logToTerminal('INIT', `Topology generated: ${data.nodes.length} nodes, ${data.edges.length} edges.`);
  } catch (err) {
    logToTerminal('ERROR', `Init failed: ${err}`);
  }
}

async function advanceStep() {
  if (!currentSession) return;

  switch (currentPhase) {
    case 1:
      // Execute Phase 2: VRF Leader Election
      await stepVRF();
      break;
    case 2:
      // Execute Phase 3: TTL Zone Probing & S_Z Split
      await stepZones();
      break;
    case 3:
      // Execute Phase 4: Global-P Binary Search
      await stepGlobalP();
      break;
    case 4:
      // Execute Phase 5: Signatures & Intra-Zone AP Clustering
      await stepClustering();
      break;
    case 5:
      // Execute Phase 6: Hierarchical SON Tree DAG
      await stepSONHierarchy();
      break;
    case 6:
    case 7:
      // Execute Phase 7+: Personalized FL Training Round
      await stepFLRound();
      break;
  }
}

async function stepVRF() {
  logToTerminal('VRF', 'Running VRF Leader Election within R-hop neighborhoods...');
  const res = await fetch('/api/v1/step/vrf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession })
  });
  const data = await res.json();
  simulationData.nodes = data.nodes;
  simulationData.initiators = data.initiators;

  setPhase(2, `Phase 2: VRF Leader Election (${data.initiators.length} Initiators elected)`);
  renderCytoscapeMesh();
  logToTerminal('VRF', `Elected ${data.initiators.length} INITIATOR leaders: [${data.initiators.join(', ')}]`);
}

async function stepZones() {
  logToTerminal('PROBE', 'Transmitting TTL-bounded probe packets & enforcing S_Z zone caps...');
  const res = await fetch('/api/v1/step/zones', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession })
  });
  const data = await res.json();
  simulationData.nodes = data.nodes;
  simulationData.zones = data.zones;
  simulationData.boundaries = data.boundaries;

  setPhase(3, `Phase 3: Zone Probing & Deterministic Split (${Object.keys(data.zones).length} Zones formed)`);
  renderCytoscapeMesh();
  logToTerminal('PROBE', `Formed ${Object.keys(data.zones).length} zones. Discovered ${data.boundaries.length} boundary interfaces.`);
}

async function stepGlobalP() {
  logToTerminal('CONSENSUS', 'Computing local P_i^{min} binary search & q-quantile consensus...');
  const res = await fetch('/api/v1/step/global-p', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession })
  });
  const data = await res.json();
  simulationData.global_p = data.global_p;

  setPhase(4, `Phase 4: Global-P Consensus (Global P = ${data.global_p})`);
  logToTerminal('CONSENSUS', `Consensus reached: Global P = ${data.global_p} (quantile: ${data.exact_quantile.toFixed(2)}, theta: ${data.theta})`);
}

async function stepClustering() {
  logToTerminal('SON', 'Extracting Top-P signatures & running intra-zone Affinity Propagation...');
  // 1. Signatures
  await fetch('/api/v1/step/signatures', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession })
  });

  // 2. Intra-zone Clustering
  const res = await fetch('/api/v1/step/clustering', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession, replication_factor: 2 })
  });
  const data = await res.json();
  simulationData.clusters = data.clusters;
  simulationData.nodes = data.nodes;

  setPhase(5, `Phase 5: Intra-Zone AP Clustering (${data.clusters.length} Super-Peers elected)`);
  renderCytoscapeMesh();
  updateSignatureSandbox();
  logToTerminal('SON', `Clustering complete: ${data.clusters.length} semantic clusters discovered with Super-Peers.`);
}

async function stepSONHierarchy() {
  logToTerminal('SON', 'Constructing global multi-level SON tree DAG across zones...');
  const res = await fetch('/api/v1/step/son-hierarchy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession, max_fanout: 4 })
  });
  const data = await res.json();
  simulationData.son_tree = data;

  setPhase(6, `Phase 6: Hierarchical SON Tree (Depth H = ${data.depth})`);
  // Automatically switch to tree view in Phase 6
  document.getElementById('btnViewTree').click();
  logToTerminal('SON', `Hierarchical tree finalized. Depth H=${data.depth}, Nodes: ${data.tree_nodes.length}, Edges: ${data.tree_edges.length}.`);
}

async function stepFLRound() {
  const kappa = parseFloat(document.getElementById('param_kappa').value);
  logToTerminal('FL-ROUND', `Executing Personalized FL Round (kappa=${kappa})...`);

  const res = await fetch('/api/v1/fl/step', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession, kappa: kappa })
  });
  const data = await res.json();
  handleFLRoundUpdate(data);
}

async function triggerChurn(nodeId) {
  const kappa = parseFloat(document.getElementById('param_kappa').value);
  logToTerminal('CHURN', `Injecting churn failure into Node ${nodeId}...`);

  const res = await fetch('/api/v1/fl/churn', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSession, node_id: nodeId, kappa: kappa })
  });
  const data = await res.json();
  handleFLRoundUpdate(data);

  if (data.replica_takeover) {
    logToTerminal('REPLICA TAKEOVER', `[TAKEOVER] Node ${data.replica_takeover.promoted_replica} promoted to active Super-Peer!`);
  }
}

function handleFLRoundUpdate(data) {
  simulationData.nodes = data.nodes;
  simulationData.history = data.history;

  setPhase(7, `Phase 7: Personalized FL Simulation (Round ${data.round})`);
  document.getElementById('churnBanner').classList.remove('hidden');

  // Update convergence metrics
  document.getElementById('metricSemantic').textContent = `${(data.metrics.acc_semantic * 100).toFixed(1)}%`;
  document.getElementById('metricFedavg').textContent = `${(data.metrics.acc_fedavg * 100).toFixed(1)}%`;
  document.getElementById('metricSolo').textContent = `${(data.metrics.acc_solo * 100).toFixed(1)}%`;

  // Update convergence chart
  chartConvergence.data.labels = data.history.map(h => `R${h.round}`);
  chartConvergence.data.datasets[0].data = data.history.map(h => h.acc_semantic);
  chartConvergence.data.datasets[1].data = data.history.map(h => h.acc_fedavg);
  chartConvergence.data.datasets[2].data = data.history.map(h => h.acc_solo);
  chartConvergence.update();

  if (viewMode === 'mesh') {
    renderCytoscapeMesh();
  } else {
    renderCytoscapeTree();
  }
}

// 6. Cytoscape Renderers
function renderCytoscapeMesh() {
  if (!simulationData.nodes) return;
  const elements = [];

  // Nodes
  simulationData.nodes.forEach(node => {
    let color = '#06b6d4';
    let type = 'client';

    if (node.zone_id !== null && node.zone_id !== undefined) {
      color = ZONE_COLORS[node.zone_id % ZONE_COLORS.length];
    }

    if (node.role === 'INITIATOR') type = 'initiator';
    if (node.role === 'SUPER_PEER') type = 'super_peer';
    if (node.role === 'REPLICA') type = 'replica';

    elements.push({
      group: 'nodes',
      data: {
        id: `node_${node.id}`,
        label: `${node.id}`,
        color: color,
        type: type,
        isDead: !node.alive,
        role: node.role,
        zone: node.zone_id,
        vrf: node.vrf_score,
        category: node.category_name,
        model_arch: node.model_architecture,
        benchmark: node.benchmark,
        peer_id: node.id
      },
      position: { x: node.coords.x, y: node.coords.y }
    });
  });

  // Physical Edges
  if (simulationData.edges) {
    simulationData.edges.forEach((edge, idx) => {
      elements.push({
        group: 'edges',
        data: {
          id: `edge_${idx}`,
          source: `node_${edge.source}`,
          target: `node_${edge.target}`,
          type: 'physical'
        }
      });
    });
  }

  cy.elements().remove();
  cy.add(elements);
  cy.fit(undefined, 30);
}

function renderCytoscapeTree() {
  if (!simulationData.son_tree) return;
  const treeNodes = simulationData.son_tree.tree_nodes;
  const treeEdges = simulationData.son_tree.tree_edges;

  const elements = [];

  treeNodes.forEach(n => {
    let color = '#06b6d4';
    if (n.type === 'super_peer') color = '#a855f7';
    if (n.type === 'replica') color = '#10b981';
    if (n.type === 'root') color = '#f43f5e';

    const isDead = simulationData.nodes?.find(nd => nd.id === n.peer_id)?.alive === false;

    elements.push({
      group: 'nodes',
      data: {
        id: n.id,
        label: n.label,
        type: n.type,
        color: color,
        isDead: isDead,
        category: n.category,
        peer_id: n.peer_id
      }
    });
  });

  treeEdges.forEach(e => {
    elements.push({
      group: 'edges',
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'hierarchy'
      }
    });
  });

  cy.elements().remove();
  cy.add(elements);

  cy.layout({
    name: 'breadthfirst',
    directed: true,
    roots: ['#son_root'],
    padding: 30,
    spacingFactor: 1.2
  }).run();
}

// 7. Interactive Signature Sandbox
function populateSandboxSelects(nodes) {
  const selA = document.getElementById('selectNodeA');
  const selB = document.getElementById('selectNodeB');
  if (!selA || !selB || !nodes) return;

  selA.innerHTML = '';
  selB.innerHTML = '';

  nodes.forEach((n, idx) => {
    const shortLabel = n.category_name.includes('(') ? n.category_name.split('(')[0].trim() : n.category_name;
    const optA = new Option(`Node ${n.id} [${shortLabel}]`, n.id);
    const optB = new Option(`Node ${n.id} [${shortLabel}]`, n.id);
    selA.add(optA);
    selB.add(optB);
  });

  if (nodes.length > 1) {
    selB.selectedIndex = 1;
  }
}

function updateSignatureSandbox() {
  if (!simulationData.nodes) return;
  const idA = parseInt(document.getElementById('selectNodeA').value);
  const idB = parseInt(document.getElementById('selectNodeB').value);

  const nodeA = simulationData.nodes.find(n => n.id === idA);
  const nodeB = simulationData.nodes.find(n => n.id === idB);
  if (!nodeA || !nodeB) return;

  const wA = nodeA.weights;
  const wB = nodeB.weights;

  const labelA = nodeA.category_name.includes('(') ? nodeA.category_name.split('(')[0].trim() : nodeA.category_name;
  const labelB = nodeB.category_name.includes('(') ? nodeB.category_name.split('(')[0].trim() : nodeB.category_name;

  // Chart datasets
  chartSignatures.data.datasets[0].label = `Node ${idA} (${labelA})`;
  chartSignatures.data.datasets[0].data = wA;
  chartSignatures.data.datasets[1].label = `Node ${idB} (${labelB})`;
  chartSignatures.data.datasets[1].data = wB;
  chartSignatures.update();


  // KaTeX Math Calculation
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < wA.length; i++) {
    dot += wA[i] * wB[i];
    normA += wA[i] * wA[i];
    normB += wB[i] * wB[i];
  }
  normA = Math.sqrt(normA);
  normB = Math.sqrt(normB);
  const cosSim = (normA > 0 && normB > 0) ? (dot / (normA * normB)) : 0;

  document.getElementById('valCosineSim').textContent = cosSim.toFixed(4);

  const formulaContainer = document.getElementById('katexFormula');
  if (formulaContainer && window.katex) {
    const tex = `\\text{sim}(u_{${idA}}, u_{${idB}}) = \\frac{${dot.toFixed(2)}}{${normA.toFixed(2)} \\times ${normB.toFixed(2)}} = ${cosSim.toFixed(4)}`;
    katex.render(tex, formulaContainer, { throwOnError: false });
  }
}

// 8. Helpers: UI & Terminal Logging
function setPhase(phaseNum, phaseTitle) {
  currentPhase = phaseNum;
  document.getElementById('phaseBadge').textContent = phaseTitle;

  // Highlight step in stepper list
  for (let i = 1; i <= 7; i++) {
    const li = document.getElementById(`step_${i}`);
    if (!li) continue;
    if (i < phaseNum) {
      li.className = 'p-1.5 rounded flex items-center text-emerald-400 bg-emerald-950/30 border border-emerald-500/20';
    } else if (i === phaseNum) {
      li.className = 'p-1.5 rounded flex items-center text-cyan-300 bg-cyan-950/50 border border-cyan-500/40 font-bold';
    } else {
      li.className = 'p-1.5 rounded flex items-center text-slate-400 bg-slate-900/50';
    }
  }
}

function logToTerminal(tag, message) {
  const terminal = document.getElementById('terminalLogs');
  if (!terminal) return;

  const now = new Date().toISOString().substring(11, 19);
  const div = document.createElement('div');
  div.className = 'flex items-start space-x-2';

  let tagClass = 'text-cyan-400';
  if (tag.includes('VRF')) tagClass = 'tag-vrf';
  if (tag.includes('PROBE')) tagClass = 'tag-probe';
  if (tag.includes('CONSENSUS')) tagClass = 'tag-consensus';
  if (tag.includes('SON')) tagClass = 'tag-son';
  if (tag.includes('FL')) tagClass = 'tag-fl';
  if (tag.includes('CHURN')) tagClass = 'tag-churn';
  if (tag.includes('TAKEOVER')) tagClass = 'tag-takeover';

  div.innerHTML = `
    <span class="text-slate-500">[${now}]</span>
    <span class="${tagClass}">[${tag}]</span>
    <span class="text-slate-200">${message}</span>
  `;
  terminal.appendChild(div);
  terminal.scrollTop = terminal.scrollHeight;
}

function toggleAutoPlay() {
  const btn = document.getElementById('btnAuto');
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer);
    autoPlayTimer = null;
    btn.textContent = 'Auto-Play 🔄';
    btn.classList.remove('bg-rose-600');
    btn.classList.add('bg-purple-600/80');
  } else {
    btn.textContent = 'Pause ⏸️';
    btn.classList.remove('bg-purple-600/80');
    btn.classList.add('bg-rose-600');
    autoPlayTimer = setInterval(async () => {
      await advanceStep();
    }, 1800);
  }
}

function resetSimulation() {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer);
    autoPlayTimer = null;
    document.getElementById('btnAuto').textContent = 'Auto-Play 🔄';
  }
  currentSession = null;
  currentPhase = 0;
  simulationData = {};
  cy.elements().remove();
  document.getElementById('sessionBadge').classList.add('hidden');
  document.getElementById('phaseBadge').textContent = 'PHASE 0: IDLE';
  document.getElementById('btnStep').disabled = true;
  document.getElementById('btnAuto').disabled = true;
  document.getElementById('churnBanner').classList.add('hidden');
  chartConvergence.data.labels = [];
  chartConvergence.data.datasets.forEach(ds => ds.data = []);
  chartConvergence.update();
  logToTerminal('RESET', 'Simulator reset to initial state.');
}
