# Keyboards

Personal keyboard configurations and keymaps for [QMK Firmware](https://qmk.fm/), organized as an
[external userspace](https://docs.qmk.fm/newbs_external_userspace).

No keyboard or build target is configured yet. Add the exact board and revision before building or
flashing firmware.

## Repository checks

With `pre-commit` already available, enable the configured Git hooks:

```sh
pre-commit install
pre-commit run --all-files
```

The hooks check YAML, JSON, formatting, Markdown, English/Spanish spelling, private keys and large
files. The commit-message hook enforces Conventional Commits, such as `feat: add keyboard keymap`.
GitHub Actions runs the same file checks on pushes and pull requests.

## Add a keyboard

With an existing QMK development environment, run these commands from this checkout. Replace
`<keyboard>` with the exact QMK keyboard identifier, including its revision when required.

```sh
qmk config user.overlay_dir="$(pwd)"
qmk new-keymap -kb <keyboard> -km themakunga
qmk userspace-add -kb <keyboard> -km themakunga
qmk userspace-compile
```

Store board keymaps under `keyboards/<keyboard>/keymaps/themakunga/`. Shared userspace code belongs
in `users/themakunga/`, and community-layout keymaps can use `layouts/<layout>/themakunga/`.

`qmk.json` records the build targets. The firmware workflow skips compilation while that list is
empty. Once targets exist, pushes to the firmware paths on `main`, or a manual workflow run, build
them through QMK's reusable workflow and upload the firmware as a GitHub Actions artifact.

Generated firmware, build output, caches and local credentials are ignored by Git. Keep the keyboard
sources and configuration files tracked.
