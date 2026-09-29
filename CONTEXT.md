# CONTEXT.md — SemanticVisual Domain Context & Architecture

## Project Overview
**SemanticVisual** is a simulation platform and interactive visualizer for **SemanticDFL** (Decentralized Federated Learning with Semantic Clustering and Hierarchical Overlay Networks, ACM 2026).

It solves the communication bottleneck and convergence degradation of Non-IID decentralized federated learning through deterministic leader election, semantic signature extraction, Affinity Propagation meta-clustering, and a 2-Tier Semantic Overlay Network (SON).

---

## Ubiquitous Domain Vocabulary

| Term | Definition & Protocol Meaning |
|:---|:---|
| **Client / Node ($p$)** | A participating edge device in the decentralized federated learning network holding local non-IID training data. |
| **Physical Graph ($G_{phys}$)** | The underlying undirected physical connectivity graph where edges represent 1-hop wireless or Euclidean physical communication channels. |
| **VRF Score ($\sigma_p$)** | Deterministic Verifiable Random Function hash value $\sigma_p = \text{VRF}_p(\text{seed}_{e-1}) \in [0, 1)$ computed independently per node to prevent Sybil attacks. |
| **Initiator ($m_p$)** | A node elected as the leader of a physical neighborhood zone by possessing the minimum $(\sigma_q, id_q)$ tuple within its 1-hop physical neighborhood. |
| **Zone ($\mathcal{Z}_z$)** | A local partition of nodes formed via TTL-bounded `PROBE` wave flooding originating from elected Initiators. |
| **Boundary Edge / Neighbor** | A physical communication link bridging two nodes residing in distinct zones. Discovered during zone probing and reported via `NOTIFY_NEIGHBOR`. |
| **Top-$P$ Signature ($\mathbf{s}_i$)** | A compact semantic representation containing the indices (or bitmask) of the top-$P$ dominant classes in a node's local dataset. Transmitted to avoid sharing raw data. |
| **$P_{\min}^i$ & Quantile Consensus** | The minimum signature dimension required by node $i$ to achieve directional cosine similarity $\ge \theta$ ($0.70$). Global $P$ is determined by the $1-q$ ($80^{\text{th}}$ percentile) quantile consensus across initiators. |
| **Cluster Exemplar** | A representative node selected by Affinity Propagation clustering within a zone to serve as the local aggregation and routing hub for similar peers. |
| **Super-Peer** | A Tier-2 backbone routing node elected across zones to manage inter-cluster discovery and query forwarding. |
| **Semantic Overlay Network (SON)** | A 2-Tier logical overlay DAG consisting of Super-Peers (Tier 2), Cluster Exemplars (Tier 1), and Leaf Nodes. |
| **Similarity-Weighted FedAvg** | Model aggregation weighted by semantic cosine similarity $\alpha_j = \frac{\exp(\beta \cdot \text{sim}(i,j))}{\sum_k \exp(\beta \cdot \text{sim}(i,k))}$ applied during pull-based parameter synchronization. |

---

## Architectural Seams & Key Codebase Paths

```text
SemanticVisual/
├── backend/
│   ├── config.py             # Canonical 10-node CIFAR-10 storyboard topology & distributions
│   ├── engine.py             # SemanticDFLEngine algorithmic simulator (AP, VRF, FedAvg, RGG, SON)
│   ├── main.py               # FastAPI REST service & session manager
│   ├── storyboard_10nodes.py # 34-step deterministic storyboard state machine
│   └── scenario_data.json    # Static step data cache
├── frontend/
│   ├── static/
│   │   ├── app.js            # Frontend Cytoscape graph controllers & animation pipelines
│   │   ├── index.html        # Interactive simulation dashboard layout
│   │   └── style.css         # Academic & Cyberpunk HUD design tokens
│   └── templates/
│       └── index.html        # Dashboard template entrypoint
├── tests/                    # Pytest test suite (45 files, 274+ passing tests)
├── STEPS.md                  # Comprehensive 34-step protocol specification
└── HANDOFF.md                # Project handoff documentation
```

---

## Testing & Quality Assurance Conventions

- **Red-Green-Refactor Loop (TDD):** Every new protocol feature or step is verified by adding a dedicated `tests/test_step*.py` file before writing production code.
- **Test Seams:**
  - Storyboard endpoints: `client.get("/api/v1/storyboard/step/<N>")`
  - Dynamic simulation engine methods in `backend.engine.SemanticDFLEngine`
  - Frontend serialization contracts & JSON payloads.
- **Verification Command:** `pytest`
