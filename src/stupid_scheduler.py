"""Simulation scheduler implementing Edmonds-Karp for drone routing."""

from __future__ import annotations

from itertools import count
from queue import PriorityQueue

from .graph import Graph
from .vertex import Vertex


class Scheduler:
    """Manages pathfinding and drone movement scheduling."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the scheduler with a graph.

        Args:
            graph: The simulation graph.

        """
        self.graph = graph
        self.paths: list[tuple[list[Vertex], int, int]] = []

    def edmonds_karp(self) -> None:
        """Find augmenting paths using Dijkstra and assign drones to paths."""
        while self._dijkstra():
            path, flow, _ = self.paths[-1]
            for i in range(len(path) - 1):
                edge = self.graph.get_edge_from_vertices(path[i], path[i + 1])
                if edge is None:
                    raise ValueError("edge not found in graph")
                edge.capacity -= flow
                if edge.capacity <= 0:
                    edge.closed = True
                path[i].capacity -= flow
                if path[i].capacity <= 0:
                    path[i].closed = True
        if not self.paths:
            raise ValueError("no path from start to end for the drones")
        self._assign_paths()

    def _dijkstra(self) -> bool:
        counter = count()
        queue: PriorityQueue[tuple[int, int, Vertex]] = PriorityQueue()
        start = self.graph.start
        if start.capacity <= 0:
            return False
        start.steps = 0
        queue.put((0, next(counter), start))
        visited = {start}
        curr = start
        while not queue.empty():
            prio, _, curr = queue.get()
            if curr is self.graph.end:
                break
            neighbors = self.graph.get_neighbors(curr)
            for neigh in neighbors:
                if (
                    neigh not in visited
                    and neigh.zone == "priority"
                    and neigh.capacity > 0
                ):
                    visited.add(neigh)
                    neigh.parent = curr
                    neigh.steps = curr.steps + neigh.cost()
                    queue.put((prio + neigh.cost(), next(counter), neigh))
            for neigh in neighbors:
                if neigh not in visited and neigh.capacity > 0:
                    visited.add(neigh)
                    neigh.parent = curr
                    neigh.steps = curr.steps + neigh.cost()
                    queue.put((prio + neigh.cost(), next(counter), neigh))
        if curr is not self.graph.end:
            return False
        path: list[Vertex] = []
        node: Vertex | None = curr
        while node is not None:
            path.append(node)
            node = node.parent
        path.reverse()
        self.paths.append((path, self.find_max_flow(path), path[-1].steps))
        return True

    # 22:35 (io e Tommi): «faindiamo il macs flou»
    def find_max_flow(self, path: list[Vertex]) -> int:
        """Find the maximum possible flow (drones) for a given path.

        Args:
            path: List of vertices forming the path.

        """
        min_cap = path[0].capacity
        for i in range(len(path) - 1):
            edge = self.graph.get_edge_from_vertices(path[i], path[i + 1])
            if edge is not None:
                min_cap = min(min_cap, edge.capacity)
            min_cap = min(min_cap, path[i].capacity)
            if min_cap == 1:
                break
        return min_cap

    # Assegno a ogni percorso numero_di_flusso droni.
    # Trovo la differenza di lunghezza tra percorso corrente e minimo
    # poi calcolo la divisione tra il numero di droni in attesa e la
    # capacità del percorso minimo, e vedo se questa roba è minore della
    # suddetta differenza, cosí da capire se ci metta di piú ad aspettare o
    # a mandarli sul percorso corrente
    def _assign_paths(self) -> None:
        if not self.paths:
            return
        _, _, min_dist = self.paths[0]
        min_flow = 0
        for _, flow, dist in self.paths:
            if dist == min_dist:
                min_flow += flow
            else:
                break

        min_flow = max(min_flow, 1)
        for path, flow, dist in self.paths:
            free = sum(1 for d in self.graph.drones if not d.path)
            if free == 0:
                break
            if dist - min_dist > (free // min_flow):
                break
            remaining = flow
            for drone in self.graph.drones:
                if remaining == 0:
                    break
                if not drone.path:
                    drone.path = path
                    drone.update_target(path[1])
                    remaining -= 1

    def turn(self) -> None:
        """Advance the simulation by one turn."""
        if not self.graph.drones:
            return
        for drone in self.graph.drones:
            drone.move()
        self.graph.turn_count += 1
        self._print_turn()
        if not all(d.path for d in self.graph.drones):
            self._assign_paths()
        for drone in list(self.graph.drones):
            if drone.pos is self.graph.end:
                self.graph.drones.remove(drone)
                continue
            if drone.target is None and drone.path:
                idx = drone.path.index(drone.pos)
                if idx + 1 < len(drone.path):
                    drone.update_target(drone.path[idx + 1])
        if not self.graph.drones:
            print("SIMULAZIONE TERMINATA")

    def _print_turn(self) -> None:
        moves = []
        for drone in self.graph.drones:
            if drone.flying():
                moves.append(f"D{drone.num}-{drone.prev.name}-{drone.target}")
            elif drone.pos is not drone.prev:
                moves.append(f"D{drone.num}-{drone.pos.name}")
                drone.prev = drone.pos
        if moves:
            print(" ".join(moves))
