"""Script for generating Watts-Strogatz metric curves."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from .bonus_metrics import average_path_length, clustering_coefficient
from .bonus_small_world import watts_strogatz

_CACHE_PATH = Path(".cache/ws_sweep.json")
_OUT_PATH = Path("ws_curves.png")
_L_COLOR = "#4da6d9"
_C_COLOR = "#e8df8a"


@dataclass
class SweepResult:
    """Contains results from a parameter sweep of Watts-Strogatz graphs."""

    ps: list[float]
    lengths: list[float]
    clustering: list[float]
    n: int
    k: int


def log_space(lo: float, hi: float, count: int) -> list[float]:
    """Generate count values in geometric progression from lo to hi."""
    if count < 2:
        return [lo]
    ratio = (hi / lo) ** (1.0 / (count - 1))
    return [lo * ratio**i for i in range(count)]


def cache_key(
    n: int,
    k: int,
    ps: list[float],
    trials: int,
    samples: int | None,
    seed: int | None,
) -> str:
    """Generate a unique key based on sweep parameters for caching."""
    payload = json.dumps(
        {
            "n": n,
            "k": k,
            "ps": ps,
            "trials": trials,
            "samples": samples,
            "seed": seed,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def load_cache(path: Path, key: str) -> SweepResult | None:
    """Load cached sweep results if they match the current key."""
    try:
        blob = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if blob.get("key") != key:
        return None
    try:
        return SweepResult(**blob["result"])
    except (KeyError, TypeError):
        return None


def save_cache(path: Path, key: str, result: SweepResult) -> None:
    """Save sweep results to a cache file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"key": key, "result": asdict(result)}, indent=1)
    )


def run_sweep(
    n: int,
    k: int,
    ps: list[float],
    trials: int,
    samples: int | None,
    seed: int | None,
) -> SweepResult:
    """Run the parameter sweep and calculate average metrics."""
    rng = random.Random(seed)
    lengths: list[float] = []
    clustering: list[float] = []
    for i, p in enumerate(ps, start=1):
        acc_l = 0.0
        acc_c = 0.0
        for _ in range(trials):
            adj = watts_strogatz(n, k, p, rng)
            acc_l += average_path_length(adj, rng, samples)
            acc_c += clustering_coefficient(adj)
        lengths.append(acc_l / trials)
        clustering.append(acc_c / trials)
        print(
            f"  p={p:9.6f}  L={lengths[-1]:6.2f}  "
            f"C={clustering[-1]:.4f}   [{i}/{len(ps)}]"
        )
    return SweepResult(ps=ps, lengths=lengths, clustering=clustering, n=n, k=k)


def plot_curves(result: SweepResult) -> None:
    """Plot the separation degree and clustering coefficient curves."""
    import matplotlib.pyplot as plt

    fig, ax_l = plt.subplots(figsize=(9, 5))
    ax_l.set_xscale("log")
    ax_l.plot(
        result.ps,
        result.lengths,
        color=_L_COLOR,
        linewidth=2.5,
        label="Gradi di separazione (L)",
    )
    ax_l.set_xlabel("% di scorciatoie (scala log)")
    ax_l.set_ylabel("Gradi di separazione", color=_L_COLOR)
    ax_l.tick_params(axis="y", labelcolor=_L_COLOR)
    ax_l.set_ylim(bottom=0)

    ax_c = ax_l.twinx()
    ax_c.plot(
        result.ps,
        result.clustering,
        color=_C_COLOR,
        linewidth=2.5,
        label="Coefficiente di gruppo (C)",
    )
    ax_c.set_ylabel("Coefficiente di gruppo", color=_C_COLOR)
    ax_c.tick_params(axis="y", labelcolor=_C_COLOR)
    ax_c.set_ylim(0, 0.7)

    ax_l.set_title(
        f"Watts-Strogatz: {result.n} nodi, {result.k} collegamenti per nodo"
    )
    ax_l.grid(True, alpha=0.2)
    fig.tight_layout()
    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(_OUT_PATH, dpi=140)
    print(f"Grafico salvato in {_OUT_PATH}")


def run_plot(
    n: int = 1000,
    k: int = 10,
    trials: int = 10,
    samples: int | None = 64,
    seed: int | None = None,
    use_cache: bool = True,
) -> None:
    """Run the full plotting process, including sweep and visualisation."""
    ps = log_space(1e-4, 1.0, 25)
    key = cache_key(n, k, ps, trials, samples, seed)
    result = load_cache(_CACHE_PATH, key) if use_cache else None
    if result is None:
        mode = "esatto" if samples is None else f"campionato a {samples}"
        print(
            f"Simulazione: n={n}, k={k}, {len(ps)} valori di p, "
            f"{trials} grafi ciascuno, L {mode}"
        )
        result = run_sweep(n, k, ps, trials, samples, seed)
        save_cache(_CACHE_PATH, key, result)
    else:
        print(f"Risultati dalla cache ({_CACHE_PATH})")
    plot_curves(result)
