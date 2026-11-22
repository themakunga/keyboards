import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KeyboardSetupTests(unittest.TestCase):
    def test_targets_follow_family_version_and_keymap(self):
        userspace = json.loads((ROOT / "qmk.json").read_text())
        targets = userspace["build_targets"]
        self.assertEqual(targets, [[board, f"themakunga_{name}"]
                                   for board, name in [("sofle/v2", "eva01"), ("corne/v2", "eva02")]])
        for keyboard, keymap in targets:
            self.assertTrue((ROOT / "keyboards" / keyboard / "keyboard.json").is_file())
            self.assertTrue((ROOT / "keyboards" / keyboard / "keymaps" / keymap / "keymap.c").is_file())

    def test_setup_preserves_parent_and_is_repeatable(self):
        with tempfile.TemporaryDirectory(prefix="qmk checkout ") as directory:
            firmware = Path(directory)
            (firmware / "keyboards/sofle").mkdir(parents=True)
            callbacks = firmware / "keyboards/sofle/sofle.c"
            callbacks.write_text("upstream callbacks")
            env = {**os.environ, "QMK_HOME": directory}
            for _ in range(2):
                subprocess.run(["sh", "scripts/link-keyboards.sh"], cwd=ROOT, env=env, check=True, capture_output=True)
            self.assertEqual(callbacks.read_text(), "upstream callbacks")
            for family in ["sofle", "corne"]:
                self.assertEqual((firmware / "keyboards" / family / "v2").resolve(), ROOT / "keyboards" / family / "v2")

    def test_setup_rejects_existing_definitions_and_broken_links(self):
        for broken_link in [False, True]:
            with self.subTest(broken_link=broken_link), tempfile.TemporaryDirectory() as directory:
                firmware = Path(directory)
                target = firmware / "keyboards/sofle/v2"
                target.parent.mkdir(parents=True)
                if broken_link:
                    target.symlink_to("missing")
                else:
                    target.mkdir()
                    (target / "marker").write_text("preserve")
                result = subprocess.run(["sh", "scripts/link-keyboards.sh"], cwd=ROOT,
                                        env={**os.environ, "QMK_HOME": directory}, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                if broken_link:
                    self.assertEqual(os.readlink(target), "missing")
                else:
                    self.assertEqual((target / "marker").read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
