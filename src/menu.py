"""Menu system for selecting simulation maps."""

from dataclasses import dataclass
from pathlib import Path

import pygame

_BG = (30, 34, 40)
_FG = (235, 235, 235)
_HOVER = (70, 110, 170)
_BONUS = (180, 90, 40)
_BONUS_HOVER = (220, 120, 60)


@dataclass
class MenuChoice:
    """Represents a choice made in the menu."""

    kind: str
    path: str | None = None
    mode: str = "stupid"


_PANEL_MAX_VISIBLE = 5


def find_maps_by_folder(root: str = "maps") -> dict[str, list[str]]:
    """Find and group map files by their parent folder.

    Args:
        root: Root directory to search for maps.

    Returns:
        Dictionary mapping folder names to lists of map file paths.

    """
    base = Path(root)
    if not base.is_dir():
        return {}
    grouped: dict[str, list[str]] = {}
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        maps = sorted(str(p) for p in folder.glob("*.txt"))
        if maps:
            grouped[folder.name] = maps
    return grouped


def _panel_width(window_width: int, count: int) -> int:
    """Larghezza pannello: pieno se ci stanno tutti, max 5 colonne."""
    if count == 0:
        return window_width
    if count <= _PANEL_MAX_VISIBLE:
        return window_width // count
    return window_width // _PANEL_MAX_VISIBLE


def run_menu(screen: pygame.surface.Surface) -> MenuChoice:
    """Display the menu and return the user's selection.

    Args:
        screen: Pygame surface.

    Returns:
        Selected MenuChoice.

    """
    groups = find_maps_by_folder()
    folders = list(groups.keys())
    clock = pygame.time.Clock()
    width, height = screen.get_size()
    scale = height / 666.0
    font = pygame.font.Font(None, max(1, int(22 * scale)))
    header_font = pygame.font.Font(None, max(1, int(28 * scale)))
    title_font = pygame.font.Font(None, max(1, int(44 * scale)))
    row_h = max(1, int(30 * scale))
    top = max(1, int(130 * scale))
    bonus_h = max(1, int(90 * scale))
    row_scroll = {name: 0 for name in folders}
    panel_scroll = 0
    mode = "stupid"

    while True:
        width, height = screen.get_size()
        panel_w = _panel_width(width, len(folders))
        max_panel_scroll = max(0, len(folders) - _PANEL_MAX_VISIBLE)
        panel_scroll = min(panel_scroll, max_panel_scroll)
        if len(folders) > _PANEL_MAX_VISIBLE:
            visible_folders = folders[
                panel_scroll: panel_scroll + _PANEL_MAX_VISIBLE
            ]
        else:
            visible_folders = folders
        panel_height = max(1, height - top - bonus_h)
        visible_rows = max(1, panel_height // row_h)
        mouse = pygame.mouse.get_pos()
        screen.fill(_BG)

        title = title_font.render("Vola dentro", True, _FG)
        screen.blit(title, (int(20 * scale), int(20 * scale)))

        mode_rect = pygame.Rect(
            width - int(280 * scale),
            int(20 * scale),
            int(260 * scale),
            int(44 * scale),
        )
        pygame.draw.rect(
            screen,
            _HOVER if mode_rect.collidepoint(mouse) else _BG,
            mode_rect,
            border_radius=6,
        )
        pygame.draw.rect(screen, _FG, mode_rect, 2, border_radius=6)
        nome = "stupida" if mode == "stupid" else "intelligente"
        mlabel = font.render(f"Modalità: {nome}", True, _FG)
        screen.blit(mlabel, mlabel.get_rect(center=mode_rect.center))

        rows: list[tuple[pygame.Rect, str]] = []
        for col, name in enumerate(visible_folders):
            px = col * panel_w
            header = header_font.render(name, True, _FG)
            screen.blit(header, (px + int(10 * scale), top - row_h))

            maps = groups[name]
            max_row_scroll = max(0, len(maps) - visible_rows)
            row_scroll[name] = min(row_scroll[name], max_row_scroll)
            offset = row_scroll[name]
            for i in range(offset, min(offset + visible_rows, len(maps))):
                rect = pygame.Rect(
                    px + int(10 * scale),
                    top + (i - offset) * row_h,
                    panel_w - int(20 * scale),
                    row_h - int(4 * scale),
                )
                rows.append((rect, maps[i]))
                if rect.collidepoint(mouse):
                    pygame.draw.rect(screen, _HOVER, rect, border_radius=4)
                label = font.render(Path(maps[i]).stem, True, _FG)
                screen.blit(
                    label, (rect.x + int(8 * scale), rect.y + int(3 * scale))
                )

        bonus = pygame.Rect(
            int(60 * scale),
            height - bonus_h + int(10 * scale),
            width - int(120 * scale),
            bonus_h - int(20 * scale),
        )
        hot = bonus.collidepoint(mouse)
        pygame.draw.rect(
            screen, _BONUS_HOVER if hot else _BONUS, bonus, border_radius=6
        )
        blabel = font.render(
            "Bonus: simulazione del «mondo piccolo» (Watts-Strogatz)",
            True,
            _FG,
        )
        screen.blit(blabel, blabel.get_rect(center=bonus.center))

        hint_parts = [
            "Frecce -> <-: scorri lista",
            "Clic: scegli",
            "Q/ESC: esci",
        ]
        if len(folders) > _PANEL_MAX_VISIBLE:
            hint_parts.insert(1, "Frecce -> <-: scorri pannelli")
        hint = font.render("   ".join(hint_parts), True, _FG)
        screen.blit(hint, (int(20 * scale), int(60 * scale)))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return MenuChoice(kind="quit")
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return MenuChoice(kind="quit")
                if event.key == pygame.K_RIGHT:
                    panel_scroll = min(max_panel_scroll, panel_scroll + 1)
                if event.key == pygame.K_LEFT:
                    panel_scroll = max(0, panel_scroll - 1)
            if event.type == pygame.MOUSEWHEEL:
                for col, name in enumerate(visible_folders):
                    px = col * panel_w
                    if px <= mouse[0] < px + panel_w:
                        row_scroll[name] = max(0, row_scroll[name] - event.y)
                        break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mode_rect.collidepoint(event.pos):
                    mode = "smart" if mode == "stupid" else "stupid"
                if bonus.collidepoint(event.pos):
                    return MenuChoice(kind="ws", mode=mode)
                for rect, path in rows:
                    if rect.collidepoint(event.pos):
                        return MenuChoice(kind="map", path=path, mode=mode)
