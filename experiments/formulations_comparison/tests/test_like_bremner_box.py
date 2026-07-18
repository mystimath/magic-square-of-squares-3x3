from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from common.validation import canonical_d4  # noqa: E402
from prototypes.like_bremner_box import search_like_bremner_box  # noqa: E402

BREMNER = (
    139129, 360721, 42025,
    83521, 180625, 277729,
    319225, 529, 222121,
)


class CompleteBoxBoundTests(unittest.TestCase):
    def test_bremner_first_appears_at_complete_box_root_601(self) -> None:
        self.assertEqual(search_like_bremner_box(600).classes, ())
        result = search_like_bremner_box(complete_box_root=601)
        self.assertEqual(result.classes, (canonical_d4(BREMNER),))
        self.assertLess(600 * 600, max(BREMNER))
        self.assertLessEqual(max(BREMNER), 601 * 601)


if __name__ == "__main__":
    unittest.main()
