import tempfile
import unittest
from pathlib import Path

import numpy as np

from akd1000_bringup.io import load_array


class IoTests(unittest.TestCase):
    def test_npz_requires_unambiguous_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.npz"
            np.savez(
                path,
                X=np.zeros((1, 8), dtype=np.uint8),
                inputs=np.ones((1, 8), dtype=np.uint8),
            )
            with self.assertRaisesRegex(ValueError, "--input-key"):
                load_array(path)
            self.assertEqual(load_array(path, "X").shape, (1, 8))

    def test_load_array_preserves_numeric_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.npy"
            expected = np.arange(24, dtype=np.float32).reshape(1, 2, 3, 4)
            np.save(path, expected)
            np.testing.assert_array_equal(load_array(path), expected)


if __name__ == "__main__":
    unittest.main()
