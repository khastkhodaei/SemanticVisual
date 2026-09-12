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
   *(Orthogonal distribution highlights the need for inter-zone Semantic Overlay links in Step 13).*


