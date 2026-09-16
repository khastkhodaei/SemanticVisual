# SemanticDFL Protocol Simulation Steps

## Step 1 — Network Creation

We have a network consisting of **10 nodes (clients)**.

The nodes are connected through the following edges:
- Node 1: connected to Nodes 2 and 4
- Node 2: connected to Nodes 1 and 3
- Node 3: connected to Nodes 2, 5, 6, and 7
- Node 4: connected to Nodes 1, 5, 6, and 7
- Node 5: connected to Nodes 3, 4, 6, and 10
- Node 6: connected to Nodes 3, 4, 5, 8, and 9
- Node 7: connected to Nodes 3, 4, and 9
- Node 8: connected to Nodes 6, 9, and 10
- Node 9: connected to Nodes 6, 7, 8, and 10
- Node 10: connected to Nodes 5, 8, and 9

Each node contains **100% of its local data**, distributed among the **10 CIFAR-10 classes** as follows:

| Node | Data Distribution |
|---|---|
| Node 1 | C1: 46%, C2: 17%, C3: 37% |
| Node 2 | C1: 19%, C2: 24%, C3: 57% |
| Node 3 | C4: 34%, C5: 20%, C6: 46% |
| Node 4 | C4: 62%, C5: 21%, C6: 17% |
| Node 5 | C4: 53%, C5: 12%, C6: 35% |
| Node 6 | C7: 23%, C8: 19%, C9: 34%, C10: 24% |
| Node 7 | C7: 11%, C8: 41%, C9: 21%, C10: 27% |
| Node 8 | C4: 32%, C5: 38%, C6: 30% |
| Node 9 | C1: 45%, C2: 32%, C3: 23% |
| Node 10 | C7: 12%, C8: 43%, C9: 33%, C10: 12% |

Where:
- C1 = Airplane
- C2 = Automobile
- C3 = Bird
- C4 = Cat
- C5 = Deer
- C6 = Dog
- C7 = Frog
- C8 = Horse
- C9 = Ship
- C10 = Truck

## Step 2 — Local Training and Vector Generation

The 10 nodes perform local training using their own local CIFAR-10 data.

After local training, the class distribution of each node is converted into a normalized 10-dimensional vector:

$$\mathbf{w}_i = [C_1, C_2, C_3, C_4, C_5, C_6, C_7, C_8, C_9, C_{10}]$$

The normalized vectors are:

```text
Node 1  → [0.46, 0.17, 0.37, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
Node 2  → [0.19, 0.24, 0.57, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
Node 3  → [0.00, 0.00, 0.00, 0.34, 0.20, 0.46, 0.00, 0.00, 0.00, 0.00]
Node 4  → [0.00, 0.00, 0.00, 0.62, 0.21, 0.17, 0.00, 0.00, 0.00, 0.00]
Node 5  → [0.00, 0.00, 0.00, 0.53, 0.12, 0.35, 0.00, 0.00, 0.00, 0.00]
Node 6  → [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.23, 0.19, 0.34, 0.24]
Node 7  → [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.11, 0.41, 0.21, 0.27]
Node 8  → [0.00, 0.00, 0.00, 0.32, 0.38, 0.30, 0.00, 0.00, 0.00, 0.00]
Node 9  → [0.45, 0.32, 0.23, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
Node 10 → [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.12, 0.43, 0.33, 0.12]
```

Each vector contains 10 values, where each value corresponds to one CIFAR-10 class.
The values are normalized from percentages to the range [0, 1] and rounded to two decimal places.

## Step 3 — Local VRF Score Calculation

The paper defines the initiator selection seed score using:
$$\sigma_p = \text{VRF}_p(\text{seed}_{e-1})$$

Each node generates its local deterministic VRF score:
- Node 1: 0.1543
- Node 2: 0.0837
- Node 3: 0.2318
- Node 4: 0.0412
- Node 5: 0.3185
- Node 6: 0.4721
- Node 7: 0.3564
- Node 8: 0.0275
- Node 9: 0.2947
- Node 10: 0.4126

Each node computes its local VRF score independently. Scores are not transmitted or received in this step.

## Step 4 — 1-Hop Score Exchange, VRF Comparison & Initiator Election

Each node broadcasts its VRF score strictly to its direct 1-hop physical neighbors and collects their received scores into a local neighborhood scoreboard.

Then each node evaluates:
$$m_p = \min_{q \in \mathcal{N}_1(p) \cup \{p\}} (\sigma_q, id_q)$$

If $(\sigma_p, id_p) == m_p$, node $p$ elects itself as an **Initiator**.

Evaluation across the 10 nodes:
- Node 1 (0.1543): Neighbors [C2: 0.0837, C4: 0.0412]. Min is C4. (Candidate)
- **Node 2 (0.0837)**: Neighbors [C1: 0.1543, C3: 0.2318]. Min is C2. (🏆 **INITIATOR**)
- Node 3 (0.2318): Neighbors [C2: 0.0837, C5: 0.3185, C6: 0.4721, C7: 0.3564]. Min is C2. (Candidate)
- **Node 4 (0.0412)**: Neighbors [C1: 0.1543, C5: 0.3185, C6: 0.4721, C7: 0.3564]. Min is C4. (🏆 **INITIATOR**)
- Node 5 (0.3185): Neighbors [C3: 0.2318, C4: 0.0412, C6: 0.4721, C10: 0.4126]. Min is C4. (Candidate)
- Node 6 (0.4721): Neighbors [C3: 0.2318, C4: 0.0412, C5: 0.3185, C8: 0.0275, C9: 0.2947]. Min is C8. (Candidate)
- Node 7 (0.3564): Neighbors [C3: 0.2318, C4: 0.0412, C9: 0.2947]. Min is C4. (Candidate)
- **Node 8 (0.0275)**: Neighbors [C6: 0.4721, C9: 0.2947, C10: 0.4126]. Min is C8. (🏆 **INITIATOR**)
- Node 9 (0.2947): Neighbors [C6: 0.4721, C7: 0.3564, C8: 0.0275, C10: 0.4126]. Min is C8. (Candidate)
- Node 10 (0.4126): Neighbors [C5: 0.3185, C8: 0.0275, C9: 0.2947]. Min is C8. (Candidate)

**Result:** Exactly Nodes 2, 4, and 8 become the Initiators.

### Step 4 Visualization & Election Rules
1. **Sequence Flow:**
   - **Score Transmission:** Local VRF scores are animated traveling along the physical edges to direct 1-hop neighbors.
   - **Score Reception:** Packets arrive at neighbor nodes, populating local 1-hop scoreboards.
   - **Winner Selection:** Each node evaluates the closed-ball minimum $m_p = \min_{q \in \mathcal{N}_1(p) \cup \{p\}} (\sigma_q, id_q)$.
   - **Initiator Identification:** Nodes whose self-score matches the neighborhood minimum are crowned as Initiators.
2. **Initiator Winner Color Highlights:**
   - **Node 4:** **Dark Green** (`#166534`, border `#14532d`)
   - **Node 2:** **Dark Red** (`#991b1b`, border `#7f1d1d`)
   - **Node 8:** **Dark Yellow** (`#a16207`, border `#713f12`)
   - Non-initiator nodes remain in standard client styling.
3. **Information Box & Scoreboard Display Rules:**
   - Directly below the connected neighbors list, each client's dataset classes are displayed (`Client data classes: ...`).
   - The normalized 10D semantic vector ($\mathbf{w}_i$) is retained in the information box.
   - The breakdown table below the vector is removed in Step 4 to maintain a clean presentation with the scoreboard.
   - **Complete Score Table:** The score table in the node information box displays the VRF scores of:
     1. The selected node itself (`C{id} (Self)`).
     2. All of its direct connected neighbors.
   - **Regular Candidate Nodes:** Display all connected neighbor scores cleanly without highlighting any winner.
   - **Initiator Nodes:** If the selected node is an Initiator (Nodes 2, 4, 8):
     - Its own row in the table is highlighted in **gold** and clearly marked as **Winner**.
     - Its winning status and color (Node 4: dark green, Node 2: dark red, Node 8: dark yellow) are prominently highlighted in the status badge and election banner.
   - These connected neighbors, client data classes, and normalized vector representations remain available unchanged in all subsequent steps.

---

## Step 5 — Zone Creation via PROBE Flooding (TTL = 1)

Elected Initiators (Nodes 2, 4, and 8) initiate local zone formation by dispatching a `PROBE` packet to their 1-hop physical neighbors ($TTL = R = 1$):
$$\text{PROBE}(p, \text{TTL} = 1)$$

- **Initiator 2** sends `PROBE` to: Node 1 and Node 3.
- **Initiator 4** sends `PROBE` to: Node 1, Node 5, Node 6, and Node 7.
- **Initiator 8** sends `PROBE` to: Node 6, Node 9, and Node 10.

Peers receiving a probe from an initiator adopt that initiator's zone identity. Where overlapping probes are received, boundary interfaces between neighboring zones are recorded.

### Step 5 Visualization & Zone Formation Rules
1. **Outgoing PROBE Flooding:**
   - Directional packet animations originate from Initiators 2, 4, and 8 traveling along physical links to their 1-hop neighbors ($TTL = 1$).
2. **Zone Membership & Palettes:**
   - **Zone 2 Palette (Emerald Green - `#059669`):** Initiator 2, Member Node 3, Boundary Node 1.
   - **Zone 4 Palette (Coral / Orange - `#ea580c`):** Initiator 4, Member Nodes 5, 7, Boundary Nodes 1, 6.
   - **Zone 8 Palette (Violet / Purple - `#7c3aed`):** Initiator 8, Member Nodes 9, 10, Boundary Node 6.
   - Initiators retain their prominent crown badge (`👑`).
3. **Boundary Interfaces:**
   - **Node 1:** Receives overlapping probes from Initiator 2 and Initiator 4 ($C1 \in \mathcal{Z}_2 \cap \mathcal{Z}_4$).
   - **Node 6:** Receives overlapping probes from Initiator 4 and Initiator 8 ($C6 \in \mathcal{Z}_4 \cap \mathcal{Z}_8$).
4. **Node Inspector Modal:**
   - **Header:** `Node C{id}` | `Role: INITIATOR / CLIENT` | `Zone: {assigned_zone}`.
   - **Connected Neighbors:** `[C...]`.
   - **Client Data Classes:** Local percentage breakdown (e.g., Airplane: 46%, Automobile: 17%, Bird: 37%).
   - **Normalized Vector ($\mathbf{w}_i$):** 10-dimensional array and visual mini bar profile.
   - **VRF Score:** $\sigma_p$ value.
   - **Probe Status:** Initiator that sent the probe, received TTL, and boundary flags if applicable.

---

## Step 6 — Official Zone Formation & Inter-Zone Boundary Discovery

Following the First-Wins arrival from Step 5, clients officially adopt their winning initiator's zone identity.

### 1. Zone Allocation & Tonal Differentiation
- **Zone 2 (Leader: C2 👑):**
  - Members: Node 1, Node 3 (rendered in Zone 2 color with a slightly lighter/pastel tone).
- **Zone 4 (Leader: C4 👑):**
  - Members: Node 5, Node 6, Node 7 (rendered in Zone 4 color with a slightly lighter/pastel tone).
- **Zone 8 (Leader: C8 👑):**
  - Members: Node 9, Node 10 (rendered in Zone 8 color with a slightly lighter/pastel tone).

### 2. Dual Boundary NEIGHBOR Notifications (Algorithm 3, L17-L20)
Frontier peers that received overlapping probes in Step 5 dispatch reverse boundary announcements along their physical paths:
- **Node 1 (Frontier between Zone 2 and Zone 4):**
  - Sends a notification to **Initiator C2** introducing adjacent **Initiator C4**.
  - Sends a notification to **Initiator C4** introducing adjacent **Initiator C2**.
- **Node 6 (Frontier between Zone 4 and Zone 8):**
  - Sends a notification to **Initiator C4** introducing adjacent **Initiator C8**.
  - Sends a notification to **Initiator C8** introducing adjacent **Initiator C4**.

### 3. Initiator Boundary Knowledge (Neighbor Zones Discovered)
As a result of these notifications:
- **Initiator C2** discovers neighbor initiator: **C4**.
- **Initiator C4** discovers neighbor initiators: **C2** and **C8**.
- **Initiator C8** discovers neighbor initiator: **C4**.

### 4. Animated Packet Visualizations & Adjacency Notice Badges
- Floating particle dots travel from frontier peers back to respective zone initiators.
- Each particle dot carries a synchronous floating label (`NEIGHBOR (C4)`, `NEIGHBOR (C2)`, `NEIGHBOR (C8)`).
- Upon arrival at the destination initiator node, the floating label smoothly fades away and a subtle golden pulse flashes on the initiator node.
- All physical communication links remain clean, solid slate lines throughout the visualization.

---

## Step 7 — Initiator P_min Query Request

Each elected Zone Initiator broadcasts a lightweight `REQ_P_MIN` control packet strictly to the members of its own zone:
$$\text{REQ\_P\_MIN}(\text{target\_zone} = Z_I, \tau = 0.80)$$

- **Initiator C2 (Zone 2)** sends request to: Node 1 and Node 3.
- **Initiator C4 (Zone 4)** sends request to: Node 5, Node 6, and Node 7.
- **Initiator C8 (Zone 8)** sends request to: Node 9 and Node 10.

Peers receive the query and prepare to execute the local binary search in the next step.

---

## Step 8 — Local Binary Search & P_min^i Reporting

Each client executes a local binary search on interval $p \in [1, 10]$ on sorted absolute weights to find:
$$P_{\min}^i = \min \{ p \in [1, 10] \mid \text{QualityRatio}(\mathbf{w}_i, p) \ge 0.80 \}$$

### Evaluation Results across the 10 Nodes:
| Node | Sorted Non-Zero Weights | Ratio p=1 | Ratio p=2 | Ratio p=3 | P_min (Cosine >= 80%) | P_min (Energy >= 80%) |
|---|---|---|---|---|:---:|:---:|
| Node 1 | [0.46, 0.37, 0.17] | 74.9% | 96.1% | 100.0% | 2 | 2 |
| Node 2 (Init) | [0.57, 0.24, 0.19] | 88.1% | 95.6% | 100.0% | 1 | 2 |
| Node 3 | [0.46, 0.34, 0.20] | 75.9% | 94.4% | 100.0% | 2 | 2 |
| Node 4 (Init) | [0.62, 0.21, 0.17] | 91.7% | 96.8% | 100.0% | 1 | 2 |
| Node 5 | [0.53, 0.35, 0.12] | 82.0% | 98.3% | 100.0% | 1 | 2 |
| Node 6 | [0.34, 0.24, 0.23, 0.19] | 66.4% | 81.3% | 92.9% | 2 | 3 |
| Node 7 | [0.41, 0.27, 0.21, 0.11] | 75.2% | 90.1% | 97.9% | 2 | 3 |
| Node 8 (Init) | [0.38, 0.32, 0.30] | 65.5% | 85.6% | 100.0% | 2 | 3 |
| Node 9 | [0.45, 0.32, 0.23] | 75.2% | 92.3% | 100.0% | 2 | 3 |
| Node 10 | [0.43, 0.33, 0.12, 0.12] | 75.7% | 95.4% | 97.7% | 2 | 3 |

Each member transmits a lightweight response packet carrying its local $P_{\min}^i$ back to its zone initiator.

---

## Step 9 — Inter-Initiator Exchange via Boundary Peers & Global Consensus

Following the internal zone reporting in Step 8, each initiator holds its local zone proposal:
- **Zone 2 (Initiator C2):** Local proposed $P = 2$
- **Zone 4 (Initiator C4):** Local proposed $P = 3$
- **Zone 8 (Initiator C8):** Local proposed $P = 3$

### 1. Boundary Relay Routes (Using Adjacencies Discovered in Step 6):
Initiators exchange these values across zone boundaries using the gateway peers:
- **C2 <---> C4 route:** Messages relay through **Node 1** (Physical links: C2 <-> C1 and C1 <-> C4).
- **C4 <---> C8 route:** Messages relay through **Node 6** (Physical links: C4 <-> C6 and C6 <-> C8).

### 2. Global Quantile Consensus:
According to the protocol formula:
$$P = \min(\text{Quantile}_q(\{P_{\min}^i\}_{i \in V}), P_{\max}) = 3 \quad (q = 0.80)$$

Initiators compare the collected zone values ($[2, 3, 3]$) and take $\max(2, 3, 3) = 3$ (80th quantile across all 10 nodes).
**Result:** All three initiators reach unanimous agreement on **$P = 3$**.

---

## Step 10 — Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3)

With global consensus locked at $P = 3$, each Zone Initiator broadcasts an official directive to its members:
$$\text{ORDER\_EXTRACT}(P = 3) \quad \forall i \in Z_I$$

- **Initiator C2 (Zone 2)** sends order to: Node 1 and Node 3.
- **Initiator C4 (Zone 4)** sends order to: Node 5, Node 6, and Node 7.
- **Initiator C8 (Zone 8)** sends order to: Node 9 and Node 10.

Upon receipt, all clients lock their target signature length to $P = 3$.

---

## Step 11 — Top-P Signature Extraction with Dual Representation (Network Indices vs. Visual Bitmask)

Following the extraction order directive from Step 10 ($P = 3$), every edge peer extracts its compact model signature.
SemanticDFL introduces a fundamental distinction between the **protocol wire transmission** and the **pedagogical visualization**:

### 1. Protocol Reality (Network Wire Footprint & Privacy)
- **Zero Value / Weight Leakage:** Clients **never** transmit floating-point model weights or magnitudes ($w_{i, r}$).
- **Unweighted Integer Sets:** Each client extracts strictly the set of coordinate indices corresponding to its top-$P$ largest absolute weights:
  $$S_i = \text{Top-}P(\text{indices of } |\mathbf{w}_i|) \subset \{1, 2, \dots, 10\}$$
- **Ultra-Compact Bandwidth:** Transmitted over the wire as a lightweight array of $P$ unsigned integers:
  $$\text{Dispatched Payload} = 3 \times \text{sizeof}(\text{uint8}) = 3\text{ Bytes}$$
  In comparison, the raw vector would consume $10 \times \text{sizeof}(\text{float32}) = 40\text{ Bytes}$ ($>92.5\%$ bandwidth savings), and full neural network parameters would consume tens of megabytes.

### 2. Pedagogical Simulator Representation (Visual Bitmask)
To make sparse overlap visually intuitive, the dashboard expands each peer's transmitted integer set into an interactive 10-cell binary indicator bitmask:
$$\mathbf{m}_i = (m_{i, 1}, m_{i, 2}, \dots, m_{i, 10}) \in \{0, 1\}^{10}, \quad m_{i, c} = \begin{cases} 1 & \text{if } c \in S_i \\ 0 & \text{otherwise} \end{cases}$$

### 10-Node Extraction & Transmission Registry ($P = 3$):
| Node | Local Zone | Top-3 Active Classes ($S_i$) | Dispatched Wire Payload | 10D Binary Mask ($\mathbf{m}_i$) | Wire Size vs. Raw Vector | Destination Initiator |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Node 1 | Zone 2 | {C1, C2, C3} (Airplane, Automobile, Bird) | `[1, 2, 3]` | `[1, 1, 1, 0, 0, 0, 0, 0, 0, 0]` | 3 B vs 40 B (-92.5%) | Initiator C2 |
| Node 2 (Init) | Zone 2 | {C1, C2, C3} (Airplane, Automobile, Bird) | `[1, 2, 3]` (Local) | `[1, 1, 1, 0, 0, 0, 0, 0, 0, 0]` | Local Storage | Zone 2 Registry |
| Node 3 | Zone 2 | {C4, C5, C6} (Cat, Deer, Dog) | `[4, 5, 6]` | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | 3 B vs 40 B (-92.5%) | Initiator C2 |
| Node 4 (Init) | Zone 4 | {C4, C5, C6} (Cat, Deer, Dog) | `[4, 5, 6]` (Local) | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | Local Storage | Zone 4 Registry |
| Node 5 | Zone 4 | {C4, C5, C6} (Cat, Deer, Dog) | `[4, 5, 6]` | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | 3 B vs 40 B (-92.5%) | Initiator C4 |
| Node 6 | Zone 4 | {C7, C9, C10} (Frog, Ship, Truck) | `[7, 9, 10]` | `[0, 0, 0, 0, 0, 0, 1, 0, 1, 1]` | 3 B vs 40 B (-92.5%) | Initiator C4 |
| Node 7 | Zone 4 | {C8, C9, C10} (Horse, Ship, Truck) | `[8, 9, 10]` | `[0, 0, 0, 0, 0, 0, 0, 1, 1, 1]` | 3 B vs 40 B (-92.5%) | Initiator C4 |
| Node 8 (Init) | Zone 8 | {C4, C5, C6} (Cat, Deer, Dog) | `[4, 5, 6]` (Local) | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | Local Storage | Zone 8 Registry |
| Node 9 | Zone 8 | {C1, C2, C3} (Airplane, Automobile, Bird) | `[1, 2, 3]` | `[1, 1, 1, 0, 0, 0, 0, 0, 0, 0]` | 3 B vs 40 B (-92.5%) | Initiator C8 |
| Node 10 | Zone 8 | {C8, C9, C10} (Horse, Ship, Truck) | `[8, 9, 10]` | `[0, 0, 0, 0, 0, 0, 0, 1, 1, 1]` | 3 B vs 40 B (-92.5%) | Initiator C8 |

### Intra-Zone Dispatch & Initiator Registries:
Zone members transmit their signature packet `{"type": "TOP_P_SIG", "indices": node.top_p_indices}` inward to their elected zone initiator:
- **Initiator C2 Registry:** Holds $\{1: [1, 2, 3], 2: [1, 2, 3], 3: [4, 5, 6]\}$.
- **Initiator C4 Registry:** Holds $\{4: [4, 5, 6], 5: [4, 5, 6], 6: [7, 9, 10], 7: [8, 9, 10]\}$.
- **Initiator C8 Registry:** Holds $\{8: [4, 5, 6], 9: [1, 2, 3], 10: [8, 9, 10]\}$.

All zone signatures are successfully aggregated at initiators, primed for intra-zone semantic clustering in Step 12.

---

## Step 12 — Intra-Zone Semantic Clustering (Affinity Propagation)

Each Zone Initiator evaluates semantic similarity across its collected member signatures ($\mathbf{m}_i, \mathbf{m}_j \in \{0, 1\}^{10}$) using the Cosine Similarity metric:
$$\text{Sim}(i, j) = \frac{\mathbf{m}_i \cdot \mathbf{m}_j}{\Vert{}\mathbf{m}_i\Vert{}_2 \Vert{}\mathbf{m}_j\Vert{}_2} = \frac{\vert{}\mathbf{m}_i \cap \mathbf{m}_j\vert{}}{3}$$

Then, each Initiator executes **Affinity Propagation (AP)** clustering with preference set to the median similarity:

### Zone-Level Clustering Results:
1. **Zone 2 (Initiator C2) — Members: {C1, C2, C3}**
   - Pairwise Cosine: $\text{Sim}(1, 2) = 1.0$, $\text{Sim}(1, 3) = 0.0$, $\text{Sim}(2, 3) = 0.0$
   - **Cluster 2-A (Exemplar C2):** {Node 1, Node 2} (100% overlap on classes C1, C2, C3)
   - **Cluster 2-B (Exemplar C3):** {Node 3} (Classes C4, C5, C6)

2. **Zone 4 (Initiator C4) — Members: {C4, C5, C6, C7}**
   - Pairwise Cosine: $\text{Sim}(4, 5) = 1.0$, $\text{Sim}(6, 7) = 0.67$, all cross pairs = $0.0$
   - **Cluster 4-A (Exemplar C4):** {Node 4, Node 5} (100% overlap on classes C4, C5, C6)
   - **Cluster 4-B (Exemplar C6):** {Node 6, Node 7} (67% overlap on classes C9, C10)

3. **Zone 8 (Initiator C8) — Members: {C8, C9, C10}**
   - Pairwise Cosine: All non-diagonal similarities $= 0.0$
   - **Cluster 8-A:** {Node 8} (Classes C4, C5, C6)
   - **Cluster 8-B:** {Node 9} (Classes C1, C2, C3)
   - **Cluster 8-C:** {Node 10} (Classes C8, C9, C10)
   *(Orthogonal distribution highlights the need for inter-zone Semantic Overlay links in subsequent steps).*

---

## Step 13 — Intra-Zone Cluster Exemplar Designation & Member Assignment

Following intra-zone clustering in Step 12, each zone initiator ($C_2, C_4, C_8$) transmits directives across direct 1-hop physical links:
1. `ORDER_SET_EXEMPLAR`: Appoints designated exemplars ($C_1, C_3, C_5, C_7, C_8, C_9, C_{10}$).
2. `ORDER_ASSIGN_EXEMPLAR`: Instructs regular members ($C_2, C_4, C_6$) of their assigned cluster exemplar.

### 10-Packet Trace Ledger (Direct 1-Hop Physical Routes)
| # | Initiator | Target | Physical Edge | Packet Type | Cluster | Assigned Exemplar / Peers | Signature |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | $C_2$ | $C_1$ | `[2, 1]` | `ORDER_SET_EXEMPLAR` | 2-A | Exemplar for $\{C_1, C_2\}$ | `[1, 2, 3]` |
| 2 | $C_2$ | $C_3$ | `[2, 3]` | `ORDER_SET_EXEMPLAR` | 2-B | Exemplar for $\{C_3\}$ | `[4, 5, 6]` |
| 3 | $C_2$ | $C_2$ | `[2]` (Local) | `ORDER_ASSIGN_EXEMPLAR` | 2-A | Assigned to $C_1$ | `[1, 2, 3]` |
| 4 | $C_4$ | $C_5$ | `[4, 5]` | `ORDER_SET_EXEMPLAR` | 4-A | Exemplar for $\{C_4, C_5\}$ | `[4, 5, 6]` |
| 5 | $C_4$ | $C_7$ | `[4, 7]` | `ORDER_SET_EXEMPLAR` | 4-B | Exemplar for $\{C_6, C_7\}$ | `[8, 9, 10]` |
| 6 | $C_4$ | $C_6$ | `[4, 6]` | `ORDER_ASSIGN_EXEMPLAR` | 4-B | Assigned to $C_7$ | `[8, 9, 10]` |
| 7 | $C_4$ | $C_4$ | `[4]` (Local) | `ORDER_ASSIGN_EXEMPLAR` | 4-A | Assigned to $C_5$ | `[4, 5, 6]` |
| 8 | $C_8$ | $C_8$ | `[8]` (Local) | `ORDER_SET_EXEMPLAR` | 8-A | Exemplar for $\{C_8\}$ | `[4, 5, 6]` |
| 9 | $C_8$ | $C_9$ | `[8, 9]` | `ORDER_SET_EXEMPLAR` | 8-B | Exemplar for $\{C_9\}$ | `[1, 2, 3]` |
| 10 | $C_8$ | $C_{10}$ | `[8, 10]` | `ORDER_SET_EXEMPLAR` | 8-C | Exemplar for $\{C_{10}\}$ | `[8, 9, 10]` |

---

## Step 14 — Top-Level Initiator Election & Super-Zone Creation (Figure 3(e))

SemanticDFL employs a recursive, hierarchical zoning scheme. Following intra-zone clustering and exemplar designation, the base initiators form an abstract higher-level overlay network:
$$\mathcal{G}_{\text{init}} = (\mathcal{V}_{\text{init}}, \mathcal{E}_{\text{init}}), \quad \mathcal{V}_{\text{init}} = \{C_2, C_4, C_8\}$$
$$\mathcal{E}_{\text{init}} = \{(C_2, C_4), (C_4, C_8)\}$$

Because the initiator overlay is a line topology $C_2 \leftrightarrow C_4 \leftrightarrow C_8$, Node 4 ($C_4$) serves as the indispensable central bridge interconnecting the Western ($C_2$) and Eastern ($C_8$) clusters.

### Phase 1: Inward VRF Score Reporting to Central Bridge $C_4$
Flanking initiators transmit their local VRF scores inward along multi-hop overlay paths to central bridge $C_4$:
- **Trace 1 ($C_2 \to C_4$ via path $[2, 1, 4]$):** $C_2$ reports $\sigma_2 = 0.0837$ to $C_4$.
- **Trace 2 ($C_8 \to C_4$ via path $[8, 6, 4]$):** $C_8$ reports $\sigma_8 = 0.0275$ to $C_4$.

### Phase 2: Outward Relay of Network-Wide Scores from $C_4$
Having accumulated the scores from both endpoints, $C_4$ relays the complete scoreboard outward to guarantee full network visibility:
- **Trace 3 ($C_4 \to C_2$ via path $[4, 1, 2]$):** $C_4$ sends its own score $\sigma_4 = 0.0412$ and relays $\sigma_8 = 0.0275$ to $C_2$.
- **Trace 4 ($C_4 \to C_8$ via path $[4, 6, 8]$):** $C_4$ sends its own score $\sigma_4 = 0.0412$ and relays $\sigma_2 = 0.0837$ to $C_8$.

### Overlay VRF Scoreboards on Initiators
Following two-way score dissemination, each initiator populates an explicit Overlay Scoreboard, validating Node $C_4$'s election as the Top-Level Super-Initiator:

1. **Node 2 ($C_2$) Scoreboard:**
   | Initiator | Role / Origin | VRF Score ($\sigma$) | Election Status |
   |---|---|---|---|
   | $C_2$ | Self | $0.0837$ | Member |
   | $C_4$ | Direct Neighbor (Gateway $C_1$) | $0.0412$ | 🏆 **Elected Top-Level Initiator** |
   | $C_8$ | Relayed via $C_4$ | $0.0275$ | Member |
   *Elected Leader: $C_4$ (Central aggregation bridge).*

2. **Node 4 ($C_4$) Scoreboard (Winner):**
   | Initiator | Role / Origin | VRF Score ($\sigma$) | Election Status |
   |---|---|---|---|
   | $C_4$ | Self (Central Bridge) | $0.0412$ | 🏆 **Elected Top-Level Initiator (👑👑)** |
   | $C_2$ | Direct Neighbor West (Gateway $C_1$) | $0.0837$ | Member |
   | $C_8$ | Direct Neighbor East (Gateway $C_6$) | $0.0275$ | Member |
   *Elected Leader: $C_4$ (Self, Central Hub).*

3. **Node 8 ($C_8$) Scoreboard:**
   | Initiator | Role / Origin | VRF Score ($\sigma$) | Election Status |
   |---|---|---|---|
   | $C_8$ | Self | $0.0275$ | Member |
   | $C_4$ | Direct Neighbor (Gateway $C_6$) | $0.0412$ | 🏆 **Elected Top-Level Initiator** |
   | $C_2$ | Relayed via $C_4$ | $0.0837$ | Member |
   *Elected Leader: $C_4$ (Central aggregation bridge).*

### Phase 3: Symmetrical TOP_PROBE Broadcast from $C_4$
With consensus established across all three scoreboards, $C_4$ symmetrically broadcasts a high-level probe outward with $\text{TTL} = 1$:
$$\text{TOP\_PROBE}(C_4, \text{TTL}_{\text{top}} = 1)$$
- $C_4 \xrightarrow{\text{via } C_1} C_2$ (Westward Branch)
- $C_4 \xrightarrow{\text{via } C_6} C_8$ (Eastward Branch)

### Phase 4: Formation of Super-Zone $\mathcal{Z}_{\text{Top}}$ Rooted at Node 4
All three initiators enroll into the **Top-Level Super-Zone $\mathcal{Z}_{\text{Top}}$ (Root: $C_4$, Members: $\{C_2, C_4, C_8\}$)**, establishing the hierarchical control plane for global cluster catalog exchange in subsequent steps.

---

## Step 15 — Top-Level Catalog Query Dispatch (`REQ_CLUSTER_CATALOG`)

### Objective
Initiate the hierarchical metadata exchange across the newly formed Super-Zone $\mathcal{Z}_{\text{Top}}$. Super-Initiator $C_4$ queries base initiators ($C_2$ and $C_8$) for their intra-zone semantic cluster catalogs, including exemplar IDs, cluster memberships, and profile signatures. This step strictly models outbound query dispatch and reception at base initiators (response transmission occurs in Step 16).

### Control Packet Specification
1. **Query Message Type**: `REQ_CLUSTER_CATALOG`
2. **Root Initiator**: $C_4$ ($\sigma = 0.0412$)
3. **Dispatch Routes & Overlay Traces**:
   - **Branch West ($C_4 \to C_2$)**:
     $$\text{Packet 1}: \quad C_4 \xrightarrow{\text{physical link}} C_1 \xrightarrow{\text{physical link}} C_2$$
     - *Path*: `[4, 1, 2]`
     - *Relay Gateway*: $C_1$ (Zone 2 Boundary Bridge)
     - *Payload*: `{"type": "REQ_CLUSTER_CATALOG", "root": 4, "target_zone": 2, "scope": "INTRA_ZONE_CLUSTERS"}`
   - **Branch East ($C_4 \to C_8$)**:
     $$\text{Packet 2}: \quad C_4 \xrightarrow{\text{physical link}} C_6 \xrightarrow{\text{physical link}} C_8$$
     - *Path*: `[4, 6, 8]`
     - *Relay Gateway*: $C_6$ (Zone 4 Boundary Bridge)
     - *Payload*: `{"type": "REQ_CLUSTER_CATALOG", "root": 4, "target_zone": 8, "scope": "INTRA_ZONE_CLUSTERS"}`

### Mathematical Formulation
$$\text{REQ\_CLUSTER\_CATALOG}(C_4) \xrightarrow{\text{overlay}} \{C_2, C_8\}$$
Across the hierarchical overlay paths $\mathcal{P}(C_4, C_2) = (C_4, C_1, C_2)$ and $\mathcal{P}(C_4, C_8) = (C_4, C_6, C_8)$.

### Node States & Lifecycle in Step 15
- **Node 4 ($C_4$ — Super-Initiator)**:
  - `query_status`: `"DISPATCHED_TO_ALL_INITIATORS"`
  - `outbound_catalog_requests`: `[{"target": 2, "path": [4, 1, 2]}, {"target": 8, "path": [4, 6, 8]}]`
  - Maintains authority over Zone 4 clusters (`4-A`, `4-B`).
- **Node 2 ($C_2$ — Zone 2 Initiator)**:
  - `query_status`: `"RECEIVED_PENDING_RESPONSE"`
  - `received_catalog_query`: `{"from": 4, "path": [4, 1, 2], "type": "REQ_CLUSTER_CATALOG"}`
  - Preparing intra-zone catalog: Clusters `2-A` (Exemplar: $C_1$) & `2-B` (Exemplar: $C_3$).
- **Node 8 ($C_8$ — Zone 8 Initiator)**:
  - `query_status`: `"RECEIVED_PENDING_RESPONSE"`
  - `received_catalog_query`: `{"from": 4, "path": [4, 6, 8], "type": "REQ_CLUSTER_CATALOG"}`
  - Preparing intra-zone catalog: Clusters `8-A` (Exemplar: $C_8$), `8-B` (Exemplar: $C_9$), & `8-C` (Exemplar: $C_{10}$).
- **Member Clients ($C_1, C_3, C_5, C_6, C_7, C_9, C_{10}$)**:
  - Unaffected in local state; $C_1$ and $C_6$ serve as transparent forwarding gateways for the supervisory control packets.

---

## Step 16 — Zone Catalog Response & Signature Ingestion at C4

### Objective
Base initiators ($C_2$ and $C_8$) reply with their intra-zone cluster metadata (exemplar IDs, member lists, and 10D binary profile masks) via frontier relays ($C_1$ and $C_6$) back to Super-Initiator $C_4$. $C_4$ ingests these payloads to assemble the complete 7-cluster Global Semantic Registry.

### Physical Multi-Hop Response Routing
Control responses are transmitted strictly across existing 1-hop physical ad-hoc edges, relaying through boundary gateways toward Super-Initiator $C_4$:
- **Branch West ($C_2 \to C_1 \to C_4$)**:
  $$\text{Packet 1}: \quad C_2 \xrightarrow{\text{physical link}} C_1 \xrightarrow{\text{physical link}} C_4$$
  - *Path*: `[2, 1, 4]`
  - *Relay Gateway*: $C_1$ (Zone 2 Boundary Bridge)
  - *Type*: `REP_CLUSTER_CATALOG`
  - *Clusters Payload*:
    ```json
    [
      {"cluster_id": "2-A", "exemplar": 1, "members": [1, 2], "mask": [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]},
      {"cluster_id": "2-B", "exemplar": 3, "members": [3], "mask": [0, 0, 0, 1, 1, 1, 0, 0, 0, 0]}
    ]
    ```
- **Branch East ($C_8 \to C_6 \to C_4$)**:
  $$\text{Packet 2}: \quad C_8 \xrightarrow{\text{physical link}} C_6 \xrightarrow{\text{physical link}} C_4$$
  - *Path*: `[8, 6, 4]`
  - *Relay Gateway*: $C_6$ (Zone 4 Boundary Bridge)
  - *Type*: `REP_CLUSTER_CATALOG`
  - *Clusters Payload*:
    ```json
    [
      {"cluster_id": "8-A", "exemplar": 8, "members": [8], "mask": [0, 0, 0, 1, 1, 1, 0, 0, 0, 0]},
      {"cluster_id": "8-B", "exemplar": 9, "members": [9], "mask": [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]},
      {"cluster_id": "8-C", "exemplar": 10, "members": [10], "mask": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1]}
    ]
    ```

### Mathematical Formulation & Global Aggregation
$$\text{REP\_CATALOG}(Z_2, Z_8) \xrightarrow{\text{boundary routes}} C_4 \quad (\text{Ingests 7 Cluster Masks})$$

$$\text{GlobalRegistry}(C_4) = \text{CATALOG}(Z_2) \cup \text{CATALOG}(Z_4) \cup \text{CATALOG}(Z_8)$$

Where:
- $\text{CATALOG}(Z_2) = \{ \text{Cluster 2-A (Exemplar } C_1), \text{Cluster 2-B (Exemplar } C_3) \}$
- $\text{CATALOG}(Z_4) = \{ \text{Cluster 4-A (Exemplar } C_5), \text{Cluster 4-B (Exemplar } C_7) \}$
- $\text{CATALOG}(Z_8) = \{ \text{Cluster 8-A (Exemplar } C_8), \text{Cluster 8-B (Exemplar } C_9), \text{Cluster 8-C (Exemplar } C_{10}) \}$

### Global Semantic Cluster Registry Table at $C_4$
| Cluster ID | Zone | Exemplar Node | Member Clients | 10D Binary Profile Mask $\mathbf{m}_c$ | Dominant Semantic Categories |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2-A** | Zone 2 | $C_1$ | $\{C_1, C_2\}$ | `[1, 1, 1, 0, 0, 0, 0, 0, 0, 0]` | Airplane, Automobile, Bird |
| **2-B** | Zone 2 | $C_3$ | $\{C_3\}$ | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | Deer, Dog, Frog |
| **4-A** | Zone 4 | $C_5$ | $\{C_4, C_5\}$ | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | Deer, Dog, Frog |
| **4-B** | Zone 4 | $C_7$ | $\{C_6, C_7\}$ | `[0, 0, 0, 0, 0, 0, 1, 1, 1, 1]` | Horse, Ship, Truck |
| **8-A** | Zone 8 | $C_8$ | $\{C_8\}$ | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | Deer, Dog, Frog |
| **8-B** | Zone 8 | $C_9$ | $\{C_9\}$ | `[1, 1, 1, 0, 0, 0, 0, 0, 0, 0]` | Airplane, Automobile, Bird |
| **8-C** | Zone 8 | $C_{10}$ | $\{C_{10}\}$ | `[0, 0, 0, 0, 0, 0, 0, 1, 1, 1]` | Ship, Truck |

Total Registered Clusters: **7 Clusters**.

### Node States & Lifecycle in Step 16
- **Node 4 ($C_4$ — Super-Initiator)**:
  - `aggregation_status`: `"GLOBAL_CATALOG_ASSEMBLED"`
  - `total_registered_clusters`: `7`
  - `global_cluster_catalog`: Array of all 7 cluster records with exemplar, member list, and 10D binary profile mask.
  - Pulses with a bright cyan/gold supervisory glow upon ingesting payloads from all zones.
- **Node 2 ($C_2$ — Zone 2 Initiator)**:
  - `catalog_response_status`: `"RESPONSE_DISPATCHED"`
  - `reported_clusters`: Clusters `2-A` and `2-B`.
- **Node 8 ($C_8$ — Zone 8 Initiator)**:
  - `catalog_response_status`: `"RESPONSE_DISPATCHED"`
  - `reported_clusters`: Clusters `8-A`, `8-B`, and `8-C`.
- **Frontier Relays ($C_1, C_6$)**:
  - Forward `REP_CLUSTER_CATALOG` packets directly across physical links to $C_4$.
- **Member Nodes ($C_3, C_5, C_7, C_9, C_{10}$)**:
  - Maintain intra-zone cluster profiles, ready for inter-cluster semantic pairing and cross-zone model aggregation in subsequent phases.

---

## Step 17 — Inter-Zone Meta-Clustering & Global Super-Cluster Formation

### Objective
Super-Initiator $C_4$ evaluates the pairwise Cosine Similarity across the 7 ingested cluster profile masks to form a $7 \times 7$ similarity matrix. Using this affinity matrix, $C_4$ partitions the clusters into **3 Global Super-Clusters ($\mathcal{SC}_1, \mathcal{SC}_2, \mathcal{SC}_3$)**, linking semantically aligned nodes across disparate topological zones for global model coordination.

### Mathematical Formulation
$$S_{a, b} = \frac{|\mathbf{m}_a \cap \mathbf{m}_b|}{\|\mathbf{m}_a\|_2 \|\mathbf{m}_b\|_2} \longrightarrow S_{7 \times 7} \in [0, 1]^{7 \times 7}$$

$$S_{7 \times 7} = \frac{|\mathbf{m}_a \cap \mathbf{m}_b|}{3} \longrightarrow \{\mathcal{SC}_1, \mathcal{SC}_2, \mathcal{SC}_3\}$$

Where:
- $\mathbf{m}_a, \mathbf{m}_b \in \{0, 1\}^{10}$ are the 10-dimensional binary profile masks of clusters $a$ and $b$.
- Intra-super-cluster similarity threshold $\tau \ge 0.85$.

### 7x7 Inter-Cluster Similarity Matrix ($S_{7 \times 7}$)
The evaluated pairwise Cosine Similarities between the 7 cluster profile masks:

| Cluster | 2-A | 2-B | 4-A | 4-B | 8-A | 8-B | 8-C | Super-Cluster | Dominant Classes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2-A** | **1.000** | 0.000 | 0.000 | 0.000 | 0.000 | **1.000** | 0.000 | **$\mathcal{SC}_1$** | Classes 1, 2, 3 (Aviation & Vehicles) |
| **2-B** | 0.000 | **1.000** | **1.000** | 0.000 | **1.000** | 0.000 | 0.000 | **$\mathcal{SC}_2$** | Classes 4, 5, 6 (Animals) |
| **4-A** | 0.000 | **1.000** | **1.000** | 0.000 | **1.000** | 0.000 | 0.000 | **$\mathcal{SC}_2$** | Classes 4, 5, 6 (Animals) |
| **4-B** | 0.000 | 0.000 | 0.000 | **1.000** | 0.000 | 0.000 | **0.866** | **$\mathcal{SC}_3$** | Classes 8, 9, 10 (Heavy Transport & Amphibians) |
| **8-A** | 0.000 | **1.000** | **1.000** | 0.000 | **1.000** | 0.000 | 0.000 | **$\mathcal{SC}_2$** | Classes 4, 5, 6 (Animals) |
| **8-B** | **1.000** | 0.000 | 0.000 | 0.000 | 0.000 | **1.000** | 0.000 | **$\mathcal{SC}_1$** | Classes 1, 2, 3 (Aviation & Vehicles) |
| **8-C** | 0.000 | 0.000 | 0.000 | **0.866** | 0.000 | 0.000 | **1.000** | **$\mathcal{SC}_3$** | Classes 8, 9, 10 (Heavy Transport & Amphibians) |

### Global Super-Clusters Specification
1. **Super-Cluster 1 ($\mathcal{SC}_1$) — Aviation & Vehicles (C1–C3)**:
   - **Clusters**: `{"2-A", "8-B"}`
   - **Member Clients / Peers**: $\{C_1, C_2, C_9\}$
   - **Exemplar Nodes**: $\{C_1, C_9\}$
   - **Dominant Semantic Features**: Classes 1, 2, 3 (Airplane, Automobile, Bird)
   - **Visual Accent**: Glowing Sky Blue (`#38bdf8`)

2. **Super-Cluster 2 ($\mathcal{SC}_2$) — Animals (C4–C6)**:
   - **Clusters**: `{"2-B", "4-A", "8-A"}`
   - **Member Clients / Peers**: $\{C_3, C_4, C_5, C_8\}$
   - **Exemplar Nodes**: $\{C_3, C_5, C_8\}$
   - **Dominant Semantic Features**: Classes 4, 5, 6 (Deer, Dog, Frog)
   - **Visual Accent**: Glowing Amber/Orange (`#fbbf24`)

3. **Super-Cluster 3 ($\mathcal{SC}_3$) — Heavy Transport & Amphibians (C7–C10)**:
   - **Clusters**: `{"4-B", "8-C"}`
   - **Member Clients / Peers**: $\{C_6, C_7, C_{10}\}$
   - **Exemplar Nodes**: $\{C_7, C_{10}\}$
   - **Dominant Semantic Features**: Classes 8, 9, 10 (Horse, Ship, Truck)
   - **Visual Accent**: Glowing Violet/Magenta (`#c084fc`)

### Node States & Lifecycle in Step 17
- **Node 4 ($C_4$ — Super-Initiator)**:
  - Computes and stores the $7 \times 7$ similarity matrix `similarity_matrix_7x7`.
  - Discovers the 3 Global Super-Clusters: `super_clusters = [SC-1, SC-2, SC-3]`.
  - Belongs to $\mathcal{SC}_2$ (`assigned_super_cluster: "SC-2"`).
- **Nodes 1, 2, 9**:
  - `assigned_super_cluster`: `"SC-1"`
  - `cross_zone_semantic_peers`: Peers within $\mathcal{SC}_1$.
- **Nodes 3, 4, 5, 8**:
  - `assigned_super_cluster`: `"SC-2"`
  - `cross_zone_semantic_peers`: Peers within $\mathcal{SC}_2$.
- **Nodes 6, 7, 10**:
  - `assigned_super_cluster`: `"SC-3"`
  - `cross_zone_semantic_peers`: Peers within $\mathcal{SC}_3$.
- **Ad-Hoc Network Topology**:
  - Base physical links remain clean solid slate lines while nodes display subtle glowing hulls or aura badges indicating their cross-zone super-cluster affinities.

---

## Step 18 — Super-Zone Meta-Cluster & Super-Peer Directives Dispatch (ORDER_SET_SUPER_CLUSTERS)

### Objective
Top-Level Super-Initiator $C_4$ informs base initiators $C_2$ and $C_8$ of the 3 Global Super-Clusters, their dominant signatures, and their designated Super-Peers:
- **SC-1 (Sig: `[1, 2, 3]`)**: Designated Super-Peer is **Node 1** (governs local exemplars 1, 9).
- **SC-2 (Sig: `[4, 5, 6]`)**: Designated Super-Peer is **Node 5** (governs local exemplars 3, 5, 8).
- **SC-3 (Sig: `[8, 9, 10]`)**: Designated Super-Peer is **Node 10** (governs local exemplars 7, 10).

This step strictly transmits across the super-zone overlay backbone from $C_4 \to C_2$ (via $C_1$) and $C_4 \to C_8$ (via $C_6$). Intra-zone notification down to individual exemplars and super-peers occurs separately in Step 19.

### Mathematical Formulation
$$C_4 \xrightarrow{\text{super-zone}} \{C_2, C_8\} \quad : \quad \{\mathcal{SC}_m, \mathbf{s}_m, SP_m \in \{C_1, C_5, C_{10}\}\}$$

Where:
- $\mathcal{SC}_m$ denotes Global Super-Cluster $m \in \{1, 2, 3\}$.
- $\mathbf{s}_m$ denotes the binary profile signature of $\mathcal{SC}_m$.
- $SP_m$ denotes the designated Global Super-Peer appointed by $C_4$.

### Super-Zone Directives Ledger
| Super-Cluster | Dominant Classes | Signature | Designated Super-Peer | Governed Exemplars | Governing Initiator Zone |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **$\mathcal{SC}_1$** | Airplane, Auto, Bird (1, 2, 3) | `[1, 1, 1, 0, 0, 0, 0, 0, 0, 0]` | **Node 1 ($C_1$)** | $\{C_1, C_9\}$ | Zone 2 ($C_2$) / Zone 8 ($C_8$) |
| **$\mathcal{SC}_2$** | Cat, Deer, Dog (4, 5, 6) | `[0, 0, 0, 1, 1, 1, 0, 0, 0, 0]` | **Node 5 ($C_5$)** | $\{C_3, C_5, C_8\}$ | Zone 4 ($C_4$) / Zone 2 ($C_2$) / Zone 8 ($C_8$) |
| **$\mathcal{SC}_3$** | Horse, Ship, Truck (8, 9, 10) | `[0, 0, 0, 0, 0, 0, 0, 1, 1, 1]` | **Node 10 ($C_{10}$)** | $\{C_7, C_{10}\}$ | Zone 8 ($C_8$) / Zone 4 ($C_4$) |

### Backbone Control Packets (`ORDER_SET_SUPER_CLUSTERS`)
Super-Initiator $C_4$ dispatches two structured directives along the super-zone backbone:
1. **West Backbone Relay ($C_4 \to C_1 \to C_2$)**:
   - `path`: `[4, 1, 2]`
   - `type`: `ORDER_SET_SUPER_CLUSTERS`
   - Informs $C_2$ of all 3 Super-Clusters, signatures, and that $C_1$ is designated Super-Peer for $\mathcal{SC}_1$.
2. **East Backbone Relay ($C_4 \to C_6 \to C_8$)**:
   - `path`: `[4, 6, 8]`
   - `type`: `ORDER_SET_SUPER_CLUSTERS`
   - Informs $C_8$ of all 3 Super-Clusters, signatures, and that $C_{10}$ is designated Super-Peer for $\mathcal{SC}_3$.

### Node Lifecycle & State in Step 18
- **Node 4 ($C_4$)**: `directive_status = "SUPER_ZONE_DIRECTIVES_DISPATCHED"`.
- **Nodes 2 & 8 ($C_2, C_8$)**: `directive_status = "SUPER_ZONE_DIRECTIVES_RECEIVED"`. Ingests the 3 Super-Clusters and appointed Super-Peers.
- **Nodes 1, 3, 5, 6, 7, 9, 10**: `directive_status = "AWAITING_INTRA_ZONE_NOTIFICATION"`. Waiting for intra-zone directives from their zone initiator.


---

## Step 19 — Intra-Zone Super-Peer Designation & Exemplar Hierarchical Binding

### Objective
Base initiators ($C_2, C_4, C_8$) enforce strict **direct 1-hop physical routing** within each zone to notify their respective zone exemplars of their official Global Super-Peer appointment or hierarchical binding:
- **Zone 2 ($C_2$)**:
  - $C_2 \to C_1$ (direct physical link `[2, 1]`): `ORDER_SET_SUPER_PEER` (Super-Peer for $\mathcal{SC}_1$, subordinates: `[1, 9]`).
  - $C_2 \to C_3$ (direct physical link `[2, 3]`): `ORDER_BIND_EXEMPLAR` (bound to Super-Peer $C_5$ in $\mathcal{SC}_2$).
- **Zone 4 ($C_4$)**:
  - $C_4 \to C_5$ (direct physical link `[4, 5]`): `ORDER_SET_SUPER_PEER` (Super-Peer for $\mathcal{SC}_2$, subordinates: `[3, 5, 8]`).
  - $C_4 \to C_7$ (direct physical link `[4, 7]`): `ORDER_BIND_EXEMPLAR` (bound to Super-Peer $C_{10}$ in $\mathcal{SC}_3$).
- **Zone 8 ($C_8$)**:
  - $C_8 \to C_{10}$ (direct physical link `[8, 10]`): `ORDER_SET_SUPER_PEER` (Super-Peer for $\mathcal{SC}_3$, subordinates: `[7, 10]`).
  - $C_8 \to C_9$ (direct physical link `[8, 9]`): `ORDER_BIND_EXEMPLAR` (bound to Super-Peer $C_1$ in $\mathcal{SC}_1$).
  - $C_8$ (local self-state update `[8]`): `ORDER_BIND_EXEMPLAR` (bound to Super-Peer $C_5$ in $\mathcal{SC}_2$).

### Mathematical Formulation
$$C_{\text{init}} \xrightarrow{\text{1-hop}} e_k \quad : \quad \{\text{SUPER\_PEER}(C_1, C_5, C_{10}) \;\lor\; \text{BIND}(e_k \to SP_m)\}$$

Where:
- $C_{\text{init}} \in \{C_2, C_4, C_8\}$ denotes the governing Zone Initiator.
- $e_k$ denotes an intra-zone exemplar node identified in Step 13.
- $\text{SUPER\_PEER}(C_m)$ promotes exemplar $C_m$ to the Global Super-Peer for its respective Super-Cluster.
- $\text{BIND}(e_k \to SP_m)$ links subordinate exemplar $e_k$ directly to its designated Global Super-Peer $SP_m$.

### Intra-Zone 1-Hop Control Packet Traces
| Source | Destination | Physical Path | Control Packet Type | Super-Cluster | Payload / Directive Details |
|:---:|:---:|:---:|:---:|:---:|:---|
| $C_2$ | $C_1$ | `[2, 1]` (1-hop) | `ORDER_SET_SUPER_PEER` | $\mathcal{SC}_1$ | Designated Super-Peer; subordinates: `[1, 9]` |
| $C_2$ | $C_3$ | `[2, 3]` (1-hop) | `ORDER_BIND_EXEMPLAR` | $\mathcal{SC}_2$ | Bound to Super-Peer $C_5$ |
| $C_4$ | $C_5$ | `[4, 5]` (1-hop) | `ORDER_SET_SUPER_PEER` | $\mathcal{SC}_2$ | Designated Super-Peer; subordinates: `[3, 5, 8]` |
| $C_4$ | $C_7$ | `[4, 7]` (1-hop) | `ORDER_BIND_EXEMPLAR` | $\mathcal{SC}_3$ | Bound to Super-Peer $C_{10}$ |
| $C_8$ | $C_{10}$ | `[8, 10]` (1-hop) | `ORDER_SET_SUPER_PEER` | $\mathcal{SC}_3$ | Designated Super-Peer; subordinates: `[7, 10]` |
| $C_8$ | $C_9$ | `[8, 9]` (1-hop) | `ORDER_BIND_EXEMPLAR` | $\mathcal{SC}_1$ | Bound to Super-Peer $C_1$ |
| $C_8$ | $C_8$ | `[8]` (local) | `ORDER_BIND_EXEMPLAR` | $\mathcal{SC}_2$ | Bound to Super-Peer $C_5$ |

### Node Lifecycle & State in Step 19
- **Global Super-Peers (Nodes 1, 5, 10)**:
  - `is_super_peer`: `true`
  - `super_cluster_id`: `"SC-1"` (for Node 1), `"SC-2"` (for Node 5), `"SC-3"` (for Node 10)
  - `governed_exemplars`: `[1, 9]` (Node 1), `[3, 5, 8]` (Node 5), `[7, 10]` (Node 10)
  - `bound_super_peer`: Self (`1`, `5`, `10`)
  - `role`: `"SUPER_PEER"`
- **Subordinate Exemplars (Nodes 3, 7, 8, 9)**:
  - `is_super_peer`: `false`
  - `is_exemplar`: `true`
  - `bound_super_peer`: `5` (Node 3), `10` (Node 7), `5` (Node 8), `1` (Node 9)
  - `super_cluster_id`: `"SC-2"` (Node 3, Node 8), `"SC-3"` (Node 7), `"SC-1"` (Node 9)
  - `role`: `"EXEMPLAR"`
- **Regular Members (Nodes 2, 4, 6)**:
  - `is_super_peer`: `false`
  - `is_exemplar`: `false`
  - `bound_super_peer`: `None`
  - Represented at cluster level by local exemplar ($C_2 \to C_1$, $C_4 \to C_5$, $C_6 \to C_7$).

---

## Step 20 — 2-Tier Semantic Overlay Network (SON) Dual-View (Figure 3(f))

According to Figure 3(f) of the SemanticDFL paper, the network visualizes the complete two-tier Semantic Overlay Network (SON), isolating semantic affinity links from physical ad-hoc routing clutter. In this view, nodes represent roles across 3 horizontal tiers:

### 1. Architectural Layout (3 Horizontal Tiers with Role-Based Virtual Nodes)
- **Tier 3 (Top — Global Super-Peers)**:
  - Super-Peer 1 ($C_1$, Top-Left, $x: 220, y: 120$)
  - Super-Peer 5 ($C_5$, Top-Center, $x: 500, y: 120$)
  - Super-Peer 10 ($C_{10}$, Top-Right, $x: 780, y: 120$)
  *(No direct horizontal line between 1, 5, 10).*

- **Tier 2 (Middle — Intra-Zone Exemplars)**:
  Enclosed inside a large horizontal rose/pink oval container (`rgba(244, 63, 94, 0.12)`, border dashed):
  - From Zone 2: $C_1 (180, 280), C_3 (260, 280)$
  - From Zone 4: $C_5 (460, 280), C_7 (540, 280)$
  - From Zone 8: $C_8 (720, 280), C_9 (780, 280), C_{10} (840, 280)$

- **Tier 1 (Bottom — Base Clients Grouped into 3 Physical Zones)**:
  Rendered inside 3 horizontal colored capsule containers:
  - **Zone 2 Capsule (Warm Yellow/Gold)**: $C_1 (160), C_2 (220), C_3 (280)$ at $y: 460$
  - **Zone 4 Capsule (Light Green)**: $C_4 (420), C_5 (480), C_6 (540), C_7 (600)$ at $y: 460$
  - **Zone 8 Capsule (Light Blue)**: $C_8 (720), C_9 (780), C_{10} (840)$ at $y: 460$

### 2. Edge Connections (Strictly Matching Figure 3(f))
#### A. Bottom-to-Middle Links (Intra-Zone Clustering):
Dashed colored lines connecting bottom leaf nodes to middle exemplars:
- **Zone 2 (Yellow dashed lines)**:
  - Bottom $C_1 \to$ Middle $C_1$
  - Bottom $C_2 \to$ Middle $C_1$
  - Bottom $C_3 \to$ Middle $C_3$
- **Zone 4 (Green dashed lines)**:
  - Bottom $C_4 \to$ Middle $C_5$
  - Bottom $C_5 \to$ Middle $C_5$
  - Bottom $C_6 \to$ Middle $C_7$
  - Bottom $C_7 \to$ Middle $C_7$
- **Zone 8 (Blue dashed lines)**:
  - Bottom $C_8 \to$ Middle $C_8$
  - Bottom $C_9 \to$ Middle $C_9$
  - Bottom $C_{10} \to$ Middle $C_{10}$

#### B. Middle-to-Top Links (Inter-Zone Super-Peer Overlays):
Prominent dashed dark reddish-brown / maroon lines (`#b91c1c`, width 2.5px):
- **To Super-Peer 1**:
  - Middle $C_1 \to$ Top $C_1$ (vertical dashed)
  - Middle $C_9 \to$ Top $C_1$ (cross-diagonal dashed line from Zone 8 to Top 1)
- **To Super-Peer 5**:
  - Middle $C_3 \to$ Top $C_5$ (cross-diagonal dashed line from Zone 2 to Top 5)
  - Middle $C_5 \to$ Top $C_5$ (vertical dashed)
  - Middle $C_8 \to$ Top $C_5$ (cross-diagonal dashed line from Zone 8 to Top 5)
- **To Super-Peer 10**:
  - Middle $C_7 \to$ Top $C_{10}$ (cross-diagonal dashed line from Zone 4 to Top 10)
  - Middle $C_{10} \to$ Top $C_{10}$ (vertical dashed)

### 3. Dual-Layout Switcher
From Step 20 onward, an interactive dual-layout switcher is available in the canvas toolbar:
- **`🔀 Layout: Physical Topology`**: Original 10-node ad-hoc physical placement with visible mesh links.
- **`✨ Layout: Hierarchical Overlay (Figure 3(f))`**: Replicates Figure 3(f) with phone device silhouettes, pink exemplar oval, and 3 colored zone capsules.
- Continuous ping-pong heartbeat loop flows:
  1. Leaves in Tier 1 $\to$ Exemplars in Tier 2 (following zone colors).
  2. Exemplars in Tier 2 $\to$ Super-Peers in Tier 3 (following the maroon cross-overlay lines).
  3. Super-Peers pulse with global consensus beacon rings, then dispatch weights downward.

---

## Step 21 — Local Model Parameter Pruning & Sparse Weight Extraction ($P = 3$)

### Objective
Transition into the Federated Data Plane. Following semantic overlay construction, edge clients prepare model updates for cross-zone aggregation by pruning parameters down to top-$P$ semantic dimensions ($P = 3$).

### 1. Mathematical Formulation
Each client applies Top-$P$ sparsification ($P = 3$) by computing the Hadamard product between its local normalized model weight vector $\mathbf{w}_i$ and its binary semantic profile mask $\mathbf{m}_i$:
$$\mathbf{w}_i^{\text{sparse}} = \mathbf{w}_i \odot \mathbf{m}_i, \quad \|\mathbf{w}_i^{\text{sparse}}\|_0 \le 3$$

### 2. Client Sparsification States
For nodes possessing $>3$ non-zero dataset classes (Nodes 6, 7, and 10), non-top-3 weights are strictly pruned to $0.00$:
- **Node 1**: $\mathbf{w}_1^{\text{sparse}} = [0.46, 0.17, 0.37, 0, 0, 0, 0, 0, 0, 0]$, Active: $\{1, 2, 3\}$
- **Node 2**: $\mathbf{w}_2^{\text{sparse}} = [0.19, 0.24, 0.57, 0, 0, 0, 0, 0, 0, 0]$, Active: $\{1, 2, 3\}$
- **Node 3**: $\mathbf{w}_3^{\text{sparse}} = [0, 0, 0, 0.34, 0.20, 0.46, 0, 0, 0, 0]$, Active: $\{4, 5, 6\}$
- **Node 4**: $\mathbf{w}_4^{\text{sparse}} = [0, 0, 0, 0.62, 0.21, 0.17, 0, 0, 0, 0]$, Active: $\{4, 5, 6\}$
- **Node 5**: $\mathbf{w}_5^{\text{sparse}} = [0, 0, 0, 0.53, 0.12, 0.35, 0, 0, 0, 0]$, Active: $\{4, 5, 6\}$
- **Node 6**: $\mathbf{w}_6^{\text{sparse}} = [0, 0, 0, 0, 0, 0, 0.23, 0, 0.34, 0.24]$, Active: $\{7, 9, 10\}$ (Pruned Class 8: $0.19 \to 0.00$)
- **Node 7**: $\mathbf{w}_7^{\text{sparse}} = [0, 0, 0, 0, 0, 0, 0, 0.41, 0.21, 0.27]$, Active: $\{8, 9, 10\}$ (Pruned Class 7: $0.11 \to 0.00$)
- **Node 8**: $\mathbf{w}_8^{\text{sparse}} = [0, 0, 0, 0.32, 0.38, 0.30, 0, 0, 0, 0]$, Active: $\{4, 5, 6\}$
- **Node 9**: $\mathbf{w}_9^{\text{sparse}} = [0.45, 0.32, 0.23, 0, 0, 0, 0, 0, 0, 0]$, Active: $\{1, 2, 3\}$
- **Node 10**: $\mathbf{w}_{10}^{\text{sparse}} = [0, 0, 0, 0, 0, 0, 0, 0.43, 0.33, 0.12]$, Active: $\{8, 9, 10\}$ (Pruned Class 7: $0.12 \to 0.00$)

All nodes transition to `status: "LOCAL_SPARSE_MODEL_READY"`.

### 3. Compression & Bandwidth Efficiency
- **Raw Dense Vector**: 10 float32 values $\times$ 4 Bytes = **40 Bytes**.
- **Sparse Wire Payload**: 3 non-zero float32 values (12 Bytes) + 3 coordinate index uint8 bytes (3 Bytes) = **15 Bytes**.
- **Bandwidth Reduction**:
  $$\text{Savings} = \frac{40 - 15}{40} = 62.5\%$$

### 4. Visualization & Dual-Layout Integration
- Both **Physical View** and **Figure 3(f) View** remain active and togglable via the toolbar switcher.
- Nodes emit a warm internal neon pulse glow indicating local model parameter extraction is complete and ready for hierarchical aggregation.
- Node Inspector Modals display the interactive **Sparsification & Compression Box** comparing raw dense vectors with pruned sparse representations.

---

## Step 22 — Hierarchical Semantic Peer Search & Discovery Query

### Objective
Implement the Top-Down Semantic Search protocol over the SON hierarchy:
1. Members send `REQ_PEER_DISCOVERY` up to their local exemplars.
2. Exemplars propagate discovery queries along multi-hop underlay routes to their designated Super-Peers.
3. Super-Peers resolve and return the authorized Model Exchange Partner Sets for each Super-Cluster.
4. Animate search query pulses traveling upwards along the Figure 3(f) tree and over corresponding physical multi-hop routes.

### 1. Mathematical Formulation
Clients query Super-Peers along the overlay hierarchy to resolve authorized model exchange partner sets:
$$q_i \xrightarrow{\text{SON}} SP_m \implies \mathcal{P}_i = \{j \in \mathcal{SC}_m \mid \text{Sim}(\mathbf{m}_i, \mathbf{m}_j) \ge \tau\}$$

### 2. Search Query Packet Traces & Routing
Physical Path Ledger (Strictly Valid Step 1 Edges):
- Node 2 -> SP 1: Path `[2, 1]` (Direct 1-hop)
- Node 9 -> SP 1: Path `[9, 7, 4, 1]` (Valid edges: (9,7), (7,4), (4,1))
- Node 4 -> SP 5: Path `[4, 5]` (Direct 1-hop)
- Node 3 -> SP 5: Path `[3, 5]` (Direct 1-hop)
- Node 8 -> SP 5: Path `[8, 6, 5]` (Valid edges: (8,6), (6,5))
- Node 7 -> SP 10: Path `[7, 9, 10]` (Valid edges: (7,9), (9,10))
- Node 6 -> SP 10: Path `[6, 4, 7, 9, 10]` (Through its exemplar C7 via valid edges (6,4), (4,7), (7,9), (9,10))
- Nodes 1, 5, 10: Self-local resolution (`[1]`, `[5]`, `[10]`)

Trace Packets:
- `{"from": 2, "to": 1, "path": [2, 1], "type": "REQ_PEER_DISCOVERY", "target_sp": 1, "label": "DISCOVERY_QUERY"}`
- `{"from": 9, "to": 1, "path": [9, 7, 4, 1], "type": "REQ_PEER_DISCOVERY", "target_sp": 1, "label": "DISCOVERY_QUERY"}`
- `{"from": 4, "to": 5, "path": [4, 5], "type": "REQ_PEER_DISCOVERY", "target_sp": 5, "label": "DISCOVERY_QUERY"}`
- `{"from": 3, "to": 5, "path": [3, 5], "type": "REQ_PEER_DISCOVERY", "target_sp": 5, "label": "DISCOVERY_QUERY"}`
- `{"from": 8, "to": 5, "path": [8, 6, 5], "type": "REQ_PEER_DISCOVERY", "target_sp": 5, "label": "DISCOVERY_QUERY"}`
- `{"from": 7, "to": 10, "path": [7, 9, 10], "type": "REQ_PEER_DISCOVERY", "target_sp": 10, "label": "DISCOVERY_QUERY"}`
- `{"from": 6, "to": 10, "path": [6, 4, 7, 9, 10], "type": "REQ_PEER_DISCOVERY", "target_sp": 10, "label": "DISCOVERY_QUERY"}`

### 3. Resolved Peer States & Matchmaking
- **Nodes 1, 2, 9 (SC-1)**: `search_status: "RESOLVED"`, `federation_partners: [1, 2, 9]`, `target_classes: "1, 2, 3"`
- **Nodes 3, 4, 5, 8 (SC-2)**: `search_status: "RESOLVED"`, `federation_partners: [3, 4, 5, 8]`, `target_classes: "4, 5, 6"`
- **Nodes 6, 7, 10 (SC-3)**: `search_status: "RESOLVED"`, `federation_partners: [6, 7, 10]`, `target_classes: "8, 9, 10"`

### 4. Visualization & Inspector Modal
- **Header & Formula HUD**: Formula card displays $q_i \xrightarrow{\text{SON}} SP_m \implies \mathcal{P}_i = \{j \in \mathcal{SC}_m \mid \text{Sim}(\mathbf{m}_i, \mathbf{m}_j) \ge \tau\}$ and badge `ACTIVE PHASE: STEP 22: HIERARCHICAL SEMANTIC PEER DISCOVERY`.
- **Canvas Animations**: Search pulses travel along physical multi-hop links to Super-Peers with floating tag `DISCOVERY_QUERY`, while in Figure 3(f) view they float straight upward from Tier 1 to Tier 2 to Tier 3.
- **Inspector Modal**: Displays **Semantic Discovery Resolution** card showing matched Federation Partners, resolved target classes, and active aggregation routing paths.

---

## Step 23 — Super-Peer Semantic Query Routing to Cluster Exemplars

Super-Peers inspect ingested discovery queries from Step 22, evaluate similarity against cluster signatures ($\text{Sim} = 1.0$), and route client queries down to Tier-2 Cluster Exemplars.

### 1. Downward Forwarding Traces
- $C_1 \xrightarrow{\text{path } [1, 4, 7, 9]} C_9$: Forward query of client $C_2$ (Signature $[1, 2, 3]$)
- $C_1 \xrightarrow{\text{internal}} C_1$: Ingest queries of $C_2$ and $C_9$ locally
- $C_5 \xrightarrow{\text{path } [5, 3]} C_3$: Forward queries of clients $C_4, C_8$ (Signature $[4, 5, 6]$)
- $C_5 \xrightarrow{\text{path } [5, 6, 8]} C_8$: Forward queries of clients $C_3, C_4$ (Signature $[4, 5, 6]$)
- $C_5 \xrightarrow{\text{internal}} C_5$: Ingest queries of $C_3, C_4, C_8$ locally
- $C_{10} \xrightarrow{\text{path } [10, 9, 7]} C_7$: Forward query of client $C_6$ (Signature $[8, 9, 10]$)
- $C_{10} \xrightarrow{\text{internal}} C_{10}$: Ingest queries of $C_6$ and $C_7$ locally

### 2. Multi-Hop Forwarding Routes & Query Routing Matrix
Every Super-Peer identifies the origin client of each query, matches its signature against cluster registries, and dispatches the payload to the responsible Cluster Exemplars:

- **Super-Peer 1 (Classes 1, 2, 3 - Aviation & Vehicles)**:
  - Ingested incoming queries:
    - Node $C_2$: Signature $[1, 2, 3]$, sparse vector $[0.19, 0.24, 0.57, 0, \dots]$
    - Node $C_9$: Signature $[1, 2, 3]$, sparse vector $[0.45, 0.32, 0.23, 0, \dots]$
  - Destination Exemplars:
    - **Local Exemplar 1**: Direct local loopback registers queries of $C_2$ and $C_9$.
    - **Exemplar 9**: SP 1 relays query of $C_2$ over physical multi-hop path $[1, 4, 7, 9]$.

- **Super-Peer 5 (Classes 4, 5, 6 - Animals)**:
  - Ingested incoming queries:
    - Nodes $C_3, C_4, C_8$ with Signature $[4, 5, 6]$
  - Destination Exemplars:
    - **Local Exemplar 5**: Direct local loopback registers queries of $C_4, C_3, C_8$.
    - **Exemplar 3**: SP 5 sends queries of $C_4, C_8$ via direct underlay path $[5, 3]$.
    - **Exemplar 8**: SP 5 sends queries of $C_3, C_4$ via 2-hop path $[5, 6, 8]$.

- **Super-Peer 10 (Classes 8, 9, 10 - Heavy Transport & Amphibians)**:
  - Ingested incoming queries:
    - Nodes $C_6$ (Signature $[7, 9, 10]$) and $C_7$ (Signature $[8, 9, 10]$)
  - Destination Exemplars:
    - **Local Exemplar 10**: Direct local loopback registers queries of $C_6$ and $C_7$.
    - **Exemplar 7**: SP 10 relays query of $C_6$ over physical route $[10, 9, 7]$.

### 3. Trace Packets
```json
[
  {
    "from": 1, "to": 9, "path": [1, 4, 7, 9],
    "type": "FWD_QUERY_TO_EXEMPLAR",
    "origin_client": 2,
    "signature": [1, 2, 3],
    "sparse_vector": [0.19, 0.24, 0.57, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "label": "FWD_QUERY (C2 -> C9)"
  },
  {
    "from": 5, "to": 3, "path": [5, 3],
    "type": "FWD_QUERY_TO_EXEMPLAR",
    "origin_client": 4,
    "signature": [4, 5, 6],
    "sparse_vector": [0.0, 0.0, 0.0, 0.62, 0.21, 0.17, 0.0, 0.0, 0.0, 0.0],
    "label": "FWD_QUERY (C4 -> C3)"
  },
  {
    "from": 5, "to": 8, "path": [5, 6, 8],
    "type": "FWD_QUERY_TO_EXEMPLAR",
    "origin_client": 3,
    "signature": [4, 5, 6],
    "sparse_vector": [0.0, 0.0, 0.0, 0.34, 0.20, 0.46, 0.0, 0.0, 0.0, 0.0],
    "label": "FWD_QUERY (C3 -> C8)"
  },
  {
    "from": 10, "to": 7, "path": [10, 9, 7],
    "type": "FWD_QUERY_TO_EXEMPLAR",
    "origin_client": 6,
    "signature": [7, 9, 10],
    "sparse_vector": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.23, 0.0, 0.34, 0.24],
    "label": "FWD_QUERY (C6 -> C7)"
  }
]
```

### 4. Dual-Role Nodes & Exemplar Inboxes
- **Dual-Role Nodes (1, 5, 10)**: Operate simultaneously as Tier-3 Super-Peers (coordinating query matchmaking and dispatch) and Tier-2 Cluster Exemplars (storing loopback ingested client queries in their exemplar inbox).
- **Cluster Exemplars (1, 3, 5, 7, 8, 9, 10)**: Ingest forwarded queries into `exemplar_inboxes` containing origin client ID, forwarding Super-Peer, requested signature, 10D sparse weight vectors, and arrival paths.

### 5. Dual-View Visualizations
- **Figure 3(f) View**: Query packets travel down from Tier 3 Super-Peers along dashed lines to Tier 2 Exemplars with tag `FWD_QUERY`.
- **Physical View**: Packets traverse strictly along `[1, 4, 7, 9]`, `[5, 3]`, `[5, 6, 8]`, and `[10, 9, 7]` with tag `FWD_QUERY`.

---

## Step 24 — Cluster Exemplar Forwarding to Leaf Members (Tier 2 -> Tier 1)

Cluster Exemplars complete downward query propagation by dispatching queries and authorized cluster partner sets to base Leaf Members (Tier 2 -> Tier 1).

### 1. Exemplar-to-Leaf Dispatch Traces
- $C_1 \xrightarrow{\text{path } [1, 2]} C_2$: Delivers peer query of $C_9$ and authorized cluster list $[1, 9]$
- $C_5 \xrightarrow{\text{path } [5, 4]} C_4$: Delivers peer queries of $C_3, C_8$ and authorized cluster list $[3, 5, 8]$
- $C_7 \xrightarrow{\text{path } [7, 4, 6]} C_6$: Delivers peer query of $C_{10}$ and authorized cluster list $[7, 10]$

### 2. Multi-Hop Physical Path Traversal
Routing paths strictly adhere to valid Step 1 physical ad-hoc edges:
- **Exemplar $C_1 \to$ Leaf $C_2$**: Direct physical link $[1, 2]$ (1 hop)
- **Exemplar $C_5 \to$ Leaf $C_4$**: Direct physical link $[5, 4]$ (1 hop)
- **Exemplar $C_7 \to$ Leaf $C_6$**: Physical multi-hop route $[7, 4, 6]$ traversing gateway node $C_4$ via valid edges $(7, 4)$ and $(4, 6)$ (2 hops)

### 3. Trace Packets
```json
[
  {
    "from": 1, "to": 2, "path": [1, 2],
    "type": "FWD_QUERY_TO_LEAF",
    "origin_client": 9,
    "signature": [1, 2, 3],
    "sparse_vector": [0.45, 0.32, 0.23, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "authorized_peers": [1, 9],
    "label": "LEAF_DISPATCH (C1 -> C2)"
  },
  {
    "from": 5, "to": 4, "path": [5, 4],
    "type": "FWD_QUERY_TO_LEAF",
    "origin_client": 3,
    "signature": [4, 5, 6],
    "sparse_vector": [0.0, 0.0, 0.0, 0.34, 0.20, 0.46, 0.0, 0.0, 0.0, 0.0],
    "authorized_peers": [3, 5, 8],
    "label": "LEAF_DISPATCH (C5 -> C4)"
  },
  {
    "from": 7, "to": 6, "path": [7, 4, 6],
    "type": "FWD_QUERY_TO_LEAF",
    "origin_client": 10,
    "signature": [8, 9, 10],
    "sparse_vector": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.43, 0.33, 0.12],
    "authorized_peers": [7, 10],
    "label": "LEAF_DISPATCH (C7 -> C6)"
  }
]
```

### 4. Leaf Aggregation Inboxes & Peer States
- **Leaf $C_2$**: Ingests queries and sparse vectors of peers $C_1$ and $C_9$. Status: `FEDERATION_CLUSTER_LOCKED`.
- **Leaf $C_4$**: Ingests queries and sparse vectors of peers $C_3$, $C_5$, and $C_8$. Status: `FEDERATION_CLUSTER_LOCKED`.
- **Leaf $C_6$**: Ingests queries and sparse vectors of peers $C_7$ and $C_{10}$. Status: `FEDERATION_CLUSTER_LOCKED`.
- **Exemplars & Super-Peers (1, 3, 5, 7, 8, 9, 10)**: Status: `FEDERATION_CLUSTER_LOCKED`. Ready for reciprocal P2P parameter aggregation in Step 25.

### 5. Dual-View Visualizations
- **Figure 3(f) View**: Packets move downward from the Tier 2 Rose Oval Hub (Mid layer nodes: mid_1 -> bot_2, mid_5 -> bot_4, mid_7 -> bot_6) to the bottom Zone Capsules (Tier 1 Leaves) with tag `LEAF_DISPATCH`.
- **Physical View**: Packets traverse strictly along $[1, 2]$, $[5, 4]$, and $[7, 4, 6]$ with tag `LEAF_DISPATCH`.

---

## Step 25 — Local Semantic Cosine Similarity Evaluation

Following Step 24's query delivery, every client node evaluates the mathematical Cosine Similarity between its local sparse model vector $\mathbf{w}_i^{\text{sparse}}$ and the received peer queries $\mathbf{w}_q^{\text{sparse}}$:
$$\text{CosSim}(\mathbf{w}_i, \mathbf{w}_q) = \frac{\mathbf{w}_i^{\text{sparse}} \cdot \mathbf{w}_q^{\text{sparse}}}{\Vert{}\mathbf{w}_i^{\text{sparse}}\Vert{}_2 \Vert{}\mathbf{w}_q^{\text{sparse}}\Vert{}_2}$$

All similarity values are explicitly hardcoded from precomputed mathematics.

### 1. Hardcoded Similarity Score Registry
- **SC-1 Group**:
  - $\text{CosSim}(C_1, C_2) = 0.8531$
  - $\text{CosSim}(C_1, C_9) = 0.9429$
  - $\text{CosSim}(C_2, C_9) = 0.7581$
- **SC-2 Group**:
  - $\text{CosSim}(C_3, C_4) = 0.8076$ | $\text{CosSim}(C_3, C_5) = 0.9323$ | $\text{CosSim}(C_3, C_8) = 0.9179$
  - $\text{CosSim}(C_4, C_5) = 0.9453$ | $\text{CosSim}(C_4, C_8) = 0.8388$
  - $\text{CosSim}(C_5, C_8) = 0.8536$
- **SC-3 Group**:
  - $\text{CosSim}(C_6, C_7) = 0.5365$
  - $\text{CosSim}(C_6, C_{10}) = 0.5341$
  - $\text{CosSim}(C_7, C_{10}) = 0.9378$

### 2. Node Pairwise Evaluation Matrix
| Node | Evaluated Peer Queries | Exact Cosine Similarity | Binary Overlap | Relative Aura Rank |
| :---: | :---: | :---: | :---: | :---: |
| **C1** | $C_9$<br>$C_2$ | **0.9429**<br>**0.8531** | 1.0 (3/3)<br>1.0 (3/3) | #1 Primary<br>#2 Secondary |
| **C2** | $C_1$<br>$C_9$ | **0.8531**<br>**0.7581** | 1.0 (3/3)<br>1.0 (3/3) | #1 Primary<br>#2 Secondary |
| **C3** | $C_5$<br>$C_8$<br>$C_4$ | **0.9323**<br>**0.9179**<br>**0.8076** | 1.0 (3/3)<br>1.0 (3/3)<br>1.0 (3/3) | #1 Primary<br>#2 Secondary<br>#3 Tertiary |
| **C4** | $C_5$<br>$C_8$<br>$C_3$ | **0.9453**<br>**0.8388**<br>**0.8076** | 1.0 (3/3)<br>1.0 (3/3)<br>1.0 (3/3) | #1 Primary<br>#2 Secondary<br>#3 Tertiary |
| **C5** | $C_4$<br>$C_3$<br>$C_8$ | **0.9453**<br>**0.9323**<br>**0.8536** | 1.0 (3/3)<br>1.0 (3/3)<br>1.0 (3/3) | #1 Primary<br>#2 Secondary<br>#3 Tertiary |
| **C6** | $C_7$<br>$C_{10}$ | **0.5365**<br>**0.5341** | 0.67 (2/3)<br>0.67 (2/3) | #1 Primary<br>#2 Secondary |
| **C7** | $C_{10}$<br>$C_6$ | **0.9378**<br>**0.5365** | 1.0 (3/3)<br>0.67 (2/3) | #1 Primary<br>#2 Secondary |
| **C8** | $C_3$<br>$C_5$<br>$C_4$ | **0.9179**<br>**0.8536**<br>**0.8388** | 1.0 (3/3)<br>1.0 (3/3)<br>1.0 (3/3) | #1 Primary<br>#2 Secondary<br>#3 Tertiary |
| **C9** | $C_1$<br>$C_2$ | **0.9429**<br>**0.7581** | 1.0 (3/3)<br>1.0 (3/3) | #1 Primary<br>#2 Secondary |
| **C10** | $C_7$<br>$C_6$ | **0.9378**<br>**0.5341** | 1.0 (3/3)<br>0.67 (2/3) | #1 Primary<br>#2 Secondary |

### 3. Node State Transitions
- All 10 nodes update status to `LOCAL_SIMILARITY_EVALUATED`.
- High similarity pairs ($\text{CosSim} \ge 0.90$) establish prioritized gradient synchronization channels for Step 26.

---

## Step 26 — Upward Similarity Score Reporting to Cluster Exemplars

Clients transmit their computed Cosine Similarity scores up to their Cluster Exemplars (Tier 1 -> Tier 2).

### 1. Packet Traces (Tier 1 -> Tier 2)
- $C_2 \xrightarrow{[2, 1]} C_1$: Reports $\text{Scores}(C_2) = \{Q_1: 0.8531, Q_9: 0.7581\}$
- $C_4 \xrightarrow{[4, 5]} C_5$: Reports $\text{Scores}(C_4) = \{Q_3: 0.8076, Q_5: 0.9453, Q_8: 0.8388\}$
- $C_6 \xrightarrow{[6, 4, 7]} C_7$: Reports $\text{Scores}(C_6) = \{Q_7: 0.5365, Q_{10}: 0.5341\}$

### 2. Exemplar Score Ingestion Buffer
- Exemplars 1, 3, 5, 7, 8, 9, 10 register their own local scores into their exemplar aggregation buffer.
- Governing exemplars merge scores received from reporting members:
  - Exemplar $C_1$ ingests $C_2$ report alongside its own evaluations.
  - Exemplar $C_5$ ingests $C_4$ report alongside its own evaluations.
  - Exemplar $C_7$ ingests $C_6$ report alongside its own evaluations.

### 3. Node State Transitions
- All governing cluster exemplars update status to `ZONE_SCORES_INGESTED`.

---

## Step 27 — Exemplar Similarity Ranking & Upward Dispatch to Super-Peers

Exemplars rank candidate nodes per query by descending Cosine Similarity and forward the sorted lists up to Super-Peers (Tier 2 -> Tier 3).

### 1. Exemplar-to-Super-Peer Traces
- $C_9 \xrightarrow{[9, 7, 4, 1]} C_1$: Transmits ranked peer matches for $Q_1, Q_2$
- $C_3 \xrightarrow{[3, 5]} C_5$: Transmits ranked peer matches for $Q_4, Q_5, Q_8$
- $C_8 \xrightarrow{[8, 6, 5]} C_5$: Transmits ranked peer matches for $Q_3, Q_4, Q_5$
- $C_7 \xrightarrow{[7, 9, 10]} C_{10}$: Transmits ranked peer matches for $Q_6, Q_{10}$

### 2. Super-Peer Ingestion
- Super-Peers $C_1, C_5, C_{10}$ register their internal sorted lists directly into their Super-Peer registry.
- Ingested rankings from subordinate exemplars are buffered for cluster-wide consolidation.

### 3. Node State Transitions
- Super-Peers transition to status: `EXEMPLAR_RANKINGS_INGESTED`.

---

## Step 28 — Global Super-Peer Cross-Cluster Similarity Consolidation

Super-Peers consolidate candidate scores across all intra-cluster branches, establishing authoritative descending similarity orders for every query.

$$\mathcal{R}(q_i) = \text{SortDescending}(\{(j, \text{CosSim}(\mathbf{w}_i, \mathbf{w}_j)) \mid j \in \mathcal{SC}_m\})$$

### 1. Definitive Consolidation Tables
- **Super-Peer 1 Consolidation (SC-1)**:
  - $Q_1$: 1st: $C_9$ (0.9429), 2nd: $C_2$ (0.8531)
  - $Q_2$: 1st: $C_1$ (0.8531), 2nd: $C_9$ (0.7581)
  - $Q_9$: 1st: $C_1$ (0.9429), 2nd: $C_2$ (0.7581)
- **Super-Peer 5 Consolidation (SC-2)**:
  - $Q_3$: 1st: $C_5$ (0.9323), 2nd: $C_8$ (0.9179), 3rd: $C_4$ (0.8076)
  - $Q_4$: 1st: $C_5$ (0.9453), 2nd: $C_8$ (0.8388), 3rd: $C_3$ (0.8076)
  - $Q_5$: 1st: $C_4$ (0.9453), 2nd: $C_3$ (0.9323), 3rd: $C_8$ (0.8536)
  - $Q_8$: 1st: $C_3$ (0.9179), 2nd: $C_5$ (0.8536), 3rd: $C_4$ (0.8388)
- **Super-Peer 10 Consolidation (SC-3)**:
  - $Q_6$: 1st: $C_7$ (0.5365), 2nd: $C_{10}$ (0.5341)
  - $Q_7$: 1st: $C_{10}$ (0.9378), 2nd: $C_6$ (0.5365)
  - $Q_{10}$: 1st: $C_7$ (0.9378), 2nd: $C_6$ (0.5341)

### 2. Node State Transitions
- Super-Peers transition to status: `GLOBAL_MATCHMAKING_LOCKED`.

---

## Step 29 — Top-K Partner Match Delivery to Requesting Clients (K = 2)

Super-Peers evaluate the consolidated similarity rankings from Step 28, prune the candidate lists down to the Top-$K$ ($K = 2$) semantically nearest peers, and dispatch the finalized federation match response back to each requesting client across valid physical underlay routes.

### 1. Multi-Hop Response Dispatch Traces (Strict Step 1 Physical Edges)
- $C_1 \xrightarrow{[1, 2]} C_2$: Resolves Top-2 partners $\{C_9 (0.9429), C_1 (0.8531)\}$
- $C_1 \xrightarrow{[1, 4, 7, 9]} C_9$: Resolves Top-2 partners $\{C_1 (0.9429), C_2 (0.7581)\}$
- $C_1 \xrightarrow{\text{local}} C_1$: Self-resolves Top-2 partners $\{C_9 (0.9429), C_2 (0.8531)\}$
- $C_5 \xrightarrow{[5, 3]} C_3$: Resolves Top-2 partners $\{C_5 (0.9323), C_8 (0.9179)\}$
- $C_5 \xrightarrow{[5, 4]} C_4$: Resolves Top-2 partners $\{C_5 (0.9453), C_8 (0.8388)\}$
- $C_5 \xrightarrow{[5, 6, 8]} C_8$: Resolves Top-2 partners $\{C_3 (0.9179), C_5 (0.8536)\}$
- $C_5 \xrightarrow{\text{local}} C_5$: Self-resolves Top-2 partners $\{C_4 (0.9453), C_3 (0.9323)\}$
- $C_{10} \xrightarrow{[10, 9, 7, 4, 6]} C_6$: Resolves Top-2 partners $\{C_7 (0.5365), C_{10} (0.5341)\}$
- $C_{10} \xrightarrow{[10, 9, 7]} C_7$: Resolves Top-2 partners $\{C_{10} (0.9378), C_6 (0.5365)\}$
- $C_{10} \xrightarrow{\text{local}} C_{10}$: Self-resolves Top-2 partners $\{C_7 (0.9378), C_6 (0.5341)\}$

### 2. Final Node Locked Partner State
- Every client receives their resolved Top-2 partners and locks their federation configuration:
  - $C_1$: $\{C_9 (0.9429), C_2 (0.8531)\}$
  - $C_2$: $\{C_9 (0.9429), C_1 (0.8531)\}$
  - $C_3$: $\{C_5 (0.9323), C_8 (0.9179)\}$
  - $C_4$: $\{C_5 (0.9453), C_8 (0.8388)\}$
  - $C_5$: $\{C_4 (0.9453), C_3 (0.9323)\}$
  - $C_6$: $\{C_7 (0.5365), C_{10} (0.5341)\}$
  - $C_7$: $\{C_{10} (0.9378), C_6 (0.5365)\}$
  - $C_8$: $\{C_3 (0.9179), C_5 (0.8536)\}$
  - $C_9$: $\{C_1 (0.9429), C_2 (0.7581)\}$
  - $C_{10}$: $\{C_7 (0.9378), C_6 (0.5341)\}$
- All 10 nodes transition to status: `FEDERATION_PARTNERS_LOCKED`.

---

## Step 30 — Pull-Based P2P Model Request Dispatch (REQ_MODEL_WEIGHTS)

Each client initiates decentralized model exchange by dispatching `REQ_MODEL_WEIGHTS` packets to its Top-2 locked federation partners across valid physical underlay paths.

### 1. Request Routing Ledger
- $C_1 \to C_9$ via $[1, 4, 7, 9]$ & $C_1 \to C_2$ via $[1, 2]$
- $C_2 \to C_9$ via $[2, 1, 4, 7, 9]$ & $C_2 \to C_1$ via $[2, 1]$
- $C_3 \to C_5$ via $[3, 5]$ & $C_3 \to C_8$ via $[3, 6, 8]$
- $C_4 \to C_5$ via $[4, 5]$ & $C_4 \to C_8$ via $[4, 6, 8]$
- $C_5 \to C_4$ via $[5, 4]$ & $C_5 \to C_3$ via $[5, 3]$
- $C_6 \to C_7$ via $[6, 4, 7]$ & $C_6 \to C_{10}$ via $[6, 8, 10]$
- $C_7 \to C_{10}$ via $[7, 9, 10]$ & $C_7 \to C_6$ via $[7, 4, 6]$
- $C_8 \to C_3$ via $[8, 6, 3]$ & $C_8 \to C_5$ via $[8, 6, 5]$
- $C_9 \to C_1$ via $[9, 7, 4, 1]$ & $C_9 \to C_2$ via $[9, 7, 4, 1, 2]$
- $C_{10} \to C_7$ via $[10, 9, 7]$ & $C_{10} \to C_6$ via $[10, 8, 6]$

### 2. Node State Transitions
- All 10 nodes transition to status: `DISPATCHED_MODEL_REQUESTS`.

---

## Step 31 — Sparse Parameter Delivery & Local Buffer Ingestion (REP_MODEL_WEIGHTS)

Requested peers reply with their Top-P sparsified model parameters (15-byte payload). Every client collects its partners' vectors into a dedicated local aggregation buffer.

### 1. Model Response Delivery Ledger
- $C_9 \to C_1$ via $[9, 7, 4, 1]$ & $C_2 \to C_1$ via $[2, 1]$
- $C_9 \to C_2$ via $[9, 7, 4, 1, 2]$ & $C_1 \to C_2$ via $[1, 2]$
- $C_5 \to C_3$ via $[5, 3]$ & $C_8 \to C_3$ via $[8, 6, 3]$
- $C_5 \to C_4$ via $[5, 4]$ & $C_8 \to C_4$ via $[8, 6, 4]$
- $C_4 \to C_5$ via $[4, 5]$ & $C_3 \to C_5$ via $[3, 5]$
- $C_7 \to C_6$ via $[7, 4, 6]$ & $C_{10} \to C_6$ via $[10, 8, 6]$
- $C_{10} \to C_7$ via $[10, 9, 7]$ & $C_6 \to C_7$ via $[6, 4, 7]$
- $C_3 \to C_8$ via $[3, 6, 8]$ & $C_5 \to C_8$ via $[5, 6, 8]$
- $C_1 \to C_9$ via $[1, 4, 7, 9]$ & $C_2 \to C_9$ via $[2, 1, 4, 7, 9]$
- $C_7 \to C_{10}$ via $[7, 9, 10]$ & $C_6 \to C_{10}$ via $[6, 8, 10]$

### 2. Local Memory Buffer State
- Each node $C_i$ stores its own local sparse vector $\mathbf{w}_i^{\text{sparse}}$ and the two incoming partner vectors $\mathbf{w}_{p_1}^{\text{sparse}}, \mathbf{w}_{p_2}^{\text{sparse}}$ in its dedicated local buffer $\mathcal{B}_i$.
- Payload size per packet: 15 Bytes (3 non-zero floats + dimension indices).
- All 10 nodes transition to status: `LOCAL_BUFFER_INGESTED` with buffer state `BUFFER_READY_FOR_ALIGNMENT`.

---

## Step 32 — Reference Model Construction & Similarity Weight Alignment

Each client calculates similarity-weighted influence coefficients ($\alpha_{i, j}$) and constructs its local Reference Model vector:
$$\mathbf{w}_i^{\text{ref}} = \alpha_{i, i} \mathbf{w}_i^{\text{sparse}} + \sum_{j \in \mathcal{P}_i^*} \alpha_{i, j} \mathbf{w}_j^{\text{sparse}}$$

### 1. Precomputed Reference Vectors
- **Node 1:** `[0.3742, 0.2419, 0.3838, 0, 0, 0, 0, 0, 0, 0]`
- **Node 2:** `[0.3600, 0.2456, 0.3944, 0, 0, 0, 0, 0, 0, 0]`
- **Node 3:** `[0, 0, 0, 0.3957, 0.2319, 0.3725, 0, 0, 0, 0]`
- **Node 4:** `[0, 0, 0, 0.4990, 0.2306, 0.2703, 0, 0, 0, 0]`
- **Node 5:** `[0, 0, 0, 0.4981, 0.1755, 0.3264, 0, 0, 0, 0]`
- **Node 6:** `[0, 0, 0, 0, 0, 0, 0.1111, 0.2171, 0.3037, 0.2169]`
- **Node 7:** `[0, 0, 0, 0, 0, 0, 0.0499, 0.3287, 0.2837, 0.2066]`
- **Node 8:** `[0, 0, 0, 0.3913, 0.2403, 0.3684, 0, 0, 0, 0]`
- **Node 9:** `[0.3805, 0.2452, 0.3743, 0, 0, 0, 0, 0, 0, 0]`
- **Node 10:** `[0, 0, 0, 0, 0, 0, 0.0497, 0.3295, 0.2867, 0.2028]`

### 2. Node State Transitions
- All 10 nodes transition to status: `REFERENCE_MODEL_BUILT`.
- Each node synthesizes an internal synthesized reference model $\mathbf{w}_i^{\text{ref}}$ with normalized weights $\alpha_{i, \cdot}$.

---

## Step 33 — Local Model Aggregation (FedAvg) & Convergence Commitment

Every node applies Federated Averaging, committing the similarity-weighted model parameters as its local model state for Round 1:
$$\mathbf{w}_i^{t+1} = \sum_{j \in \mathcal{P}_i^* \cup \{i\}} \alpha_{i, j} \mathbf{w}_j^{\text{sparse}}$$

### 1. Final Aggregated Model Registry (Round 1)
- **Node 1:** `[0.3742, 0.2419, 0.3838, 0, 0, 0, 0, 0, 0, 0]`
- **Node 2:** `[0.3600, 0.2456, 0.3944, 0, 0, 0, 0, 0, 0, 0]`
- **Node 3:** `[0, 0, 0, 0.3957, 0.2319, 0.3725, 0, 0, 0, 0]`
- **Node 4:** `[0, 0, 0, 0.4990, 0.2306, 0.2703, 0, 0, 0, 0]`
- **Node 5:** `[0, 0, 0, 0.4981, 0.1755, 0.3264, 0, 0, 0, 0]`
- **Node 6:** `[0, 0, 0, 0, 0, 0, 0.1111, 0.2171, 0.3037, 0.2169]`
- **Node 7:** `[0, 0, 0, 0, 0, 0, 0.0499, 0.3287, 0.2837, 0.2066]`
- **Node 8:** `[0, 0, 0, 0.3913, 0.2403, 0.3684, 0, 0, 0, 0]`
- **Node 9:** `[0.3805, 0.2452, 0.3743, 0, 0, 0, 0, 0, 0, 0]`
- **Node 10:** `[0, 0, 0, 0, 0, 0, 0.0497, 0.3295, 0.2867, 0.2028]`

### 2. Node State Transitions
- All 10 nodes transition to status: `AGGREGATION_COMMITTED`.
- Updated local model convergence achieved: $\mathbf{w}_i^{t+1} = \mathbf{w}_i^{\text{ref}}$.
- Model convergence certified with estimated accuracy gains across all clients.