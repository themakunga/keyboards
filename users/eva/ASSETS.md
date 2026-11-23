# OLED assets

The portrait composition follows [zmk-nice-oled](https://github.com/mctechnology17/zmk-nice-oled),
adapted to the existing QMK renderer and 32 × 128 SSD1306 displays.

## Nerd Font glyphs

`icons.h` contains rasterized glyphs from Hack Nerd Font Regular 3.4.0 (Hack 3.003). The firmware
stores only five 14 × 14 monochrome cells; it does not decode UTF-8 or load a TTF.

| Purpose    | Glyph | Codepoint | Nerd Fonts name           |
| ---------- | ----- | --------- | ------------------------- |
| Command    | 󰘳     | U+F0633   | md-apple_keyboard_command |
| Option/Alt | 󰘵     | U+F0635   | md-apple_keyboard_option  |
| Control    | 󰘴     | U+F0634   | md-apple_keyboard_control |
| Shift      | 󰘶     | U+F0636   | md-apple_keyboard_shift   |
| Layers     |      | U+EBD2    | cod-layers                |

Glyph identities follow the
[Nerd Fonts mapping](https://github.com/ryanoasis/nerd-fonts/blob/v3.4.0/glyphnames.json). The four
Apple keyboard glyphs are from Pictogrammers Material Design Icons, licensed under
[Apache 2.0](LICENSE.icons-apache); see the
[original license](https://github.com/ryanoasis/nerd-fonts/blob/v3.4.0/src/glyphs/materialdesign/LICENSE).
The layers glyph is from Microsoft Codicons, copyright Microsoft Corporation, licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with
[source and license](https://github.com/microsoft/vscode-codicons). Changes: rasterization, size
reduction and conversion to monochrome.

For each glyph, ImageMagick renders the installed font at 256 points, trims the result, fits it
inside 12 × 12 pixels, centers it in a 14 × 14 cell and thresholds it at 45 percent. Each C row
stores the leftmost pixel in bit 13. No font installation is required to build the firmware.

Modifier cells have rounded outlines with a two-pixel corner inset. EVA01 uses the original 12 × 12
source symbols inside 16 × 16 cells in a portrait 2 × 2 grid, with one blank pixel between rows. A
one-pixel inner margin keeps each symbol separate from its border in both modifier states. EVA02
retains 14 × 14 cells and sampled 8 × 8 symbols, with four blank pixels between columns and six
between rows. Active fills stay inside the rounded outlines. The original source bitmaps are
unchanged. EVA01 replaces the static layers glyph with four overlapping 29-pixel-wide procedural
planes, offset vertically by four pixels. The compact stack fills only the selected layer, leaving
Base outlined when another layer is selected.

EVA01's left status block is shifted down by 22 pixels and its right Luna/history block up by eight.
The resting compositions have balanced 24/25-pixel vertical margins and horizontal margins that
differ by at most one pixel. The original artwork and spacing within each composition are unchanged.

## Luna keyboard pet

`luna.c` preserves the ten original 32 × 24 monochrome bitmap frames (two each for sit, walk, run,
bark and sneak) from
[HellSingCoder's Sofle keymap](https://github.com/HellSingCoder/qmk_firmware/blob/33d7fa1180d232dcdb024c68a8f4629dced32afb/keyboards/sofle/keymaps/helltm/keymap.c).
Copyright 2021 HellSingCoder, GPL-2.0-or-later; the source notice is preserved and the full license
is in [LICENSE](LICENSE).

Adaptations: a standalone C renderer, portrait centering, a cleared jump region, explicit timeout,
and complete display state sent from the USB master over QMK RPC. EVA01 uses a portrait left status
display and portrait right Luna/three-output history. EVA02 repeats its full portrait layout with
two outputs on both sides. No Luna artwork was rescaled or redrawn. The former monitor animation is
no longer built. Historical Bongo Cat license notices are retained.
