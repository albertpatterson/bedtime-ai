from __future__ import annotations

import unittest

from scripts.build_windows_exe import TARGETS, build_pyinstaller_args, parse_args


class WindowsPackagingTests(unittest.TestCase):
    def test_parse_args_defaults_to_onefile_clean_build(self) -> None:
        args = parse_args(["guard_screen"])

        self.assertEqual(args.target, "guard_screen")
        self.assertFalse(args.onedir)
        self.assertFalse(args.skip_clean)

    def test_guard_screen_build_args_include_onefile_and_script(self) -> None:
        target = TARGETS["guard_screen"]

        args = build_pyinstaller_args(target=target, onefile=True, clean=True)

        self.assertIn("--onefile", args)
        self.assertIn("--clean", args)
        self.assertIn(target.name, args)
        self.assertEqual(args[-1], str(target.script_path))

    def test_overlay_spike_build_args_support_onedir(self) -> None:
        target = TARGETS["windows_overlay_spike"]

        args = build_pyinstaller_args(target=target, onefile=False, clean=False)

        self.assertNotIn("--onefile", args)
        self.assertNotIn("--clean", args)
        self.assertIn(target.name, args)
        self.assertEqual(args[-1], str(target.script_path))


if __name__ == "__main__":
    unittest.main()
