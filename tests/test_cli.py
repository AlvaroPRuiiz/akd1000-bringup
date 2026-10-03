import unittest

from akd1000_bringup.cli import build_parser


class CliTests(unittest.TestCase):
    def test_public_commands_are_minimal_and_generic(self):
        parser = build_parser()
        subparsers = parser._subparsers._group_actions[0].choices
        self.assertEqual(set(subparsers), {"doctor", "verify", "run", "benchmark"})


if __name__ == "__main__":
    unittest.main()
