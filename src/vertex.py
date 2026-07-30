"""Vertex class for the simulation graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .drone import Drone

import hashlib

import pygame
from pygame.sprite import Sprite


def color_from_name(name: str) -> tuple[int, int, int]:
    """Generate an RGB color from the MD5 hash of a name."""
    digest = hashlib.md5(name.encode()).digest()
    return (digest[0], digest[1], digest[2])


_HALO = (255, 215, 0)
_ZONE_MARKERS = {"restricted": "R", "priority": "P", "blocked": "X"}


def _zone_marker(zone: str) -> str | None:
    return _ZONE_MARKERS.get(zone)


class Vertex(Sprite):
    """Represents a node in the simulation graph."""

    def __init__(
        self,
        nb_drones: int,
        name: str,
        coord: tuple[int, int],
        start: bool = False,
        end: bool = False,
        color: str = "black",
        max_drones: int = 1,
        zone: str = "normal",
    ) -> None:
        """Initialize a vertex.

        Args:
            nb_drones: total number of drones in the simulation.
            name: vertex name.
            coord: (x, y) coordinates.
            start: true if this is the starting hub.
            end: true if this is the ending hub.
            color: color name for hashing.
            max_drones: maximum number of drones allowed at the vertex.
            zone: zone type (normal, restricted, priority, blocked).

        """
        super().__init__()
        self.name = name
        self.coord = coord
        self.start = start
        self.end = end
        self.color: tuple[int, int, int] = color_from_name(color)
        self.zone = zone
        self.blocked = zone == "blocked"
        self.max_drones = nb_drones if (start or end) else max_drones

        self.capacity: int = self.max_drones
        self.closed: bool = False
        self.steps: int = 0
        self.parent: Vertex | None = None

        self.radius: int = 15
        self.show_label: bool = True
        self.show_name: bool = True
        self.label_size: int = 18

        self.image = pygame.surface.Surface((30, 30), pygame.SRCALPHA)
        if self.image is not None:
            self.rect = self.image.get_rect()

    def set_screen_pos(
        self, scale_x: float, scale_y: float, offset_x: float, offset_y: float
    ) -> None:
        """Calculate and set the screen position based on scale and offset."""
        if self.rect is not None:
            self.rect.center = (
                int(offset_x + self.coord[0] * scale_x),
                int(offset_y + self.coord[1] * scale_y),
            )

    def cost(self) -> int:
        """Return the turn cost to enter this vertex."""
        if self.zone == "restricted":
            return 2
        return 1

    def draw(self,
             screen: pygame.surface.Surface,
             drones: list[Drone]) -> None:
        """Draw the vertex and its current load on the screen.

        Args:
            screen: Pygame surface.
            drones: list of all drones to calculate vertex load.

        """
        # late import
        from .renderer import get_font

        if self.rect is None:
            return
        center = self.rect.center
        pygame.draw.circle(screen, self.color, center, self.radius)
        if self.zone == "priority":
            pygame.draw.circle(screen, _HALO, center, self.radius + 5, 3)
        marker = _zone_marker(self.zone)
        if marker:
            marker_color = (
                (200, 0, 0) if self.zone == "blocked" else (255, 255, 255)
            )
            marker_label = get_font(self.label_size).render(
                marker,
                True,
                marker_color,
            )
            screen.blit(marker_label, marker_label.get_rect(center=center))
        if not self.show_label:
            return
        font = get_font(self.label_size)
        present = sum(1 for d in drones if d.pos is self and d.target is None)
        if self.show_name:
            text = f"{self.name} ({present} / {self.max_drones})"
        else:
            text = f"{present} / {self.max_drones}"
        label = font.render(text, True, (0, 0, 0))
        centerx = self.rect.centerx
        centery = self.rect.centery
        rect = label.get_rect(
            center=(centerx, centery + self.radius + 7),
        )
        screen.blit(label, rect)

    def __str__(self) -> str:
        """Return the vertex name."""
        return self.name

    def __repr__(self) -> str:
        """Return the vertex name."""
        return self.name
