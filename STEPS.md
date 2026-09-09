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
