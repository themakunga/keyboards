# eva01 — Sofle RGB

The `themakunga_eva01` QMK keymap targets `sofle/v2`. Hardware, key assignments and OLED behavior
are documented below.

## Hardware previsto

- Base: `sofle/rev1`, utilizada por las placas estándar Sofle v1, v2 y RGB.
- Controlador: Pro Micro ATmega32U4, 5 V / 16 MHz, gestor de arranque Caterina.
- USB en la mitad izquierda (`MASTER_LEFT`).
- Matriz estándar: 58 teclas y dos pulsadores de codificador.
- Matriz RGB: 72 LED, 36 por mitad, pin D3.
- OLED: SSD1306, 128 × 32 physical pixels; both halves portrait (32 × 128).

Estos datos proceden de la configuración original. Comprueba las marcas de la placa y el controlador
antes de grabar el firmware. Este destino no describe Sofle Keyhive, Sofle Choc ni un controlador
RP2040. Compara los pines específicos del fabricante con la definición de QMK cuando corresponda.

El flujo de compilación fija QMK 0.34.5 en `b1aea2556040c28d58d611c8aef0082b5780bb6d`. Consulta las
[notas originales del hardware](https://github.com/qmk/qmk_firmware/blob/b1aea2556040c28d58d611c8aef0082b5780bb6d/keyboards/sofle/readme.md).

## Compilación

Desde la raíz de este repositorio, con un entorno QMK existente:

```sh
make setup
qmk compile -kb sofle/v2 -km themakunga_eva01
```

Run `make setup QMK_HOME="/path/to/qmk_firmware"` for a custom checkout, or `make update` to refresh
both revision links. See the root README for setup and update behavior.

This keymap is registered in `qmk.json` for standard QMK userspace builds and releases. Ambas
mitades utilizan el mismo firmware. VIA está desactivado y Git ignora los archivos de firmware
generados.

## Capas y controles

![Distribución de eva01 con sus tres capas y pulsadores de codificador](../../../../../docs/eva01-layout.svg)

La imagen sigue las posiciones de `keyboard.json` y las acciones de `keymap.c`. Las teclas atenuadas
heredan la acción base. Cada capa se muestra activada por separado; si mantienes L2 y L3 a la vez,
QMK resuelve primero L3, después L2 y finalmente la base. Los círculos representan los pulsadores de
los codificadores.

Utiliza la distribución **US** en el sistema operativo. La base es QWERTY con Ctrl en la posición de
bloqueo de mayúsculas. La esquina inferior izquierda envía **Ctrl+S**; Ctrl sigue disponible en la
fila de A. En los pulgares izquierdos, **L2** está entre Alt y **Mac**; Mac envía Command
(`KC_LGUI`).

Mantén **L2** (`MO(1)`, capa QMK 1) para símbolos y **L3** (`MO(2)`, capa QMK 2) para funciones,
multimedia y RGB. Al soltar la tecla vuelves a la capa anterior. El pulgar derecho usa una secuencia
de toques: uno envía Espacio, dos envían Enter y Shift más esa tecla envía Enter. Both inner Space
thumb keys send Enter directly on L2 and L3, including when both layers are held.

| Capa                  | Giro izquierdo antihorario / horario | Pulsador izquierdo | Giro derecho antihorario / horario | Pulsador derecho |
| --------------------- | ------------------------------------ | ------------------ | ---------------------------------- | ---------------- |
| Base, QMK 0           | Shift+Arriba / Shift+Abajo           | Botón de ratón 1   | Shift+Izquierda / Shift+Derecha    | Botón de ratón 2 |
| Símbolos, QMK 1       | Alt+Arriba / Alt+Abajo               | Silenciar          | Alt+Izquierda / Alt+Derecha        | Inicio           |
| Multimedia/RGB, QMK 2 | Bajar / subir volumen                | Silenciar          | Bajar / subir brillo de pantalla   | GUI+Ctrl+Q       |

En las capas superiores, la función personalizada convierte `KC_DOWN` en `KC_UP`, incluidas las
teclas heredadas. Por eso la imagen muestra Arriba en esas posiciones, incluso en la zona de
navegación de L3. La base mantiene Abajo. La combinación GUI+Ctrl+Q bloquea la sesión en macOS.

El mapa conserva sus modificadores, teclas de función y controles multimedia y RGB.
`MOUSEKEY_MOVE_DELTA` es 16; el brillo RGB se limita a 100/255, con valor inicial 64/255 y tono
violeta 191/255. La configuración guardada en EEPROM puede reemplazar los valores iniciales.

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

## Comprobaciones locales

Ejecuta desde la raíz del repositorio:

```sh
python3 scripts/check_oled.py
```

Python 3 and a C compiler are required. The check verifies key and encoder assignments and compiles
the actual OLED module with local substitutes. It covers final USB-report forwarding, characters and
shortcuts, all modifier combinations, layer changes, RPC retries, portrait pixel bounds and complete
monitor frames.

These checks do not validate physical pins, encoder direction, OLED orientation, actual brightness
or final firmware size. Hardware validation requires building and testing the firmware on the board.
