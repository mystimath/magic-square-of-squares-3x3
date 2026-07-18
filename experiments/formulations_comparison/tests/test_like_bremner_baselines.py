from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from prototypes.model import generate_square_progressions_parametric  # noqa: E402
from search_non_square_center_v2_2_safe import (  # noqa: E402
    recombine_center_offsets as recombine_v2_2,
)
from search_non_square_center_v2_3_structural import (  # noqa: E402
    recombine_center_offsets as recombine_v2_3,
)


class LikeBremnerBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        catalog = generate_square_progressions_parametric(601)
        cls.offsets = {
            progression.difference
            for progression in catalog
            if progression.center == 180625
        }

    def test_v2_2_safe_keeps_bremner_at_r601(self) -> None:
        rows, stats = recombine_v2_2(
            180625,
            self.offsets,
            "relaxed7",
            7,
            True,
            True,
            1_000_000,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(stats["candidates_kept_relaxed7"], 1)

    def test_v2_3_non_square_center_filter_is_not_an_oracle_here(self) -> None:
        rows, stats = recombine_v2_3(
            180625,
            self.offsets,
            "relaxed7",
            7,
            True,
            True,
            1_000_000,
        )
        self.assertEqual(rows, [])
        self.assertEqual(stats["centers_no_candidate"], 1)


if __name__ == "__main__":
    unittest.main()
