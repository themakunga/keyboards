"""Release versioning against Conventional Commits and real Git histories."""

import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/release_version.py"
sys.path.insert(0, str(SCRIPT.parent))
from release_version import next_version


class VersionTests(unittest.TestCase):
    def test_conventional_commit_precedence(self):
        cases = [
            (["fix: correct an encoder"], (1, 2, 4)),
            (["chore: update CI"], (1, 2, 4)),
            (["docs: explain flashing"], (1, 2, 4)),
            (["fix: correct a key", "feat(oled): add a display"], (1, 3, 0)),
            (["FEAT: add a key"], (1, 3, 0)),
            (["feat!: replace the layout"], (2, 0, 0)),
            (["fix(matrix)!: replace the pin map"], (2, 0, 0)),
            (["refactor: change layout\n\nBREAKING CHANGE: incompatible pins"], (2, 0, 0)),
            (["fix: change layout\n\nBREAKING-CHANGE: incompatible pins"], (2, 0, 0)),
            (["fix: label says BREAKING CHANGE: but is not a footer"], (1, 2, 4)),
            (["docs: example\n\nfeat: this body is not a feature header"], (1, 2, 4)),
            ([], (1, 2, 3)),
        ]
        for messages, expected in cases:
            with self.subTest(messages=messages):
                self.assertEqual(next_version((1, 2, 3), messages), expected)


class GitRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="keyboard release ")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        # Git hooks export repository paths; fixtures must not inherit them.
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Release tests")
        self.git("config", "user.email", "release@example.invalid")

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.repo, env=self.env, text=True, stderr=subprocess.PIPE
        ).strip()

    def commit(self, message):
        self.git("commit", "--allow-empty", "-qm", message)

    def version(self):
        return subprocess.check_output(
            [sys.executable, str(SCRIPT)], cwd=self.repo, env=self.env, text=True
        ).strip()


class HookIsolationTests(GitRepositoryTest):
    def test_fixture_ignores_outer_repository_environment(self):
        self.commit("chore: outer repository")
        config = (self.repo / ".git/config").read_bytes()
        head = self.git("rev-parse", "HEAD")
        nested = GitRepositoryTest()
        self.addCleanup(nested.doCleanups)
        with patch.dict(os.environ, {
            "GIT_DIR": str(self.repo / ".git"),
            "GIT_COMMON_DIR": str(self.repo / ".git"),
            "GIT_WORK_TREE": str(self.repo),
            "GIT_INDEX_FILE": str(self.repo / ".git/index"),
        }):
            nested.setUp()
        nested.commit("feat: isolated keyboard")
        nested.git("init", "-q", "--bare", str(nested.repo / "origin.git"))
        self.assertEqual((self.repo / ".git/config").read_bytes(), config)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)


class GitHistoryTests(GitRepositoryTest):
    def test_initial_feature_release(self):
        self.commit("chore: initialize repository")
        self.commit("feat: add keyboard")
        self.assertEqual(self.version(), "v0.1.0")

    def test_only_commits_since_previous_annotated_tag_count(self):
        self.commit("feat!: initial hardware")
        self.git("tag", "-a", "v1.2.3", "-m", "Previous release")
        self.commit("fix: correct encoder")
        self.assertEqual(self.version(), "v1.2.4")

    def test_existing_tag_on_same_commit_is_reused_for_recovery(self):
        self.commit("feat: add keyboard")
        self.git("tag", "v0.1.0")
        self.assertEqual(self.version(), "v0.1.0")

    def test_tags_outside_main_and_prereleases_are_ignored(self):
        self.commit("feat: add keyboard")
        self.git("tag", "v0.1.0")
        self.git("switch", "-qc", "other-branch")
        self.commit("feat!: unrelated hardware")
        self.git("tag", "v99.0.0")
        self.git("switch", "-q", "main")
        self.commit("fix: correct key")
        self.git("tag", "v1.0.0-rc.1")
        self.git("tag", "v01.0.0")
        self.assertEqual(self.version(), "v0.1.1")

    def test_latest_version_is_numeric(self):
        self.commit("feat: add keyboard")
        self.git("tag", "v0.9.0")
        self.commit("feat: add display")
        self.git("tag", "v0.10.0")
        self.commit("fix: correct display")
        self.assertEqual(self.version(), "v0.10.1")

    def test_feature_behind_merge_is_included(self):
        self.commit("chore: initialize repository")
        self.git("tag", "v0.1.0")
        self.git("switch", "-qc", "feature")
        self.commit("feat: add display")
        self.git("switch", "-q", "main")
        self.git("merge", "--no-ff", "feature", "-m", "Merge pull request")
        self.assertEqual(self.version(), "v0.2.0")


class PublicationTests(GitRepositoryTest):
    def setUp(self):
        super().setUp()
        self.commit("feat: add keyboard")
        self.sha = self.git("rev-parse", "HEAD")
        self.origin = self.repo / "origin.git"
        self.git("init", "-q", "--bare", str(self.origin))
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "-u", "origin", "main")
        (self.repo / "firmware").mkdir()
        (self.repo / "firmware/eva01.hex").write_text("firmware fixture")
        tools = self.repo / "bin"
        tools.mkdir()
        gh = tools / "gh"
        gh.write_text("#!/usr/bin/env python3\n" + textwrap.dedent('''
            import json, os, pathlib, sys
            path = pathlib.Path("release-state.json")
            state = json.loads(path.read_text()) if path.exists() else {"uploads": 0}
            command = sys.argv[1:3]
            if command == ["auth", "setup-git"]:
                sys.exit(0)
            if command == ["release", "view"]:
                if "draft" not in state:
                    sys.exit(1)
                print(str(state["draft"]).lower())
                sys.exit(0)
            if command == ["release", "create"]:
                state["draft"] = True
            elif command == ["release", "upload"]:
                if os.environ.get("FAIL_UPLOAD"):
                    sys.exit(1)
                assert state["draft"]
                assert "firmware/eva01.hex" in sys.argv
                state["uploads"] += 1
            elif command == ["release", "edit"]:
                assert state["uploads"] > 0
                state["draft"] = False
            else:
                sys.exit("Unexpected GitHub operation")
            path.write_text(json.dumps(state))
        '''))
        gh.chmod(0o755)
        self.env.update(PATH=str(tools) + os.pathsep + os.environ["PATH"],
                        GITHUB_SHA=self.sha, TAG="v0.1.0")
        workflow = (SCRIPT.parents[1] / ".github/workflows/promote-release.yaml").read_text()
        step = workflow.split("      - name: Publish firmware release\n", 1)[1]
        self.publish = textwrap.dedent(step.split("        run: |\n", 1)[1])

    def run_publish(self, **env):
        return subprocess.run(
            ["bash", "-euo", "pipefail", "-c", self.publish], cwd=self.repo,
            env=dict(self.env, **env), text=True, capture_output=True
        )

    def test_upload_failure_can_resume_without_replacing_published_assets(self):
        self.assertNotEqual(self.run_publish(FAIL_UPLOAD="1").returncode, 0)
        self.assertTrue(json.loads((self.repo / "release-state.json").read_text())["draft"])
        self.git("fetch", "-q", "--tags", "origin")
        self.assertEqual(self.version(), "v0.1.0")
        self.assertEqual(self.run_publish().returncode, 0)
        state = json.loads((self.repo / "release-state.json").read_text())
        self.assertEqual(state, {"draft": False, "uploads": 1})
        self.assertEqual(self.run_publish().returncode, 0)
        self.assertEqual(json.loads((self.repo / "release-state.json").read_text()), state)
        for ref in ("refs/heads/main", "refs/heads/release/v0.1.0", "refs/tags/v0.1.0"):
            self.assertEqual(self.git("--git-dir", str(self.origin), "rev-parse", ref), self.sha)

    def test_existing_release_branch_is_not_fast_forwarded(self):
        self.git("push", "-q", "origin", "HEAD:refs/heads/release/v0.1.0")
        self.commit("fix: correct key")
        self.env["GITHUB_SHA"] = self.git("rev-parse", "HEAD")
        self.git("push", "-q", "origin", "main")
        self.assertNotEqual(self.run_publish().returncode, 0)
        self.assertEqual(self.git("--git-dir", str(self.origin), "rev-parse",
                                  "refs/heads/release/v0.1.0"), self.sha)
        self.assertFalse(self.git("--git-dir", str(self.origin), "tag", "--list"))
        self.assertFalse((self.repo / "release-state.json").exists())

    def test_empty_build_does_not_create_release_refs(self):
        (self.repo / "firmware/eva01.hex").unlink()
        self.assertNotEqual(self.run_publish().returncode, 0)
        self.assertFalse(self.git("--git-dir", str(self.origin), "tag", "--list"))
        self.assertEqual(self.git("--git-dir", str(self.origin), "branch", "--list"), "main")
        self.assertFalse((self.repo / "release-state.json").exists())


if __name__ == "__main__":
    unittest.main()
