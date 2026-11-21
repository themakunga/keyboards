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
            for word in ["setup", "update", "build", "flash-left", "flash-right", "eva01", "eva02"]:
                self.assertIn(word, result.stdout)
        self.assertFalse(self.calls.exists())

    def test_build_compiles_both_sides_and_flash_selects_only_one(self):
        for keyboard, board in [("eva01", "sofle/v2"), ("eva02", "corne/v2")]:
            for action, command, sides in [
                ("build", "compile", ["left", "right"]),
                ("flash-left", "flash", ["left"]),
                ("flash-right", "flash", ["right"]),
            ]:
                with self.subTest(keyboard=keyboard, action=action):
                    result = self.make(action, keyboard)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(self.calls.read_text().splitlines(), [
                        f"{command} -kb {board} -km themakunga_{keyboard}_{side}"
                        for side in sides
                    ])
                    self.calls.unlink()

    def test_invalid_requests_do_not_call_qmk(self):
        for args in [
            ("build",), ("flash",), ("slash",), ("eva01",),
            ("flash", "eva01"), ("slash", "eva01"),
            ("flash-left",), ("flash-right", "unknown"),
            ("flash-left", "eva01", "right"),
            ("flash", "unknown"), ("flash", "%"), ("flash", "eva01", "eva02"),
            ("build", "flash", "eva01"), ("eva01", "flash"),
            ("flash", "help"), ("setup", "eva01"), ("update", "setup"),
            ("setup", "build", "eva01"),
        ]:
            with self.subTest(args=args):
                self.assertNotEqual(self.make(*args).returncode, 0)
                self.assertFalse(self.calls.exists())

    def test_dry_run_does_not_call_qmk(self):
        result = self.make("-n", "flash-right", "eva01")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("qmk flash -kb sofle/v2 -km themakunga_eva01_right", result.stdout)
        self.assertFalse(self.calls.exists())

    def firmware(self):
        firmware = Path(self.directory.name) / "qmk firmware"
        (firmware / "keyboards").mkdir(parents=True)
        (firmware / "paths.mk").touch()
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

    def fake_git(self):
        git = Path(self.directory.name) / "git"
        git.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$*" >> "$QMK_GIT_CALLS"\n'
            'if [ "$1" = init ]; then mkdir -p "$2"; fi\n'
            'if [ "${QMK_GIT_FAIL:-}" = fetch ] && [ "$3" = fetch ]; then exit 1; fi\n'
            'if [ "$3" = checkout ]; then mkdir -p "$2/keyboards"; touch "$2/paths.mk"; fi\n'
        )
        git.chmod(0o755)
        self.env["QMK_GIT_CALLS"] = str(Path(self.directory.name) / "git-calls")
        return Path(self.env["QMK_GIT_CALLS"])

    def test_setup_bootstraps_missing_checkout(self):
        git_calls = self.fake_git()
        firmware = Path(self.directory.name) / "new qmk firmware"
        result = self.make("setup", f"QMK_HOME={firmware}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("QMK_HOME has no keyboards directory", result.stderr)
        self.assertTrue((firmware / "keyboards/corne/v2").is_symlink())
        commands = git_calls.read_text()
        revision = "b1aea2556040c28d58d611c8aef0082b5780bb6d"
        self.assertIn(f"fetch --depth=1 origin {revision}", commands)
        self.assertIn(f"checkout --detach {revision}", commands)
        self.assertIn("submodule update --init --recursive --depth=1", commands)
        self.assertEqual(self.make("setup", f"QMK_HOME={firmware}").returncode, 0)
        self.assertEqual(git_calls.read_text(), commands)

    def test_missing_qmk_cli_is_reported_before_downloading(self):
        git_calls = self.fake_git()
        (Path(self.directory.name) / "qmk").unlink()
        self.env["PATH"] = f"{self.directory.name}:/usr/bin:/bin"
        firmware = Path(self.directory.name) / "new qmk firmware"
        result = self.make("setup", f"QMK_HOME={firmware}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("QMK CLI not found", result.stderr)
        self.assertFalse(firmware.exists())
        self.assertFalse(git_calls.exists())

    def test_failed_download_preserves_missing_checkout_and_configuration(self):
        self.fake_git()
        self.env["QMK_GIT_FAIL"] = "fetch"
        firmware = Path(self.directory.name) / "new qmk firmware"
        result = self.make("setup", f"QMK_HOME={firmware}")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(firmware.exists())
        self.assertFalse(list(firmware.parent.glob(firmware.name + ".bootstrap.*")))
        self.assertFalse(self.calls.exists())

    def test_setup_with_invalid_checkout_does_not_configure_qmk(self):
        firmware = Path(self.directory.name) / "incomplete checkout"
        firmware.mkdir()
        (firmware / "keyboards").mkdir()
        result = self.make("setup", f"QMK_HOME={firmware}")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls.exists())

    def test_qmk_failure_is_propagated(self):
        self.env["QMK_EXIT"] = "1"
        self.assertNotEqual(self.make("build", "eva01").returncode, 0)
        self.assertEqual(len(self.calls.read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
