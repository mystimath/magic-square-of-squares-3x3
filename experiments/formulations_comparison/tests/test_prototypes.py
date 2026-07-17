from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from common.validation import is_magic  # noqa: E402
from prototypes.formulation_a import search_formulation_a  # noqa: E402
from prototypes.formulation_b1 import search_formulation_b1  # noqa: E402
from prototypes.formulation_b2 import search_formulation_b2  # noqa: E402
from prototypes.formulation_c import search_formulation_c  # noqa: E402
from prototypes.formulation_d import probe_formulation_d  # noqa: E402
from prototypes.model import (  # noqa: E402
    build_centered_grid,
    generate_square_progressions,
    generate_square_progressions_parametric,
)


class ProgressionTests(unittest.TestCase):
    def test_known_progression_1_25_49_is_generated(self) -> None:
        rows = generate_square_progressions(7)
        signatures = {
            (row.low_root, row.center_root, row.high_root, row.difference)
            for row in rows
        }
        self.assertIn((1, 5, 7, 24), signatures)

    def test_progressions_are_exact_and_unique(self) -> None:
        rows = generate_square_progressions(30)
        signatures = set()
        for row in rows:
            self.assertEqual(row.center - row.low, row.high - row.center)
            self.assertLess(row.low_root, row.center_root)
            self.assertLess(row.center_root, row.high_root)
            signature = (row.low_root, row.center_root, row.high_root)
            self.assertNotIn(signature, signatures)
            signatures.add(signature)

    def test_parametric_catalog_matches_quadratic_oracle(self) -> None:
        for bound in (10, 50, 100, 250, 500):
            with self.subTest(max_root=bound):
                self.assertEqual(
                    generate_square_progressions(bound),
                    generate_square_progressions_parametric(bound),
                )


class CenteredFormTests(unittest.TestCase):
    def test_centered_form_is_magic_for_arbitrary_integer_parameters(self) -> None:
        grid = build_centered_grid(100, 7, 19)
        self.assertTrue(is_magic(grid))


class CrossValidationTests(unittest.TestCase):
    def test_a_b1_b2_agree_on_tiny_complete_bounds(self) -> None:
        for bound in (10, 20, 30):
            with self.subTest(max_root=bound):
                result_a = search_formulation_a(bound)
                result_b1 = search_formulation_b1(bound)
                result_b2 = search_formulation_b2(bound)
                self.assertEqual(result_a.classes, result_b1.classes)
                self.assertEqual(result_b1.classes, result_b2.classes)

    def test_b1_b2_index_the_same_progression_catalog_size(self) -> None:
        result_b1 = search_formulation_b1(30)
        result_b2 = search_formulation_b2(30)
        self.assertEqual(result_b1.stats["progressions"], result_b2.stats["progressions"])

    def test_shared_catalog_preserves_all_adapter_results(self) -> None:
        bound = 50
        catalog = generate_square_progressions(bound)
        engines = (
            search_formulation_b1,
            search_formulation_b2,
            search_formulation_c,
            probe_formulation_d,
        )
        for engine in engines:
            with self.subTest(engine=engine.__name__):
                standalone = engine(bound)
                shared = engine(bound, progressions=catalog)
                self.assertEqual(standalone.classes, shared.classes)
                self.assertEqual(standalone.stats, shared.stats)

    def test_invalid_bound_is_rejected_by_all_formulations(self) -> None:
        for search in (search_formulation_a, search_formulation_b1, search_formulation_b2):
            with self.subTest(search=search.__name__):
                with self.assertRaises(ValueError):
                    search(0)


if __name__ == "__main__":
    unittest.main()
