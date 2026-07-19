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
    def test_handle_cache_validation(self) -> None:
        for invalid in (True, 0, -1, 1.5, "2"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    ValueError,
                    "max_open_shard_handles",
                ):
                    CanonicalProgressionIncidenceStream(
                        127,
                        max_open_shard_handles=invalid,
                    )
        for invalid in (True, 0, 24, 1.5, "1024"):
            with self.subTest(invalid_buffer=invalid):
                with self.assertRaisesRegex(
                    ValueError,
                    "max_buffered_write_bytes",
                ):
                    CanonicalProgressionIncidenceStream(
                        127,
                        max_buffered_write_bytes=invalid,
                    )
        with self.assertRaisesRegex(ValueError, "mutuellement exclusifs"):
            CanonicalProgressionIncidenceStream(
                127,
                max_open_shard_handles=3,
                max_buffered_write_bytes=1024,
            )
        for invalid in (True, -1, 1, 1.5, "512"):
            with self.subTest(invalid_handle_buffering=invalid):
                with self.assertRaisesRegex(
                    ValueError,
                    "write_handle_buffering",
                ):
                    CanonicalProgressionIncidenceStream(
                        127,
                        write_handle_buffering=invalid,
                    )
        with self.assertRaisesRegex(ValueError, "mutuellement exclusifs"):
            CanonicalProgressionIncidenceStream(
                127,
                max_buffered_write_bytes=1024,
                write_handle_buffering=512,
            )

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
                self.assertEqual(
                    stream.stats["write_handle_opens"],
                    stream.stats["shards_used"],
                )
                self.assertEqual(stream.stats["write_handle_evictions"], 0)
                self.assertEqual(
                    stream.stats["max_open_write_handles"],
                    stream.stats["shards_used"],
                )

    def test_bounded_lru_preserves_classes_and_exhaustive_counters(self) -> None:
        complete_box_root = 2000
        with tempfile.TemporaryDirectory() as temporary:
            unbounded = CanonicalProgressionIncidenceStream(
                complete_box_root,
                shard_count=11,
                temp_dir=pathlib.Path(temporary),
            )
            expected = search_lo_shu_seven_incidence_groups(
                complete_box_root,
                unbounded,
                validate_incidence_groups=False,
            )
        with tempfile.TemporaryDirectory() as temporary:
            bounded = CanonicalProgressionIncidenceStream(
                complete_box_root,
                shard_count=11,
                max_open_shard_handles=3,
                temp_dir=pathlib.Path(temporary),
            )
            actual = search_lo_shu_seven_incidence_groups(
                complete_box_root,
                bounded,
                validate_incidence_groups=False,
            )

        self.assertEqual(actual.classes, expected.classes)
        self.assertEqual(actual.orbit_class_counts, expected.orbit_class_counts)
        self.assertEqual(actual.stats, expected.stats)
        coverage_keys = (
            "progressions",
            "raw_incidence_records",
            "shards_used",
            "duplicate_incidence_records",
            "max_incidence_records_in_shard",
            "indexed_square_values",
        )
        self.assertEqual(
            {key: bounded.stats[key] for key in coverage_keys},
            {key: unbounded.stats[key] for key in coverage_keys},
        )
        self.assertEqual(bounded.stats["write_handle_cache_capacity"], 3)
        self.assertLessEqual(bounded.stats["max_open_write_handles"], 3)
        self.assertGreater(bounded.stats["write_handle_evictions"], 0)
        self.assertEqual(
            bounded.stats["write_handle_opens"],
            3 + bounded.stats["write_handle_evictions"],
        )

    def test_buffered_lru_preserves_exhaustive_results(self) -> None:
        complete_box_root = 2000
        with tempfile.TemporaryDirectory() as temporary:
            unbounded = CanonicalProgressionIncidenceStream(
                complete_box_root,
                shard_count=11,
                temp_dir=pathlib.Path(temporary),
            )
            expected = search_lo_shu_seven_incidence_groups(
                complete_box_root,
                unbounded,
                validate_incidence_groups=False,
            )
        with tempfile.TemporaryDirectory() as temporary:
            buffered = CanonicalProgressionIncidenceStream(
                complete_box_root,
                shard_count=11,
                max_buffered_write_bytes=1024,
                temp_dir=pathlib.Path(temporary),
            )
            actual = search_lo_shu_seven_incidence_groups(
                complete_box_root,
                buffered,
                validate_incidence_groups=False,
            )
            self.assertEqual(list(pathlib.Path(temporary).iterdir()), [])

        self.assertEqual(actual.classes, expected.classes)
        self.assertEqual(actual.orbit_class_counts, expected.orbit_class_counts)
        self.assertEqual(actual.stats, expected.stats)
        coverage_keys = (
            "progressions",
            "raw_incidence_records",
            "shards_used",
            "duplicate_incidence_records",
            "max_incidence_records_in_shard",
            "indexed_square_values",
        )
        self.assertEqual(
            {key: buffered.stats[key] for key in coverage_keys},
            {key: unbounded.stats[key] for key in coverage_keys},
        )
        self.assertEqual(buffered.stats["write_buffer_capacity_bytes"], 1024)
        self.assertLessEqual(
            buffered.stats["max_buffered_write_bytes"],
            1024,
        )
        self.assertGreater(buffered.stats["write_buffer_evictions"], 0)
        self.assertGreater(
            buffered.stats["write_buffer_flushes"],
            buffered.stats["shards_used"],
        )
        self.assertEqual(
            buffered.stats["write_handle_opens"],
            buffered.stats["write_buffer_flushes"],
        )

    def test_grouped_writes_preserve_exhaustive_results(self) -> None:
        complete_box_root = 2000
        with tempfile.TemporaryDirectory() as temporary:
            grouped = CanonicalProgressionIncidenceStream(
                complete_box_root,
                shard_count=11,
                group_writes_by_shard=True,
                temp_dir=pathlib.Path(temporary),
            )
            actual = search_lo_shu_seven_incidence_groups(
                complete_box_root,
                grouped,
                validate_incidence_groups=False,
            )

        expected = search_lo_shu_seven_box(complete_box_root)
        self.assertEqual(actual.classes, expected.classes)
        self.assertEqual(actual.stats, expected.stats)
        self.assertEqual(grouped.stats["group_writes_by_shard"], 1)
        self.assertEqual(grouped.stats["write_handle_opens"], 11)
        self.assertEqual(grouped.stats["max_open_write_handles"], 1)
        self.assertGreater(grouped.stats["max_buffered_write_bytes"], 0)

    def test_reduced_handle_buffering_preserves_exhaustive_results(self) -> None:
        complete_box_root = 2000
        expected = search_lo_shu_seven_box(complete_box_root)
        with tempfile.TemporaryDirectory() as temporary:
            stream = CanonicalProgressionIncidenceStream(
                complete_box_root,
                shard_count=11,
                write_handle_buffering=512,
                temp_dir=pathlib.Path(temporary),
            )
            actual = search_lo_shu_seven_incidence_groups(
                complete_box_root,
                stream,
                validate_incidence_groups=False,
            )
            self.assertEqual(list(pathlib.Path(temporary).iterdir()), [])

        self.assertEqual(actual.classes, expected.classes)
        self.assertEqual(actual.orbit_class_counts, expected.orbit_class_counts)
        self.assertEqual(actual.stats, expected.stats)
        self.assertEqual(stream.stats["write_handle_buffering"], 512)
        self.assertEqual(
            stream.stats["write_handle_opens"],
            stream.stats["shards_used"],
        )
        self.assertEqual(stream.stats["write_handle_evictions"], 0)
        self.assertEqual(
            stream.stats["max_open_write_handles"],
            stream.stats["shards_used"],
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
