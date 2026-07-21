"""Produit un rapport D4 : artefact elliptique normalisé, graines B4 et fermetures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.elliptic_b4_bridge import (  # noqa: E402
    inferred_complete_box_root,
    integer_grids_from_elliptic_artifact,
    progressions_from_elliptic_artifact,
    search_b4_from_elliptic_artifact,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--complete-box-root", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    grids = integer_grids_from_elliptic_artifact(args.artifact)
    progressions = progressions_from_elliptic_artifact(args.artifact)
    bound = args.complete_box_root or inferred_complete_box_root(grids)
    result = search_b4_from_elliptic_artifact(args.artifact, bound)
    payload = {
        "engine": "D4-elliptic-to-B4-bridge",
        "source_artifact": str(args.artifact).replace("\\", "/"),
        "integer_grid_count": len(grids),
        "complete_box_root": bound,
        "progressions": [
            {
                "roots": [item.low_root, item.center_root, item.high_root],
                "difference": item.difference,
            }
            for item in progressions
        ],
        "b4": {
            "formulation": result.formulation,
            "stats": result.stats,
            "orbit_class_counts": result.orbit_class_counts,
            "classes": [list(grid) for grid in result.classes],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()