# Sofle RGB EVA-01

QMK keymap `nicolas`, migrated from
[`themakunga/public-dotfiles`](https://github.com/themakunga/public-dotfiles/tree/d04247cea7cb029a036994025541a2ba4762d9c0/qmk/sofle/nicolas).
The keyboard sources and settings are preserved; the host check now follows the actual keymap.

## Hardware assumptions

- QMK target: `sofle/rev1`, used by standard Sofle v1, v2 and RGB PCBs.
- Controller: Pro Micro ATmega32U4, 5 V / 16 MHz, Caterina bootloader.
- USB on the left half (`MASTER_LEFT`).
- Standard matrix: 58 keys and two encoder switches.
- RGB Matrix: 72 LEDs, 36 per half, pin D3.
- OLED: SSD1306, 128 by 32 pixels, landscape orientation.

These assumptions come from the original configuration. Check the actual PCB markings and controller
before flashing. This target does not describe Sofle Keyhive, Sofle Choc or an RP2040 controller.
Compare vendor-specific pin assignments with QMK's board definition when applicable.

The firmware workflow pins QMK 0.34.5 at `b1aea2556040c28d58d611c8aef0082b5780bb6d`. See the
[upstream hardware notes](https://github.com/qmk/qmk_firmware/blob/b1aea2556040c28d58d611c8aef0082b5780bb6d/keyboards/sofle/readme.md).

## Build

From this repository's root, with an existing QMK environment:

```sh
qmk config user.overlay_dir="$(pwd)"
qmk compile -kb sofle/rev1 -km nicolas
```

The target is registered in `qmk.json`, so `qmk userspace-compile` builds it as well. The same
firmware is used on both halves. VIA is disabled; generated firmware files remain ignored by Git.

## Layers and controls

Use the US keyboard layout in the operating system. The base is QWERTY with Ctrl in the Caps Lock
position. `MO(1)` and `MO(2)` are momentary symbol and media/RGB layers. The right thumb uses tap
dance: one tap sends Space, two taps send Enter, and Shift plus that key sends Enter.

| Layer            | Left encoder counterclockwise / clockwise | Left switch    | Right encoder counterclockwise / clockwise | Right switch   |
| ---------------- | ----------------------------------------- | -------------- | ------------------------------------------ | -------------- |
| Base, QMK 0      | Shift+Up / Shift+Down                     | Mouse button 1 | Shift+Left / Shift+Right                   | Mouse button 2 |
| Symbols, QMK 1   | Alt+Up / Alt+Down                         | Mute           | Alt+Left / Alt+Right                       | Home           |
| Media/RGB, QMK 2 | Volume down / up                          | Mute           | Screen brightness down / up                | GUI+Ctrl+Q     |

On the upper layers, the custom record handler remaps the Down key to Up. The source retains its
existing modifiers, function keys, media and RGB controls. `MOUSEKEY_MOVE_DELTA` is 16; brightness
is limited to 100/255, with an initial value of 64/255 and violet hue 191/255. Existing EEPROM
settings can override the defaults.

## OLED and animation

The left OLED shows the keyboard name and layer reminders. The right OLED shows the active layer,
modifier indicators, the last three key presses and Bongo Cat. State synchronizes through QMK RPC;
the animation reacts to key presses and returns to rest after 220 ms.

The original Bongo Cat source credits
[dancarroll/qmk-bongo](https://github.com/dancarroll/qmk-bongo), James Incandenza, pixelbenny and
obosob. Copyright notices and both original license files are retained. The complete GPL text is in
[LICENSE](LICENSE); the inherited `bongo/LICENSE` file is empty. `rules.mk` compiles
`bongo/bongo_cat.c`; the additional root-level copy is preserved from the source repository.

The OLED uses the included reduced QMK ASCII font, with printable characters 32 through 126.
Hardware orientation must be checked on the actual assembly.

## Host checks

```sh
python3 keyboards/sofle/keymaps/nicolas/check_oled.py
```

Run from the repository root. Python 3 and a C compiler are required. The check verifies key and
encoder assignments and compiles the real OLED module against local stubs. It covers labels,
history, modifiers, layer state, RPC retries, display bounds and preservation of the animation's
central pixels.

These checks do not validate hardware pins, physical encoder direction, OLED orientation, actual
brightness or the final firmware size. The keyboard has not been flashed as part of this migration.
