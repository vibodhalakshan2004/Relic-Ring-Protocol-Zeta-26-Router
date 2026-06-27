import math

from app.config_loader import load_universe_config
from app.geometry import void_distance_km
from app.graph import UniverseGraph
from app.latency import internal_latency, void_latency


def test_void_latency_formula():
    graph = UniverseGraph(load_universe_config())
    origin = graph.nodes["Aegis"]
    destination = graph.nodes["Boreas"]
    distance = void_distance_km(origin, destination, graph.metadata)
    latency = void_latency(origin, destination, distance, graph.metadata)
    expected = (
        (origin.atmosphere_thickness_km * origin.refraction_index)
        + (destination.atmosphere_thickness_km * destination.refraction_index)
        + distance
    ) / graph.metadata.speed_of_light_kms * 1000
    assert math.isclose(latency.total_void_ms, expected)


def test_internal_latency_same_tower_dedupes_processing():
    graph = UniverseGraph(load_universe_config())
    latency = internal_latency(graph.nodes["Aegis"], 3, 3, graph.metadata)
    assert latency.segments_travelled == 0
    assert latency.distinct_towers_hit == 1
    assert latency.fiber_ms == 0
    assert latency.tower_processing_ms == graph.metadata.tower_processing_delay_ms


def test_internal_latency_uses_shortest_ring_segment():
    graph = UniverseGraph(load_universe_config())
    latency = internal_latency(graph.nodes["Aegis"], 0, 7, graph.metadata)
    assert latency.segments_travelled == 1
    assert latency.distinct_towers_hit == 2
    assert latency.arc_length_km > 0
