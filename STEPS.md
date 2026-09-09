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

## Step 3 — VRF Generation & 1-Hop Neighbor Score Exchange

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

Each node broadcasts its VRF score strictly to its direct 1-hop physical neighbors and collects their received scores into a local neighborhood scoreboard.

