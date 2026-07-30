"""Utilities for converting adjacency lists to simulation graphs."""

from __future__ import annotations

import math

from .edge import Edge
from .vertex import Vertex


def circle_layout(n: int, radius: int = 1000) -> list[tuple[int, int]]:
    """Calculate integer coordinates for n points spaced evenly on a circle.

    Args:
        n: Number of points.
        radius: Radius of the circle.

    Returns:
        List of (x, y) coordinates.

    """
    coords = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        x = round(radius * math.cos(angle))
        y = round(radius * math.sin(angle))
        coords.append((x, y))
    return coords


def adj_to_graph(
    adj: list[set[int]],
    coords: list[tuple[int, int]],
    nb_drones: int,
    start: int,
    end: int,
) -> tuple[int, list[Vertex], list[Edge]]:
    """Convert an adjacency list into vertices and edges for the simulation.

    Args:
        adj: Adjacency list (indices 0..n-1).
        coords: Coordinates for each node.
        nb_drones: Number of drones.
        start: Index of the start node.
        end: Index of the end node.

    Returns:
        A tuple containing the number of drones, vertices, and edges.

    Raises:
        ValueError: If start == end, indices are out of range, or lengths
        mismatch.

    """
    n = len(adj)
    if len(coords) != n:
        raise ValueError("coords e adj hanno lunghezze diverse")
    if not 0 <= start < n or not 0 <= end < n:
        raise ValueError("start o end fuori range")
    if start == end:
        raise ValueError("start ed end coincidono")
    vertices = []
    for i in range(n):
        vertices.append(
            Vertex(
                nb_drones,
                str(i),
                coords[i],
                start=i == start,
                end=i == end,
                max_drones=nb_drones,
            )
        )
    edges = []
    for i in range(n):
        for j in adj[i]:
            if i < j:
                edges.append(Edge(vertices[i], vertices[j], nb_drones))
    return nb_drones, vertices, edges
