from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes.lo_shu_seven import search_lo_shu_seven_box  # noqa: E402
from prototypes.lo_shu_seven_grouped import (  # noqa: E402
    group_progression_incidences,
    search_lo_shu_seven_incidence_groups,
)
from prototypes.streaming_seven_incidences import (  # noqa: E402
    CanonicalProgressionIncidenceStream,
)


class StreamingSevenIncidenceTests(unittest.TestCase):
    def test_stream_matches_material_b4_classes_and_stats(self) -> None:
        for complete_box_root in (127, 601, 2000):
            with self.subTest(complete_box_root=complete_box_root):
                expected = search_lo_shu_seven_box(complete_box_root)
                with tempfile.TemporaryDirectory() as temporary:
                    temporary_path = pathlib.Path(temporary)
                    stream = CanonicalProgressionIncidenceStream(
                        complete_box_root,
                        shard_count=11,
                        temp_dir=temporary_path,
                    )
                    actual = search_lo_shu_seven_incidence_groups(
                        complete_box_root,
                        stream,
                        validate_incidence_groups=False,
                    )
                    self.assertEqual(list(temporary_path.iterdir()), [])
                self.assertEqual(actual.classes, expected.classes)
                self.assertEqual(
                    actual.orbit_class_counts,
                    expected.orbit_class_counts,
                )
                self.assertEqual(actual.stats, expected.stats)
                self.assertEqual(
                    stream.stats["raw_incidence_records"],
                    3 * stream.stats["progressions"],
                )
                self.assertEqual(
                    stream.stats["duplicate_incidence_records"],
                    0,
                )
                self.assertEqual(
                    actual.stats["incidence_group_validation"],
                    0,
                )

    def test_trusted_and_validated_groups_have_identical_results(self) -> None:
        catalog = generate_square_progressions_parametric_canonical(601)
        groups = group_progression_incidences(catalog)
        validated = search_lo_shu_seven_incidence_groups(601, groups)
        trusted = search_lo_shu_seven_incidence_groups(
            601,
            groups,
            validate_incidence_groups=False,
        )
        self.assertEqual(trusted.classes, validated.classes)
        self.assertEqual(
            trusted.orbit_class_counts,
            validated.orbit_class_counts,
        )
        validated_stats = dict(validated.stats)
        trusted_stats = dict(trusted.stats)
        self.assertEqual(validated_stats.pop("incidence_group_validation"), 1)
        self.assertEqual(trusted_stats.pop("incidence_group_validation"), 0)
        self.assertEqual(trusted_stats, validated_stats)

    def test_default_validation_rejects_malformed_groups(self) -> None:
        catalog = generate_square_progressions_parametric_canonical(127)
        groups = group_progression_incidences(catalog)

        with self.assertRaisesRegex(ValueError, "strictement croissants"):
            search_lo_shu_seven_incidence_groups(
                127,
                tuple(reversed(groups)),
            )

        shared_square, incidences = groups[0]
        duplicated = (
            (shared_square, (incidences[0], incidences[0])),
        )
        with self.assertRaisesRegex(ValueError, "dupliquée"):
            search_lo_shu_seven_incidence_groups(127, duplicated)


if __name__ == "__main__":
    unittest.main()
