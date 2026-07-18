from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from _eight_square_v2_2_oracle import (  # noqa: E402
    search_v2_2_eight_box,
)
from prototypes.eight_square_masks import (  # noqa: E402
    EIGHT_SQUARE_MASK_ORBITS,
    ORBIT_BY_MASK,
)
from prototypes.lo_shu_eight import (  # noqa: E402
    search_lo_shu_eight_box,
    search_lo_shu_eight_incidence_groups,
    seed_crosses_for_mask,
)
from prototypes.lo_shu_seven import PARAMETER_POSITIONS  # noqa: E402
from prototypes.streaming_seven_incidences import (  # noqa: E402
    CanonicalProgressionIncidenceStream,
)
from search_non_square_center_v2_2_safe import (  # noqa: E402
    recombine_center_offsets,
)


class EightSquareMaskTests(unittest.TestCase):
    def test_three_orbits_partition_all_nine_masks(self) -> None:
        self.assertEqual(len(EIGHT_SQUARE_MASK_ORBITS), 3)
        self.assertEqual(len(ORBIT_BY_MASK), 9)
        self.assertEqual(
            sorted(len(orbit.masks) for orbit in EIGHT_SQUARE_MASK_ORBITS),
            [1, 4, 4],
        )

    def test_every_mask_has_four_complete_parameter_crosses(self) -> None:
        for orbit in EIGHT_SQUARE_MASK_ORBITS:
            for mask in orbit.masks:
                with self.subTest(orbit=orbit.key, mask=mask):
                    selected = set(mask)
                    crosses = seed_crosses_for_mask(mask)
                    self.assertEqual(len(crosses), 4)
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


class LoShuEightSearchTests(unittest.TestCase):
    def test_b5_matches_exhaustive_v2_2_oracle(self) -> None:
        for complete_box_root in (127, 601, 1202):
            with self.subTest(complete_box_root=complete_box_root):
                b5 = search_lo_shu_eight_box(complete_box_root)
                oracle_classes, _, oracle_orbits = search_v2_2_eight_box(
                    complete_box_root,
                    recombine_center_offsets,
                )
                self.assertEqual(b5.classes, oracle_classes)
                self.assertEqual(b5.orbit_class_counts, oracle_orbits)

    def test_stream_matches_material_classes_and_stats(self) -> None:
        for complete_box_root in (127, 601, 2000):
            with self.subTest(complete_box_root=complete_box_root):
                expected = search_lo_shu_eight_box(complete_box_root)
                with tempfile.TemporaryDirectory() as temporary:
                    temporary_path = pathlib.Path(temporary)
                    stream = CanonicalProgressionIncidenceStream(
                        complete_box_root,
                        shard_count=11,
                        temp_dir=temporary_path,
                    )
                    actual = search_lo_shu_eight_incidence_groups(
                        complete_box_root,
                        stream,
                    )
                    self.assertEqual(list(temporary_path.iterdir()), [])
                self.assertEqual(actual.classes, expected.classes)
                self.assertEqual(actual.stats, expected.stats)
                self.assertEqual(
                    actual.orbit_class_counts,
                    expected.orbit_class_counts,
                )

    def test_bremner_is_rejected_because_it_is_exactly_seven(self) -> None:
        result = search_lo_shu_eight_box(601)
        self.assertEqual(result.classes, ())
        self.assertEqual(result.stats["validated_candidates"], 0)


if __name__ == "__main__":
    unittest.main()
