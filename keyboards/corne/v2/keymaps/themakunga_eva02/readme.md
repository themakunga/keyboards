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

Both halves use the same 270-degree portrait layout (32 × 128), from top to bottom:

1. The Nerd Font layers glyph and current layer number (1/2/3).
2. Luna, using the original ten 32 × 24 frames by HellSingCoder.
3. A centered 2 × 2 grid: Command/Option above Control/Shift. Every icon has a border and spacing;
   held modifiers invert the icon interior.
4. The last two transmitted keyboard outputs, oldest above newest, with pixel-centered labels.
   Shortcut flags (`M`, `A`, `C`, `S`) stay attached to the corresponding output.

![Shared OLED framebuffer on both halves, layers 1/2/3](../../../../../docs/eva-oled-preview.png)

The USB master observes final QMK 6-key reports, including tap dance, Shift overrides and arrow
remaps. Releases and modifier/layer-only actions preserve both history entries. US Shift and Caps
Lock affect labels; host input methods, dead keys and text transformations remain outside the
keyboard's view. Mouse, RGB and consumer/media reports do not replace the history.

Luna sits at up to 10 WPM, walks at 11–40 and runs above 40. Control makes it sneak, Caps Lock makes
it bark (with priority over Control), and Space makes it jump. Short Space taps survive release;
held Space keeps the dog raised. Luna animates every 200 ms and both displays sleep after 60 seconds
of input/LED inactivity. A 29-byte RPC packet synchronizes active layers, modifiers, three outputs
and Luna state, with attempts limited to once per 50 ms; this layout displays only the newest two
outputs. See [asset provenance and licenses](../../../../../users/eva/ASSETS.md).

Both halves use the same firmware image. Keep USB on the left for normal use and update both halves
together; previous RPC state formats are incompatible. Verify portrait orientation and split
behavior on physical hardware.

## Compilación

Desde la raíz del repositorio, con un entorno QMK existente:

```sh
make setup
make build eva02
make flash eva02
```

Run `make setup QMK_HOME="/path/to/qmk_firmware"` for a custom checkout, or `make update` to refresh
both revision links. See the root README for setup and update behavior.

The **Build QMK firmware** and **Promote release** workflows compile the targets in `qmk.json`. The
`themakunga_eva02` target uses one shared keymap and image for both halves. Flash both halves with
that same image by running `make flash eva02` once per connected half. VIA is disabled.

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
