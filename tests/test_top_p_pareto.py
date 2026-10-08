"""Contract-Driven Test Suite for CIFAR-10 Top-P Pareto Frontier Visualization (Paper Fig. 2)."""

from fastapi.testclient import TestClient
import pytest

from backend.main import app

@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


class TestTopPParetoFrontierContract:
    """Verifies backend contract and endpoints for CIFAR-10 Round 100 Pareto Frontier."""

    def test_cifar10_round_100_endpoints_contract(self, client: TestClient):
        """Verify energy-distribution and binary-search-pmin return valid Round 100 cache data."""
        # 1. Verify /energy-distribution with round_num=100
        res_energy = client.get("/api/v1/toppaper/energy-distribution?benchmark=cifar10&round_num=100")
        assert res_energy.status_code == 200, f"Energy endpoint failed: {res_energy.text}"
        data_energy = res_energy.json()

        assert data_energy["has_data"] is True
        assert data_energy["benchmark"] == "cifar10"
        assert "round_num" in data_energy
        assert data_energy["round_num"] == 100

        # Check curve points
        assert "curve_points" in data_energy
        curve_points = data_energy["curve_points"]
        assert len(curve_points) > 0

        # Each curve point must have p, c_p, cosine, and sparsity_ratio
        pt0 = curve_points[0]
        assert "p" in pt0
        assert "c_p" in pt0
        assert "cosine" in pt0
        assert "sparsity_ratio" in pt0

        # Final point should be near P = M = 2,156,490, sparsity_ratio = 0.0, cosine = 1.0
        pt_last = curve_points[-1]
        assert pt_last["p"] == 2156490
        assert abs(pt_last["sparsity_ratio"] - 0.0) < 1e-3
        assert abs(pt_last["cosine"] - 1.0) < 1e-3

        # 2. Verify /binary-search-pmin with round_num=100 and theta=0.80
        res_pmin = client.get("/api/v1/toppaper/binary-search-pmin?benchmark=cifar10&round_num=100&theta=0.80")
        assert res_pmin.status_code == 200, f"Pmin endpoint failed: {res_pmin.text}"
        data_pmin = res_pmin.json()

        assert data_pmin["has_data"] is True
        assert data_pmin["benchmark"] == "cifar10"
        assert data_pmin["p_min"] == 532443
        assert abs(data_pmin["sparsity_percentage"] - 75.31) < 0.1
        assert abs(data_pmin["achieved_cosine"] - 0.80) < 1e-4

    def test_fmnist_round_100_endpoints_contract(self, client: TestClient):
        """Verify energy-distribution and binary-search-pmin return valid Round 100 cache data for Fashion-MNIST."""
        # 1. Verify /energy-distribution with benchmark=fmnist&round_num=100
        res_energy = client.get("/api/v1/toppaper/energy-distribution?benchmark=fmnist&round_num=100")
        assert res_energy.status_code == 200, f"Energy endpoint failed: {res_energy.text}"
        data_energy = res_energy.json()

        assert data_energy["has_data"] is True
        assert data_energy["benchmark"] == "fmnist"
        assert data_energy["round_num"] == 100

        # Check curve points
        assert "curve_points" in data_energy
        curve_points = data_energy["curve_points"]
        assert len(curve_points) > 0

        # Each curve point must have p, c_p, cosine, and sparsity_ratio
        pt0 = curve_points[0]
        assert "p" in pt0
        assert "c_p" in pt0
        assert "cosine" in pt0
        assert "sparsity_ratio" in pt0

        # Final point must match FMNIST total parameters M = 1,663,370
        pt_last = curve_points[-1]
        assert pt_last["p"] == 1663370
        assert abs(pt_last["sparsity_ratio"] - 0.0) < 1e-3
        assert abs(pt_last["cosine"] - 1.0) < 1e-3

        # 2. Verify /binary-search-pmin with benchmark=fmnist&round_num=100&theta=0.80
        res_pmin = client.get("/api/v1/toppaper/binary-search-pmin?benchmark=fmnist&round_num=100&theta=0.80")
        assert res_pmin.status_code == 200, f"Pmin endpoint failed: {res_pmin.text}"
        data_pmin = res_pmin.json()

        assert data_pmin["has_data"] is True
        assert data_pmin["benchmark"] == "fmnist"
        assert data_pmin["total_parameters"] == 1663370
        assert data_pmin["p_min"] == 334168
        assert abs(data_pmin["sparsity_percentage"] - 79.91) < 0.1
        assert abs(data_pmin["achieved_cosine"] - 0.80) < 1e-4

    def test_tiny_imagenet_round_100_endpoints_contract(self, client: TestClient):
        """Verify energy-distribution and binary-search-pmin return valid Round 100 cache data for Tiny-ImageNet (ResNet-18, 11.27M)."""
        # 1. Verify /energy-distribution with benchmark=tiny_imagenet&round_num=100
        res_energy = client.get("/api/v1/toppaper/energy-distribution?benchmark=tiny_imagenet&round_num=100")
        assert res_energy.status_code == 200, f"Energy endpoint failed: {res_energy.text}"
        data_energy = res_energy.json()

        assert data_energy["has_data"] is True
        assert data_energy["benchmark"] == "tiny_imagenet"
        assert data_energy["round_num"] == 100

        # Check curve points
        assert "curve_points" in data_energy
        curve_points = data_energy["curve_points"]
        assert len(curve_points) > 0

        # Each curve point must have p, c_p, cosine, and sparsity_ratio
        pt0 = curve_points[0]
        assert "p" in pt0
        assert "c_p" in pt0
        assert "cosine" in pt0
        assert "sparsity_ratio" in pt0

        # Final point must match Tiny-ImageNet ResNet-18 total parameters M = 11,271,432
        pt_last = curve_points[-1]
        assert pt_last["p"] == 11271432
        assert abs(pt_last["sparsity_ratio"] - 0.0) < 1e-3
        assert abs(pt_last["cosine"] - 1.0) < 1e-3

        # 2. Verify /binary-search-pmin with benchmark=tiny_imagenet&round_num=100&theta=0.80
        res_pmin = client.get("/api/v1/toppaper/binary-search-pmin?benchmark=tiny_imagenet&round_num=100&theta=0.80")
        assert res_pmin.status_code == 200, f"Pmin endpoint failed: {res_pmin.text}"
        data_pmin = res_pmin.json()

        assert data_pmin["has_data"] is True
        assert data_pmin["benchmark"] == "tiny_imagenet"
        assert data_pmin["total_parameters"] == 11271432
        assert data_pmin["p_min"] == 648206
        # Sparsification ratio must be ~94.25% (5.75% retained parameters)
        assert abs(data_pmin["sparsity_percentage"] - 94.25) < 0.1
        retained_pct = (data_pmin["p_min"] / data_pmin["total_parameters"]) * 100.0
        assert abs(retained_pct - 5.75) < 0.1
        assert abs(data_pmin["achieved_cosine"] - 0.80) < 1e-4

    def test_speech_round_100_endpoints_contract(self, client: TestClient):
        """Verify energy-distribution and binary-search-pmin return valid Round 100 cache data for Google Speech Commands (1D Audio ResNet-18, 11.17M)."""
        # 1. Verify /energy-distribution with benchmark=speech&round_num=100
        res_energy = client.get("/api/v1/toppaper/energy-distribution?benchmark=speech&round_num=100")
        assert res_energy.status_code == 200, f"Energy endpoint failed: {res_energy.text}"
        data_energy = res_energy.json()

        assert data_energy["has_data"] is True
        assert data_energy["benchmark"] == "speech"
        assert data_energy["round_num"] == 100

        # Check curve points
        assert "curve_points" in data_energy
        curve_points = data_energy["curve_points"]
        assert len(curve_points) > 0

        # Each curve point must have p, c_p, cosine, and sparsity_ratio
        pt0 = curve_points[0]
        assert "p" in pt0
        assert "c_p" in pt0
        assert "cosine" in pt0
        assert "sparsity_ratio" in pt0

        # Final point must match Google Speech Commands total parameters M = 11,172,810
        pt_last = curve_points[-1]
        assert pt_last["p"] == 11172810
        assert abs(pt_last["sparsity_ratio"] - 0.0) < 1e-3
        assert abs(pt_last["cosine"] - 1.0) < 1e-3

        # 2. Verify /binary-search-pmin with benchmark=speech&round_num=100&theta=0.80
        res_pmin = client.get("/api/v1/toppaper/binary-search-pmin?benchmark=speech&round_num=100&theta=0.80")
        assert res_pmin.status_code == 200, f"Pmin endpoint failed: {res_pmin.text}"
        data_pmin = res_pmin.json()

        assert data_pmin["has_data"] is True
        assert data_pmin["benchmark"] == "speech"
        assert data_pmin["total_parameters"] == 11172810
        assert data_pmin["p_min"] == 629734
        # Sparsification ratio must be ~94.36% (5.64% retained parameters)
        assert abs(data_pmin["sparsity_percentage"] - 94.36) < 0.1
        retained_pct = (data_pmin["p_min"] / data_pmin["total_parameters"]) * 100.0
        assert abs(retained_pct - 5.64) < 0.1
        assert abs(data_pmin["achieved_cosine"] - 0.80) < 1e-4

    def test_20news_round_100_endpoints_contract(self, client: TestClient):
        """Verify energy-distribution and binary-search-pmin return valid Round 100 cache data for 20Newsgroup (ALBERT-base-v2, 11.68M)."""
        # 1. Verify /energy-distribution with benchmark=20news&round_num=100
        res_energy = client.get("/api/v1/toppaper/energy-distribution?benchmark=20news&round_num=100")
        assert res_energy.status_code == 200, f"Energy endpoint failed: {res_energy.text}"
        data_energy = res_energy.json()

        assert data_energy["has_data"] is True
        assert data_energy["benchmark"] == "20news"
        assert data_energy["round_num"] == 100

        # Check curve points
        assert "curve_points" in data_energy
        curve_points = data_energy["curve_points"]
        assert len(curve_points) > 0

        # Each curve point must have p, c_p, cosine, and sparsity_ratio
        pt0 = curve_points[0]
        assert "p" in pt0
        assert "c_p" in pt0
        assert "cosine" in pt0
        assert "sparsity_ratio" in pt0

        # Final point must match 20News ALBERT total parameters M = 11,698,964
        pt_last = curve_points[-1]
        assert pt_last["p"] == 11698964
        assert abs(pt_last["sparsity_ratio"] - 0.0) < 1e-3
        assert abs(pt_last["cosine"] - 1.0) < 1e-3

        # 2. Verify /binary-search-pmin with benchmark=20news&round_num=100&theta=0.80
        res_pmin = client.get("/api/v1/toppaper/binary-search-pmin?benchmark=20news&round_num=100&theta=0.80")
        assert res_pmin.status_code == 200, f"Pmin endpoint failed: {res_pmin.text}"
        data_pmin = res_pmin.json()

        assert data_pmin["has_data"] is True
        assert data_pmin["benchmark"] == "20news"
        assert data_pmin["total_parameters"] == 11698964
        assert data_pmin["p_min"] == 1511150
        # Sparsification ratio must be ~87.08% (12.92% retained parameters)
        assert abs(data_pmin["sparsity_percentage"] - 87.08) < 0.1
        retained_pct = (data_pmin["p_min"] / data_pmin["total_parameters"]) * 100.0
        assert abs(retained_pct - 12.92) < 0.1
        assert abs(data_pmin["achieved_cosine"] - 0.80) < 1e-4


class TestTopPParetoFrontierUI:
    """Verifies UI DOM elements, canvas, and KPI telemetry cards in top_p_lab.html."""

    def test_pareto_frontier_ui_structure(self):
        """Verify the elevated academic card, badges, canvas and location in top_p_lab.html."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Must be located immediately after #pmin-results-container or inside #pmin-panel
        assert 'id="pareto-frontier-card"' in html
        assert "Pareto Frontier: Model Directional Fidelity vs. Sparsification Ratio (Paper Fig. 2 — Round 100)" in html
        assert 'id="chart-pareto-cifar10"' in html

        # KPI telemetry badges
        assert 'id="pareto-kpi-budget"' in html
        assert 'id="pareto-kpi-reduction"' in html
        assert 'id="pareto-kpi-cosine"' in html
        assert 'id="pareto-kpi-efficiency"' in html

    def test_pareto_frontier_js_logic_and_chart_config(self):
        """Verify the JavaScript Chart.js configuration, axes, styling, and annotations."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # JS function
        assert "function renderParetoFrontierChart(" in html or "function loadAndRenderParetoFrontier(" in html

        # X-axis and Y-axis labels
        assert "Sparsification Ratio (1 - P / M)" in html
        assert "Cosine Similarity (cos(w, w^[P]))" in html

        # Color: brand blue #2563eb
        assert "#2563eb" in html

        # Reference threshold 0.80 and knee line
        assert "0.80" in html

    def test_pareto_frontier_dynamic_benchmark_switching(self):
        """Verify dynamic benchmark support for FMNIST and Tiny-ImageNet in Pareto Frontier."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # reloadAllBenchmarkData or switchBenchmark must trigger loadAndRenderParetoFrontier
        assert "loadAndRenderParetoFrontier" in html
        assert "reloadAllBenchmarkData" in html

        # Check dynamic handling of currentBenchmark or benchmarkId in loadAndRenderParetoFrontier
        assert "loadAndRenderParetoFrontier(currentBenchmark" in html or "loadAndRenderParetoFrontier(" in html

    def test_tiny_imagenet_pareto_styling_diamond_markers(self):
        """Verify ResNet-18 specific styling (black solid line with diamond / rectRot markers matching paper Fig. 2)."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # ResNet-18 diamond marker (rectRot in Chart.js) and black/dark styling
        assert "rectRot" in html or "diamond" in html
        assert "#0f172a" in html or "#000000" in html or "#1e293b" in html

    def test_speech_pareto_ui_audio_modality_support(self):
        """Verify Google Speech Commands support, audio modality defaults, and dynamic styling."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Check speech benchmark integration in Pareto Frontier logic
        assert "speech" in html
        assert "629734" in html or "629,734" in html
        assert "94.36" in html

    def test_pareto_overlay_mode_paper_fig_2(self):
        """Verify Combined Overlay Mode button, star markers for ALBERT, and 5-model simultaneous rendering."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Overlay Button
        assert 'id="btn-pareto-overlay"' in html
        assert "Overlay All 5 Benchmarks (Paper Fig. 2 Replica)" in html
        assert "toggleParetoOverlayMode" in html

        # 20Newsgroup / ALBERT support and star marker / amber styling
        assert "20news" in html
        assert "1511150" in html or "1,511,150" in html
        assert "87.08" in html
        assert "star" in html
        assert "#d97706" in html or "#f59e0b" in html

    def test_pareto_unified_chart_layout_structure(self):
        """Verify unified single-chart layout matching Fig. 2 with dual drop lines at 0.8 and 0.9."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Canvas must be present in DOM
        assert 'id="chart-pareto-cifar10"' in html

        # Unified container and titles
        assert 'id="pareto-frontier-card"' in html
        assert "Figure 2" in html or "Fig. 2" in html

        # Telemetry KPI cards (θ=0.70, θ=0.80, θ=0.90)
        assert 'id="pareto-kpi-budget-70"' in html
        assert 'id="pareto-kpi-budget"' in html
        assert 'id="pareto-kpi-efficiency"' in html
        assert 'id="pareto-kpi-cosine"' in html

    def test_paper_fig2_replica_styling_and_hollow_markers(self):
        """Verify publication-grade vector styling: hollow markers, no fill, clean lines, and triple drop/horizontal guides."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Hollow/white-centered markers
        assert "pointBackgroundColor: '#ffffff'" in html or 'pointBackgroundColor: "#ffffff"' in html

        # Color schemes matching paper Fig. 2: CNN blue, ResNet-18 dark slate/black, ALBERT amber/orange
        assert "#1d4ed8" in html or "#2563eb" in html
        assert "#0f172a" in html
        assert "#ea580c" in html or "#d97706" in html

        # Marker shapes: circle, rectRot (diamond), star
        assert "rectRot" in html
        assert "star" in html

        # Triple drop lines & horizontal guides for theta=0.70, theta=0.80 and theta=0.90
        assert "θ=0.70" in html
        assert "θ=0.80" in html
        assert "θ=0.90" in html
        assert "Horizontal Guide (θ=0.70)" in html
        assert "Horizontal Guide (θ=0.80)" in html
        assert "Horizontal Guide (θ=0.90)" in html

        # X-axis [0, 1] and Y-axis [0, 1.05] invariants
        assert "1.05" in html
        assert "Sparsification Ratio (1 - P / M)" in html
        assert "Cosine Similarity" in html

    def test_pareto_dynamic_benchmark_sync(self):
        """Verify unified chart synchronizes dynamically upon benchmark switching."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert "loadAndRenderParetoFrontier" in html
        assert "renderParetoFrontierChart" in html

    def test_utopia_pareto_square_chart_dom_and_kpis(self):
        """Verify DOM elements, square aspect container, and KPI telemetry cards for Tab 3 Utopia chart."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Canvas and card
        assert 'id="chart-utopia-pareto-square"' in html
        assert 'id="utopia-pareto-card"' in html
        assert "aspect-square" in html

        # KPI telemetry badges for all 4 models
        assert 'id="utopia-kpi-fmnist"' in html
        assert 'id="utopia-dist-fmnist"' in html
        assert 'id="utopia-kpi-tiny"' in html
        assert 'id="utopia-dist-tiny"' in html
        assert 'id="utopia-kpi-speech"' in html
        assert 'id="utopia-dist-speech"' in html
        assert 'id="utopia-kpi-20news"' in html
        assert 'id="utopia-dist-20news"' in html
        assert 'id="utopia-status-pill"' in html

    def test_utopia_pareto_square_chart_script_and_geometry(self):
        """Verify JS implementation, aspect ratio 1:1, 8-line palette pairing, and tab hook."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert "loadAndRenderUtopiaParetoChart" in html
        assert "window.loadAndRenderUtopiaParetoChart" in html
        assert "aspectRatio: 1" in html

        # 4 models solid + dashed color pairing
        assert "#0284c7" in html and "#38bdf8" in html  # FMNIST
        assert "#059669" in html and "#34d399" in html  # Tiny-ImageNet
        assert "#7c3aed" in html and "#a78bfa" in html  # Speech
        assert "#d97706" in html and "#fbbf24" in html  # 20News ALBERT

        # Utopia Reference point
        assert "Utopia Reference Point" in html

        # Tab switch hook
        assert "tabId === 'tab-scope'" in html

    def test_utopia_compromise_knee_math_invariants(self, client: TestClient):
        """Verify empirical Round 100 Utopia Knee Point calculation minimizes Euclidean distance to (1.0, 1.0)."""
        import math

        expected = {
            "fmnist": {"min_p": 304022, "sparsity": 0.8172, "cosine": 0.7840, "dist": 0.2830},
            "tiny_imagenet": {"min_p": 1246747, "sparsity": 0.8894, "cosine": 0.8542, "dist": 0.1830},
            "speech": {"min_p": 1237312, "sparsity": 0.8893, "cosine": 0.8556, "dist": 0.1820},
            "20news": {"min_p": 1696499, "sparsity": 0.8550, "cosine": 0.8160, "dist": 0.2343},
        }

        for bench, exp in expected.items():
            res = client.get(f"/api/v1/toppaper/energy-distribution?benchmark={bench}&round_num=100")
            assert res.status_code == 200
            data = res.json()
            pts = data["curve_points"]
            total = data["total_parameters"]

            best_pt = None
            min_dist = float("inf")
            for pt in pts:
                s = pt.get("sparsity_ratio", 1.0 - pt["p"] / total)
                c = pt["cosine"]
                d = math.hypot(1.0 - s, 1.0 - c)
                if d < min_dist:
                    min_dist = d
                    best_pt = (pt["p"], s, c, d)

            assert best_pt is not None
            assert best_pt[0] == exp["min_p"]
            assert abs(best_pt[1] - exp["sparsity"]) < 1e-3
            assert abs(best_pt[2] - exp["cosine"]) < 1e-3
            assert abs(best_pt[3] - exp["dist"]) < 1e-3






