"""Graph class managing vertices, edges, and drones."""

from __future__ import annotations

import pygame

from .drone import Drone
from .edge import Edge
from .vertex import Vertex


class Graph:
    """Represents the simulation graph."""

    def __init__(
        self,
        nb_drones: int,
        vertices: list[Vertex],
        edges: list[Edge],
    ) -> None:
        """Initialize the graph with drones, vertices, and edges.

        Args:
            nb_drones: Total number of drones.
            vertices: List of vertices in the graph.
            edges: List of edges in the graph.

        """
        self.vertices = vertices
        self.edges = edges
        start = next((v for v in vertices if v.start), None)
        end = next((v for v in vertices if v.end), None)
        if start is None or end is None:
            raise ValueError("the graph must have a start and an end")
        self.start: Vertex = start
        self.end: Vertex = end
        self.grid: dict[Vertex, list[Edge]] = {
            v: [e for e in edges if e.src is v or e.dst is v] for v in vertices
        }
        self.drones: list[Drone] = [
            Drone(self.start, i) for i in range(1, nb_drones + 1)
        ]
        self.turn_count = 0

    def get_neighbors(self, vertex: Vertex) -> list[Vertex]:
        """Return a list of accessible neighboring vertices.

        Args:
            vertex: The vertex to find neighbors for.

        """
        out: list[Vertex] = []
        for edge in self.grid[vertex]:
            if edge.closed or edge.capacity <= 0:
                continue
            other = edge.get_other(vertex)
            if other.closed or other.blocked:
                continue
            out.append(other)
        return out

    def get_edge_from_vertices(self, v1: Vertex, v2: Vertex) -> Edge | None:
        """Return the edge connecting two vertices, if it exists.

        Args:
            v1: First vertex.
            v2: Second vertex.

        """
        for edge in self.grid[v1]:
            if edge.get_other(v1) is v2:
                return edge
        return None

    def draw_graph(self,
                   screen: pygame.surface.Surface,
                   frac: float = 0.0) -> None:
        """Draw all graph elements (edges, vertices, drones) on the screen.

        Args:
            screen: Pygame surface.
            frac: Animation progress.

        """
        for edge in self.edges:
            edge.draw(screen, self.drones)
        for vertex in self.vertices:
            vertex.draw(screen, self.drones)
        for drone in self.drones:
            drone.draw(screen, frac)

    def __str__(self) -> str:
        """Return a string representation of the graph adjacency list."""
        return "\n".join(
            f"{v}: {self.get_neighbors(v)}" for v in self.vertices
        )
