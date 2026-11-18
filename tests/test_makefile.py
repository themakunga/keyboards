import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MakefileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        directory = Path(self.directory.name)
        self.calls = directory / "calls"
        qmk = directory / "qmk"
        qmk.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$*" >> "$QMK_CALLS"\n'
            'exit "${QMK_EXIT:-0}"\n'
        )
        qmk.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{directory}{os.pathsep}{os.environ['PATH']}",
            "QMK_CALLS": str(self.calls),
        }

    def make(self, *args):
        return subprocess.run(
            ["make", *args], cwd=ROOT, env=self.env, text=True, capture_output=True
        )

    def test_default_and_explicit_help_do_not_call_qmk(self):
        for args in [(), ("help",)]:
            result = self.make(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            for word in ["setup", "update", "build", "flash", "slash", "eva01", "eva02"]:
                self.assertIn(word, result.stdout)
        self.assertFalse(self.calls.exists())

    def test_build_flash_and_alias_for_each_registered_keyboard(self):
        for keyboard, board in [("eva01", "sofle/v2"), ("eva02", "corne/v2")]:
            for action, command in [("build", "compile"), ("flash", "flash"), ("slash", "flash")]:
                with self.subTest(keyboard=keyboard, action=action):
                    result = self.make(action, keyboard)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(
                        self.calls.read_text(),
                        f"{command} -kb {board} -km themakunga_{keyboard}\n",
                    )
                    self.calls.unlink()

    def test_invalid_requests_do_not_call_qmk(self):
        for args in [
            ("build",), ("flash",), ("slash",), ("eva01",),
            ("flash", "unknown"), ("flash", "%"), ("flash", "eva01", "eva02"),
            ("build", "flash", "eva01"), ("eva01", "flash"),
            ("flash", "help"), ("setup", "eva01"), ("update", "setup"),
            ("setup", "build", "eva01"),
        ]:
            with self.subTest(args=args):
                self.assertNotEqual(self.make(*args).returncode, 0)
                self.assertFalse(self.calls.exists())

    def test_dry_run_does_not_call_qmk(self):
        result = self.make("-n", "flash", "eva01")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("qmk flash -kb sofle/v2 -km themakunga_eva01", result.stdout)
        self.assertFalse(self.calls.exists())

    def firmware(self):
        firmware = Path(self.directory.name) / "qmk firmware"
        (firmware / "keyboards").mkdir(parents=True)
        return firmware

    def test_setup_links_and_configures_userspace_repeatably(self):
        firmware = self.firmware()
        for _ in range(2):
            result = self.make("setup", f"QMK_HOME={firmware}")
            self.assertEqual(result.returncode, 0, result.stderr)
        expected = [f"config user.qmk_home={firmware}", f"config user.overlay_dir={ROOT}", "userspace-doctor"]
        self.assertEqual(self.calls.read_text().splitlines(), expected * 2)
        for family in ["sofle", "corne"]:
            self.assertEqual((firmware / "keyboards" / family / "v2").resolve(), ROOT / "keyboards" / family / "v2")

    def test_update_links_without_changing_qmk_configuration(self):
        firmware = self.firmware()
        for _ in range(2):
            result = self.make("update", f"QMK_HOME={firmware}")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.calls.exists())
        self.assertTrue((firmware / "keyboards/sofle/v2").is_symlink())
        self.assertTrue((firmware / "keyboards/corne/v2").is_symlink())

    def test_setup_with_invalid_checkout_does_not_configure_qmk(self):
        result = self.make("setup", f"QMK_HOME={self.directory.name}/missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls.exists())

    def test_qmk_failure_is_propagated(self):
        self.env["QMK_EXIT"] = "1"
        self.assertNotEqual(self.make("build", "eva01").returncode, 0)


if __name__ == "__main__":
    unittest.main()
