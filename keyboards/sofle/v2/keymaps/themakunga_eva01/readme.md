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
make build eva01
make flash eva01
```

Run `make setup QMK_HOME="/path/to/qmk_firmware"` for a custom checkout, or `make update` to refresh
both revision links. See the root README for setup and update behavior.

`themakunga_eva01` is the single target registered in `qmk.json` for QMK userspace builds and
releases. Run `make flash eva01` once per connected half to flash the same image to both. VIA is
disabled; generated firmware is ignored.

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
of input/LED inactivity. A 21-byte RPC packet synchronizes layer, modifiers, both outputs and Luna
state, with attempts limited to once per 50 ms. See
[asset provenance and licenses](../../../../../users/eva/ASSETS.md).

Both halves use the same firmware image. Keep USB on the left for normal use and update both halves
together; the old side-specific RPC state is incompatible. Verify portrait orientation and split
behavior on physical hardware.

## Comprobaciones locales

Ejecuta desde la raíz del repositorio:

```sh
python3 scripts/check_oled.py
```

Python 3 and a C compiler are required. The check verifies key and encoder assignments and compiles
the actual OLED module with local substitutes. It covers final USB-report forwarding, characters and
shortcuts, all modifier combinations, layer changes, RPC retries, portrait pixel bounds and all Luna
states. It compiles both master/peripheral render paths and checks sleep and short/held Space jumps.

These checks do not validate physical pins, encoder direction, OLED orientation, actual brightness
or final firmware size. Hardware validation requires building and testing the firmware on the board.
