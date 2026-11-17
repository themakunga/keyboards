# Keyboards

Personal keyboard configurations and keymaps for [QMK Firmware](https://qmk.fm/), organized as an
[external userspace](https://docs.qmk.fm/newbs_external_userspace).

## Registered keyboards

| Keyboard          | QMK target         | Keymap    | Documentation                                                                     |
| ----------------- | ------------------ | --------- | --------------------------------------------------------------------------------- |
| eva01 (Sofle RGB) | `themakunga/eva01` | `nicolas` | [Hardware, layout and OLED](keyboards/themakunga/eva01/keymaps/nicolas/readme.md) |

The Sofle sources were migrated from `themakunga/public-dotfiles` commit
`d04247cea7cb029a036994025541a2ba4762d9c0`. The firmware workflow uses the same documented QMK
revision, `b1aea2556040c28d58d611c8aef0082b5780bb6d` (0.34.5). Verify the physical board and
controller before flashing.

## Repository checks

With `pre-commit` already available, enable the configured Git hooks:

```sh
pre-commit install
pre-commit run --all-files
```

The hooks check the Sofle keymap and OLED module, YAML, JSON, formatting, Markdown, English/Spanish
spelling, private keys and large files. The commit-message hook enforces Conventional Commits, such
as `feat: add keyboard keymap`. GitHub Actions runs the same file checks on pushes and pull
requests.

The Sofle check requires Python 3 and a C compiler (`cc`):

```sh
python3 keyboards/themakunga/eva01/keymaps/nicolas/check_oled.py
```

With an existing QMK environment, expose the custom keyboard definition once. Set `QMK_HOME` to your
existing firmware checkout; the guards preserve any existing `themakunga` directory or symlink:

```sh
export QMK_HOME="$HOME/qmk_firmware"
test ! -e "$QMK_HOME/keyboards/themakunga" &&
  test ! -L "$QMK_HOME/keyboards/themakunga" &&
  ln -s "$(pwd)/keyboards/themakunga" "$QMK_HOME/keyboards/themakunga"
qmk config user.qmk_home="$QMK_HOME"
qmk config user.overlay_dir="$(pwd)"
qmk compile -kb themakunga/eva01 -km nicolas
```

`qmk userspace-compile` builds the same registered target. This QMK revision discovers keyboard
definitions inside the firmware checkout and external keymaps through userspace. CI creates the same
link before compiling; no upstream firmware files are replaced.

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
