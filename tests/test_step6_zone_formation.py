"""Automated Verification Suite for Step 6: Official Zone Membership, Tonal Color Morphing, and Dual Boundary Notifications.

Verifies:
1. All 10 nodes have status == "ASSIGNED".
2. Exact zone memberships:
   - Zone 2 (Leader: C2 👑): {1, 2, 3}
   - Zone 4 (Leader: C4 👑): {4, 5, 6, 7}
   - Zone 8 (Leader: C8 👑): {8, 9, 10}
3. Initiator Boundary Knowledge (Neighbor Zones Discovered):
   - Initiator C2 discovers: ["C4"]
   - Initiator C4 discovers: ["C2", "C8"]
   - Initiator C8 discovers: ["C4"]
4. Frontier Clients (C1 and C6) emit exact dual boundary notifications (Algorithm 3, L17-L20):
   - Node 1:
     - { target: "C2 (Own Initiator)", introduced_neighbor: "C4" }
     - { target: "C4 (Competing Initiator)", introduced_neighbor: "C2" }
   - Node 6:
     - { target: "C4 (Own Initiator)", introduced_neighbor: "C8" }
     - { target: "C8 (Competing Initiator)", introduced_neighbor: "C4" }
5. Accumulated metadata preserved for all 10 nodes:
   - neighbors, distribution, vector_10d, vrf_score, role.
6. API endpoints GET and POST /api/v1/storyboard/step/6 return HTTP 200 with packet events and boundary edges.
7. STEPS.md documents Step 6 requirements.
8. Frontend files (index.html, app.js, style.css) support Step 6 stepper, navigation, modals, and tonal morphing.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_ADJACENCY,
    STORYBOARD_10_DISTRIBUTION,
    STORYBOARD_10_VECTORS,
    STORYBOARD_10_VRF_SCORES,
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step6_all_10nodes_have_assigned_status():
    """Assert all 10 nodes have status == 'ASSIGNED'."""
    data = get_10node_step_data(6)
    nodes = data["nodes"]
    assert len(nodes) == 10

    for node in nodes:
        assert node.get("status") == "ASSIGNED", f"Node {node['id']} does not have status == 'ASSIGNED'"


def test_step6_exact_zone_memberships():
    """Assert exact zone memberships:
    Zone 2: {1, 2, 3}
    Zone 4: {4, 5, 6, 7}
    Zone 8: {8, 9, 10}
    """
    data = get_10node_step_data(6)
    nodes = {n["id"]: n for n in data["nodes"]}

    expected_zones = {
        2: {1, 2, 3},
        4: {4, 5, 6, 7},
        8: {8, 9, 10},
    }

    actual_zones = {2: set(), 4: set(), 8: set()}
    for nid, node in nodes.items():
        zid = node["assigned_zone"]
        assert zid in actual_zones, f"Node {nid} has unexpected assigned_zone {zid}"
        actual_zones[zid].add(nid)

    for zid, expected_members in expected_zones.items():
        assert actual_zones[zid] == expected_members, (
            f"Zone {zid} members {actual_zones[zid]} != expected {expected_members}"
        )


def test_step6_initiator_neighbor_zone_discovery():
    """Assert Initiator boundary knowledge:
    - Initiator C2 discovers: ['C4']
    - Initiator C4 discovers: ['C2', 'C8']
    - Initiator C8 discovers: ['C4']
    """
    data = get_10node_step_data(6)
    nodes = {n["id"]: n for n in data["nodes"]}

    c2 = nodes[2]
    assert c2.get("is_initiator") is True
    assert c2.get("discovered_neighbor_zones") == ["C4"]

    c4 = nodes[4]
    assert c4.get("is_initiator") is True
    assert sorted(c4.get("discovered_neighbor_zones", [])) == ["C2", "C8"]

    c8 = nodes[8]
    assert c8.get("is_initiator") is True
    assert c8.get("discovered_neighbor_zones") == ["C4"]


def test_step6_frontier_dual_boundary_notifications():
    """Assert Frontier nodes C1 and C6 emit exact dual boundary notifications."""
    data = get_10node_step_data(6)
    nodes = {n["id"]: n for n in data["nodes"]}

    c1 = nodes[1]
    assert c1.get("is_boundary") is True
    c1_notifs = c1.get("sent_boundary_notifications", [])
    assert len(c1_notifs) == 2, f"Node 1 should have 2 notifications, got {len(c1_notifs)}"
    c1_targets = {n["target"]: n["introduced_neighbor"] for n in c1_notifs}
    assert "C2 (Own Initiator)" in c1_targets
    assert c1_targets["C2 (Own Initiator)"] == "C4"
    assert "C4 (Competing Initiator)" in c1_targets
    assert c1_targets["C4 (Competing Initiator)"] == "C2"

    c6 = nodes[6]
    assert c6.get("is_boundary") is True
    c6_notifs = c6.get("sent_boundary_notifications", [])
    assert len(c6_notifs) == 2, f"Node 6 should have 2 notifications, got {len(c6_notifs)}"
    c6_targets = {n["target"]: n["introduced_neighbor"] for n in c6_notifs}
    assert "C4 (Own Initiator)" in c6_targets
    assert c6_targets["C4 (Own Initiator)"] == "C8"
    assert "C8 (Competing Initiator)" in c6_targets
    assert c6_targets["C8 (Competing Initiator)"] == "C4"


def test_step6_all_10nodes_retain_full_metadata():
    """Assert all 10 nodes preserve neighbors, distribution, vector_10d, vrf_score, and role."""
    data = get_10node_step_data(6)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == 10

    for nid in range(1, 11):
        node = nodes[nid]
        # 1. neighbors
        assert "neighbors" in node
        assert sorted(node["neighbors"]) == sorted(STORYBOARD_10_ADJACENCY[nid])

        # 2. distribution
        assert "distribution" in node
        assert node["distribution"] == STORYBOARD_10_DISTRIBUTION[nid]
        assert sum(node["distribution"].values()) == 100

        # 3. vector_10d
        assert "vector_10d" in node
        assert len(node["vector_10d"]) == 10
        assert node["vector_10d"] == STORYBOARD_10_VECTORS[nid]
        assert sum(node["vector_10d"]) == pytest.approx(1.0, abs=1e-3)

        # 4. vrf_score
        assert "vrf_score" in node
        assert node["vrf_score"] == pytest.approx(STORYBOARD_10_VRF_SCORES[nid], abs=1e-4)

        # 5. role
        if nid in (2, 4, 8):
            assert node["role"] == "INITIATOR"
            assert node["is_initiator"] is True
        else:
            assert node["role"] == "CLIENT"


def test_step6_tonal_colors_and_boundary_edges():
    """Assert tonal pastel styling on member nodes and dashed boundary links."""
    data = get_10node_step_data(6)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Initiators: bold colors
    assert nodes[2]["color"] == "#059669"
    assert nodes[4]["color"] == "#ea580c"
    assert nodes[8]["color"] == "#7c3aed"

    # Zone 2 members: pastel emerald
    assert nodes[1]["color"] == "#34d399"
    assert nodes[3]["color"] == "#34d399"

    # Zone 4 members: pastel coral
    assert nodes[5]["color"] == "#fb923c"
    assert nodes[6]["color"] == "#fb923c"
    assert nodes[7]["color"] == "#fb923c"

    # Zone 8 members: pastel violet
    assert nodes[9]["color"] == "#a78bfa"
    assert nodes[10]["color"] == "#a78bfa"

    # Edges in Step 6: All physical links are uniform solid slate lines (#64748b, solid)
    edges = data["edges"]
    for e in edges:
        assert e.get("style") == "solid"
        assert e.get("line_color") == "#64748b"

    # Confirm Step 5 edges also have uniform solid slate styling
    data_step5 = get_10node_step_data(5)
    for e in data_step5["edges"]:
        assert e.get("style") == "solid"
        assert e.get("line_color") == "#64748b"


def test_step6_api_endpoints(client):
    """Assert GET and POST /api/v1/storyboard/step/6 return HTTP 200 with complete data."""
    res_get = client.get("/api/v1/storyboard/step/6")
    assert res_get.status_code == 200
    d_get = res_get.json()
    assert d_get["step"] == 6
    assert d_get["phase_badge"] == "STEP 6: ZONE CREATION & BOUNDARY DISCOVERY"
    assert len(d_get["nodes"]) == 10
    assert len(d_get["packet_events"]) == 4
    for n in d_get["nodes"]:
        assert n["status"] == "ASSIGNED"

    res_post = client.post("/api/v1/storyboard/step/6")
    assert res_post.status_code == 200
    d_post = res_post.json()
    assert d_post["step"] == 6
    assert len(d_post["nodes"]) == 10
    assert len(d_post["packet_events"]) == 4


def test_step6_steps_md_documentation():
    """Verify STEPS.md documents Step 6 requirements, memberships, and dual notifications."""
    with open("STEPS.md", "r", encoding="utf-8") as f:
        md = f.read()

    assert "## Step 6 — Official Zone Formation & Inter-Zone Boundary Discovery" in md
    assert "Zone 2 (Leader: C2 👑):" in md
    assert "Zone 4 (Leader: C4 👑):" in md
    assert "Zone 8 (Leader: C8 👑):" in md
    assert "Dual Boundary NEIGHBOR Notifications (Algorithm 3, L17-L20)" in md
    assert "Node 1 (Frontier between Zone 2 and Zone 4):" in md
    assert "Node 6 (Frontier between Zone 4 and Zone 8):" in md
    assert "Initiator Boundary Knowledge (Neighbor Zones Discovered)" in md
    assert "Initiator C2" in md
    assert "Initiator C4" in md
    assert "Initiator C8" in md


def test_step6_frontend_elements_and_logic():
    """Verify index.html and app.js implement Step 6 elements and modal logic."""
    with open("frontend/templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="stepNav6"' in html
    assert 'id="cardBoundaryDiscoverySection"' in html
    assert 'id="cardBoundaryDiscoveryBadge"' in html
    assert 'id="cardBoundaryDiscoveryContent"' in html

    with open("frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "renderStep6" in js
    assert "animateStep6BoundaryPackets" in js
    assert "ACTIVE PHASE: STEP 6: ZONE CREATION & BOUNDARY DISCOVERY" in js
    assert "Neighbor Zone Initiators Discovered:" in js
    assert "Dispatched Boundary Notifications Table" in js
    assert "zone-pastel-2" in js
    assert "zone-pastel-4" in js
    assert "stepNav" in js
    assert "cardBoundaryDiscoverySection" in js
    assert "cardBoundaryDiscoveryContent" in js
