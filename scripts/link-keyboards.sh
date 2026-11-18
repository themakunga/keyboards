#!/bin/sh
set -eu
: "${QMK_HOME:?Set QMK_HOME to an existing QMK Firmware checkout}"
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
[ -d "$QMK_HOME/keyboards" ] || { echo 'QMK_HOME has no keyboards directory' >&2; exit 1; }
for family in sofle corne; do
    source="$root/keyboards/$family/v2"
    target="$QMK_HOME/keyboards/$family/v2"
    mkdir -p "$QMK_HOME/keyboards/$family"
    if [ -e "$target" ] || [ -L "$target" ]; then
        [ "$target" -ef "$source" ] || { echo "Refusing to replace $target" >&2; exit 1; }
    else
        ln -s "$source" "$target"
    fi
done
