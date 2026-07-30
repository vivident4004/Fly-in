"""Renderer for the drone simulation using Pygame."""

from dataclasses import dataclass, field

import pygame

from .graph import Graph
from .scheduler import Scheduler
from .stupid_scheduler import Scheduler as StupidScheduler

# Quanti fotogrammi dura a schermo un turno di simulazione
_FRAMES_PER_TURN = 45.0
_BASE_HEIGHT = 666.0
# Testo e nodi scalano con l'altezza della finestra, ma entro questi limiti
_MIN_UI_SCALE = 0.8
_MAX_UI_SCALE = 1.35
_MAX_NODES_FOR_NAMES = 20
_BACKGROUND_COLOR = (208, 229, 251)

_cache: dict[int, pygame.font.Font] = {}


def get_font(size: int) -> pygame.font.Font:
    """Return a font of the specified size, using a cache for performance.

    Args:
        size: Font size.

    """
    font = _cache.get(size)
    if font is None:
        font = pygame.font.Font(None, size)
        _cache[size] = font
    return font


@dataclass
class Panel:
    """Represents a display panel containing a graph and its scheduler."""

    graph: Graph
    scheduler: Scheduler | StupidScheduler
    title: str = ""
    rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    node_radius: int = 15
    show_labels: bool = True
    done_at: int | None = None
    clustering: float | None = None


class Renderer:
    """Handles simulation rendering and user input."""

    def __init__(self,
                 screen: pygame.surface.Surface,
                 panels: list[Panel]) -> None:
        """Initialise the renderer with a surface and panels.

        Args:
            screen: Pygame surface.
            panels: list of panels to display.

        """
        self.screen = screen
        self.panels = panels
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.frames_per_turn: float = _FRAMES_PER_TURN
        # Fotogrammi già animati del turno in corso.
        self.frame: float = 0.0
        self.unhandled_keys: list[int] = []
        self.hint = ""
        # Cosa fare quando il ciclo finisce: "quit", "menu" o "replay".
        self.action = "quit"
        # La schermata di fine simulazione la vuole solo la mappa singola.
        self.end_overlay = False
        pygame.display.set_caption("Vola dentro")
        self._recompute_scale()
        self.layout()

    def _scaled(self, base: int) -> int:
        return max(1, int(base * self.ui_scale))

    def _recompute_scale(self) -> None:
        self.width, self.height = self.screen.get_size()
        raw = self.height / _BASE_HEIGHT
        self.ui_scale = max(_MIN_UI_SCALE, min(_MAX_UI_SCALE, raw))
        self.font = pygame.font.Font(None, self._scaled(30))
        self.title_font = pygame.font.Font(None, self._scaled(30))

    def layout(self) -> None:
        """Arrange panels and recompute scaling based on window size."""
        self._recompute_scale()
        count = len(self.panels)
        panel_w = self.width // count
        for i, panel in enumerate(self.panels):
            panel.rect = pygame.Rect(i * panel_w, 0, panel_w, self.height)
            self._layout_panel(panel)

    def set_panels(self, panels: list[Panel]) -> None:
        """Update the list of panels and refresh the layout.

        Args:
            panels: New list of panels.

        """
        self.panels = panels
        self.frame = 0.0
        self.layout()

    def _layout_panel(self, panel: Panel) -> None:
        vertices = panel.graph.vertices
        xs = [v.coord[0] for v in vertices]
        ys = [v.coord[1] for v in vertices]
        span_x = max(xs) - min(xs)
        span_y = max(ys) - min(ys)
        # margine del 12% per non far toccare i bordi al grafo
        usable_w = panel.rect.width * 0.88
        usable_h = panel.rect.height * 0.80
        scale_x = usable_w / span_x if span_x else float("inf")
        scale_y = usable_h / span_y if span_y else float("inf")
        scale = min(scale_x, scale_y)
        if scale == float("inf"):
            scale = 1.0
        center_x = (min(xs) + max(xs)) / 2
        center_y = (min(ys) + max(ys)) / 2
        offset_x = panel.rect.centerx - center_x * scale
        offset_y = panel.rect.centery - center_y * scale
        show_names = len(vertices) <= _MAX_NODES_FOR_NAMES
        for v in vertices:
            v.set_screen_pos(scale, scale, offset_x, offset_y)
            v.radius = panel.node_radius
            v.show_label = panel.show_labels
            v.show_name = show_names
            v.label_size = self._scaled(18)
        for edge in panel.graph.edges:
            edge.width = max(1, self._scaled(3))
            edge.show_label = panel.show_labels
        for drone in panel.graph.drones:
            drone.radius = max(2, self._scaled(6))

    def step(self) -> None:
        """Advance the animation and trigger simulation turns."""
        if self.paused:
            return
        self.frame += 1
        if self.frame < self.frames_per_turn:
            return
        self.frame = 0.0
        for panel in self.panels:
            if panel.graph.drones:
                panel.scheduler.turn()
            elif panel.done_at is None:
                panel.done_at = panel.graph.turn_count

    def render(self) -> None:
        """Draw the current frame of the simulation."""
        frac = self.frame / self.frames_per_turn
        self.screen.fill(_BACKGROUND_COLOR)
        for panel in self.panels:
            panel.graph.draw_graph(self.screen, frac)
            self._draw_panel_hud(panel)
        self._draw_global_hud()
        if self.finished():
            self._draw_end_overlay()
        pygame.display.flip()
        self.clock.tick(60)
        self.handle_events()

    def _draw_panel_hud(self, panel: Panel) -> None:
        if not panel.title:
            return
        lines = [panel.title, f"Turni: {panel.graph.turn_count}"]
        if panel.clustering is not None:
            lines.append(f"Coefficiente di gruppo: {panel.clustering:.3f}")
        if panel.done_at is not None:
            lines.append(f"Simulazione terminata in {panel.done_at} turni")
        y = panel.rect.top + self._scaled(10)
        for i, text in enumerate(lines):
            font = self.title_font if i == 0 else self.font
            label = font.render(text, True, (0, 0, 0))
            rect = label.get_rect(midtop=(panel.rect.centerx, y))
            self.screen.blit(label, rect)
            y += label.get_height() + self._scaled(4)

    def _draw_global_hud(self) -> None:
        if len(self.panels) == 1:
            turns = self.panels[0].graph.turn_count
            label = self.font.render(f"Turno: {turns}", True, (0, 0, 0))
            self.screen.blit(label, (10, 10))
        parts = ["P: pausa", "M: menu"]
        if self.hint:
            parts.append(self.hint)
        parts.append("Q / ESC: esci")
        parts.append("\nV: velocizza - L: rallenta")
        legend = self.font.render("   ".join(parts), True, (0, 0, 0))
        y = self.height - legend.get_height() - self._scaled(10)
        self.screen.blit(legend, (10, y))

    def finished(self) -> bool:
        """Tell whether the end-of-simulation screen has to be shown."""
        return self.end_overlay and all(
            p.done_at is not None for p in self.panels
        )

    def _draw_end_overlay(self) -> None:
        veil = pygame.surface.Surface((self.width, self.height),
                                      pygame.SRCALPHA)
        veil.fill((0, 0, 0, 120))
        self.screen.blit(veil, (0, 0))
        big = get_font(self._scaled(90))
        label = big.render("SIMULAZIONE TERMINATA", True, (255, 255, 255))
        center = (self.width // 2, self.height // 2)
        self.screen.blit(label, label.get_rect(center=center))
        hint = self.font.render(
            "R: ripeti   M: menu   Q: esci", True, (255, 255, 255)
        )
        self.screen.blit(
            hint,
            hint.get_rect(midtop=(center[0], center[1] + self._scaled(60))),
        )

    def _change_speed(self, factor: float) -> None:
        """Scala la durata a schermo di un turno: i turni non cambiano."""
        new = self.frames_per_turn * factor
        if not 2.0 <= new <= 240.0:
            return
        self.frames_per_turn = new
        self.frame = min(self.frame, new)

    def handle_events(self) -> None:
        """Process Pygame events and update renderer state."""
        self.unhandled_keys = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self.running = False
                elif event.key == pygame.K_m:
                    self.action = "menu"
                    self.running = False
                elif event.key == pygame.K_r and self.finished():
                    self.action = "replay"
                    self.running = False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_v:
                    self._change_speed(0.5)
                elif event.key == pygame.K_l:
                    self._change_speed(2.0)
                else:
                    self.unhandled_keys.append(event.key)
            elif event.type == pygame.VIDEORESIZE:
                self.layout()
