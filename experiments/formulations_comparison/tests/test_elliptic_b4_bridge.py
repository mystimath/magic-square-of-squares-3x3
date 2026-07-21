from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from common.validation import canonical_d4  # noqa: E402
from prototypes.elliptic_b4_bridge import (  # noqa: E402
    inferred_complete_box_root,
    integer_grids_from_elliptic_artifact,
    progressions_from_elliptic_artifact,
    progressions_from_integer_grid,
)
from prototypes.lo_shu_seven import search_lo_shu_seven_box  # noqa: E402


BREMNER = (
    139129, 360721, 42025,
    83521, 180625, 277729,
    319225, 529, 222121,
)


class EllipticB4BridgeTests(unittest.TestCase):
    def test_bremner_grid_exposes_the_two_b4_seed_progressions(self) -> None:
        progressions = progressions_from_integer_grid(BREMNER)
        signatures = {
            (item.low_root, item.center_root, item.high_root, item.difference)
            for item in progressions
        }
        self.assertIn((23, 205, 289, 41496), signatures)
        self.assertIn((23, 373, 527, 138600), signatures)

    def test_sparse_elliptic_seeds_recover_bremner_through_b4(self) -> None:
        progressions = progressions_from_integer_grid(BREMNER)
        result = search_lo_shu_seven_box(601, progressions=progressions)
        self.assertEqual(result.classes, (canonical_d4(BREMNER),))
        self.assertEqual(result.stats["progressions"], 3)
        self.assertEqual(result.stats["accepted_classes"], 1)

    def test_d2_nested_artifact_is_deduplicated_and_calibrates_b4(self) -> None:
        repository = pathlib.Path(__file__).resolve().parents[3]
        artifact = repository / "results/formulations_comparison/sage/d2_rank2_curves_bounds2_3.json"
        grids = integer_grids_from_elliptic_artifact(artifact)
        self.assertEqual(grids, (BREMNER,))
        self.assertEqual(inferred_complete_box_root(grids), 601)
        self.assertEqual(len(progressions_from_elliptic_artifact(artifact)), 3)


if __name__ == "__main__":
    unittest.main()