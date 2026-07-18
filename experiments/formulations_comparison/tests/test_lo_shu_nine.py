from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from _nine_square_v2_2_oracle import search_v2_2_nine_box  # noqa: E402
from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes.formulation_b1 import search_formulation_b1  # noqa: E402
from prototypes.formulation_b2 import search_formulation_b2  # noqa: E402
from prototypes.lo_shu_nine import (  # noqa: E402
    search_lo_shu_nine_box,
    search_lo_shu_nine_incidence_groups,
)
from prototypes.lo_shu_seven import PARAMETER_POSITIONS  # noqa: E402
from prototypes.streaming_seven_incidences import (  # noqa: E402
    CanonicalProgressionIncidenceStream,
)
from search_non_square_center_v2_2_safe import (  # noqa: E402
    recombine_center_offsets,
)


class LoShuNineSearchTests(unittest.TestCase):
    def test_all_square_mask_has_nine_complete_parameter_crosses(self) -> None:
        selected = set("abcdefghi")
        crosses = tuple((x, k) for x in range(3) for k in range(3))
        self.assertEqual(len(crosses), 9)
        for x, k in crosses:
            self.assertTrue(set(PARAMETER_POSITIONS[x]) <= selected)
            self.assertTrue(
                {PARAMETER_POSITIONS[row][k] for row in range(3)}
                <= selected
            )

    def test_b6_matches_b1_and_b2_on_shared_catalogs(self) -> None:
        for complete_box_root in (30, 127, 601):
            with self.subTest(complete_box_root=complete_box_root):
                catalog = generate_square_progressions_parametric_canonical(
                    complete_box_root
                )
                b1 = search_formulation_b1(
                    complete_box_root,
                    primitive_only=True,
                    progressions=catalog,
                )
                b2 = search_formulation_b2(
                    complete_box_root,
                    primitive_only=True,
                    progressions=catalog,
                )
                b6 = search_lo_shu_nine_box(
                    complete_box_root,
                    progressions=catalog,
                )
                self.assertEqual(b6.classes, b1.classes)
                self.assertEqual(b6.classes, b2.classes)

    def test_b6_matches_exhaustive_v2_2_oracle(self) -> None:
        for complete_box_root in (127, 601, 1202):
            with self.subTest(complete_box_root=complete_box_root):
                b6 = search_lo_shu_nine_box(complete_box_root)
                oracle_classes, _ = search_v2_2_nine_box(
                    complete_box_root,
                    recombine_center_offsets,
                )
                self.assertEqual(b6.classes, oracle_classes)

    def test_stream_matches_material_classes_and_stats(self) -> None:
        for complete_box_root in (127, 601, 2000):
            with self.subTest(complete_box_root=complete_box_root):
                expected = search_lo_shu_nine_box(complete_box_root)
                with tempfile.TemporaryDirectory() as temporary:
                    temporary_path = pathlib.Path(temporary)
                    stream = CanonicalProgressionIncidenceStream(
                        complete_box_root,
                        shard_count=11,
                        temp_dir=temporary_path,
                    )
                    actual = search_lo_shu_nine_incidence_groups(
                        complete_box_root,
                        stream,
                    )
                    self.assertEqual(list(temporary_path.iterdir()), [])
                self.assertEqual(actual.classes, expected.classes)
                self.assertEqual(actual.stats, expected.stats)

    def test_bremner_is_rejected_because_it_has_only_seven_squares(self) -> None:
        result = search_lo_shu_nine_box(601)
        self.assertEqual(result.classes, ())
        self.assertEqual(result.stats["validated_candidates"], 0)


if __name__ == "__main__":
    unittest.main()
