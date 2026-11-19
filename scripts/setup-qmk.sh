#!/bin/sh
set -eu
: "${QMK_HOME:?Set QMK_HOME to the QMK Firmware checkout path}"
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
command -v qmk >/dev/null 2>&1 || {
    echo 'QMK CLI not found. Enable QMK CLI in your host configuration, then run make setup again.' >&2
    exit 1
}
if [ ! -e "$QMK_HOME" ] && [ ! -L "$QMK_HOME" ]; then
    revision=b1aea2556040c28d58d611c8aef0082b5780bb6d
    mkdir -p "$(dirname -- "$QMK_HOME")"
    temporary=$(mktemp -d "$QMK_HOME.bootstrap.XXXXXX")
    trap 'rm -rf "$temporary"' 0
    trap 'exit 1' 1 2 15
    git init "$temporary"
    git -C "$temporary" remote add origin https://github.com/qmk/qmk_firmware.git
    git -C "$temporary" fetch --depth=1 origin "$revision"
    git -C "$temporary" checkout --detach "$revision"
    git -C "$temporary" submodule update --init --recursive --depth=1
    [ ! -e "$QMK_HOME" ] && [ ! -L "$QMK_HOME" ] || {
        echo 'QMK_HOME appeared during bootstrap; refusing to replace it.' >&2
        exit 1
    }
    mv "$temporary" "$QMK_HOME"
fi
[ -f "$QMK_HOME/paths.mk" ] || {
    echo 'QMK_HOME is not a complete QMK Firmware checkout; refusing to replace it.' >&2
    exit 1
}
sh "$root/scripts/link-keyboards.sh"
