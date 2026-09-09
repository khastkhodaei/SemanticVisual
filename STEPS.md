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

