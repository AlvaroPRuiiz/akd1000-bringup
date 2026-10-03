import hashlib
import tempfile
import unittest
from pathlib import Path

from akd1000_bringup.artifacts import sha256_file, verify_artifact


class ArtifactTests(unittest.TestCase):
    def test_verify_artifact_with_full_hash_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.fbz"
            path.write_bytes(b"validated-model")
            digest = hashlib.sha256(b"validated-model").hexdigest()
            result = verify_artifact(path, {"size_bytes": 15, "sha256": digest})
            self.assertTrue(result["valid"])
            self.assertEqual(sha256_file(path), digest)

    def test_verify_artifact_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.fbz"
            path.write_bytes(b"wrong")
            with self.assertRaisesRegex(ValueError, "Size mismatch"):
                verify_artifact(path, {"size_bytes": 99, "sha256": sha256_file(path)})


if __name__ == "__main__":
    unittest.main()
