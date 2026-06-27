import math

from app.config_loader import load_universe_config
from app.geometry import scaled_center, tower_position, void_distance_km
from app.graph import UniverseGraph


def test_config_loading_and_scaling():
    config = load_universe_config()
    graph = UniverseGraph(config)
    assert config.universe_metadata.system_name == "Zeta-26"
    assert len(graph.nodes) == 6
    assert scaled_center(graph.nodes["Boreas"], graph.metadata) == (15_000_000.0, 10_000_000.0)


def test_tower_zero_top_and_clockwise_order():
    config = load_universe_config()
    planet = next(node for node in config.nodes if node.id == "Aegis")
    top = tower_position(planet, config.universe_metadata, 0)
    right = tower_position(planet, config.universe_metadata, 2)
    assert math.isclose(top.x_km, 0.0, abs_tol=1e-6)
    assert math.isclose(top.y_km, planet.radius_km, rel_tol=1e-9)
    assert right.x_km > 0
    assert math.isclose(right.y_km, 0.0, abs_tol=1e-6)


def test_void_distance_formula_and_lmax_pruning():
    config = load_universe_config()
    graph = UniverseGraph(config)
    aegis = graph.nodes["Aegis"]
    boreas = graph.nodes["Boreas"]
    expected = (
        math.hypot(boreas.x - aegis.x, boreas.y - aegis.y)
        * graph.metadata.coordinate_scale_unit_km
        - (aegis.radius_km + aegis.atmosphere_thickness_km)
        - (boreas.radius_km + boreas.atmosphere_thickness_km)
    )
    assert math.isclose(void_distance_km(aegis, boreas, graph.metadata), expected)
    assert ("Aegis", "Boreas") in graph.links
    assert ("Aegis", "Caelum") not in graph.links


def test_closest_tower_pair_indices_are_valid():
    graph = UniverseGraph(load_universe_config())
    link = graph.links[("Aegis", "Boreas")]
    assert 0 <= link.send_tower < graph.nodes["Aegis"].active_towers
    assert 0 <= link.receive_tower < graph.nodes["Boreas"].active_towers
    assert link.tower_distance_km > 0
