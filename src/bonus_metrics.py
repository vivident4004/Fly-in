"""Metrics for analyzing graph structures."""

from __future__ import annotations

import random
from collections import deque


def bfs_distances(adj: list[set[int]], src: int) -> list[int]:
    """Calculate the shortest distance from src to all other nodes using BFS.

    Args:
        adj: adjacency list where adj[i] contains neighbors of node i.
        src: starting node.

    Returns:
        List of distances, where -1 indicates unreachable nodes.

    """
    dist = [-1] * len(adj)
    dist[src] = 0
    queue = deque([src])
    while queue:
        i = queue.popleft()
        for j in adj[i]:
            if dist[j] == -1:
                dist[j] = dist[i] + 1
                queue.append(j)
    return dist


def clustering_coefficient(adj: list[set[int]]) -> float:
    """Calculate the average clustering coefficient of the graph.

    The clustering coefficient measures the degree to which nodes in a graph
    tend to cluster together.

    Returns:
        The average clustering coefficient in [0, 1].

    """
    total = 0.0
    for i in range(len(adj)):
        d = len(adj[i])
        if d < 2:
            continue
        links = 0
        for j in adj[i]:
            for m in adj[i]:
                if j < m and m in adj[j]:
                    links += 1
        total += 2 * links / (d * (d - 1))
    return total / len(adj)


def average_path_length(
    adj: list[set[int]],
    rng: random.Random,
    samples: int | None = None,
) -> float:
    """Calculate the average shortest path length between node pairs.

    Args:
        adj: adjacency list.
        rng: random number generator for sampling.
        samples: number of source nodes to sample for estimation. If None,
            calculate the exact value.

    Returns:
        The average path length.

    """
    n = len(adj)
    if samples is None or samples >= n:
        sources = list(range(n))
    else:
        sources = rng.sample(range(n), samples)
    total = 0
    count = 0
    for src in sources:
        for dist in bfs_distances(adj, src):
            if dist > 0:
                total += dist
                count += 1
    return total / count
