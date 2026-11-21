# eva02 — Corne v2

The `themakunga_eva02` QMK keymap targets `corne/v2`, adapting EVA01 to the 42-key Corne v2. It
provides QWERTY, dedicated modifiers, three layers and a left-thumb Space/Enter tap dance.

## Hardware previsto

- Corne v2 estándar, 42 teclas, distribución `LAYOUT_split_3x6_3`.
- Pro Micro ATmega32U4, 5 V / 16 MHz, gestor de arranque Caterina.
- USB en la mitad izquierda (`MASTER_LEFT`), comunicación serie por D2.
- Matriz: filas D4, C6, D7 y E6; columnas F4, F5, F6, F7, B1 y B3.
- Matriz RGB opcional: 54 LED, 27 por mitad, datos por D3.
- Optional SSD1306 OLED: 128 × 32 physical pixels; both halves portrait (32 × 128).
- Sin codificadores ni pulsadores adicionales.

Este perfil declara el controlador Pro Micro estándar; comprueba el controlador real antes de
grabarlo. Un Corne con RP2040 necesita una conversión de controlador y su firmware correspondiente.
No utilices este archivo `.hex` directamente en un RP2040. Tampoco corresponde a Corne v4 ni a la
variante de 36 teclas.

QMK asigna Corne v1–v3 al destino original `crkbd/rev1`. `keyboard.json` combina sus metadatos
compartidos y la definición rev1 de QMK 0.34.5, revisión `b1aea2556040c28d58d611c8aef0082b5780bb6d`;
solo cambia el nombre del teclado y su responsable. Consulta la
[documentación original de Corne](https://github.com/qmk/qmk_firmware/blob/b1aea2556040c28d58d611c8aef0082b5780bb6d/keyboards/crkbd/readme.md).
Los metadatos conservan la autoría de foostan; la licencia GPL se incluye en
[LICENSE](../../LICENSE).

## Distribución y capas

![Distribución de eva02: base QWERTY, L2 de números y símbolos y L3 de funciones, navegación, multimedia y RGB](../../../../../docs/eva02-layout.svg)

Configura **US** en el sistema operativo. Las teclas atenuadas heredan la base y cada capa se
muestra activada por separado. Si mantienes L2 y L3 simultáneamente, QMK resuelve L3, luego L2 y
finalmente la base.

- **Base (QMK 0):** letras y puntuación en las mismas columnas que eva01. Esc queda arriba a la
  izquierda; Ctrl, en la fila de A; Shift, en ambos extremos inferiores.
- **Left thumbs, left to right:** Command, L2 (`MO(1)`) and Space/Enter. The inner key sends Space
  on one tap, Enter on a double tap, and Enter with Shift on the base. It sends Enter directly on
  both L2 and L3.
- **Right thumbs, left to right:** Space, L3 (`MO(2)`) and Alt. The inner key sends only Space on
  the base, with no tap dance. It sends Enter directly on both L2 and L3. Both inner thumb keys also
  send Enter when L2 and L3 are held together.
- **L2 · Números y símbolos (QMK 1):** mantener L2 coloca 1–0 sobre las letras superiores; con Shift
  produce sus símbolos US. Tab queda en la esquina superior izquierda y Suprimir a la derecha. Las
  filas restantes incluyen barras, comillas, llaves, corchetes y operadores.
- **L3 · Funciones y multimedia (QMK 2):** mantener L3 activa F1–F12, las cuatro flechas en H/J/K/L,
  volumen, reproducción, brillo, efectos y tono RGB. La combinación Mac+Ctrl+Q bloquea la sesión en
  macOS.

eva02 conserva **Abajo** en L3: las cuatro direcciones siguen disponibles aunque no haya flechas
dedicadas en la base. Los números y las funciones pasan a capas porque el Corne no tiene la fila
numérica del Sofle. No se utilizan modificadores al mantener teclas de letras ni retardos de
pulsación para acceder a las capas.

El brillo RGB máximo es 100/255, con valor inicial 64/255 y tono violeta 191/255. Los valores
guardados en EEPROM pueden reemplazar estos ajustes.

## OLED and animation

Both displays use 270-degree rotation and the same synchronized 32 × 128 portrait composition,
shared by Sofle and Corne through `users/eva/`. The design follows
[zmk-nice-oled](https://github.com/mctechnology17/zmk-nice-oled):

- The Nerd Font layers glyph `` at the top: **1** for base, **2** for L2 and **3** for L3.
- A 2 × 2 modifier grid: Command `󰘳` and Option/Alt `󰘵` above Control `󰘴` and Shift `󰘶`. Held
  modifiers invert their 14 × 14 cells; either left or right modifier key activates its icon.
- A monitor-only animation in the middle, without a cat or glasses. It reacts to keyboard output and
  returns to idle after 220 ms.
- Only the last transmitted character or shortcut below the monitor. Shortcut modifiers appear above
  its key as compact `M` (Command), `A` (Alt), `C` (Control) and `S` (Shift) flags. For example,
  `MC` above `Q` means Command+Control+Q. Releasing keys or pressing a layer/modifier alone
  preserves the last output.

![OLED framebuffer previews: base, L2 and L3](../../../../../docs/eva-oled-preview.png)

The display observes final QMK 6-key USB reports, so tap dance, Shift overrides and the Sofle arrow
remap show the resulting output. US Shift punctuation and Caps Lock are reflected in the displayed
character. Host text transformations, dead keys and input methods cannot be inferred from USB key
reports. Mouse, RGB and consumer/media reports do not replace the last keyboard output.

QMK RPC synchronizes that single transient output, layer, held modifiers and animation between
halves; no key history is retained. Text uses the included QMK ASCII subset. Nerd Font glyphs are
pre-rendered bitmaps, so firmware builds do not require a font installation or UTF-8 support. See
[asset provenance and licenses](../../../../../users/eva/ASSETS.md). Existing source notices and the
legacy Bongo Cat copy remain preserved. Verify both OLED orientations on the real keyboard.

## Compilación

Desde la raíz del repositorio, con un entorno QMK existente:

```sh
make setup
qmk compile -kb corne/v2 -km themakunga_eva02
```

Run `make setup QMK_HOME="/path/to/qmk_firmware"` for a custom checkout, or `make update` to refresh
both revision links. See the root README for setup and update behavior.

The **Build QMK firmware** and **Promote release** workflows compile the targets in `qmk.json`. Both
halves use the same firmware. VIA is disabled.

## Comprobaciones

```sh
python3 scripts/check_eva02.py
python3 scripts/check_oled.py
pre-commit run --all-files
```

Ejecuta desde la raíz. La comprobación local valida los pines declarados, las 42 posiciones por
capa, el acceso a las capas, las teclas principales y la correspondencia de la imagen con el mapa.
La compilación QMK comprueba el firmware completo. Ninguna de estas comprobaciones verifica el
controlador instalado, el cableado, la orientación física del OLED ni el brillo real de los LED.
