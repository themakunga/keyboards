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

## Central monitor

The active 32 × 24 monochrome art is a locally drawn monitor, with no cat or glasses. Two screen
states react to keyboard output and an empty screen is used at rest. The existing
`bongo/bongo_cat.c` renderer path is retained to keep the shared build/API unchanged.

The earlier Bongo Cat reference was
[zmk-nice-oled at 84a9880](https://github.com/mctechnology17/zmk-nice-oled/tree/84a98807fd97f8930859d1eb633966aaec17b72a).
Its preserved notice is in [LICENSE.nice-oled](bongo/LICENSE.nice-oled). Existing GPL notices and
the legacy source copy remain preserved; that reference artwork is no longer rendered.
