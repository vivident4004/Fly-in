"""Functions for generating Watts-Strogatz small-world graphs."""

import random

from .bonus_metrics import bfs_distances


def ring_lattice(n: int, k: int) -> list[set[int]]:
    """Create a regular ring with n nodes each connected to k neighbors.

    Each node i is connected to k // 2 preceding and k // 2 following nodes.

    Args:
        n: number of nodes.
        k: number of neighbors per node (must be even and < n).

    Returns:
        Symmetric adjacency list.

    Raises:
        ValueError: if k is odd, negative, or k >= n.

    """
    if k % 2 == 1 or k < 0 or k >= n or n < 1:
        raise ValueError
    adj: list[set[int]] = [set() for _ in range(n)]
    for i in range(n):
        for d in range(1, k // 2 + 1):
            j = (i + d) % n
            adj[i].add(j)
            adj[j].add(i)
    return adj


def rewire(
    adj: list[set[int]], p: float, rng: random.Random
) -> list[set[int]]:
    """Randomly rewire a fraction p of edges following Watts-Strogatz (1998).

    Args:
        adj: starting ring lattice (modified in place).
        p: rewiring probability in [0, 1].
        rng: random number generator.

    Returns:
        The rewired adjacency list.

    Raises:
        ValueError: if p is not in [0, 1].

    """
    if not 0.0 <= p <= 1.0:
        raise ValueError
    n = len(adj)
    k = len(adj[0])
    for d in range(1, k // 2 + 1):
        for i in range(n):
            if rng.random() >= p:
                continue
            j = (i + d) % n
            candidates = [m for m in range(n) if m != i and m not in adj[i]]
            if not candidates:
                continue
            m = rng.choice(candidates)
            adj[i].remove(j)
            adj[j].remove(i)
            adj[i].add(m)
            adj[m].add(i)
    return adj


def is_connected(adj: list[set[int]]) -> bool:
    """Check if the graph is connected starting from node 0."""
    return -1 not in bfs_distances(adj, 0)


def watts_strogatz(
    n: int,
    k: int,
    p: float,
    rng: random.Random,
    max_attempts: int = 100,
) -> list[set[int]]:
    """Generate a connected Watts-Strogatz small-world graph.

    Args:
        n: number of nodes.
        k: neighbors per node (even and < n).
        p: rewiring probability.
        rng: random number generator.
        max_attempts: maximum attempts to generate a connected graph.

    Returns:
        Connected adjacency list.

    Raises:
        RuntimeError: if graph remains disconnected after max_attempts.

    """
    for _ in range(max_attempts):
        adj = rewire(ring_lattice(n, k), p, rng)
        if is_connected(adj):
            return adj
    raise RuntimeError(f"grafo disconnesso dopo {max_attempts} tentativi")
