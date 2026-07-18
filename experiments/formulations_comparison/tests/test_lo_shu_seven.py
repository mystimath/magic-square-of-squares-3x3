from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from _seven_square_v2_2_oracle import (  # noqa: E402
    search_v2_2_seven_box,
)
from common.validation import canonical_d4  # noqa: E402
from prototypes.lo_shu_seven import (  # noqa: E402
    PARAMETER_POSITIONS,
    search_lo_shu_seven_box,
    seed_crosses_for_mask,
)
from prototypes.seven_square_masks import (  # noqa: E402
    ORBIT_BY_MASK,
    SEVEN_SQUARE_MASK_ORBITS,
    mask_orbit,
)
from search_non_square_center_v2_2_safe import (  # noqa: E402
    recombine_center_offsets,
)

BREMNER = (
    139129, 360721, 42025,
    83521, 180625, 277729,
    319225, 529, 222121,
)


class SevenSquareMaskTests(unittest.TestCase):
    def test_eight_orbits_partition_all_thirty_six_masks(self) -> None:
        self.assertEqual(len(SEVEN_SQUARE_MASK_ORBITS), 8)
        self.assertEqual(len(ORBIT_BY_MASK), 36)
        self.assertEqual(
            sorted(len(orbit.masks) for orbit in SEVEN_SQUARE_MASK_ORBITS),
            [2, 2, 4, 4, 4, 4, 8, 8],
        )
        self.assertEqual(
            mask_orbit("acdefgh").key,
            "corner_edge_nonincident",
        )

    def test_every_mask_has_a_complete_parameter_cross(self) -> None:
        for orbit in SEVEN_SQUARE_MASK_ORBITS:
            for mask in orbit.masks:
                with self.subTest(orbit=orbit.key, mask=mask):
                    selected = set(mask)
                    crosses = seed_crosses_for_mask(mask)
                    self.assertGreaterEqual(len(crosses), 1)
                    for x, k in crosses:
                        self.assertTrue(
                            set(PARAMETER_POSITIONS[x]) <= selected
                        )
                        self.assertTrue(
                            {
                                PARAMETER_POSITIONS[row][k]
                                for row in range(3)
                            }
                            <= selected
                        )


class LoShuSevenSearchTests(unittest.TestCase):
    def test_complete_box_threshold_and_bremner_orbit(self) -> None:
        self.assertEqual(search_lo_shu_seven_box(600).classes, ())
        result = search_lo_shu_seven_box(601)
        self.assertEqual(result.classes, (canonical_d4(BREMNER),))
        self.assertEqual(
            result.orbit_class_counts,
            {"corner_edge_nonincident": 1},
        )

    def test_b4_matches_exhaustive_v2_2_oracle(self) -> None:
        for complete_box_root in (127, 601, 1202):
            with self.subTest(complete_box_root=complete_box_root):
                b4 = search_lo_shu_seven_box(complete_box_root)
                oracle_classes, _, oracle_orbits = search_v2_2_seven_box(
                    complete_box_root,
                    recombine_center_offsets,
                )
                self.assertEqual(b4.classes, oracle_classes)
                self.assertEqual(b4.orbit_class_counts, oracle_orbits)

    def test_scaled_classes_are_removed_only_in_primitive_mode(self) -> None:
        primitive = search_lo_shu_seven_box(1202)
        all_scalings = search_lo_shu_seven_box(
            1202,
            primitive_only=False,
        )
        self.assertEqual(primitive.classes, (canonical_d4(BREMNER),))
        self.assertIn(canonical_d4(BREMNER), all_scalings.classes)
        self.assertGreater(len(all_scalings.classes), len(primitive.classes))
        self.assertGreater(
            primitive.stats["rejected_nonprimitive_seed"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
