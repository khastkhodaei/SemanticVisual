# SemanticVisual / SemanticDFL Simulator — Comprehensive Project Handoff

> **Project Name:** SemanticVisual (SemanticDFL Protocol Simulator & Interactive Visualizer)  
> **Based on:** ACM 2026 Decentralized Federated Learning with Semantic Clustering & Overlay Networks  
> **Status:** Production-Ready Simulator (34/34 Protocol Steps Implemented, 311 Passing Tests)  
> **Last Updated:** October 2026  

---

## 1. Executive Summary & Project Purpose

**SemanticVisual** is a research-grade, full-stack visualizer and distributed systems simulator implementing the **SemanticDFL** decentralized federated learning protocol.

In standard Decentralized Federated Learning (DFL), participating nodes experience significant convergence degradation when local dataset distributions are **Non-IID** (heterogeneous class distributions) and physical network bandwidth is constrained. Furthermore, naive gossip and random-walk peer matching incur high communication latency, Sybil/Byzantine vulnerabilities, and suboptimal parameter aggregation.

**SemanticDFL** solves these fundamental challenges through a **multi-phase, hierarchical semantic clustering framework**:
1. **Deterministic Initiator Election** via Verifiable Random Functions (VRF) to prevent Sybil attacks.
2. **TTL-Bounded Physical Zone Formation** and boundary discovery.
3. **Quantile Consensus & Top-P Compact Signature Extraction** to capture data semantics without leaking raw local training data.
4. **Intra-Zone & Inter-Zone Affinity Propagation (AP) Clustering** forming a 2-Tier Semantic Overlay Network (SON).
5. **Hierarchical Semantic Peer Discovery** to route model requests directly to semantically similar peers.
6. **Pull-based P2P Model Aggregation** with Cosine Similarity-Weighted Federated Averaging (FedAvg).

The **SemanticVisual** platform provides both:
- A **Deterministic 10-Node CIFAR-10 Storyboard Simulator** implementing the exact 34-step benchmark protocol from the research paper.
- A **Dynamic Random Geometric Graph (RGG) Engine** allowing customizable $N$-node networks ($N \le 500$), varying communication radii ($D_{limit}$), Byzantine fractions ($q$), and similarity thresholds ($\theta$).
- An **Interactive Cyberpunk / Academic Dashboard** featuring Cytoscape.js graph dual-views, KaTeX math rendering, animated packet-wave transmissions, and real-time Chart.js telemetry.

---

## 2. Technology Stack & Key Dependencies

### Backend Stack
- **Language & Runtime:** Python 3.10+ / Python 3.13+
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (`fastapi>=0.110.0`) with [Pydantic v2](https://docs.pydantic.dev/) (`pydantic>=2.6.0`)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (`uvicorn[standard]>=0.28.0`)
- **Scientific & ML Libraries:**
  - `numpy>=1.26.0` (vector mathematics, normalization, matrix operations)
  - `scipy>=1.12.0` (spatial metrics, distance matrices, quantile calculations)
  - `scikit-learn>=1.4.0` (Affinity Propagation clustering, cosine similarity)
  - `networkx>=3.2.0` (Random Geometric Graph generation, shortest-path multi-hop routing)
- **Testing & Quality Assurance:**
  - `pytest>=8.0.0`
  - `httpx>=0.27.0` (FastAPI TestClient)

### Frontend Stack
- **Architecture:** Vanilla JavaScript (ES6+ Modules) with Academic Paper & Cyberpunk HUD themes.
- **Styling:** Vanilla CSS design system (`frontend/static/style.css`) augmented with Tailwind CSS utility classes.
- **Graph & Topology Visualization:**
  - [Cytoscape.js](https://js.cytoscape.org/) `v3.28.1` (Interactive Canvas node-link rendering)
  - `dagre.js` & `cytoscape-dagre.js` (Hierarchical DAG layout engine for 2-Tier SON overlay)
  - Built-in layout engines (`cose`, `concentric`, `preset`, `grid`)
- **Mathematical Formula Rendering:** [KaTeX](https://katex.org/) `v0.16.9` with auto-render for LaTeX formulas.
- **Telemetry & Charts:** [Chart.js](https://www.chartjs.org/) `v4.4.1` for real-time loss, accuracy, and communication overhead tracking.
- **Offline Reliability:** Local vendor libraries in `frontend/static/vendor/` with automatic CDN fallback.

---

## 3. Directory & File Structure

```text
SemanticVisual/
├── backend/
│   ├── __init__.py                 # Package initializer
│   ├── config.py                   # Canonical 10-node CIFAR-10 storyboard topology & distributions
│   ├── engine.py                   # SemanticDFLEngine core algorithmic simulator (AP, VRF, FedAvg, RGG)
│   ├── main.py                     # FastAPI application, REST endpoints, and static file mount
│   ├── scenario_data.json          # Pre-computed step data & node distribution metadata
│   ├── storyboard_10nodes.py       # Deterministic 34-step state machine for the 10-node CIFAR-10 storyboard
│   ├── top_p_costs.py              # Pure cost model and parameter sizing calculator
│   ├── top_p_lab.py                # Standalone algorithmic engine for Top-P signature math
│   ├── top_p_router.py             # FastAPI router for Top-P Deep-Dive endpoints
│   ├── models/
│   │   ├── __init__.py             # Model package exports
│   │   ├── cifar_cnn.py            # Clean PyTorch CIFAR10CNN (2-Conv, 2-FC, 2.15M params)
│   │   └── flattening.py           # Pure deterministic parameter flattening & reconstruction
│   └── training/
│       ├── __init__.py             # Training package exports
│       └── train_cifar.py          # CIFAR-10 training & evaluation pipeline and CLI
├── frontend/
│   ├── static/
│   │   ├── app.js                  # Frontend UI state machine, Cytoscape controllers, packet animations
│   │   ├── index.html              # Interactive simulation dashboard layout
│   │   ├── style.css               # Design tokens, cyber/academic styling, custom Cytoscape styles
│   │   ├── top_p_faq.json          # Externalized, editable Q&A data source with provenance tags
│   │   ├── top_p_lab.css           # Scoped stylesheet for Top-P Deep-Dive Lab
│   │   ├── top_p_lab.html          # Interactive 5-tab Deep-Dive Lab user interface
│   │   └── vendor/                 # Local offline assets (Cytoscape, Dagre, Chart.js, KaTeX)
│   └── templates/
│       └── index.html              # Production template entrypoint
├── output/
│   └── models/
│       ├── cifar10_cnn_checkpoint.pt   # Serialized PyTorch state dictionary checkpoint
│       ├── cifar10_flat_parameters.pt  # Serialized 1D flat parameter tensor (2,156,490 float32)
│       └── model_metadata.json         # Comprehensive topology, metrics, & hyperparameter metadata
├── tests/
│   ├── __init__.py
│   ├── test_cifar_cnn.py           # Unit tests for CIFAR10CNN, flattening, and training pipeline
│   ├── test_dual_layout_switcher.py# Tests for Physical vs Overlay layout toggle
│   ├── test_phase1.py ... test_phase4.py # Phase-based integration tests
│   ├── test_step1_*.py ... test_step34_*.py # Step-by-step unit tests (34 distinct step test files)
│   ├── test_top_p_cnn_training_api.py # Integration tests for interactive CNN training endpoint
│   ├── test_top_p_cnn_ui.py        # Contract tests for Top-P CNN weights endpoint & UI slices
│   ├── test_top_p_costs.py         # Cost model analytical verification tests
│   ├── test_top_p_lab.py           # Top-P algorithmic & cosine similarity tests
│   ├── test_top_p_worked_example.py# Step-by-step numerical verification tests
│   └── test_ui_rendering.py        # Backend contract tests for UI rendering payloads
├── requirements.txt                # Python package dependencies
├── STEPS.md                        # Exhaustive specification of the 34-step protocol
└── HANDOFF.md                      # Complete project handoff documentation (this document)
```

---

## 4. The 34-Step Protocol Lifecycle

The simulation is architected as an end-to-end, 10-phase pipeline spanning 34 discrete protocol steps:

```mermaid
flowchart TD
    subgraph Phase 1: Bootstrap & Initiators
        S1[Step 1: Network Creation] --> S2[Step 2: Vector Generation]
        S2 --> S3[Step 3: VRF Score Calculation]
        S3 --> S4[Step 4: VRF Exchange & Election]
    end
    subgraph Phase 2: Distributed Zone Formation
        S4 --> S5[Step 5: PROBE Flooding TTL=1]
        S5 --> S6[Step 6: Zone Formation & Boundaries]
    end
    subgraph Phase 3: Quantile Consensus & Signatures
        S6 --> S7[Step 7: P_min Query Request]
        S7 --> S8[Step 8: Binary Search & P_min Reporting]
        S8 --> S9[Step 9: Inter-Initiator Quantile Consensus]
        S9 --> S10[Step 10: Extraction Order Broadcast P=3]
        S10 --> S11[Step 11: Top-P Signature Extraction]
    end
    subgraph Phase 4: Intra-Zone Clustering
        S11 --> S12[Step 12: Affinity Propagation Clustering]
        S12 --> S13[Step 13: Cluster Exemplar Designation]
    end
    subgraph Phase 5 & 6: Meta-Clustering & Super-Peers
        S13 --> S14[Step 14: Top-Level Initiator Election]
        S14 --> S15[Step 15: Catalog Query Dispatch]
        S15 --> S16[Step 16: Zone Catalog Response at C4]
        S16 --> S17[Step 17: Inter-Zone Meta-Clustering]
        S17 --> S18[Step 18: Super-Zone Directives Broadcast]
        S18 --> S19[Step 19: Super-Peer Designation]
    end
    subgraph Phase 7 & 8: 2-Tier SON & Sparsification
        S19 --> S20[Step 20: 2-Tier SON Dual-View]
        S20 --> S21[Step 21: Weight Sparsification P=3]
    end
    subgraph Phase 9 & 10: Discovery, Matching & FedAvg
        S21 --> S22[Step 22: Hierarchical Query Dispatch]
        S22 --> S23[Step 23: Super-Peer Query Routing]
        S23 --> S24[Step 24: Exemplar Leaf Forwarding]
        S24 --> S25[Step 25: Cosine Similarity Evaluation]
        S25 --> S26[Step 26: Similarity Reporting to Exemplars]
        S26 --> S27[Step 27: Exemplar Ranking & Dispatch]
        S27 --> S28[Step 28: Super-Peer Consolidation]
        S28 --> S29[Step 29: Top-K Match Delivery K=2]
        S29 --> S30[Step 30: P2P Pull Model Weights]
        S30 --> S31[Step 31: Sparse Buffer Ingestion]
        S31 --> S32[Step 32: Reference Model Alignment]
        S32 --> S33[Step 33: Similarity FedAvg Aggregation]
        S33 --> S34[Step 34: Round Finalization & Benchmarks]
    end
```

### Detailed Step-by-Step Overview:

| Step | Name | Primary Objective & Algorithmic Logic | Key Messages / Packets |
|:---|:---|:---|:---|
| **1** | **Network Creation** | Initialize 10 nodes (C1–C10) with canonical physical topology (undirected graph) and CIFAR-10 data distributions (10 classes). | Initial physical graph |
| **2** | **Vector Generation** | Compute 10-dimensional normalized class distribution vectors $\mathbf{w}_i \in [0,1]^{10}$ from local training data. | Local computation |
| **3** | **VRF Score Calculation** | Compute deterministic VRF hash scores $\sigma_p = \text{VRF}_p(\text{seed}_{e-1})$ per node. | Local computation |
| **4** | **VRF Exchange & Election** | 1-hop scoreboard exchange. Each node computes $m_p = \min_{q \in \mathcal{N}_1(p) \cup \{p\}} (\sigma_q, id_q)$. Initiators elected: **Node 2** ($\mathcal{Z}_1$), **Node 4** ($\mathcal{Z}_2$), **Node 8** ($\mathcal{Z}_3$). | `VRF_EXCHANGE` |
| **5** | **PROBE Flooding** | Initiators broadcast `PROBE(TTL=1, Zone_ID, Initiator_ID)`. Direct neighbors evaluate and join candidate zone. | `PROBE` (TTL=1) |
| **6** | **Zone Formation & Boundaries** | Zones finalize: $\mathcal{Z}_1 = \{1, 2\}$, $\mathcal{Z}_2 = \{3, 4, 5, 7\}$, $\mathcal{Z}_3 = \{6, 8, 9, 10\}$. Nodes discover boundary edges and notify initiators via `NOTIFY_NEIGHBOR`. | `NOTIFY_NEIGHBOR` |
| **7** | **P_min Query Request** | Initiators issue `REQ_PMIN_QUERY` to all intra-zone members to evaluate minimum signature dimension $P$. | `REQ_PMIN_QUERY` |
| **8** | **Local Binary Search** | Each node executes binary search to determine $P_{\min}^i$ such that directional semantic similarity $\ge \theta$ ($0.70$). | `REP_PMIN_QUERY` |
| **9** | **Quantile Consensus** | Initiators exchange $P_{\min}$ across boundary edges. Evaluate $1-q$ ($80^{\text{th}}$) quantile $\to$ Global Consensus $P = 3$. | `CONSENSUS_EXCHANGE` |
| **10** | **Extraction Order Broadcast** | Initiators broadcast `ORDER_EXTRACT(P=3)` to all zone members. | `ORDER_EXTRACT` |
| **11** | **Top-P Signature Extraction** | Nodes extract Top-3 class index signatures and visual bitmasks (e.g. Node 1: `{C1, C2, C3}` $\to$ `1110000000`). Transmit to initiators. | `REP_SIGNATURE` |
| **12** | **Affinity Propagation Clustering** | Initiators run Affinity Propagation on received signatures using negative Euclidean / Cosine distances to identify intra-zone clusters. | Local AP execution |
| **13** | **Exemplar Designation** | Initiators assign cluster exemplars (e.g., Node 1 in $\mathcal{Z}_1$; Nodes 3 & 4 in $\mathcal{Z}_2$; Nodes 6, 8 & 9 in $\mathcal{Z}_3$) and dispatch `ORDER_SET_EXEMPLAR`. | `ORDER_SET_EXEMPLAR` |
| **14** | **Top-Level Initiator Election** | Multi-hop VRF score reporting to central bridge Node 4 $\to$ Node 4 elected as Top-Level Initiator for Super-Zone $\mathcal{Z}_{\text{Top}}$. | `TOP_PROBE` |
| **15** | **Catalog Query Dispatch** | Node 4 dispatches `REQ_CLUSTER_CATALOG` to all zone initiators. | `REQ_CLUSTER_CATALOG` |
| **16** | **Zone Catalog Response** | Initiators return their zone cluster catalog & signatures to Node 4 via multi-hop shortest paths. | `REP_CLUSTER_CATALOG` |
| **17** | **Inter-Zone Meta-Clustering** | Node 4 builds $7 \times 7$ cluster similarity matrix and clusters exemplars into Global Super-Clusters ($\mathcal{SC}_1, \mathcal{SC}_2, \mathcal{SC}_3$). | Meta-AP clustering |
| **18** | **Super-Cluster Directives** | Node 4 broadcasts `ORDER_SET_SUPER_CLUSTERS` across the network. | `ORDER_SET_SUPER_CLUSTERS` |
| **19** | **Super-Peer Designation** | Nodes elect Tier-2 Super-Peers (Nodes 1, 4, 8) and bind cluster exemplars hierarchically. | `BIND_SUPER_PEER` |
| **20** | **2-Tier SON Dual-View** | Network switches seamlessly between Physical Topology and 2-Tier Semantic Overlay Network (SON) tree view. | Dual-layout rendering |
| **21** | **Weight Sparsification** | Clients extract Top-$P$ ($P=3$) parameter weight matrices corresponding to dominant semantic classes. | Local sparsification |
| **22** | **Hierarchical Peer Discovery** | Target nodes (e.g. Node 1) issue `QUERY_DISCOVER_PEERS` up to their Super-Peer. | `QUERY_DISCOVER_PEERS` |
| **23** | **Super-Peer Query Routing** | Super-Peer routes query across overlay backbone to relevant remote cluster exemplars. | `ROUTE_OVERLAY_QUERY` |
| **24** | **Exemplar Leaf Dispatch** | Cluster exemplars forward discovery query downward to leaf nodes. | `DISPATCH_LEAF_QUERY` |
| **25** | **Cosine Similarity Evaluation** | Leaf nodes evaluate local cosine similarity against the requesting client's signature. | Local similarity check |
| **26** | **Score Reporting** | Leaf nodes report similarity scores back up to their cluster exemplar. | `REP_SIMILARITY_SCORE` |
| **27** | **Exemplar Ranking** | Exemplars rank scores and send top candidate lists to Super-Peers. | `DISPATCH_TOP_CANDIDATES` |
| **28** | **Super-Peer Consolidation** | Super-Peers aggregate cross-cluster reports and filter top candidates globally. | `CONSOLIDATE_MATCHES` |
| **29** | **Top-K Match Delivery** | Super-Peer delivers Top-$K$ ($K=2$) best peer matches (e.g. Node 9 and Node 2 for Node 1) to requesting node. | `DELIVER_TOP_K_MATCHES` |
| **30** | **P2P Model Pull Request** | Requesting node sends direct `REQ_MODEL_WEIGHTS` to selected partner nodes. | `REQ_MODEL_WEIGHTS` |
| **31** | **Sparse Parameter Delivery** | Partners transmit sparse model weights; receiving node ingests into local buffer. | `REP_MODEL_WEIGHTS` |
| **32** | **Reference Model Construction** | Receiver aligns sparse weights and constructs semantic reference model. | Local reference creation |
| **33** | **Similarity FedAvg Aggregation** | Client computes normalized similarity weights $\alpha_j = \frac{\text{sim}(i, j)}{\sum_k \text{sim}(i, k)}$ and aggregates model parameters: $\mathbf{w}_i^{(t+1)} = \sum_j \alpha_j \mathbf{w}_j^{(t)}$. | Local FedAvg aggregation |
| **34** | **Round 1 Finalization** | Verify convergence metrics, compute round communication savings (up to 70% reduction vs dense gossip), update telemetry, and advance to Round 2. | Epoch transition commit |

---

## 5. Core Mathematical Formulations

### 1. Deterministic VRF Initiator Election
$$\sigma_p = \text{VRF}_p(\text{seed}_{e-1}) \in [0, 1)$$
$$m_p = \min_{q \in \mathcal{N}_1(p) \cup \{p\}} (\sigma_q, id_q)$$
$$\text{IsInitiator}(p) \iff (\sigma_p, id_p) == m_p$$

### 2. Directional Semantic Similarity
$$\text{Sim}_{\text{dir}}(\mathbf{w}_i, \mathbf{w}_j) = \frac{\mathbf{w}_i \cdot \mathbf{w}_j}{\|\mathbf{w}_i\|_2 \|\mathbf{w}_j\|_2} = \cos(\theta_{i, j})$$

### 3. Quantile Consensus ($1-q$ Quantile)
$$\text{Global } P = \text{Quantile}_{1-q}\left(\{ P_{\min}^i \mid i \in \mathcal{V} \}\right)$$
For $q = 0.20$ (Byzantine tolerance limit), Global $P$ is the $80^{\text{th}}$ percentile of all reported local $P_{\min}^i$.

### 4. Similarity-Weighted Federated Averaging
$$\alpha_j = \frac{\exp(\beta \cdot \text{Sim}(i, j))}{\sum_{k \in \mathcal{K}_i} \exp(\beta \cdot \text{Sim}(i, k))}, \quad \mathbf{w}_i^{(t+1)} = \sum_{j \in \mathcal{K}_i} \alpha_j \mathbf{w}_j^{(t)}$$

---

## 6. API Reference & Endpoint Specifications

### Storyboard Endpoints (Deterministic 10-Node Simulation)

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/v1/storyboard/config` | Returns global topology metadata, CIFAR-10 class maps, and node distributions. |
| `GET` | `/api/v1/storyboard/nodes` | Returns 10 nodes with initial physical coordinates, roles, and status. |
| `GET/POST` | `/api/v1/storyboard/step/{step_number}` | Returns full deterministic state, node states, packet animations, and telemetry for step $1 \le \text{step} \le 34$. |
| `GET/POST` | `/api/v1/storyboard/step/1` to `/step/34` | Dedicated per-step endpoints matching individual test assertions. |

### Dynamic RGG & Parameterized Simulation Endpoints

| Method | Endpoint | Description | Payload Schema |
|:---|:---|:---|:---|
| `POST` | `/api/v1/init` | Initialize new $N$-node RGG network | `SimulationInitRequest(num_nodes, d_limit, r_hops, max_zone_size, theta, q, benchmark)` |
| `POST` | `/api/v1/step/vrf-compute` | Compute local VRF hashes | `VRFComputeStepRequest(session_id)` |
| `POST` | `/api/v1/step/vrf-exchange` | R-Hop VRF exchange & election | `VRFExchangeStepRequest(session_id, r_hops)` |
| `POST` | `/api/v1/step/zone-probing` | TTL-bounded zone flooding | `ZoneProbingStepRequest(session_id, ttl, max_zone_size)` |
| `POST` | `/api/v1/step/global-p` | Binary search & Quantile consensus | `GlobalPStepRequest(session_id, theta, q)` |
| `POST` | `/api/v1/step/signatures` | Top-$P$ signature extraction | `SignaturesStepRequest(session_id, global_p)` |
| `POST` | `/api/v1/step/clustering` | Intra-zone Affinity Propagation | `ClusteringStepRequest(session_id, replication_factor)` |
| `POST` | `/api/v1/step/son-hierarchy` | Construct 2-Tier SON Overlay | `HierarchyStepRequest(session_id, max_fanout)` |
| `POST` | `/api/v1/fl/step` | Run 1 round of Personalized FL | `FLStepRequest(session_id, k_pull, kappa, alpha)` |
| `POST` | `/api/v1/fl/churn` | Inject node failure & failover | `FLChurnRequest(session_id, node_id)` |

---

## 7. Frontend Architecture & Visualization Engine

The visualizer dashboard (`frontend/static/app.js` and `index.html`) is structured with modular controllers:

1. **Dual-Layout Graph Controller (Cytoscape.js):**
   - **Physical Layout:** Renders 10 physical nodes with true Euclidean relative coordinates, physical communication links, and zone boundary colors.
   - **SON Overlay Layout:** Transitions nodes via Dagre hierarchical tree into Super-Peers (Tier 2, top layer), Cluster Exemplars (Tier 1, middle layer), and Leaf Clients (bottom layer).
   - **Smooth Animations:** Dynamic morphing and position tweening between views.

2. **Packet Animation & Wave Pipeline:**
   - Visualizes multi-hop and single-hop packet transmissions across edges as glowing SVG particle waves.
   - Accurately renders packet types: `PROBE`, `NOTIFY_NEIGHBOR`, `ORDER_EXTRACT`, `REQ_MODEL_WEIGHTS`, etc.

3. **Academic Detail & Step Panel:**
   - **Mathematical Formulation:** Live KaTeX formulas explaining current step equations.
   - **Execution Log:** Chronological terminal showing protocol events, cryptographic hashes, and consensus values.
   - **Interactive Node Inspector:** Click on any node to view its local data distribution pie chart, VRF score, active role, current model accuracy, and peer partners.

4. **Navigation & Playback Engine:**
   - Prev/Next step buttons, Jump-to-Step slider (1 to 34), Auto-Play with configurable speed (500ms – 3000ms), and Round Reset.

---

## 8. Test Suite & Verification

The test suite contains **314 test items** (309 passing, 5 skipped) across 49 test files covering all 34 steps, API endpoints, serialization contracts, clustering math, cost models, worked examples, CIFAR-10 CNN flattening, and UI rendering payloads.

### Running Tests
To run the complete test suite:
```bash
pytest
```

To run tests for a specific step or module:
```bash
# Run CIFAR-10 CNN, flattening & serialization tests
pytest tests/test_cifar_cnn.py

# Run Top-P CNN UI & weights endpoint tests
pytest tests/test_top_p_cnn_ui.py

# Run tests for Step 4 (Initiator Election)
pytest tests/test_step4_election.py

# Run tests for Step 20 (2-Tier Overlay Topology)
pytest tests/test_step20_overlay_topology.py

# Run tests for Step 33 (FedAvg Convergence)
pytest tests/test_step33_fedavg_convergence.py

# Run Top-P Deep-Dive tests
pytest tests/test_top_p_lab.py tests/test_top_p_costs.py tests/test_top_p_worked_example.py

# Run Dual Layout Switcher tests
pytest tests/test_dual_layout_switcher.py
```

---

## 9. Setup, Installation & Developer Runbook

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Modern web browser (Chrome, Edge, Firefox)

### Setup Instructions

1. **Clone and enter repository:**
   ```bash
   cd d:\Dev\SemanticVisual
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the FastAPI Server:**
   ```bash
   uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Open Dashboard:**
   Navigate to [http://localhost:8000/](http://localhost:8000/) in your browser.

---

## 10. Key Maintenance Notes & Future Roadmap

- **Deterministic vs Dynamic Mode:**  
  `backend/storyboard_10nodes.py` houses the deterministic 10-node CIFAR-10 storyboard state machine. `backend/engine.py` houses the general parameterized engine for arbitrary $N$. When modifying protocol behavior, update both to keep the storyboard aligned with dynamic simulations.
- **Frontend Vendor Assets:**  
  If operating in an isolated/air-gapped environment without external internet access, ensure vendor libraries in `frontend/static/vendor/` (`cytoscape.min.js`, `dagre.min.js`, `chart.umd.min.js`, `katex.min.js`) are kept up to date.
- **Future Enhancements:**
  1. **WebSocket Event Streaming:** Add bidirectional WebSockets for real-time packet-by-packet streaming on large ($N > 100$) networks.
  2. **Adversarial Byzantine Simulator:** Interactive injection of Poisoning / Sybil attacks in Step 8 to demonstrate the robustness of the $(1-q)$ Quantile Consensus algorithm.
  3. **Custom Dataset Importers:** Allow uploading CSV / NPZ feature matrices for domain-specific Non-IID benchmarks (e.g. Medical Imaging, IoT Sensors).

---
*SemanticVisual is maintained and validated against the SemanticDFL protocol standard.*

---

## 11. Top-P Deep-Dive & Worked Example Lab (add-on)

### Purpose
The **Top-P Deep-Dive** module is a self-contained, additive area within the SemanticVisual application. It implements the exact mathematical formulation of Top-$P$ signature extraction from the SemanticDFL paper (Section 3.2 and Appendix B.1), provides an interactive analytical cost calculator reproducing the ResNet-18 worked example (§3.4, Appendix D), hosts an editable Q&A reference, details the simulation scope, and provides a step-by-step concrete worked example with real numbers plugged into every formula.

### File List
- `backend/top_p_lab.py`: Standalone algorithmic engine implementing EMA importance scoring ($s = \beta \cdot s_{\text{prev}} + (1-\beta)|w|$), binary search for minimal $P$ ($\cos = \sqrt{c_P} / \|w\|_2$), discrete $(1-q)$ quantile consensus, raw masked signature extraction, and sparse cosine similarity over index intersections.
- `backend/top_p_costs.py`: Pure mathematical cost model calculating signature bytes, dense bytes, hierarchical discovery query overhead ($15$ signatures), pull + serve model transfers ($2K$ models), and round search share.
- `backend/top_p_router.py`: Dedicated FastAPI router mounted at `/api/v1/toppaper` (includes `GET /cnn-weights` inspector endpoint).
- `frontend/static/top_p_lab.html`: Interactive 5-tab user interface:
  1. **Simulation Lab:** Synthetic parameter extraction, binary search trace, quantile consensus, and full vs. sparse cosine ranking heatmap.
  2. **Top-P CNN:** Real CIFAR-10 model parameter inspector introspecting the true $M = 2,156,490$ parameter vector, dual-slice view (Head / Tail), top-magnitude parameters, and layer breakdown.
  3. **Paper Models & Savings:** Comprehensive paper cost, savings, and 16-scenario non-IID benchmark accuracy reference.
  4. **Q&A & Theory:** Searchable, categorized FAQ accordion with provenance tags.
  5. **Worked Example:** 7-step vertical stepper walkthrough with concrete substituted numbers, KaTeX formula cards, sorted $|w|$ and $\cos(P)$ charts.
- `frontend/static/top_p_lab.css`: Scoped stylesheet for the Deep-Dive Lab (design tokens, stepper cards, provenance badges, KPI cards).
- `frontend/static/top_p_faq.json`: Externalized, editable Q&A data source with explicit provenance tags (`[Paper §x]`, `[Derived]`, `[Simulator]`).
- `tests/test_top_p_lab.py`: Pytest suite for Top-P algorithmic functions and sparse cosine accuracy.
- `tests/test_top_p_costs.py`: Pytest suite verifying cost calculations against paper worked examples, schema validations, and FAQ integrity.
- `tests/test_top_p_worked_example.py`: Pytest suite verifying the exact numerical results of the 7-step worked example against `backend.top_p_lab`.
- `tests/test_top_p_cnn_ui.py`: Pytest suite verifying `GET /api/v1/toppaper/cnn-weights` contract, slice boundaries, and layer mapping.

### Route List
- `GET /api/v1/toppaper/cnn-weights`: Returns true flattened model parameters (Head, Tail, Top-K magnitude) and layer slice boundaries from `output/models/cifar10_flat_parameters.pt`.
- `POST /api/v1/toppaper/run`: Executes synthetic parameter extraction, binary search trace, quantile consensus, and full vs. sparse cosine ranking matrices.
- `POST /api/v1/toppaper/costs`: Computes communication wire sizes (in MiB reported as MB), transfer latencies at specified bandwidths, compression ratios, protocol comparison tables, and complexity breakdowns.

### How to Add a FAQ Entry
To add or update answers without modifying Python or JavaScript code:
1. Open [frontend/static/top_p_faq.json](file:///d:/Dev/SemanticVisual/frontend/static/top_p_faq.json).
2. Append a new JSON item to the array:
   ```json
   {
     "id": "my-new-question",
     "category": "Cost model",
     "q": "Your question text here?",
     "a": "Detailed factual answer with provenance tags [Paper §x].",
     "refs": ["[Paper §x]"]
   }
   ```
3. The UI will automatically render the new entry, add its category pill to the filter bar, and index it for search.

### How to Run Top-P Tests
```bash
pytest tests/test_top_p_lab.py tests/test_top_p_costs.py tests/test_top_p_worked_example.py
```

---

## 12. CIFAR-10 CNN & Parameter Flattening Pipeline

### Architectural Specification
The model architecture implements the exact 2-stage Convolutional Neural Network specified in **Section 5.1 ("Experimental Setup — Datasets and Models")** of the SemanticDFL research paper:

| Layer / Block | Component Specification | Output Shape | Parameters |
|:---|:---|:---|:---|
| **Input** | RGB 10-Class Image | `(B, 3, 32, 32)` | $0$ |
| **Conv Block 1** | `Conv2d(3, 32, kernel_size=5, padding=2)` $\to$ `ReLU()` $\to$ `MaxPool2d(2, 2)` | `(B, 32, 16, 16)` | $2,432$ ($2,400$ wt + $32$ bias) |
| **Conv Block 2** | `Conv2d(32, 64, kernel_size=5, padding=2)` $\to$ `ReLU()` $\to$ `MaxPool2d(2, 2)` | `(B, 64, 8, 8)` | $51,264$ ($51,200$ wt + $64$ bias) |
| **Flatten** | Spatial feature vector concatenation | `(B, 4096)` | $0$ |
| **Dense FC1** | `Linear(4096, 512)` $\to$ `ReLU()` $\to$ `Dropout(p=0.0)` | `(B, 512)` | $2,097,664$ ($2,097,152$ wt + $512$ bias) |
| **Dense FC2 (Head)** | `Linear(512, 10)` | `(B, 10)` | $5,130$ ($5,120$ wt + $10$ bias) |
| **Total Model** | **2 Convolutional + 2 Fully Connected Layers** | **Logits (B, 10)** | **2,156,490 (~8.63 MB FP32)** |

### Parameter Flattening & Mathematical Invariants
The flattening utility ([`backend/models/flattening.py`](file:///d:/Dev/SemanticVisual/backend/models/flattening.py)) provides pure, deterministic vector transformation routines:
1. **Canonical Parameter Order:** Parameters are strictly ordered layer-by-layer matching the theoretical model formulation:
   $$\mathbf{w} = \big[ \mathbf{w}_{\text{conv1}}, \mathbf{b}_{\text{conv1}}, \mathbf{w}_{\text{conv2}}, \mathbf{b}_{\text{conv2}}, \mathbf{w}_{\text{fc1}}, \mathbf{b}_{\text{fc1}}, \mathbf{w}_{\text{fc2}}, \mathbf{b}_{\text{fc2}} \big] \in \mathbb{R}^{2156490}$$
2. **Slice Index Mapping:** Returns explicit `{start_idx, end_idx, shape, numel}` descriptors per tensor slice, enabling exact, lossless bidirectional unflattening ([`unflatten_parameters`](file:///d:/Dev/SemanticVisual/backend/models/flattening.py#L98)).
3. **$L_2$ Norm Computation:** Automatically calculates $\|W\|_2 = \sqrt{\sum_i w_i^2}$ required for directional cosine similarity and Top-$P$ thresholding.
4. **Side-Effect Free:** Extracts parameters via `.detach().cpu().to(torch.float32)` without mutating computational graphs or in-flight gradients.

### Serialized Artifact Bundle (`output/models/`)
Executing training and flattening produces a reproducible artifact bundle:
- **`output/models/cifar10_cnn_checkpoint.pt`**: PyTorch checkpoint containing the model `state_dict`, configuration parameters, and layer topology.
- **`output/models/cifar10_flat_parameters.pt`**: 1D contiguous parameter tensor (`torch.float32`, shape `(2156490,)`) bundled with layer slices and $L_2$ norm.
- **`output/models/model_metadata.json`**: JSON metadata file containing:
  - Final training & validation accuracy and loss metrics.
  - Complete hyperparameter specification (learning rate $0.01$, batch size $64$, SGD momentum $0.9$, weight decay $10^{-4}$).
  - Canonical CIFAR-10 class-to-index mapping (`0: airplane` ... `9: truck`).
  - UTC execution timestamp and PyTorch runtime version.

### CLI Usage & Reproducibility

```bash
# 1. Train model on CIFAR-10 (standard paper parameters)
python -m backend.training.train_cifar --epochs 5 --batch-size 64 --lr 0.01 --output-dir output/models

# 2. Fast deterministic synthetic training run (for isolated CI/CD verification)
python -m backend.training.train_cifar --epochs 5 --batch-size 64 --lr 0.01 --synthetic --synthetic-samples 1024

# 3. Export flattened 1D parameter vector artifact
python -m backend.models.flattening --checkpoint output/models/cifar10_cnn_checkpoint.pt --output output/models/cifar10_flat_parameters.pt

# 4. Run automated CIFAR-10 test suite
pytest tests/test_cifar_cnn.py -v
```

