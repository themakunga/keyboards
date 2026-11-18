# Keyboards

Configuraciones y mapas de teclas personales para [QMK Firmware](https://qmk.fm/), organizados como
un [espacio de usuario externo](https://docs.qmk.fm/newbs_external_userspace).

## Teclados registrados

| Teclado           | Destino QMK        | Mapa      | Documentación                                                                         |
| ----------------- | ------------------ | --------- | ------------------------------------------------------------------------------------- |
| eva01 (Sofle RGB) | `themakunga/eva01` | `nicolas` | [Hardware, distribución y OLED](keyboards/themakunga/eva01/keymaps/nicolas/readme.md) |
| eva02 (Corne v2)  | `themakunga/eva02` | `nicolas` | [Hardware, distribución y OLED](keyboards/themakunga/eva02/keymaps/nicolas/readme.md) |

## Distribución de eva01

![Distribución física de eva01: capa base, L2 de símbolos y L3 de funciones, multimedia y RGB](docs/eva01-layout.svg)

La imagen muestra cada capa por separado, con la posición física de las 58 teclas y los dos
pulsadores de los codificadores. Las teclas atenuadas heredan la acción de la capa base. Los
círculos representan los pulsadores; los giros están detallados en la
[guía de eva01](keyboards/themakunga/eva01/keymaps/nicolas/readme.md#capas-y-controles).

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
[guía de eva02](keyboards/themakunga/eva02/keymaps/nicolas/readme.md) detalla las diferencias y los
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
python3 keyboards/themakunga/eva01/keymaps/nicolas/check_oled.py
python3 scripts/check_eva02.py
```

## Compilar los teclados

Con un entorno QMK existente, expón la definición del teclado una sola vez. Ejecuta desde la raíz de
este repositorio y ajusta `QMK_HOME` a tu copia local de QMK Firmware. Las condiciones conservan
cualquier directorio o enlace `themakunga` existente:

```sh
export QMK_HOME="$HOME/qmk_firmware"
test ! -e "$QMK_HOME/keyboards/themakunga" &&
  test ! -L "$QMK_HOME/keyboards/themakunga" &&
  ln -s "$(pwd)/keyboards/themakunga" "$QMK_HOME/keyboards/themakunga"
qmk config user.qmk_home="$QMK_HOME"
qmk config user.overlay_dir="$(pwd)"
qmk compile -kb themakunga/eva01 -km nicolas
qmk compile -kb themakunga/eva02 -km nicolas
```

`qmk userspace-compile` compila ambos destinos registrados. Esta revisión de QMK descubre las
definiciones de teclado dentro de su copia local y los mapas externos mediante el espacio de
usuario. La integración continua crea el mismo enlace antes de compilar, sin reemplazar archivos
originales de QMK.

## Build and flash with Make

Run these commands from the repository root after completing the QMK setup above. Both keyboards use
the `nicolas` keymap. GNU Make and an existing QMK development environment are required; the
Makefile does not install tools or change QMK configuration.

```sh
make help
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

## Agregar un teclado

Con un entorno de desarrollo QMK existente, ejecuta estos comandos desde este repositorio. Reemplaza
`<keyboard>` por el identificador exacto de QMK, incluida su revisión cuando corresponda.

```sh
qmk config user.overlay_dir="$(pwd)"
qmk new-keymap -kb <keyboard> -km themakunga
qmk userspace-add -kb <keyboard> -km themakunga
qmk userspace-compile
```

Guarda los mapas en `keyboards/<keyboard>/keymaps/themakunga/`. El código compartido del espacio de
usuario va en `users/themakunga/`; los mapas de distribuciones comunitarias pueden usar
`layouts/<layout>/themakunga/`.

`qmk.json` registra los destinos de compilación. El flujo de firmware omite la compilación si esa
lista está vacía. Con destinos registrados, los cambios en las rutas del firmware de `main`, o una
ejecución manual, los compilan mediante el flujo compartido de QMK y publican el firmware como
archivo para descargar de GitHub Actions.

Git ignora el firmware generado, los resultados de compilación, los archivos temporales y las
credenciales locales. Mantén las fuentes del teclado y sus archivos de configuración bajo control de
versiones.

## Promover una versión

Abre **Actions → Promote release → Run workflow**, selecciona `main` y ejecútalo como `themakunga`.
El flujo utiliza la revisión exacta de `main` seleccionada al iniciar la ejecución.

Calcula la próxima versión estable `vMAJOR.MINOR.PATCH` a partir de los commits posteriores a la
versión estable más alta accesible desde esa revisión. `BREAKING CHANGE:`, `BREAKING-CHANGE:` o `!`
incrementan la versión mayor; `feat` incrementa la menor; `fix` incrementa el parche. En las
promociones manuales, otros commits nuevos también incrementan el parche. Se incluyen los commits de
integración, por lo que cuentan los Conventional Commits de las ramas integradas. En un repositorio
sin etiquetas, un primer `feat` produce `v0.1.0`.

El flujo compila los destinos QMK registrados, descarga el firmware y crea de forma atómica la rama
`release/vMAJOR.MINOR.PATCH` y la etiqueta `vMAJOR.MINOR.PATCH` en esa misma revisión. Crea una
versión en borrador en GitHub Releases, adjunta los archivos `.hex`, `.bin` y `.uf2` generados y
publica la versión únicamente cuando termina la carga. Descarga el firmware desde la sección
**[Releases](https://github.com/themakunga/keyboards/releases)** del repositorio.

Las promociones simultáneas se ejecutan en serie. Repetir una ejecución para una revisión ya
etiquetada reutiliza su versión: permite completar un borrador pendiente y conserva intacta una
versión publicada. El flujo no publica cambios en `main` ni graba firmware en el teclado.
