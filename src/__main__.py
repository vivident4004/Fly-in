"""Entry point for the fly-in drone simulation."""

import sys
from pathlib import Path

import pygame

from .graph import Graph
from .menu import run_menu
from .parser import ParserError, parse_file
from .renderer import Panel, Renderer
from .scheduler import Scheduler
from .stupid_scheduler import Scheduler as StupidScheduler


def _print_simulation_start(nome_mappa: str) -> None:
    print(f"\n\nINIZIO SIMULAZIONE DI {nome_mappa}")


def _run_map(screen: pygame.surface.Surface, path: str, mode: str) -> str:
    """Play a map until the user quits, and say what to do next.

    Args:
        screen: Pygame surface.
        path: path of the map file.
        mode: "stupid" for the stupid scheduler, "smart" for the other one.

    Returns:
        "quit", "menu" or "replay".

    """
    try:
        nb_drones, vertices, edges = parse_file(path)
    except (FileNotFoundError, ParserError) as err:
        print(err)
        return "menu"
    _print_simulation_start(Path(path).stem)
    graph = Graph(nb_drones, vertices, edges)
    scheduler: Scheduler | StupidScheduler

    if mode == "stupid":
        scheduler = StupidScheduler(graph)
    else:
        # scheduler = Scheduler(graph, capacity_info=capacity_info)
        scheduler = Scheduler(graph)
    scheduler.edmonds_karp()
    renderer = Renderer(screen, [Panel(graph, scheduler)])
    renderer.end_overlay = True
    while renderer.running:
        renderer.render()
        renderer.step()
    return renderer.action


def _play(screen: pygame.surface.Surface, path: str, mode: str) -> str:
    """Run a map again and again while the user asks to repeat it.

    Args:
        screen: Pygame surface.
        path: path of the map file.
        mode: scheduler mode.

    Returns:
        "quit" or "menu".

    """
    action = "replay"
    while action == "replay":
        # action = _run_map(screen, path, mode, capacity_info)
        action = _run_map(screen, path, mode)
    return action


def main() -> None:
    """Run the main simulation loop or map selector."""
    args = sys.argv[1:]

    # --plot non apre una finestra: esegue la simulazione e salva il grafico.
    if "--plot" in args:
        from .bonus_ws_plot import run_plot

        run_plot()
        return

    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
    try:
        if "--ws" in args:
            from .bonus_ws_demo import run_demo

            run_demo(screen)
        elif args:
            _play(screen, args[0], "stupid")
        else:
            while True:
                choice = run_menu(screen)
                if choice.kind == "ws":
                    from .bonus_ws_demo import run_demo

                    run_demo(screen)
                elif choice.kind == "map" and choice.path is not None:
                    if _play(screen, choice.path, choice.mode) == "quit":
                        break
                else:
                    break
    except ValueError as err:
        print(f"errore: {err}")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
