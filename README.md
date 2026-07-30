*This project has been created as part of the 42 curriculum by aflorea.*

![banner](https://upload.wikimedia.org/wikipedia/en/4/44/MuseDronesCover.jpg)

# Fly-in

### Drones are (not) cool (if used for surveillance or war)
Route a fleet of drones from a start zone to an end zone over a weighted graph of
connected zones, in the fewest simulation turns, while respecting zone and connection
capacities, zone movement costs, and collision rules. The router is an 
Edmonds-Karp-style max-flow scheduler; the whole simulation is drawn live with pygame.

---

## Description

The input is a network of *zones* (graph vertices) joined by *connections* (undirected,
weighted edges). Every drone starts in the single `start_hub` and must reach the single
`end_hub`. Drones move in discrete turns and may move simultaneously, so the objective is
not a single shortest path but a *schedule*: how to spread the fleet across several paths so
that the last drone arrives as early as possible.

Three things make this harder than plain shortest-path:

- **zone cost**: entering a `restricted` zone costs 2 turns instead of 1; `priority` zones
  cost 1 turn but are preferred; `blocked` zones are impassable.
- **capacity**: each zone holds at most `max_drones` drones at once (default 1), and each
  connection carries at most `max_link_capacity` drones at once (default 1). The `start_hub`
  and `end_hub` are exempt.
- **contention**: two drones may not occupy the same zone or the same connection on the same
  turn unless capacity allows it, and deadlocks must be avoided.

The solver models this as a minimum-cost maximum-flow problem: it repeatedly extracts the
cheapest augmenting path with Dijkstra, saturates residual capacities, then assigns drones to
the cheapest paths first, only opening a longer path when the wait on the shorter ones would
cost more than the detour.

A separate **bonus** builds and animates Watts-Strogatz *small-world* 
simulation on the same engine, to show how a handful of random "shortcut" 
links collapses the distance across a network while its local clustering 
stays high (see the [bonus section](#bonus-the-watts-strogatz-small-world-model)).

No third-party graph library is used: the graph, the search and the flow are all hand-written,
as the subject requires.

---

## Instructions

The project targets Python 3.10+ and uses `uv` for dependency management and `pygame-ce` for
rendering. Everything is driven through the `Makefile`.

```bash
make install      # uv sync --extra plots  (installs deps, incl. matplotlib for the plot)
make run          # open the map menu and run the simulation
make bonus        # run the Watts-Strogatz small-world demo directly
make bonus-plot   # compute L(p) and C(p) and save ws_curves.png (no window)
make debug        # run under pdb on the map set in the Makefile MAP variable
make clean        # remove __pycache__, .mypy_cache, .ruff_cache
make lint         # flake8 + mypy (subject flags)
make lint-strict  # flake8 + mypy --strict
```

Direct invocation without the Makefile:

```bash
python -m src                      # map menu
python -m src maps/easy/01_linear_path.txt   # run one map straight away
python -m src --ws                 # Watts-Strogatz demo
python -m src --plot               # save the metric curves, then exit
```

In the menu, each `maps/` sub-folder becomes a scrollable column; a toggle switches between
the simple scheduler (`stupid`, which is apparently what the evaluation 
sheet wants us to code) and the  capacity-aware one (`intelligent`, or 
simply the correct one to interpret the subject), and a 
button at the bottom opens the small-world demo. During a run: `P` pauses, 
`V` / `L` speed the animation up or down (this changes only the frame rate, 
never the turn count), `M` returns to the menu,
`R` replays once finished, `Q` / `ESC` quits.

---

### Map file format

Blank lines and `#` comments are skipped. The first non-comment line must be `nb_drones`.

The parser is a single line-oriented pass. It rejects the maps, specifying 
the line number where the first error was found: a missing
or non-leading `nb_drones`, a count of `start_hub`/`end_hub` different from one, duplicate names,
`-` inside a name, a connection to an undefined zone, a duplicate connection (`a-b` equals `b-a`),
an unknown zone type, a non-positive capacity, and any graph where no start-to-end path exists that
avoids `blocked` zones.

---

## Algorithm and implementation strategy

The code is fully object-oriented and splits into four responsibilities.

### Data model

`Vertex` (`src/vertex.py`), `Edge` (`src/edge.py`) and `Drone` (`src/drone.py`) hold both the
simulation state and their own pygame drawing. A `Vertex` carries a residual `capacity` (starting
at `max_drones`, or `nb_drones` for start/end) and a `cost()` of 2 turns for `restricted` zones,
1 otherwise. An `Edge` carries a residual `capacity` (starting at `max_link_capacity`). `Graph`
(`src/graph.py`) builds an adjacency map `vertex -> [incident edges]` and exposes `get_neighbors`,
which hides `blocked`, `closed` and saturated targets from the search.

### Pathfinding: Dijkstra with zone weights and priority

`Scheduler._dijkstra` (`src/scheduler.py`) is a standard Dijkstra over `get_neighbors`, with the
edge weight replaced by the destination zone's `cost()`. Ties are broken with a monotonic counter
so heap entries stay orderable. Two passes over each frontier implement the `priority` preference:
priority neighbours are relaxed before the rest, so at equal cost the search commits to preferred
zones. Once `end` is reached the path is rebuilt from `parent` pointers.

### Flow: an Edmonds-Karp variant

`Scheduler.edmonds_karp` repeatedly asks Dijkstra for the current cheapest augmenting path. For
each path it computes the bottleneck `find_max_flow` (the minimum residual capacity over the
vertices and edges on the path), subtracts that flow from every residual capacity, and marks any
zone or connection that hits zero as `closed`, removing it from later searches. This is the
Edmonds-Karp idea (augment along shortest paths, track residual capacity) with two adaptations:
the "shortest" path is measured in weighted zone cost rather than hop count, and each path is a
*bundle* that can carry several drones at once.

### Assignment and turn scheduling

`_assign_paths` distributes drones over the discovered paths, cheapest first. It fills the
minimum-cost paths, then admits a longer path only while its extra cost over the minimum does not
exceed `free_drones // min_flow` -- that is, only when routing a drone the long way is faster than
letting it queue behind the others. `turn()` then advances the simulation one step: every drone
moves, delivered drones are removed at `end`, and `_advance` promotes drones farthest along their
path first so that capacity freed by a departing drone is reusable within the same turn.
`_can_enter` enforces, at run time, both the connection limit (`max_cap`) and the zone limit
(`max_drones`), and reserves the destination for drones crossing a restricted zone so the slot is
guaranteed on arrival. `stupid_scheduler.py` shares the planner but skips this run-time capacity
guard; the menu's `intelligente` mode selects the capacity-aware scheduler.

### Complexity

Let $V$ be the number of zones and $E$ the number of connections.

**Dijkstra.** With a binary min-heap, each of the $V$ `extract-min` operations costs $O(\log V)$
and each of the $E$ edge relaxations may trigger a $O(\log V)$ key update, giving[<sup>5</sup>](#ref5)

$$T_{\text{Dijkstra}} = O\big((V + E)\log V\big) = O(E \log V)$$

for a connected graph, where $E \ge V - 1$.

**Edmonds-Karp.** Ford-Fulkerson augmenting along BFS shortest paths performs $O(VE)$ augmentations,
each found by a $O(E)$ search, so the classical bound is[<sup>5</sup>](#ref5)

$$T_{\text{Edmonds-Karp}} = O(V E^2)$$

independent of the edge capacities. This implementation replaces the BFS with a weighted Dijkstra
(hence an extra $\log V$ per augmentation) and, because each augmenting path is saturated by a whole
drone bundle in one step, in practice needs far fewer augmentations than the $O(VE)$ worst case.

Paths are computed once, up front, then cached in the drones' `path` field; the turn loop only reads
them, so per-turn work is linear in the number of live drones.

---

## Visual representation

Rendering (`src/renderer.py`) is a fixed-timestep pygame loop: each simulation turn is spread over a
number of frames, and drone positions are linearly interpolated along their current edge, so movement
reads as continuous flight rather than teleporting. One `Panel` holds one graph; the layout auto-scales
the zone coordinates to the window and re-scales on resize.

- **zones** are circles whose colour is derived from the map's `color` token (hashed to RGB, so the
  same name is always the same colour). `priority` zones wear a gold ring; `restricted`, `blocked` and
  `priority` zones carry an `R`, `X` (red) or `P` marker.
- **occupancy** is shown live: each zone is labelled `name (present / max_drones)` and each connection
  `present / max_cap`, so a viewer can watch capacities fill and free.
- **drones** are blue dots; a drone crossing a restricted zone animates across the two-turn transit.
- **HUD** shows the turn counter, the per-panel title (and, in the bonus, the clustering coefficient),
  and the control legend. Controls: `P` pause, `V`/`L` faster/slower animation, `M` menu, `R` replay,
  `Q`/`ESC` quit. A closing overlay announces the final turn count.

The menu (`src/menu.py`) renders one column per `maps/` sub-folder with mouse-wheel scrolling, a
scheduler-mode toggle, and the bonus entry point. The visual feedback is the fastest way to sanity-check
a schedule: capacity labels expose contention, the restricted-zone animation makes the 2-turn cost
visible, and the turn counter is exactly the score the subject optimises.

---

## Bonus: the Watts-Strogatz small-world model

### What it demonstrates

Real networks -- social ties, the web, neural wiring -- share two traits that look contradictory. They
are strongly **clustered**: a vertex's neighbours tend to be neighbours of each other, as in a regular
lattice or a clique of friends[<sup>1</sup>](#ref1). Yet they are also **shallow**: any two vertices are
separated by very few steps -- the *small-world effect*, popularised as the "six degrees of separation",
and measured directly by Milgram's 1967 letter experiment, the Kevin Bacon game and the Erdos
number[<sup>1</sup>](#ref1). A purely regular lattice is clustered but has long distances; a purely random
graph (Erdős–Rényi) has short distances but almost no clustering
[<sup>1</sup>](#ref1). Neither alone
matches reality.

Watts and Strogatz (1998) showed that the two regimes are joined by a broad middle
ground[<sup>2</sup>](#ref2)<sup>,</sup>[<sup>4</sup>](#ref4): starting from a 
clustered lattice and rewiring only a
*tiny* fraction of links into long-range shortcuts collapses the average distance almost to the
random-graph value, while the clustering barely drops. As the encyclopedia puts it, a few "shortcut"
links between otherwise distant, tightly-knit groups are enough to keep the whole society close-knit and
short-range[<sup>1</sup>](#ref1). That coexistence -- high clustering *and* short paths -- is the
small-world.

### How the model works

Build a ring of $N$ nodes and join each node to its $k$ nearest neighbours ($k/2$ on each side): a regular
ring lattice. Then walk over the edges and, with probability $p$, rewire each one to a new random target,
avoiding self-loops and duplicates[<sup>4</sup>](#ref4). The single knob $p$ interpolates between the two
extremes:

- $p = 0$: the untouched lattice -- clustering $C(0) \approx \tfrac{3}{4}$, average path length
  $L(0) \approx \tfrac{N}{2k}$ (grows linearly with $N$).
- $p = 1$: every edge randomised -- $C \approx \tfrac{k}{N}$, $L \approx \tfrac{\ln N}{\ln k}$
  (grows only logarithmically).

The two metrics are the **characteristic path length** $L$ (the average shortest-path distance over all
vertex pairs) and the **clustering coefficient** $C$. For a vertex $i$ of degree $k_i$, with $e_i$ edges
actually present among its $k_i$ neighbours, the local coefficient is[<sup>3</sup>](#ref3)

$$C_i = \frac{2\,e_i}{k_i\,(k_i - 1)}, \qquad C = \frac{1}{N}\sum_{i} C_i .$$

The key finding is that $L$ and $C$ fall on very different scales of $p$: a handful of shortcuts
($p \approx 0.01$ to $0.1$) is enough to send $L$ tumbling toward its random-graph value, whereas $C$
only decays much later. The window where $L$ is already small but $C$ is still large is the small-world
regime.

### In this project

The bonus reuses the exact simulation engine (`Vertex`, `Edge`, `Graph`, `Scheduler`), so the generator
had to be written from scratch too.

- `src/bonus_small_world.py`: `ring_lattice(n, k)` and `rewire(adj, p)` 
  implement the construction
  above, and `watts_strogatz` retries until the result is connected.
- `src/bonus_metrics.py`: `clustering_coefficient` (the formula above) and 
  `average_path_length` (BFS
  from every source, exact or sampled).
- `src/bonus_ws_graph.py`: lays the nodes on a circle and converts an 
  adjacency list into the
  simulation's vertices and edges.
- `src/bonus_ws_demo.py` (`make bonus`): three side-by-side panels, regular 
  ($p=0$), small-world
  ($p=0.2$) and random ($p=1$), on the same node layout. Original ring edges are drawn grey and rewired
  shortcuts red, each panel prints its measured clustering, and the drone router runs on all three so the
  difference in distances is visible. `R` regenerates.
- `src/bonus_ws_plot.py` (`make bonus-plot`): sweeps $p$ on a logarithmic 
  grid (default $N=1000$,
  $k=10$, averaged over several graphs), computes $L(p)$ and $C(p)$, and saves `ws_curves.png` -- the two
  curves on different scales that make the small-world window obvious. Results are cached under
  `.cache/ws_sweep.json`.

---

## Resources

### Classic references

- <a id="ref1"></a>**[1]** G. Caldarelli, *Le reti complesse*, in E. Bartocci, P. Odifreddi (eds.),
  *Pensare il mondo. (Enciclopedia del)La matematica. Volume IV*. Einaudi, 2010. ISBN: 9788806164270.
- <a id="ref2"></a>**[2]** D. J. Watts, S. H. Strogatz, *Collective dynamics of "small-world" networks*,
  *Nature* 393 (1998), 440-442.
  <https://worrydream.com/refs/Watts_1998_-_Collective_dynamics_of_'small-world'_networks.pdf>
- <a id="ref3"></a>**[3]** *Coefficiente di clustering*, Wikipedia (Italian).
  <https://it.wikipedia.org/wiki/Coefficiente_di_clustering>
- <a id="ref4"></a>**[4]** *Watts-Strogatz model*, Wikipedia (English).
  <https://en.wikipedia.org/wiki/Watts%E2%80%93Strogatz_model>
- <a id="ref5"></a>**[5]** T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein, *Introduzione agli
  algoritmi e strutture dati*, 3rd Italian ed., McGraw-Hill -- Dijkstra's algorithm (ch. 24, single-source
  shortest paths) and the Edmonds-Karp bound (ch. 26, maximum flow).

### Use of artificial intelligence (a.i.)

A.i.'s assistance was used for supporting tasks, not for the core 
implementation:

- drafting and structuring this README;
- cross-checking the algorithm's complexity statements against the references above;
- parts of the menu user interface were slopped with a.i. because I did not have *sbatti* to make something beautiful;
- reviewing code and acting as a reviewer while designing the scheduler.

The parser, graph model, pathfinder, flow scheduler, renderer and the Watts-Strogatz bonus were written
and are understood by the author; every a.i. suggestion that entered the 
codebase was verified and reworked by hand.

---

## Acknowledgements

I want to thank all my peers at 42 Firenze for helping me complete this 
tedious project that I very much did not like.

A special thanks goes to my close small-world made up by
`fbertozz`, `nirugger` e `tvanni` (strictly in alphabetical order), for their 
help on the (too many) rewritings of this code and for their invaluable 
help in brainstorming ideas and supporting me. I want to thank in 
particular `tvanni` with which I implemented the core idea of the algorithm 
in a lonely night this past spring.
The idea of using an MD5 hash for converting arbitrary strings to RGB 
colours was `nirugger`'s. I stole the idea of markers on nodes for special 
zones from `lciardo`.

There are other people whom I have not mentioned here 
that helped me in various ways and are also invaluable at making 42 a great 
place to be in, where cool ideas are shared, discussed, written down and contested.
All the errors which might still be present are solely my own.

Drones, used for war, repression of liberties and for population control 
and surveillance, are NOT cool.
Fuck Palantir, fuck Flock, and fuck all the 
shit dystopian companies that are flourishing on the back of a falling 
democratic society and rising populism, using high-tech such as drones to 
further their liberticide agendas.
With this project (and my bonus part) I wanted to demonstrate that a better 
alternative could be to model networks of people, information, ideas, connections. That's 
what we should strive to achieve as human beings.