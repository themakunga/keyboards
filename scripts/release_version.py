"""Choose a stable release tag from commits reachable from the checked-out main commit."""

import re
import subprocess


def next_version(current, messages):
    if not messages:
        return current
    major, minor, patch = current
    feature = False
    for message in messages:
        header = message.splitlines()[0]
        commit = re.fullmatch(r"([a-z][a-z0-9-]*)(?:\([^()]+\))?(!)?: .+", header, re.I)
        breaking = re.search(r"^BREAKING(?: CHANGE|-CHANGE):[ \t]+\S", message, re.M)
        if breaking or (commit and commit[2]):
            return major + 1, 0, 0
        if commit and commit[1].lower() == "feat":
            feature = True
    return (major, minor + 1, 0) if feature else (major, minor, patch + 1)


def release_tag():
    tags = subprocess.check_output(
        ["git", "tag", "--merged", "HEAD", "--list", "v*"], text=True
    ).splitlines()
    versions = {}
    for tag in tags:
        match = re.fullmatch(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", tag)
        if match:
            versions[tuple(map(int, match.groups()))] = tag
    current = max(versions, default=(0, 0, 0))
    revision = f"{versions[current]}..HEAD" if versions else "HEAD"
    history = subprocess.check_output(
        ["git", "log", revision, "--format=%B%x00"], text=True
    )
    messages = [message.strip() for message in history.split("\0") if message.strip()]
    return "v" + ".".join(map(str, next_version(current, messages)))


if __name__ == "__main__":
    print(release_tag())
