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
            for word in ["build", "flash", "slash", "eva01", "eva02"]:
                self.assertIn(word, result.stdout)
        self.assertFalse(self.calls.exists())

    def test_build_flash_and_alias_for_each_registered_keyboard(self):
        for keyboard in ["eva01", "eva02"]:
            for action, command in [("build", "compile"), ("flash", "flash"), ("slash", "flash")]:
                with self.subTest(keyboard=keyboard, action=action):
                    result = self.make(action, keyboard)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(
                        self.calls.read_text(),
                        f"{command} -kb themakunga/{keyboard} -km nicolas\n",
                    )
                    self.calls.unlink()

    def test_invalid_requests_do_not_call_qmk(self):
        for args in [
            ("build",), ("flash",), ("slash",), ("eva01",),
            ("flash", "unknown"), ("flash", "%"), ("flash", "eva01", "eva02"),
            ("build", "flash", "eva01"), ("eva01", "flash"),
            ("flash", "help"),
        ]:
            with self.subTest(args=args):
                self.assertNotEqual(self.make(*args).returncode, 0)
                self.assertFalse(self.calls.exists())

    def test_dry_run_does_not_call_qmk(self):
        result = self.make("-n", "flash", "eva01")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("qmk flash -kb themakunga/eva01 -km nicolas", result.stdout)
        self.assertFalse(self.calls.exists())

    def test_qmk_failure_is_propagated(self):
        self.env["QMK_EXIT"] = "1"
        self.assertNotEqual(self.make("build", "eva01").returncode, 0)


if __name__ == "__main__":
    unittest.main()
