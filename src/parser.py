"""Parser for simulation map files."""

from __future__ import annotations

from collections import deque

from .edge import Edge
from .vertex import Vertex

VALID_ZONES = {"normal", "blocked", "restricted", "priority"}
HUB_META = {"zone", "color", "max_drones"}
CONN_META = {"max_link_capacity"}


class ParserError(Exception):
    """Exception raised for errors during map parsing."""

    def __init__(self, line: int, message: str) -> None:
        """Initialize the parser error.

        Args:
            line: Line number where the error occurred.
            message: Error description.

        """
        self.line = line
        self.message = message
        super().__init__(f"line {line}: {message}")


def _int(line_no: int, raw: str, what: str) -> int:
    try:
        return int(raw)
    except ValueError:
        raise ParserError(line_no, f"{what} must be an integer") from None


def _parse_metadata(
    line_no: int, tokens: list[str], allowed: set[str]
) -> dict[str, str]:
    if not tokens:
        return {}
    text = " ".join(tokens)
    if not (text.startswith("[") and text.endswith("]")):
        raise ParserError(line_no, "malformed metadata block")
    if text.count("[") != 1 or text.count("]") != 1:
        raise ParserError(line_no, "malformed metadata block")
    text = text[1:-1].strip()
    if not text:
        return {}
    meta: dict[str, str] = {}
    for pair in text.split():
        key, sep, value = pair.partition("=")
        if sep != "=" or not key or not value:
            raise ParserError(line_no, f"invalid metadata '{pair}'")
        if key not in allowed:
            raise ParserError(line_no, f"unknown metadata '{key}'")
        if key in meta:
            raise ParserError(line_no, f"duplicate metadata '{key}'")
        meta[key] = value
    return meta


def _parse_drones(line_no: int, parts: list[str], current: int) -> int:
    if current != -1:
        raise ParserError(line_no, "duplicate nb_drones")
    if len(parts) != 2:
        raise ParserError(line_no, "invalid nb_drones syntax")
    value = _int(line_no, parts[1], "nb_drones")
    if value <= 0:
        raise ParserError(line_no, "nb_drones must be positive")
    return value


def _parse_hub(
    line_no: int,
    parts: list[str],
    kind: str,
    nb_drones: int,
    by_name: dict[str, Vertex],
) -> Vertex:
    if len(parts) < 4:
        raise ParserError(line_no, "malformed hub definition")
    name = parts[1]
    if "-" in name:
        raise ParserError(line_no, "hub names cannot contain '-'")
    if name in by_name:
        raise ParserError(line_no, f"duplicate hub '{name}'")
    x = _int(line_no, parts[2], "coordinate")
    y = _int(line_no, parts[3], "coordinate")
    meta = _parse_metadata(line_no, parts[4:], HUB_META)
    zone = meta.get("zone", "normal")
    if zone not in VALID_ZONES:
        raise ParserError(line_no, f"invalid zone '{zone}'")
    max_drones = 1
    if "max_drones" in meta:
        max_drones = _int(line_no, meta["max_drones"], "max_drones")
        if max_drones <= 0:
            raise ParserError(line_no, "max_drones must be positive")
    return Vertex(
        nb_drones,
        name,
        (x, y),
        start=(kind == "start_hub"),
        end=(kind == "end_hub"),
        color=meta.get("color", "black"),
        max_drones=max_drones,
        zone=zone,
    )


def _parse_conn(
    line_no: int,
    parts: list[str],
    by_name: dict[str, Vertex],
    seen: set[frozenset[str]],
) -> Edge:
    if len(parts) < 2:
        raise ParserError(line_no, "malformed connection")
    names = parts[1].split("-")
    if len(names) != 2:
        raise ParserError(line_no, "invalid connection syntax")
    src, dst = names
    if src == dst:
        raise ParserError(line_no, "self-connections are forbidden")
    if src not in by_name:
        raise ParserError(line_no, f"unknown hub '{src}'")
    if dst not in by_name:
        raise ParserError(line_no, f"unknown hub '{dst}'")
    key = frozenset((src, dst))
    if key in seen:
        raise ParserError(line_no, "duplicate connection")
    seen.add(key)
    meta = _parse_metadata(line_no, parts[2:], CONN_META)
    cap = 1
    if "max_link_capacity" in meta:
        cap = _int(line_no, meta["max_link_capacity"], "capacity")
        if cap <= 0:
            raise ParserError(line_no, "max_link_capacity must be > 0")
    return Edge(by_name[src], by_name[dst], cap)


def _validate(vertices: list[Vertex], edges: list[Edge]) -> None:
    starts = [v for v in vertices if v.start]
    ends = [v for v in vertices if v.end]
    if len(starts) != 1:
        raise ParserError(0, "there must be exactly one start_hub")
    if len(ends) != 1:
        raise ParserError(0, "there must be exactly one end_hub")
    start, end = starts[0], ends[0]
    if start.zone == "blocked":
        raise ParserError(0, "start_hub cannot be blocked")
    if end.zone == "blocked":
        raise ParserError(0, "end_hub cannot be blocked")

    adj: dict[str, set[str]] = {v.name: set() for v in vertices}
    for e in edges:
        adj[e.src.name].add(e.dst.name)
        adj[e.dst.name].add(e.src.name)
    if not adj[start.name]:
        raise ParserError(0, "start_hub is isolated")
    if not adj[end.name]:
        raise ParserError(0, "end_hub is isolated")

    blocked = {v.name for v in vertices if v.zone == "blocked"}
    visited = {start.name}
    queue: deque[str] = deque([start.name])
    while queue:
        cur = queue.popleft()
        if cur == end.name:
            return
        for nb in adj[cur]:
            if nb in visited or nb in blocked:
                continue
            visited.add(nb)
            queue.append(nb)
    raise ParserError(0, "no valid path from start_hub to end_hub")


def parse_file(path: str) -> tuple[int, list[Vertex], list[Edge]]:
    """Parse a map file and return the simulation data.

    Args:
        path: Path to the map file.

    Returns:
        A tuple containing the number of drones, vertices, and edges.

    Raises:
        ParserError: If the file is malformed.
        FileNotFoundError: If the file does not exist.

    """
    nb_drones = -1
    vertices: list[Vertex] = []
    edges: list[Edge] = []
    by_name: dict[str, Vertex] = {}
    seen: set[frozenset[str]] = set()
    first = True

    with open(path, encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            raw = raw.split("#")[0].strip()
            if not raw:
                continue
            key_part, sep, rest = raw.partition(":")
            if not sep:
                raise ParserError(line_no, "missing ':' after keyword")
            key = key_part.strip()
            parts = [key] + rest.split()
            if first:
                first = False
                if key != "nb_drones":
                    raise ParserError(
                        line_no, "first statement must be nb_drones"
                    )
            if key == "nb_drones":
                nb_drones = _parse_drones(line_no, parts, nb_drones)
            elif key in ("start_hub", "end_hub", "hub"):
                vertex = _parse_hub(line_no, parts, key, nb_drones, by_name)
                vertices.append(vertex)
                by_name[vertex.name] = vertex
            elif key == "connection":
                edges.append(_parse_conn(line_no, parts, by_name, seen))
            else:
                raise ParserError(line_no, f"unknown keyword '{key}'")

    if nb_drones == -1:
        raise ParserError(0, "missing nb_drones definition")
    _validate(vertices, edges)
    return nb_drones, vertices, edges
