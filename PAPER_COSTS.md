# SemanticDFL — Paper Cost & Savings Reference (stage by stage)

> **Source:** Dogani, Khastkhodaei, Khunjush, Laoutaris. *SemanticDFL: Similarity-Aware Pull-based Personalized Decentralized Federated Learning.* Proc. ACM Meas. Anal. Comput. Syst. 10(2), Art. 51, June 2026.
> **Purpose:** single source of truth for every cost (bytes, messages, compute, memory, latency) and every improvement reported or derivable from the paper, organised to follow the simulator's protocol phases.
> **Audience:** humans browsing the "4. Paper Models & Savings" tab **and** a coding agent that must read this file and wire numbers into the simulator.

## How to read this file

**Provenance tags** (every number carries one):

| Tag | Meaning |
|---|---|
| `[Paper §x]` / `[Paper Tbl x]` / `[Paper Fig x]` / `[Paper App x]` | Stated explicitly in the paper |
| `[Derived]` | Computed from paper formulas or values (formula shown) |
| `[Fig≈]` | Read off a chart, approximate |
| `[Simulator]` | Simulator choice or preset, **not** claimed by the paper |

**Units:** the paper reports sizes in MiB but writes "MB". Decimal MB = bytes / 10⁶; MiB = bytes / 2²⁰. Both are given where they differ.

**Symbols:** `N` peers · `M` model parameters · `P` signature cardinality · `K` neighbours pulled · `S_Z` zone cap · `R` TTL radius · `H` SON depth · `B` beam · `F` fan-out · `r` replication · `n_z` zone size · `d̄` avg overlay degree.

## Contents

- [S0 Global constants & default parameters](#s0--global-constants--default-parameters)
- [S1 Bootstrap & VRF initiator election (steps 1–4)](#s1--bootstrap--vrf-initiator-election-steps-14)
- [S2 Zone formation (steps 5–6)](#s2--zone-formation-steps-56)
- [S3 P selection & signature extraction (steps 7–11)](#s3--p-selection--signature-extraction-steps-711)
- [S4 Intra-zone clustering (steps 12–13)](#s4--intra-zone-clustering-steps-1213)
- [S5 Inter-zone recursive SON build (steps 14–19)](#s5--inter-zone-recursive-son-build-steps-1419)
- [S6 Overlay ready: maintenance & replication (steps 20–21)](#s6--overlay-ready-maintenance--replication-steps-2021)
- [S7 Similarity search per round (steps 22–29)](#s7--similarity-search-per-round-steps-2229)
- [S8 Model pull & aggregation (steps 30–33)](#s8--model-pull--aggregation-steps-3033)
- [S9 Round totals & measured overhead (step 34)](#s9--round-totals--measured-overhead-step-34)
- [S10 Churn & robustness](#s10--churn--robustness)
- [S11 Improvements (what the paper gains)](#s11--improvements-what-the-paper-gains)
- [S12 Benchmark models & compression ratios](#s12--benchmark-models--compression-ratios)
- [S13 Caveats & hidden costs](#s13--caveats--hidden-costs)
- [S14 Corrections to the previous tab](#s14--corrections-to-the-previous-tab)

---

## S0 — Global constants & default parameters

| Parameter | Value | Tag |
|---|---|---|
| Signature entry size | 6 B = 4 B index + 2 B value (FP16) | `[Paper §3.4]` |
| Dense model size | 4 B × M (FP32) | `[Paper §3.4]` |
| Signature size | `S_sig = 6·P` bytes | `[Paper §3.4]` |
| Wire reduction vs dense | `4M / 6P = 2 / (3·P/M)` | `[Derived]` |
| Link assumption (worked example) | 200 Mbps ≈ 25 MB/s | `[Paper §3.4]` |
| Neighbours pulled | `K = 0.10·N` (ablated 5–25 %) | `[Paper §5.1]` |
| Zone cap | `S_Z = 0.05·N` | `[Paper §5.1]` |
| Replication | `r = 3` | `[Paper §5.1]` |
| Beam / fan-out | `(B, F) = (8, 8)` | `[Paper §5.1]` |
| Personalization weight | `ψ = 2` (mixing α = ηψ/(1+ηψ)) | `[Paper §5.1, Tbl 11]` |
| FL rounds | 100 | `[Paper §5.1]` |
| Cosine retention target `τ_min` | cos(w, w_[P]) ≥ 0.8 (empirical) | `[Paper §3.2, Fig 2]` |
| Quantile for global P | `q ∈ [0.8, 0.9]`, `P = min(Quantile_q({P_min}), P_max)` | `[Paper §3.2, App B.1]` |
| Threshold relax step | `δ = 0.02` when fewer than K candidates | `[Paper §3.5]` |
| Simulator storyboard | N=10, P=3, K=2, θ=0.70, q=0.20 | `[Simulator]` |

**Reduction lookup** (`2 / (3·P/M)`, saved % = `1 − 3P/(2M)`):

| P/M | 8.5 % | 9.6 % | 10 % | 10.8 % | 11.2 % | 12.3 % | 12.8 % | 13.3 % |
|---|---|---|---|---|---|---|---|---|
| Reduction | 7.84× | 6.94× | 6.67× | 6.17× | 5.95× | 5.42× | 5.21× | 5.01× |
| Saved | 87.3 % | 85.6 % | 85.0 % | 83.8 % | 83.2 % | 81.5 % | 80.8 % | 80.0 % |

---

## S1 — Bootstrap & VRF initiator election (steps 1–4)

| Cost item | Type | Formula / value | Tag |
|---|---|---|---|
| VRF score per node per epoch | compute | one VRF evaluation `σ_p = VRF_p(seed(e−1))` | `[Paper §3.3.1]` |
| Initiator selection | messages | each node learns `(σ,id)` of its R-hop neighbourhood, ≈ `|N_R(p)|` small headers | `[Derived]` |
| Election frequency | schedule | once per overlay epoch (not per FL round) | `[Paper §3.3.1]` |
| Node state | memory | O(1) | `[Paper App B.2]` |
| Byte cost | — | **not quantified in the paper**; negligible next to signatures | `[Derived]` |

Outcome: dispersed initiators at granularity `R`; ties broken by ID.

---

## S2 — Zone formation (steps 5–6)

| Cost item | Type | Formula / value | Tag |
|---|---|---|---|
| PROBE flood, TTL = R, first-wins | messages | **O(S_Z) per zone** | `[Paper §3.3.1, App B.2]` |
| Zone latency | latency | O(R) hops; wall-clock O(R·t_a) | `[Paper §3.3.1]` |
| Adjacency notifications (`NOTIFY_NEIGHBOR`) | messages | O(∂Z), zone boundary size | `[Paper App B.2]` |
| Diameter timeout before cap check | latency | `R · t_a` | `[Paper §3.3.1]` |
| Deterministic split if `|Z| > S_Z` | messages | hand remainder to next-lowest VRF, re-probe | `[Paper §3.3.1]` |
| Initiator memory | memory | O(S_Z) member metadata | `[Paper App B.2]` |
| Ordinary peer memory | memory | O(1) | `[Paper App B.2]` |
| Number of zones at a level | count | `Z_ℓ = Θ(N / S_Z)` | `[Paper App D.1]` |
| Total zone-formation messages | messages | `Z_ℓ · O(S_Z) = O(N)` | `[Derived]` |
| Example: N=200 | count | `S_Z = 10` | `[Derived]` |

---

## S3 — P selection & signature extraction (steps 7–11)

### Local binary search for `P_min` (steps 7–8)

| Cost item | Type | Formula | Tag |
|---|---|---|---|
| Sort coordinates by importance score | compute | O(M log M) | `[Paper App B.1]` |
| Prefix sums of squared weights | compute | O(M) | `[Paper App B.1]` |
| Each feasibility test | compute | O(1): `c_P ≥ θ²·‖w‖²` | `[Paper App B.1]` |
| Binary-search iterations | compute | ≈ log₂ M tests | `[Derived]` |
| Working memory | memory | O(M) | `[Paper App B.1]` |
| Recompute cadence | schedule | every `T_ref` rounds or when guard `cos < θ − ε` fires | `[Paper App B.1]` |
| Importance score | compute | `s = β·s_prev + (1−β)·|w|` (EMA, β∈[0,1)) | `[Paper §3.2]` |

### Global P consensus (steps 9–10)

| Cost item | Type | Formula | Tag |
|---|---|---|---|
| Report `P_min` to zone initiator | messages | n_z scalars per zone (one int each) | `[Derived]` |
| Quantile aggregation | compute | sort n_z values, pick `q`-quantile | `[Paper §3.2]` |
| Broadcast global `P` (`ORDER_EXTRACT`) | messages | n_z small orders per zone | `[Derived]` |
| Guarantee | quality | ≥ q-fraction of clients reach cos ≥ τ_min | `[Paper §3.2]` |
| Local clip if P exceeds device budget | rule | recall may degrade, routing stays consistent | `[Paper App B.1]` |

### Signature extraction (step 11)

| Cost item | Type | Formula / value | Tag |
|---|---|---|---|
| Signature payload | bytes | `6·P` (or `O(P(b_idx+b_val))` bits) | `[Paper §3.2, §3.4]` |
| Similarity computation | compute | **O(P)** (merge sorted index lists) vs Θ(M) full | `[Paper §3.2]` |
| Index refresh | schedule | indices refresh every few rounds; values reflect current w every round | `[Paper §3.2]` |
| Pruning quality | quality | pruning **84–93 %** of parameters keeps cos ≥ 0.8 | `[Paper Fig 2]` |
| Tuned optimum P (fraction of M) | config | FMNIST 12.3 %, Tiny-ImageNet 9.6 %, Google Speech 11.2 %, ALBERT 12.8 % | `[Paper §5.1, App E.1]` |
| Worked-example P (fraction of M) | config | 10 % generic, Tiny-ImageNet 10.8 %, Google Speech 13.3 % | `[Paper §3.4]` |
| Sensitivity | quality | P ± 1 → median −0.6 pp (0.4–1.3); P ± 2 → median −1.1 pp (0.8–1.8); using P−1 costs only 0.4–0.9 pp and shrinks payload proportionally | `[Paper App E.1]` |

Worked payload sizes (ResNet-18, M = 11.7 M, dense ≈ 46.8 MB decimal ≈ "47 MB"):

| P/M | Signature (decimal MB) | Signature (MiB, as printed in paper) | Source |
|---|---|---|---|
| 10 % | 7.02 | 6.7 | `[Paper §3.4]` (6.7 MB) |
| 10.8 % | 7.58 | 7.24 | `[Paper §3.4]` |
| 13.3 % | 9.34 | 8.91 | `[Paper §3.4]` |

---

## S4 — Intra-zone clustering (steps 12–13)

| Cost item | Type | Formula | Tag |
|---|---|---|---|
| Gather signatures (`SigProbe`) | bytes | **O(n_z · P)** bytes per zone | `[Paper §3.3.2]` |
| Similarity matrix `n_z × n_z` | compute | **O(n_z² · P)** ops (tractable under cap `S_Z`) | `[Paper §3.3.2]` |
| Similarity matrix memory at initiator | memory | O(n_z²) | `[Derived]` |
| Affinity Propagation | compute | number of clusters discovered from data, no a-priori `k` | `[Paper §3.3.2]` |
| Prototype per cluster | data | `ū_j = TopP( (1/|C_j|) Σ u_i )` (signature-sized) | `[Paper §3.3.2]` |
| Cluster descriptor | bytes | `CD_j = (j, e_j, ū_j, R_j, |C_j|, zoneID)`, `S_D ≈ S_P + small header` | `[Paper §3.3.2]`, `[Derived]` |
| Descriptor replication | bytes | `r ×` (r = 3) copies to super-peer replica set `R_j ⊆ C_j` | `[Paper §3.7, §5.1]` |
| Super-peer state | memory | descriptors + member pointers only | `[Paper §3.3.2]` |

---

## S5 — Inter-zone recursive SON build (steps 14–19)

| Cost item | Type | Formula / value | Tag |
|---|---|---|---|
| Levels (depth) | structure | `H = ⌈log_{S_Z} N⌉ = O(log N)` | `[Paper §3.3.3, Prop 2]` |
| Recursion stop | rule | when level-ℓ super-peers `< S_Z` | `[Paper §3.3.3]` |
| Per-level clustering | compute | same as S4 on prototypes `{ū_j}` | `[Paper §3.3.3]` |
| Node state | memory | parent/child descriptors only, no global snapshot | `[Paper §3.3.3]` |
| Per-level control bytes | bytes | `N·d̄·S_H + N·S_P + Z_ℓ·C·S_D·r` | `[Paper Prop 1, App D.1]` |
| Total control cost | bytes | `C_tot = Θ(N(d̄·S_H + S_P + C·S_D))` | `[Paper Prop 1]` |
| Per-node control cost | bytes | **O(1)**; total **O(N)** | `[Paper Prop 1]` |
| Root synchronisation among F super-peers | bytes | Θ(F²·S_D) mesh, Θ(F·S_D) tree | `[Paper Prop 1]` |
| Per-level build time | latency | O(D_Z) + O(1) = O(log S_Z), `D_Z = O(log S_Z)` | `[Paper Prop 2]` |
| End-to-end build time | latency | `T_build = Θ(log_{S_Z} N) + Θ(log F) = Θ(log N)` | `[Paper Prop 2]` |
| Worst-case super-peer memory | memory | `M_max ≤ H · S_Z · (S_P + r·S_D) = O((S_P+S_D)·S_Z·log N)` | `[Paper Prop 3]` |
| Example: N=200, S_Z=10 | structure | `H = 3` | `[Derived]` |
| Amortisation | method | creation cost amortised over FL rounds in all reported overhead | `[Paper §5.4.1]` |

Note: the paper describes a hierarchy of depth `O(log N)`. The simulator storyboard shows two tiers (super-peers, exemplars) plus leaves for N = 10 `[Simulator]`.

---

## S6 — Overlay ready: maintenance & replication (steps 20–21)

| Cost item | Type | Formula / value | Tag |
|---|---|---|---|
| Replica set per zone initiator | memory/msgs | size `r` (= 3), state replicated | `[Paper §3.7]` |
| Replica set per cluster super-peer | memory/msgs | `|R_j| = r`, holds `CD_j` | `[Paper §3.7]` |
| Leadership | protocol | short leases; deterministic successor by (VRF, id) on expiry | `[Paper §3.7]` |
| Super-peer failure | repair | replica takes over immediately; initiator backfills `|R_j| = r` | `[Paper §3.7]` |
| Repair scope | messages | only parent and children notified; no global state | `[Paper §3.7]` |
| Fault masking | guarantee | `r ≥ 2` masks single-node failures | `[Paper §3.7]` |
| Join | compute/msgs | forward to ancestor, top-down compare to child prototypes (≈ `H` levels × `m_ℓ` prototype cosines), update `CD_j` | `[Paper §3.7]` |
| Graceful leave | messages | notify cluster super-peer; promote replacement if leaver ∈ `R_j` | `[Paper §3.7]` |
| Dropout | repair | lease expiry → promote replica, refresh `CD_j`, patch adjacent pointers | `[Paper §3.7]` |
| Load balancing | design | replicas share query load; hard cap `S_Z`; beam caps `B_ℓ` | `[Paper §3.8]` |
| Weight sparsification (step 21) | compute | apply Top-P mask to model for pulling / serving | `[Paper §3.2]` |

---

## S7 — Similarity search per round (steps 22–29)

| Cost item | Type | Formula | Tag |
|---|---|---|---|
| Signature comparisons per query | compute | **O(P · F · B · H)** (exact: `O(P Σ v_ℓ m_ℓ)`) | `[Paper §3.4]` |
| Messages per query | messages | **O(B · H)** (exact: `O(Σ v_ℓ B_ℓ)`) | `[Paper §3.4]` |
| Bottom-up top-K merge | compute | `O(K log K · H)` | `[Paper §3.4]` |
| Visited nodes per level | bound | `v_ℓ ≤ Π_{r=ℓ+1..H} B_r` | `[Paper §3.4]` |
| What travels | data | signatures and descriptors only; **no full models** | `[Paper §3.4]` |
| Adaptive threshold τ⁽ᵗ⁾ | compute | small controller: `τ ← clip(τ + η_τ(â − φ) − γ(1 − ρ))` | `[Paper §3.5]` |
| Retry if `< K` candidates | messages | relax `τ −= δ (0.02)`, re-descend under same beam, stop at `C ≥ K` or visit budget | `[Paper §3.5]` |
| Soft barrier | latency | aggregate when K replies arrive or timeout `Δ_t`; late replies accepted within `Δ_max` if `sim ≥ T_fresh` | `[Paper §3.6]` |

**Worked example** (`H≈3`, `B=2`, ≈7 super-peers visited, ≈4 leaves of size `n_L=2`, 200 Mbps):

| Quantity | Tiny-ImageNet (P=10.8 %) | Google Speech (P=13.3 %) | Tag |
|---|---|---|---|
| Signatures fetched `(7 + 4·n_L)` | 15 | 15 | `[Paper §3.4]` |
| Search traffic | ≈ 109 MB | ≈ 133 MB | `[Paper §3.4]` |
| Search time | ≈ 4.4 s | ≈ 5.3 s | `[Paper §3.4]` |

Search-recall quality:

**Recall@K and oracle gap at K = 10 %** (`Recall / Acc★ (oracle) / Acc SemanticDFL`, `[Paper Tbl 4]`):

| Dataset | N | Dir(0.1) | Patho(20 %) |
|---|---|---|---|
| FMNIST | 50 | 0.95 / 80.2 / 80.0 | 0.91 / 76.4 / 76.2 |
| | 100 | 0.96 / 79.1 / 78.9 | 0.92 / 75.1 / 74.9 |
| | 200 | 0.96 / 77.8 / 77.5 | 0.93 / 73.6 / 73.2 |
| | 400 | 0.97 / 76.5 / 76.1 | 0.92 / 72.0 / 71.5 |
| Tiny-ImageNet | 50 | 0.93 / 47.3 / 47.0 | 0.88 / 42.0 / 41.6 |
| | 100 | 0.94 / 46.0 / 45.7 | 0.89 / 40.8 / 40.3 |
| | 200 | 0.94 / 44.4 / 44.0 | 0.90 / 39.0 / 38.4 |
| | 400 | 0.95 / 42.8 / 42.2 | 0.90 / 37.2 / 36.4 |
| Google Speech | 50 | 0.96 / 89.4 / 89.2 | 0.93 / 86.2 / 86.0 |
| | 100 | 0.97 / 88.6 / 88.4 | 0.94 / 85.1 / 84.9 |
| | 200 | 0.97 / 87.3 / 87.0 | 0.94 / 83.6 / 83.2 |
| | 400 | 0.98 / 85.9 / 85.5 | 0.95 / 82.0 / 81.4 |
| 20Newsgroup | 50 | 0.97 / 65.8 / 65.6 | 0.94 / 62.3 / 62.0 |
| | 100 | 0.98 / 64.6 / 64.4 | 0.95 / 61.2 / 60.9 |
| | 200 | 0.98 / 63.0 / 62.6 | 0.95 / 59.6 / 59.1 |
| | 400 | 0.99 / 61.5 / 61.0 | 0.96 / 58.1 / 57.4 |

Oracle gap: sub-percentage-point for small/medium N, up to ≈ 0.8 pp at N = 400.

**Recall@K vs K at N = 200** (`[Paper Tbl 5]`):

| Dataset | Dir(0.1) K=5/10/15/20 % | Patho(20 %) K=5/10/15/20 % |
|---|---|---|
| FMNIST | 0.94 / 0.96 / 0.97 / 0.99 | 0.90 / 0.93 / 0.95 / 0.97 |
| Tiny-ImageNet | 0.92 / 0.94 / 0.96 / 0.98 | 0.88 / 0.90 / 0.92 / 0.94 |
| Google Speech | 0.95 / 0.97 / 0.98 / 0.99 | 0.91 / 0.94 / 0.96 / 0.98 |
| 20Newsgroup | 0.96 / 0.98 / 0.99 / 1.00 | 0.93 / 0.95 / 0.97 / 0.99 |

---

## S8 — Model pull & aggregation (steps 30–33)

| Cost item | Type | Formula / value | Tag |
|---|---|---|---|
| Pull K full models | bytes (down) | **O(K · M)** once per round | `[Paper §3.4]` |
| Serve models to others | bytes (up) | comparable to K models (pull-serves) | `[Paper §5.4.1, §5.4.2]` |
| Worked example, ResNet-18, K = 10 | bytes/time | pull + upload ≈ **935 MB ≈ 38.5 s** at 200 Mbps | `[Paper §3.4]` |
| Search vs transfer | ratio | search traffic (109–133 MB) ≪ mandatory transfers (935 MB) | `[Paper §3.4]` |
| Similarity weights | compute | `W_ij = softmax_j((s_ij − c_i)/κ)` over Top-K ∪ {i} | `[Paper §2.1]` |
| Neighbour anchor | compute | `m_i = Σ_j W_ij w_j`, O(K·M) | `[Paper §2.1]`, `[Derived]` |
| Personalised update | compute | `w_i ← (1−α_i)·w̃_i + α_i·m_i`, `α_i = ηψ/(1+ηψ)` | `[Paper §2.1]` |
| Local SGD | compute | `E_loc` local epochs (1 in all experiments) | `[Paper §5.1]` |

Comparison of the data-plane cost model against alternatives (`[Paper §2.3]`):

| Scheme | Data plane / round | Control plane |
|---|---|---|
| Gossip / push | Θ(M · |E|) | negligible |
| Naive similarity-pull | Θ(K · M) | Θ(N · M) for global k-NN (prohibitive) |
| **SemanticDFL** | Θ(K · M) | O(P · F · B · H) + O(B · H) messages |
| Full-model similarity | Θ(M · |N_i|) compute, Θ(M) bytes per comparison | — |

**Personalization weight ψ** (Dir 0.3, `[Paper Tbl 11]`): ψ=0 (local only) → FMNIST 71.0, Tiny 41.5, Speech 83.5, 20NG 55.5; **ψ=2 (best)** → 79.6, 48.8, 89.1, 64.2; ψ=5 → 79.1, 48.2, 88.5, 63.4.

---

## S9 — Round totals & measured overhead (step 34)

### Per-node round time breakdown, BW = 200 Mbps, K = 0.1·N (`[Paper Fig 5]`, seconds)

| Dataset | N | Training | Model communication | SON creation + search |
|---|---|---|---|---|
| FMNIST | 50 | 1.96 | 0.88 | 0.15 |
| | 100 | 1.00 | 1.76 | 0.16 |
| | 150 | 0.88 | 2.64 | 0.19 |
| | 200 | 0.72 | 3.52 | 0.24 |
| Tiny-ImageNet | 50 | 17.76 | 22.36 | 4.84 |
| | 100 | 12.50 | 46.42 | 5.37 |
| | 150 | 10.60 | 70.48 | 6.45 |
| | 200 | 8.21 | 92.54 | 8.06 |
| Google Speech | 50 | 16.36 | 22.48 | 4.10 |
| | 100 | 13.67 | 46.86 | 5.26 |
| | 150 | 11.41 | 71.08 | 6.49 |
| | 200 | 7.56 | 93.24 | 8.06 |
| 20Newsgroup | 50 | 33.27 | 167.34 | 34.22 |
| | 100 | 25.40 | 306.34 | 38.35 |
| | 150 | 21.50 | 468.90 | 46.41 |
| | 200 | 16.60 | 671.30 | 57.50 |

**SON share of round time (average over N)** `[Paper §5.4.1]`: FMNIST **5.2 %** · Tiny-ImageNet **8.5 %** · Google Speech **8.1 %** · 20Newsgroup **10.3 %** · overall ≈ **8.0 %**. Global range across all settings **1.7–12.6 %** `[Paper Abstract, Tbl 6]`.

### Scaling with K and N — round time / SON search time (search share) `[Paper Tbl 6]`, seconds

**FMNIST (CNN)**

| N | K=10 % | K=15 % | K=20 % | K=25 % |
|---|---|---|---|---|
| 100 | 2.92/0.16 (5.56 %) | 3.82/0.18 (4.68 %) | 4.71/0.19 (3.97 %) | 5.59/0.19 (3.45 %) |
| 200 | 4.26/0.24 (5.71 %) | 6.05/0.27 (4.43 %) | 7.82/0.28 (3.58 %) | 9.59/0.29 (3.02 %) |
| 300 | 5.90/0.26 (4.40 %) | 8.57/0.29 (3.34 %) | 11.22/0.30 (2.66 %) | 13.87/0.31 (2.23 %) |
| 400 | 7.59/0.28 (3.64 %) | 11.13/0.30 (2.73 %) | 14.67/0.32 (2.16 %) | 18.20/0.33 (1.81 %) |

**Tiny-ImageNet (ResNet-18)**

| N | K=10 % | K=15 % | K=20 % | K=25 % |
|---|---|---|---|---|
| 50 | 44.21/3.03 (6.86 %) | 56.22/3.34 (5.94 %) | 68.08/3.49 (5.13 %) | 79.90/3.61 (4.52 %) |
| 100 | 59.09/3.37 (5.71 %) | 82.84/3.71 (4.48 %) | 106.42/3.88 (3.64 %) | 129.97/4.01 (3.09 %) |
| 150 | 80.21/4.05 (5.04 %) | 115.73/4.45 (3.85 %) | 151.05/4.65 (3.08 %) | 186.33/4.81 (2.58 %) |
| 200 | 103.15/5.06 (4.90 %) | 150.48/5.56 (3.70 %) | 197.56/5.82 (2.94 %) | 244.59/6.02 (2.46 %) |

**Google Speech (ResNet-18)**

| N | K=10 % | K=15 % | K=20 % | K=25 % |
|---|---|---|---|---|
| 100 | 59.06/3.93 (6.66 %) | 82.86/4.33 (5.22 %) | 106.47/4.52 (4.25 %) | 130.04/4.68 (3.60 %) |
| 200 | 103.71/5.90 (5.69 %) | 151.13/6.49 (4.29 %) | 198.25/6.78 (3.42 %) | 245.31/7.02 (2.86 %) |
| 300 | 149.54/6.29 (4.21 %) | 220.40/6.92 (3.14 %) | 290.95/7.24 (2.49 %) | 361.44/7.49 (2.07 %) |
| 400 | 196.07/6.69 (3.41 %) | 290.39/7.36 (2.53 %) | 384.37/7.69 (2.00 %) | 478.28/7.96 (1.66 %) |

**20Newsgroup (ALBERT-base)**

| N | K=10 % | K=15 % | K=20 % | K=25 % |
|---|---|---|---|---|
| 50 | 229.52/28.89 (12.59 %) | 316.00/31.78 (10.06 %) | 401.04/33.22 (8.28 %) | 485.79/34.38 (7.08 %) |
| 100 | 383.28/32.10 (8.38 %) | 553.68/35.31 (6.38 %) | 722.47/36.92 (5.11 %) | 890.94/38.20 (4.29 %) |
| 150 | 551.28/38.52 (6.99 %) | 805.91/42.37 (5.26 %) | 1058.62/44.30 (4.19 %) | 1310.94/45.84 (3.50 %) |
| 200 | 725.31/48.15 (6.64 %) | 1064.50/52.97 (4.98 %) | 1401.28/55.37 (3.95 %) | 1737.58/57.30 (3.30 %) |

Rules: round time grows roughly proportional to K; search grows only mildly; the search share therefore falls monotonically as K grows.

### Bandwidth sensitivity — Comm / Search (search share of round), seconds `[Paper Tbl 12]`

Training time is bandwidth-independent and decreases sub-linearly with N; 0–5 % jitter is injected per cell.

**FMNIST**

| N | Train | 50 Mbps | 100 Mbps | 150 Mbps | 200 Mbps |
|---|---|---|---|---|---|
| 100 | 1.00 | 3.58/0.32 (6.48 %) | 1.78/0.16 (5.31 %) | 1.20/0.11 (4.79 %) | 0.89/0.08 (3.92 %) |
| 200 | 0.66 | 7.33/0.50 (5.89 %) | 3.58/0.24 (5.03 %) | 2.37/0.16 (4.96 %) | 1.77/0.12 (4.74 %) |
| 300 | 0.50 | 11.03/0.53 (4.58 %) | 5.41/0.27 (4.57 %) | 3.55/0.17 (4.33 %) | 2.75/0.13 (4.27 %) |
| 400 | 0.42 | 14.75/0.56 (3.65 %) | 7.39/0.29 (3.69 %) | 4.78/0.19 (3.61 %) | 3.60/0.14 (3.67 %) |

**Tiny-ImageNet**

| N | Train | 50 Mbps | 100 Mbps | 150 Mbps | 200 Mbps |
|---|---|---|---|---|---|
| 50 | 17.76 | 48.36/6.32 (8.53 %) | 23.61/3.13 (6.93 %) | 16.21/2.06 (5.66 %) | 11.72/1.59 (5.09 %) |
| 100 | 11.18 | 97.40/6.82 (6.09 %) | 47.10/3.45 (5.82 %) | 31.64/2.35 (5.49 %) | 23.73/1.71 (5.01 %) |
| 150 | 8.10 | 147.13/8.15 (5.07 %) | 73.61/4.07 (4.87 %) | 48.59/2.72 (4.76 %) | 36.63/2.10 (4.71 %) |
| 200 | 7.27 | 196.39/10.13 (4.84 %) | 95.82/5.19 (4.96 %) | 64.03/3.44 (4.82 %) | 47.50/2.65 (4.88 %) |

**Google Speech**

| N | Train | 50 Mbps | 100 Mbps | 150 Mbps | 200 Mbps |
|---|---|---|---|---|---|
| 100 | 8.30 | 95.51/8.10 (7.28 %) | 49.10/4.09 (6.69 %) | 31.73/2.67 (6.28 %) | 24.27/1.98 (5.75 %) |
| 200 | 5.56 | 193.57/12.29 (5.96 %) | 94.65/5.96 (5.79 %) | 63.77/3.94 (5.58 %) | 47.43/3.02 (5.61 %) |
| 300 | 4.10 | 290.57/12.79 (4.20 %) | 143.99/6.31 (4.14 %) | 97.25/4.25 (4.09 %) | 72.72/3.17 (4.05 %) |
| 400 | 3.56 | 381.48/13.41 (3.41 %) | 193.89/7.01 (3.48 %) | 127.02/4.62 (3.48 %) | 94.26/3.35 (3.39 %) |

**20Newsgroup (ALBERT)**

| N | Train | 50 Mbps | 100 Mbps | 150 Mbps | 200 Mbps |
|---|---|---|---|---|---|
| 50 | 33.44 | 350.28/60.29 (13.52 %) | 174.10/29.88 (12.55 %) | 115.93/20.10 (11.83 %) | 84.99/14.57 (10.93 %) |
| 100 | 20.73 | 699.95/65.19 (8.45 %) | 347.18/33.40 (8.48 %) | 233.93/22.37 (8.25 %) | 172.25/16.35 (8.02 %) |
| 150 | 16.00 | 1046.64/78.72 (6.98 %) | 508.52/40.00 (7.19 %) | 346.40/25.99 (6.80 %) | 253.82/19.42 (6.86 %) |
| 200 | 14.30 | 1399.55/99.84 (6.64 %) | 699.56/48.52 (6.43 %) | 467.87/33.38 (6.57 %) | 342.48/24.69 (6.59 %) |

### Communication time vs baselines, 200 Mb/s (`[Paper Fig 6]`, `[Fig≈]`)

| Group | Behaviour |
|---|---|
| Centralized FL (FedAvg/FedProx/Ditto), pFedGraph, Per-FedAvg | worst; server fan-in/out bottleneck; grows steeply with N and model size |
| DPFL (one-hop gossip) | lowest (only immediate neighbours) |
| DFedPGP | above DPFL, far below centralized |
| **SemanticDFL** | slightly above DPFL, **≈ 10× below centralized** (`[Fig≈]`: FMNIST N=400 ≈ 8 s vs ≈ 72 s; Tiny N=200 ≈ 90 s vs ≈ 920 s; Speech N=400 ≈ 190 s vs ≈ 1870 s; 20NG N=200 ≈ 650 s vs ≈ 6700 s) |

---

## S10 — Churn & robustness

| Cost item | Type | Value | Tag |
|---|---|---|---|
| Control-plane time under churn (20NG, N 50–200, K 10–25 %, churn 0–15 %) | time | ≈ 35 s to ≈ 87 s per node per round; ≈ +20–25 % from 0 % to 15 % churn | `[Paper Fig 7]`, `[Fig≈]` |
| Where the uplift comes from | cause | amortised creation work updating zone/replica state; SON *search* stays ≈ constant | `[Paper §5.5.2]` |

**Accuracy under churn, Dir(0.1), N = 200** (`[Paper Tbl 7]`, churn = fraction of peers leaving/arriving per round):

| Method | FMNIST 0/10/25/40 % | Tiny-ImageNet 0/10/25/40 % | Google Speech 0/10/25/40 % | 20NG 0/10/25/40 % |
|---|---|---|---|---|
| FedAvg | 62.0 / 59.0 / 54.0 / 48.0 | 36.0 / 33.0 / 28.0 / 23.0 | 76.6 / 74.6 / 70.6 / 64.6 | 49.4 / 47.4 / 42.4 / 35.4 |
| DPFL | 71.0 / 68.0 / 64.0 / 58.0 | 45.2 / 42.2 / 37.2 / 31.2 | 86.2 / 84.2 / 80.2 / 74.2 | 59.1 / 57.1 / 53.1 / 46.1 |
| DFedPGP | 71.3 / 69.3 / 65.3 / 59.3 | 47.1 / 45.1 / 41.1 / 35.1 | 86.6 / 84.6 / 81.6 / 75.6 | 58.2 / 56.2 / 52.2 / 45.2 |
| **SemanticDFL** | **73.1 / 72.1 / 70.1 / 67.1** | **47.3 / 46.3 / 44.3 / 40.3** | **86.8 / 85.8 / 83.8 / 80.8** | **63.3 / 62.3 / 60.3 / 56.3** |

Drop from 0 % to 40 % churn: **SemanticDFL ≈ 6–7 points**; FedAvg/FedProx ≈ 12–14; decentralized graph/gossip baselines ≈ 9–14.

---

## S11 — Improvements (what the paper gains)

### Structural

| Problem in prior work | SemanticDFL answer | Tag |
|---|---|---|
| Fixed / stochastic peer graphs mismatch data similarity | proximity-bounded zones + AP clustering on signatures | `[Paper §1]` |
| Needs any-to-any connectivity (CGNAT, firewalls, segmentation) | hierarchical overlay, only bounded-hop links; queries relayed via super-peers | `[Paper §1]` |
| Gossip attenuation of minority signals | pull only Top-K similar peers, no blind propagation | `[Paper §1, §2.3]` |
| Central coordinator / cluster-count knob | AP discovers cluster count; rotating replica-backed super-peers | `[Paper §1]` |
| Full-model similarity too costly | compact Top-P signatures, O(P) similarity, 80–87 % smaller payloads | `[Paper §3.2]` |
| Instability under churn / lossy links | replica sets, leases, local repair, soft barrier | `[Paper §3.6–3.7]` |

### Theory

| Result | Statement | Tag |
|---|---|---|
| Theorem 2 | oblivious graph mixing has an irreducible mis-aggregation bias growing with `λ₂(L)` and smoothing weight `γ`, independent of T | `[Paper App A]` |
| Theorem 1 | `O(1/√T)` stationarity with error floor `8ζ²`, where `ζ` shrinks with higher recall and tighter staleness | `[Paper §4.2]` |
| Selection deviation | `‖μ_S − μ_O‖ ≤ 2(1 − r_t)·G` | `[Paper Lemma 1]` |

### Accuracy (test %, mean over 3 runs, `[Paper Tbl 2]`)

SemanticDFL is best in all 16 dataset × partition settings.

| Dataset | Partition | FedAvg | DPFL | DFedPGP | **SemanticDFL** |
|---|---|---|---|---|---|
| FMNIST | Dir 0.3 | 66.4 | 76.8 | 77.9 | **79.6** |
| | Dir 0.1 | 62.0 | 71.0 | 71.3 | **73.1** |
| | Patho 30 % | 57.0 | 68.4 | 69.8 | **71.5** |
| | Patho 20 % | 53.5 | 65.7 | 67.4 | **68.4** |
| Tiny-ImageNet | Dir 0.3 | 38.3 | 47.0 | 48.6 | **48.8** |
| | Dir 0.1 | 36.0 | 45.2 | 47.1 | **47.3** |
| | Patho 30 % | 36.7 | 45.8 | 47.8 | **48.0** |
| | Patho 20 % | 36.2 | 44.9 | 45.8 | **45.9** |
| Google Speech | Dir 0.3 | 79.3 | 88.8 | 89.0 | **89.1** |
| | Dir 0.1 | 76.6 | 86.2 | 86.6 | **86.8** |
| | Patho 30 % | 72.4 | 82.5 | 83.0 | **83.3** |
| | Patho 20 % | 68.2 | 78.9 | 79.5 | **79.8** |
| 20Newsgroup | Dir 0.3 | 50.8 | 61.0 | 60.1 | **64.2** |
| | Dir 0.1 | 49.4 | 59.1 | 58.2 | **63.3** |
| | Patho 30 % | 48.0 | 58.3 | 57.2 | **63.9** |
| | Patho 20 % | 48.6 | 58.4 | 57.5 | **64.5** |

Relative gains the paper quotes for Patho(20 %) (relative %, **not** percentage points): vs FedAvg +27.9 / +26.8 / +17.0 / +32.7 % and vs DFedPGP +1.5 / +0.2 / +0.4 / +12.2 % (FMNIST / Tiny / Speech / 20NG).
Absolute gain vs FedAvg at ψ=2, Dir 0.3, in percentage points (`[Paper Tbl 11]`): FMNIST **+13.2**, Tiny **+10.5**, Speech **+9.8**, 20NG **+13.4**.

### Convergence speed — rounds to first reach target (`[Paper Tbl 3]`)

| Method | FMNIST Dir0.1 | FMNIST Patho20 | Tiny Dir0.1 | Tiny Patho20 | Speech Dir0.1 | Speech Patho20 | 20NG Dir0.1 | 20NG Patho20 |
|---|---|---|---|---|---|---|---|---|
| Target accuracy | 60 | 50 | 34 | 33 | 74 | 66 | 46 | 45 |
| FedAvg | 24 | 28 | 60 | 58 | 22 | 30 | 36 | 34 |
| FedProx | 22 | 25 | 54 | 52 | 20 | 28 | 32 | 30 |
| Per-FedAvg | 16 | 19 | 46 | 44 | 16 | 22 | 26 | 25 |
| Ditto | 14 | 17 | 42 | 40 | 14 | 20 | 22 | 21 |
| pFedGraph | 12 | 14 | 38 | 36 | 12 | 17 | 19 | 18 |
| DPFL | 18 | 22 | 48 | 46 | 13 | 18 | 27 | 26 |
| DFedPGP | 13 | 16 | 40 | 38 | 12 | 17 | 21 | 20 |
| **SemanticDFL** | **9** | **11** | **33** | **31** | **9** | **12** | **14** | **13** |

Median speed-up ≈ **2.5×** vs FedAvg, ≈ **1.3×** vs the best decentralized baseline.

### Retrieval quality summary

Recall@K **0.88–1.00** overall (Tbl 4 minimum 0.88, Tbl 5 up to 1.00); accuracy within **≈ 0.2–0.8 pp** of the centralized oracle (`[Paper Tbl 4]`).

### Ablations (cost/quality trade-offs)

| Ablation | Result | Tag |
|---|---|---|
| Signature size P | narrow optimum per dataset (see S3) | `[Paper App E.1, Tbl 9]` |
| Zone cap `S_Z ∈ {0.04, 0.05, 0.08, 0.10}·N` | no monotone trend; median |Δacc| ≈ 0.8 pp (max +1.5 / −2.1 pp) | `[Paper App E.2, Tbl 10]` |
| Personalization ψ | best at ψ = 2 (see S8) | `[Paper App E.3, Tbl 11]` |
| Local vs global test | local acc grows fast, global acc stays much lower: expected personalization trade-off | `[Paper App E.5, Fig 8]` |
| Model-similarity vs label-distribution peer selection | label-distribution slightly higher acc on FMNIST, but leaks label stats and is harder to refresh under drift | `[Paper App E.6, Fig 9]` |

---

## S12 — Benchmark models & compression ratios

### Models evaluated in the paper (`[Paper §5.1]`)

Signature bytes use `6·P`; dense bytes use `4·M`. **Two P values exist in the paper** (see S13 item 7): the §3.4 worked example and the §5.1/App. E.1 tuned optimum. Both are shown.

| Dataset | Model | M (params) | P/M (tuned, §5.1) | P/M (worked ex., §3.4) | Dense FP32 | Signature @ tuned P | Reduction @ tuned P | SON share of round | Acc (Dir 0.3) | Δ vs FedAvg |
|---|---|---|---|---|---|---|---|---|---|---|
| FMNIST | CNN: two 5×5 conv, FC-512, 10 classes | not stated in paper `[Simulator: user input]` | 12.3 % | — | `4·M` | `6·P` | 5.42× (81.5 % saved) | 5.2 % | 79.6 | +13.2 pp |
| Tiny-ImageNet | ResNet-18 (64×64 stem, 200 cls) | ≈ 11.7 M | 9.6 % | 10.8 % | ≈ 46.8 MB | 6.74 MB (tuned) / 7.58 MB (10.8 %) | 6.94× (tuned) / 6.17× (10.8 %) | 8.5 % | 48.8 | +10.5 pp |
| Google Speech | ResNet-18 (log-mel front-end) | ≈ 11.7 M | 11.2 % | 13.3 % | ≈ 46.8 MB | 7.86 MB (tuned) / 9.34 MB (13.3 %) | 5.95× (tuned) / 5.01× (13.3 %) | 8.1 % | 89.1 | +9.8 pp |
| 20Newsgroup | ALBERT-base-v2 (12 layers, 768 hidden, 12 heads) | ≈ 11.68 M `[Derived]` | 12.8 % | — | ≈ 46.7 MB | 8.97 MB | 5.21× (80.8 % saved) | 10.3 % | 64.2 | +13.4 pp |

Learning setup `[Paper §5.1]`: `[lr, batch, local epochs]` CNN `[0.01, 64, 1]`, ResNet-18/Tiny `[0.05, 64, 1]`, ResNet-18/Speech `[0.01, 64, 1]`, ALBERT `[2e-5, 16, 1]`. Testbed: EU SLICES, up to N = 400 (Medium class) and N = 200 (XLarge/GPU).

### Simulator-only presets (NOT evaluated in the paper)

| Preset | M | Assumed P/M | Dense | Signature | Reduction | Tag |
|---|---|---|---|---|---|---|
| MobileNetV2 | ≈ 3.4 M | 11.2 % | 13.6 MB | 2.28 MB | 5.95× | `[Simulator]` |
| BERT-Base | ≈ 110 M | 8.5 % | 440 MB | 56.1 MB | 7.84× | `[Simulator]` |

These extrapolate the paper's formula. The paper reports **no accuracy, recall or overhead results** for these models; label them "extrapolated" in the UI.

---

## S13 — Caveats & hidden costs

1. **Data plane grows linearly with N.** With `K = 0.10·N`, per-node pull cost is `O(0.1·N·M)`. The `O(log N)` scaling applies to search and build, not to model transfer (see Tbl 6 round time rising ≈ linearly with N).
2. **The signature is raw weights.** `u = mask(w, Top-P indices)` exposes ≈ 10 % of parameters to other nodes. Privacy (DP/HE/MPC), Byzantine and Sybil robustness are explicitly out of scope; honest clients are assumed `[Paper §2.4, §2.5]`.
3. **Assumptions:** common model architecture; partially synchronous, near-equal-capability peers `[Paper §2.4, §3.6]`.
4. **Local compute of signature building and AP** (O(M log M) sort, O(n_z²·P) matrix) is **not measured separately**; unclear whether Fig 5 "SON creation+search" includes it.
5. **Headline "3–12 % better than decentralized baselines" does not hold in every cell.** On Tiny-ImageNet and Google Speech the margin over DFedPGP is ≈ 0.1–0.5 pp (within std). On 20Newsgroup the server-based Ditto trails by only ≈ 0.4 pp at Patho(20 %). Percentages in the text are relative, not points.
6. **Bandwidth-insensitivity claim vs Tbl 12:** search time also falls ≈ 4× when bandwidth rises 50 → 200 Mbps (Tiny N=200: 10.13 s → 2.65 s), so its share stays ≈ constant instead of shrinking.
7. **P inconsistency:** §3.4 uses 10.8 % (Tiny) and 13.3 % (Speech); §5.1 and App. E.1 use 9.6 % and 11.2 %. The simulator should expose both and default to the tuned §5.1 values for experiments and §3.4 values when reproducing the worked example.
8. **Scale of evidence:** N ≤ 400, 100 rounds, 3 runs. O(log N) behaviour beyond that is analytical.
9. **Search vs training overlap:** Fig 5 FMNIST uses N = 50–200 while Tbl 6 uses N = 100–400; totals (e.g. FMNIST N=200, K=10 %: 4.48 s summed from Fig 5 vs 4.26 s in Tbl 6) do not match exactly.

---

## S14 — Corrections to the previous tab

The previous "4. Paper Models & Savings" tab contained values that are not in the paper or that differ from it. Replace them as follows.

| Previous claim | Problem | Correct value |
|---|---|---|
| FMNIST CNN = 62,000 params, dense 248 KB, payload 45.8 KB | Parameter count not stated in the paper | Mark M as "not stated"; keep P/M = 12.3 % |
| 20Newsgroup P = 10.0 %, 6.7×, payload 7.02 MB | Paper's tuned P is 12.8 % | 12.8 % → 8.97 MB, 5.21× |
| 20Newsgroup accuracy 82.4 % (+12.2 pp) | Not in paper. Paper reports 64.2 % (Dir 0.3) and +13.4 pp vs FedAvg; +12.2 is a *relative* gain vs DFedPGP at Patho(20 %) | 64.2 %, +13.4 pp |
| "Search ≤ 8.1–10.3 % … preserving > 89.7 % bandwidth" | Range is wrong | 1.7–12.6 % across all settings, ≈ 8 % average |
| Recall@K 0.90–0.99 | Range is wrong | 0.88–1.00 (Tbl 4/5); accuracy gap to oracle ≈ 0.2–0.8 pp |
| "Matches Oracle" for MobileNetV2 / BERT-Base with "App. D" | App. D contains control-traffic/memory proofs, not these experiments | Move to simulator-only presets, no accuracy claims |
| Tiny-ImageNet 7.58 MB, Speech 9.33 MB shown next to "paper" | These are decimal MB; paper prints 7.24 and 8.91 (MiB) | Show both units |
| "2-Tier SON" as the paper's structure | Paper's overlay has depth `O(log N)`; 2 tiers is the N = 10 storyboard | Label as simulator view |
| HANDOFF step 34: "up to 70 % reduction vs dense gossip" | Not stated in the paper; 80–87 % is per-signature payload vs dense model, not round savings | Remove or relabel as `[Simulator]` |
