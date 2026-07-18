from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.lo_shu_seven import search_lo_shu_seven_box  # noqa: E402
from prototypes.lo_shu_seven_grouped import (  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
