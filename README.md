# Keyboards

Configuraciones y mapas de teclas personales para [QMK Firmware](https://qmk.fm/), organizados como
un [espacio de usuario externo](https://docs.qmk.fm/newbs_external_userspace).

## Teclados registrados

| Keyboard  | Version | QMK target | Keymap             | Documentation                                                                      |
| --------- | ------- | ---------- | ------------------ | ---------------------------------------------------------------------------------- |
| Sofle RGB | v2      | `sofle/v2` | `themakunga_eva01` | [Hardware, layout and OLED](keyboards/sofle/v2/keymaps/themakunga_eva01/readme.md) |
| Corne     | v2      | `corne/v2` | `themakunga_eva02` | [Hardware, layout and OLED](keyboards/corne/v2/keymaps/themakunga_eva02/readme.md) |

Hardware definitions are grouped by keyboard family and version; personal keymaps live beneath
`keymaps/`:

```text
keyboards/
├── sofle/v2/
│   ├── keyboard.json
│   └── keymaps/themakunga_eva01/
└── corne/v2/
    ├── keyboard.json
    └── keymaps/themakunga_eva02/
```

## Distribución de eva01

![Distribución física de eva01: capa base, L2 de símbolos y L3 de funciones, multimedia y RGB](docs/eva01-layout.svg)

La imagen muestra cada capa por separado, con la posición física de las 58 teclas y los dos
pulsadores de los codificadores. Las teclas atenuadas heredan la acción de la capa base. Los
círculos representan los pulsadores; los giros están detallados en la
[guía de eva01](keyboards/sofle/v2/keymaps/themakunga_eva01/readme.md#capas-y-controles).

- **Base (QMK 0):** QWERTY, Ctrl en la posición de bloqueo de mayúsculas y **Ctrl+S** en la esquina
  inferior izquierda. **Mac** envía Command y está entre **L2** y Espacio.
- **L2 · Símbolos (QMK 1):** mantener **L2** (`MO(1)`) activa los símbolos. La tecla del pulgar
  derecho pasa a Enter.
- **L3 · Funciones y multimedia (QMK 2):** mantener **L3** (`MO(2)`) activa F1–F12, controles
  multimedia, navegación y RGB.
- **Espacio / Enter:** en la base, la tecla del pulgar derecho envía Espacio con un toque y Enter
  con dos; Shift más esa tecla también envía Enter.

Configura la distribución **US** en el sistema operativo. En L2 y L3, el código convierte todas las
acciones `KC_DOWN` en Arriba; la imagen muestra ese resultado. En la base, Abajo se conserva.

Firmware builds use QMK revision `b1aea2556040c28d58d611c8aef0082b5780bb6d` (0.34.5). Verify the
physical board and controller before flashing firmware.

## Distribución de eva02

![Distribución de eva02: base QWERTY, L2 de números y símbolos y L3 de funciones y multimedia](docs/eva02-layout.svg)

Corne v2 de 42 teclas, con un perfil para Pro Micro ATmega32U4. Conserva las columnas de letras de
eva01, Ctrl en la fila de A y Ctrl+S. Los pulgares izquierdos son **Ctrl+S · L2 · Mac**; los
derechos, **Espacio / Enter · L3 · Alt**. Mac envía Command.

Mantén **L2** para números y símbolos, o **L3** para F1–F12, navegación, multimedia y RGB. Espacio /
Enter conserva el toque sencillo, doble y con Shift en todas las capas. Las cuatro flechas están en
H/J/K/L de L3; Abajo se conserva en este teclado. La
[guía de eva02](keyboards/corne/v2/keymaps/themakunga_eva02/readme.md) detalla las diferencias y los
requisitos del controlador. Comprueba el hardware real antes de utilizar el firmware; el perfil
estándar no es para RP2040.

## Comprobaciones del repositorio

Con `pre-commit` disponible, activa los controles de Git:

```sh
pre-commit install
pre-commit run --all-files
```

Los controles verifican los mapas de ambos teclados, la imagen de eva02, el módulo OLED de Sofle,
YAML, JSON, formato, Markdown, ortografía en inglés y español, claves privadas y archivos grandes.
El control de mensajes exige Conventional Commits, por ejemplo `feat: add keyboard keymap`. GitHub
Actions ejecuta las mismas comprobaciones de archivos al publicar cambios y en las solicitudes de
integración.

La comprobación de Sofle necesita Python 3 y un compilador de C (`cc`):

```sh
python3 keyboards/sofle/v2/keymaps/themakunga_eva01/check_oled.py
python3 scripts/check_eva02.py
```

## Compilar los teclados

Use an existing QMK Firmware checkout at revision `b1aea2556040c28d58d611c8aef0082b5780bb6d`. From
this repository root:

```sh
make setup
# For a checkout in a different directory:
make setup QMK_HOME="/path/to/qmk_firmware"
```

`QMK_HOME` defaults to `$HOME/qmk_firmware`. `make setup` links both keyboard revisions, saves QMK's
firmware and userspace paths, then runs `qmk userspace-doctor`. It requires an existing checkout and
QMK tools; it does not clone QMK, install dependencies or flash hardware.

```sh
make update
# With the same custom checkout used during setup:
make update QMK_HOME="/path/to/qmk_firmware"
```

`make update` refreshes the links to the local keyboard definitions, preserving QMK's existing
families and Sofle callbacks. Repeated runs are safe; conflicting files or links are rejected.
Source changes are visible immediately through the links. This command does not fetch newer QMK
revisions or update firmware on a connected keyboard.

The flat keymap names work with standard QMK commands and userspace builds:

```sh
qmk compile -kb sofle/v2 -km themakunga_eva01
qmk compile -kb corne/v2 -km themakunga_eva02
qmk userspace-compile
```

`qmk.json` registers both targets. CI uses the same link-update target and the standard QMK
userspace workflow, producing the `Firmware` artifact consumed by releases.

## Build and flash with Make

Run these commands from the repository root after completing the QMK setup above. The shortcuts
select the keyboard and its keymap from the table above. GNU Make and an existing QMK development
environment are required; `setup` configures QMK; `update` refreshes links. Neither command installs
tools.

```sh
make help
make setup
make update
make build eva01
make flash eva01
make build eva02
make flash eva02
```

`make` without arguments shows help. `make slash eva01` and `make slash eva02` are aliases for
`flash`. Choose exactly one keyboard per command; missing or unknown keyboard names fail before QMK
runs. `make build` uses `qmk compile`; `make flash` uses `qmk flash`, which compiles and then writes
firmware, so a separate build is optional.

Connect the intended keyboard half over USB and follow QMK's prompt to enter bootloader mode. Repeat
the flash command for the other half when updating both controllers. Verify the board and controller
against its hardware guide first; the standard profiles target ATmega32U4, not RP2040. To preview a
command without building or flashing, use `make -n flash eva01`. See the
[QMK flashing guide](https://docs.qmk.fm/newbs_flashing) for the underlying command.

The command tests simulate QMK and never access hardware:

```sh
python3 -m unittest discover -s tests -p test_makefile.py
```

## Add a keyboard

Place its hardware definition in `keyboards/<family>/<version>/` and its keymap in
`keymaps/themakunga_<name>/` beneath that directory. Retain upstream copyright notices and licenses.
Add the hardware revision to `scripts/link-keyboards.sh`, then add the shortcut name to `KEYBOARDS`
and its `BOARD_<name>` mapping in the Makefile. The shortcut selects `themakunga_<name>` as the
keymap. Register the hardware/keymap pair in `qmk.json`, and update the command tests and
documentation. The firmware workflow discovers registered targets automatically.

Generated firmware, temporary build output and local credentials are ignored by Git.

## Promover una versión

Abre **Actions → Promote release → Run workflow**, selecciona `main` y ejecútalo como `themakunga`.
El flujo utiliza la revisión exacta de `main` seleccionada al iniciar la ejecución.

Calcula la próxima versión estable `vMAJOR.MINOR.PATCH` a partir de los commits posteriores a la
versión estable más alta accesible desde esa revisión. `BREAKING CHANGE:`, `BREAKING-CHANGE:` o `!`
incrementan la versión mayor; `feat` incrementa la menor; `fix` incrementa el parche. En las
promociones manuales, otros commits nuevos también incrementan el parche. Se incluyen los commits de
integración, por lo que cuentan los Conventional Commits de las ramas integradas. En un repositorio
sin etiquetas, un primer `feat` produce `v0.1.0`.

El flujo compila ambos keymaps, descarga el firmware y crea de forma atómica la rama
`release/vMAJOR.MINOR.PATCH` y la etiqueta `vMAJOR.MINOR.PATCH` en esa misma revisión. Crea una
versión en borrador en GitHub Releases, adjunta los archivos `.hex`, `.bin` y `.uf2` generados y
publica la versión únicamente cuando termina la carga. Descarga el firmware desde la sección
**[Releases](https://github.com/themakunga/keyboards/releases)** del repositorio.

Las promociones simultáneas se ejecutan en serie. Repetir una ejecución para una revisión ya
etiquetada reutiliza su versión: permite completar un borrador pendiente y conserva intacta una
versión publicada. El flujo no publica cambios en `main` ni graba firmware en el teclado.
