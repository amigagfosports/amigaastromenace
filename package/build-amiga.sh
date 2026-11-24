#!/bin/sh
# The release archive, for Cradle's stove_build (target package, STOVE= and
# OUT= set): the game built as build-amigaos3-runtime-fixed.sh builds it
# (the launcher, AstroMenace.bin, gamedata.vfs, the licences and the
# README), the GlowIcons from icons/ put in the drawer, then the drawer, its
# icon and the Installer script beside it packed as
# AstroMenace-VERSION-68040.lha (tools/pack_dist.py, tools/lha_archive.py)
# with its .sha256 and a short .readme. VERSION is the Installer script's
# $VER. SRC is the pinned upstream source (gameports/catalog.json); when it
# is not there, scripts/game_port_prepare.py fetches it. STOVE is a
# GCC 16 stove; scripts/record_stove.py records which compiler built it.
# Nothing is published from here.
# MIT, Copyright (c) 2026 AmiCradle Team.
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/.." && pwd)
: "${STOVE:?Set STOVE to a GCC 16 stove}"
OUT=${OUT:-"$ROOT/build-amiga-package"}
SRC=${SRC:-"$ROOT/build/game-ports/sources/astromenace"}
mkdir -p "$OUT"
OUT=$(CDPATH= cd -- "$OUT" && pwd)
cd "$ROOT"
if [ ! -d "$SRC" ]; then
    python3 "$ROOT/scripts/game_port_prepare.py" prepare --game astromenace --allow-network
fi
BUILD=$(mktemp -d "${TMPDIR:-/tmp}/astromenace-package.XXXXXX")
trap 'rm -rf "$BUILD"' EXIT INT TERM

STOVE="$STOVE" sh "$ROOT/build-amigaos3-runtime-fixed.sh" "$SRC" "$BUILD/out" > "$OUT/build-output.txt" 2>&1 \
    || { tail -n 60 "$OUT/build-output.txt"; exit 1; }

DIST="$BUILD/dist"
mkdir -p "$DIST"
cp -R "$BUILD/out/package/AstroMenace" "$DIST/AstroMenace"
cp icons/AstroMenace.info icons/README-AmiCradle.txt.info icons/LICENSE.md.info "$DIST/AstroMenace/"
cp icons/AstroMenace-drawer.info "$DIST/AstroMenace.info"
cp package/Install-AstroMenace package/Install-AstroMenace.info "$DIST/"
python3 "$ROOT/tools/pack_dist.py" --dist "$DIST" --name AstroMenace --out "$OUT"
# which compiler built it (scripts/record_stove.py, BL-144)
[ ! -f "$BUILD/out/build-info.json" ] || cp "$BUILD/out/build-info.json" "$OUT/"
