#!/bin/sh
# The nightly build's entry (autobuild.md): package/build-amiga.sh on the
# open9 stove, the .lha and build-info.json into NIGHTLY_OUT. The kitchen's
# 2700 s limit is too short for a full AstroMenace package beside other
# builds; the nightly gives it its own minutes.
# STOVE (a path or a name) and STOVES come from the nightly.
# MIT, Copyright (c) 2026 AmiCradle Team.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PACKAGE=${NIGHTLY_PACKAGE:-"$HERE/package/build-amiga.sh"}
WANT=os32-gcc16-open9
if [ -n "${STOVES:-}" ] && [ -d "$STOVES/$WANT" ]; then
    STOVE="$STOVES/$WANT"
elif [ -n "${STOVE:-}" ] && [ ! -d "$STOVE" ] && [ -n "${STOVES:-}" ]; then
    STOVE="$STOVES/$STOVE"
fi
[ -n "${STOVE:-}" ] && [ -d "$STOVE" ] || { echo "astromenace-nightly: no stove (STOVE=${STOVE:-})"; exit 1; }
OUT=${NIGHTLY_OUT:-"$HERE/out"}
STOVE="$STOVE" OUT="$OUT" sh "$PACKAGE"
ls "$OUT"/*.lha >/dev/null 2>&1 || { echo "astromenace-nightly: no .lha in $OUT"; exit 1; }
echo "astromenace-nightly: built"
