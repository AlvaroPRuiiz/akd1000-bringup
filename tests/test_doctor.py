import unittest

from akd1000_bringup.doctor import _driver_kernel_note, diagnostics_exit_code


class DoctorTests(unittest.TestCase):
    def test_driver_kernel_range(self):
        self.assertEqual(_driver_kernel_note("5.4.0")["status"], "within_documented_range")
        self.assertEqual(_driver_kernel_note("6.8.12-v8+")["status"], "within_documented_range")
        self.assertEqual(_driver_kernel_note("5.3.18")["status"], "review_required")
        self.assertEqual(_driver_kernel_note("6.9.0")["status"], "review_required")
        self.assertEqual(_driver_kernel_note("custom")["status"], "unknown")

    def test_version_neutral_and_explicit_exit_codes(self):
        report = {
            "akida": {
                "import_ok": True,
                "devices": [{"description": "AKD1000"}],
                "version": "2.19.3",
            }
        }
        self.assertEqual(diagnostics_exit_code(report), 0)
        self.assertEqual(diagnostics_exit_code(report, "2.19.3"), 0)
        self.assertEqual(diagnostics_exit_code(report, "2.19.1"), 1)
        self.assertEqual(diagnostics_exit_code({"akida": {"import_ok": False}}), 2)
        self.assertEqual(diagnostics_exit_code({"akida": {"import_ok": True, "devices": []}}), 2)


if __name__ == "__main__":
    unittest.main()
