"""Edge class for the simulation graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .drone import Drone
    from .vertex import Vertex


class Edge:
    """Represents an undirected connection between two vertices."""

    def __init__(
        self,
        src: Vertex,
        dst: Vertex,
        max_link_capacity: int = 1,
    ) -> None:
        """Initialize an edge between two vertices.

        Args:
            src: source vertex.
            dst: destination vertex.
            max_link_capacity: maximum number of drones allowed on the edge.

        """
        self.src: Vertex = src
        self.dst: Vertex = dst
        self.capacity: int = max_link_capacity
        self.max_cap: int = max_link_capacity
        self.closed: bool = False
        self.width: int = 3
        self.color: tuple[int, int, int] = (60, 60, 60)
        self.show_label: bool = True

    def get_other(self, vertex: Vertex) -> Vertex:
        """Return the opposite vertex of the edge.

        Args:
            vertex: one of the edge's vertices.

        """
        if vertex is self.src:
            return self.dst
        if vertex is self.dst:
            return self.src
        raise ValueError("vertex must be src or dst")

    def draw(self,
             screen: pygame.surface.Surface,
             drones: list[Drone]) -> None:
        """Draw the edge and its current load on the screen.

        Args:
            screen: Pygame surface.
            drones: list of all drones to calculate edge load.

        """
        # late import
        from .renderer import get_font

        src_rect = self.src.rect
        dst_rect = self.dst.rect
        if src_rect is None or dst_rect is None:
            return
        pygame.draw.line(
            screen,
            self.color,
            src_rect.center,
            dst_rect.center,
            self.width,
        )
        if not self.show_label:
            return
        font = get_font(22)
        present = sum(
            1
            for d in drones
            if d.target is not None
            and {d.pos, d.target} == {self.src, self.dst}
        )
        label = font.render(
            f"{present} / {self.max_cap}",
            True,
            (0, 0, 0),
        )
        centerx = (src_rect.centerx + dst_rect.centerx) / 2
        centery = (src_rect.centery + dst_rect.centery) / 2
        rect = label.get_rect(center=(centerx, centery + 15))
        screen.blit(label, rect)

    def __str__(self) -> str:
        """Return a string representation of the edge."""
        return f"{self.src.name}-{self.dst.name} (cap {self.max_cap})"

    def __repr__(self) -> str:
        """Return a string representation of the edge."""
        return self.__str__()
