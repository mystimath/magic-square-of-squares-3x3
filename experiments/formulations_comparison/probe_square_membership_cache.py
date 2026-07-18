"""Mesure la réutilisation des tests de carré dans le flux exact B6."""

from __future__ import annotations

import argparse
from collections import OrderedDict
import json
import math
import pathlib
import sys
import time

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes import lo_shu_nine  # noqa: E402


class CacheProbeMembership:
    """Oracle direct qui simule plusieurs LRU sans modifier les décisions."""

    def __init__(self, max_root: int, capacities: tuple[int, ...]) -> None:
        self.upper = max_root * max_root
        self.capacities = capacities
        self.caches = {
            capacity: OrderedDict() for capacity in capacities
        }
        self.hits = {capacity: 0 for capacity in capacities}
        self.misses = {capacity: 0 for capacity in capacities}
        self.queries = 0
        self.unique_values: set[int] = set()

    def __contains__(self, value: object) -> bool:
        self.queries += 1
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            or value > self.upper
        ):
            result = False
        else:
            root = math.isqrt(value)
            result = root * root == value
            self.unique_values.add(value)

        for capacity, cache in self.caches.items():
            if value in cache:
                self.hits[capacity] += 1
                cache.move_to_end(value)
            else:
                self.misses[capacity] += 1
                cache[value] = result
                if len(cache) > capacity:
                    cache.popitem(last=False)
        return result

    def payload(self) -> dict[str, object]:
        return {
            "queries": self.queries,
            "unique_values": len(self.unique_values),
            "repeated_queries": self.queries - len(self.unique_values),
            "global_repeat_rate": (
                (self.queries - len(self.unique_values)) / self.queries
                if self.queries
                else 0.0
            ),
            "lru": {
                str(capacity): {
                    "hits": self.hits[capacity],
                    "misses": self.misses[capacity],
                    "hit_rate": self.hits[capacity] / self.queries,
                    "final_entries": len(self.caches[capacity]),
                }
                for capacity in self.capacities
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-root", type=int, default=100_000)
    parser.add_argument(
        "--capacities",
        type=int,
        nargs="+",
        default=(256, 1024, 4096, 16384, 65536),
    )
    parser.add_argument("--json-out", type=pathlib.Path)
    args = parser.parse_args()
    capacities = tuple(sorted(set(args.capacities)))
    if not capacities or capacities[0] < 1:
        parser.error("les capacités doivent être strictement positives")

    catalog_started = time.perf_counter()
    catalog = generate_square_progressions_parametric_canonical(args.max_root)
    catalog_seconds = time.perf_counter() - catalog_started
    probe = CacheProbeMembership(args.max_root, capacities)
    original_factory = lo_shu_nine.build_square_membership
    lo_shu_nine.build_square_membership = lambda _root, _mode="isqrt": probe
    try:
        search_started = time.perf_counter()
        result = lo_shu_nine.search_lo_shu_nine_box(
            args.max_root,
            progressions=catalog,
            square_membership_mode="isqrt",
        )
        search_seconds = time.perf_counter() - search_started
    finally:
        lo_shu_nine.build_square_membership = original_factory

    payload = {
        "probe": "B6 bounded LRU square-membership reuse",
        "max_square_root": args.max_root,
        "catalog_progressions": len(catalog),
        "catalog_seconds": catalog_seconds,
        "search_seconds_instrumented": search_seconds,
        "class_count": len(result.classes),
        "membership": probe.payload(),
    }
    json_out = (
        args.json_out
        or PROJECT_ROOT
        / "results"
        / "formulations_comparison"
        / "benchmarks"
        / f"lo_shu_b6_membership_cache_probe_r{args.max_root}.json"
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
