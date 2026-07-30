"""Drone class for the simulation."""

import pygame
from pygame.sprite import Sprite

from .vertex import Vertex


class Drone(Sprite):
    """Represents a drone in the simulation.

    Drones move between vertices in turns, potentially incurring costs
    based on zone types.
    """

    def __init__(self, vertex: Vertex, num: int = 1) -> None:
        """Initialize the drone at a starting vertex.

        Args:
            vertex: initial position.
            num: drone identifier.

        """
        super().__init__()
        self.num = num
        self.pos = vertex
        # Vertice da cui parte il movimento in corso: serve a stampare il
        # nome della connessione e a capire chi si è mosso nel turno.
        self.prev = vertex
        self.target: Vertex | None = None
        self.path: list[Vertex] = []
        self.radius: int = 6
        self.cost: int = 1
        self.left: int = 0

    def update_target(self, target: Vertex) -> None:
        """Set a new target vertex for the drone.

        Args:
            target: the vertex to move towards.

        """
        self.prev = self.pos
        self.target = target
        self.cost = target.cost()
        self.left = self.cost

    def move(self) -> None:
        """Advance the drone's movement by one turn."""
        if self.target is None:
            return
        self.left -= 1
        if self.left <= 0:
            self.pos = self.target
            self.target = None

    def flying(self) -> bool:
        """Check if the drone is currently moving between vertices."""
        return self.target is not None and self.left < self.cost

    def progress(self, frac: float) -> float:
        """Calculate the progress along the current edge in [0, 1].

        Args:
            frac: Animation progress within the current turn.

        """
        if self.target is None:
            return 0.0
        return min(1.0, (self.cost - self.left + frac) / self.cost)

    def point(self, frac: float) -> tuple[float, float]:
        """Calculate the interpolated screen position.

        Args:
            frac: Animation progress.

        """
        pos_rect = self.pos.rect
        if pos_rect is None:
            return (0.0, 0.0)
        ax, ay = pos_rect.center
        if self.target is None:
            return (ax, ay)
        target_rect = self.target.rect
        if target_rect is None:
            return (ax, ay)
        bx, by = target_rect.center
        p = self.progress(frac)
        return (ax + p * (bx - ax), ay + p * (by - ay))

    def draw(self, screen: pygame.surface.Surface, frac: float = 0.0) -> None:
        """Draw the drone on the screen.

        Args:
            screen: Pygame surface to draw on.
            frac: animation progress.

        """
        x, y = self.point(frac)
        center = (int(x), int(y))
        pygame.draw.circle(screen, (20, 20, 220), center, self.radius)
        pygame.draw.circle(screen, (200, 220, 255), center, self.radius, 2)

    def __str__(self) -> str:
        """Return the name of the current vertex."""
        return self.pos.name
