"""Demo for Watts-Strogatz small-world networks."""

import random

import pygame

from .graph import Graph
from .bonus_metrics import clustering_coefficient
from .renderer import Panel, Renderer
from .scheduler import Scheduler
from .bonus_small_world import watts_strogatz
from .bonus_ws_graph import adj_to_graph, circle_layout


def is_ring_edge(i: int, j: int, n: int, k: int) -> bool:
    """Check if an edge (i, j) belongs to the original ring lattice.

    Args:
        i: first node index.
        j: second node index.
        n: total number of nodes.
        k: number of neighbors in the original ring.

    """
    gap = abs(i - j)
    return min(gap, n - gap) <= k // 2


def _print_simulation_start(coords: list[tuple[int, int]]) -> None:
    print("\n\nINIZIO SIMULAZIONE DI WATTS-STROGATZ")


def build_panels(
    n: int, k: int, p: float, nb_drones: int, rng: random.Random
) -> list[Panel]:
    """Create three panels for comparison: regular, small-world, and random.

    Args:
        n: number of nodes.
        k: neighbors per node.
        p: rewiring probability for the small-world panel.
        nb_drones: number of drones.
        rng: random number generator.

    """
    start, end = rng.sample(range(n), 2)
    coords = circle_layout(n)
    _print_simulation_start(coords)
    specs = [
        (0.0, "Regolare"),
        (p, f"«Mondo piccolo» (p = {p:g})"),
        (1.0, "Casuale"),
    ]
    panels: list[Panel] = []
    for prob, title in specs:
        adj = watts_strogatz(n, k, prob, rng)
        nb, vertices, edges = adj_to_graph(adj, coords, nb_drones, start, end)
        for vertex in vertices:
            vertex.color = (41, 41, 41)
        vertices[start].color = (0, 255, 0)
        vertices[end].color = (255, 0, 0)
        for edge in edges:
            ring = is_ring_edge(int(edge.src.name), int(edge.dst.name), n, k)
            edge.color = (150, 150, 150) if ring else (200, 60, 60)
        graph = Graph(nb, vertices, edges)
        scheduler = Scheduler(graph)
        scheduler.edmonds_karp()
        panels.append(
            Panel(
                graph=graph,
                scheduler=scheduler,
                title=title,
                node_radius=6,
                show_labels=False,
                clustering=clustering_coefficient(adj),
            )
        )
    return panels


def run_demo(
    screen: pygame.surface.Surface,
    n: int = 100,
    k: int = 4,
    p: float = 0.2,
    nb_drones: int = 10,
    seed: int | None = None,
) -> None:
    """Run the Watts-Strogatz demonstration.

    Args:
        screen: Pygame surface.
        n: number of nodes.
        k: neighbors per node.
        p: rewiring probability.
        nb_drones: number of drones.
        seed: random seed.

    """
    rng = random.Random(seed)
    renderer = Renderer(screen, build_panels(n, k, p, nb_drones, rng))
    renderer.hint = "R: rigenera"
    while renderer.running:
        renderer.render()
        renderer.step()
        if pygame.K_r in renderer.unhandled_keys:
            renderer.set_panels(build_panels(n, k, p, nb_drones, rng))
