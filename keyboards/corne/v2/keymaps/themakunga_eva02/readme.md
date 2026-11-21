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

Both halves use 270-degree rotation (32 × 128 portrait) and share `users/eva/`, with different
content compiled into each side:

- **Left / USB master:** the Nerd Font layers glyph (1/2/3), the 2 × 2 Command/Option/Control/Shift
  grid and the last transmitted character or shortcut. Held modifiers invert their icons. Shortcut
  flags use `M`, `A`, `C` and `S`; releasing keys or pressing only a layer/modifier preserves the
  last output.
- **Right / peripheral:**
  [Luna by HellSingCoder](https://github.com/HellSingCoder/qmk_firmware/tree/33d7fa1180d232dcdb024c68a8f4629dced32afb/keyboards/sofle/keymaps/helltm).
  The dog sits at up to 10 WPM, walks at 11–40 and runs above 40. Control makes it sneak, Caps Lock
  makes it bark (taking priority over Control), and Space makes it jump. Short Space taps remain
  visible even after release. The original ten 32 × 24 bitmap frames are preserved.

![Actual OLED framebuffer previews: left status and right Luna](../../../../../docs/eva-oled-preview.png)

The left display observes final QMK 6-key USB reports, including tap dance, Shift overrides and
Sofle's arrow remap. US Shift punctuation and Caps Lock affect the character shown. Host text
transformations, dead keys and input methods cannot be inferred from USB reports. Mouse, RGB and
consumer/media reports do not replace the last keyboard output.

A compact RPC packet sends only Luna's WPM, modifiers, Caps Lock, Space/jump and wake state from
left to right, with attempts limited to once per 50 ms. Luna alternates frames every 200 ms and
sleeps after 60 seconds of input/LED inactivity. Status glyphs and output formatting are absent from
the right firmware; Luna's bitmaps are absent from the left. See
[asset provenance and licenses](../../../../../users/eva/ASSETS.md).

The side-specific firmware fixes the left half as USB master and the right as peripheral so LTO can
remove unused role paths. Connect USB to the left during normal use. Match each firmware filename to
its physical side; do not swap them. Verify both OLED orientations and split behavior on hardware.

## Compilación

Desde la raíz del repositorio, con un entorno QMK existente:

```sh
make setup
make build eva02
make flash-left eva02
make flash-right eva02
```

Run `make setup QMK_HOME="/path/to/qmk_firmware"` for a custom checkout, or `make update` to refresh
both revision links. See the root README for setup and update behavior.

The **Build QMK firmware** and **Promote release** workflows compile the targets in `qmk.json`. The
`themakunga_eva02_left` and `themakunga_eva02_right` targets include this shared keymap and
configuration. Flash each matching side separately. VIA is disabled.

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
