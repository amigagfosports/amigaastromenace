#!/usr/bin/env python3
"""Fail-closed toolchain check for AstroMenace AmigaOS builds: Open8 or later.

Two kinds of stove pass:
- a staged Open8 stove (provenance.json, made by the staging tool): the core
  compiler/runtime files must agree with the official Open8 archive lock.
  Donor NDK/SDK files are recorded in the stove receipt as *reused*; this
  guard does not claim those donors were rebuilt or runtime-qualified.
- a Cradle stove (STOVE.json) of a published GFOpenAmigaGCC release, 16.2.0-open8
  or later, by the game ports' shared gate (scripts/verify_gameport_stove.py,
  the copy of DalsinAI/amicradle-stoves gameports/verify_gameport_stove.py):
  STOVE.json names the release archive's SHA-256 and the release, and the
  stove's own compiler says the same release. Open8 is the floor because it
  fixed the fold-mem-offsets wrong code of open6 and open7; open9 keeps that
  fix and adds libpthread's (the open9 rebuild, GF-109).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

RELEASE = "16.2.0-open8"
MINIMUM = 8          # 16.2.0-open8: the oldest release a Cradle stove may be
ARCHIVE_SHA256 = "4855915429d8d623037af5aa911b2c3dd6b3ae98eb557eb22c4e76c4fbacf31b"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def verify(stove: Path, *, check_version: bool = True) -> dict:
    stove = stove.resolve(strict=True)
    if not (stove / "provenance.json").is_file():
        return verify_cradle_stove(stove)
    receipt = json.loads((stove / "provenance.json").read_text(encoding="utf-8"))
    if (receipt.get("schema") != 1
            or receipt.get("release") != RELEASE
            or receipt.get("archive_sha256") != ARCHIVE_SHA256):
        raise ValueError("AstroMenace requires verified GCC 16.2.0-open8 stove")
    files = receipt.get("compiler_runtime_sha256")
    if not isinstance(files, dict) or not files:
        raise ValueError("Missing compiler/runtime provenance")
    root = stove / "prefix"
    for name, expected in files.items():
        p = PurePosixPath(name)
        if (p.is_absolute() or ".." in p.parts or p.as_posix() != name
                or len(expected) != 64):
            raise ValueError(f"Invalid compiler/runtime receipt entry: {name!r}")
        source = root / name
        if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing or external compiler/runtime entry: {name}")
        if digest(source) != expected:
            raise ValueError(f"Compiler/runtime checksum mismatch: {name}")
    compiler = root / "bin/m68k-amigaos-g++"
    if check_version:
        result = subprocess.run([str(compiler), "--version"],
                                text=True, capture_output=True, check=True,
                                timeout=20)
        if "GFOpenAmigaGCC 16.2.0-open8" not in result.stdout.splitlines()[0]:
            raise ValueError("Wrong compiler executable version")
    print(f"ASTROMENACE_OPEN8_STOVE_PASS: {len(files)} compiler/runtime files")
    return receipt


def verify_cradle_stove(stove: Path) -> dict:
    """A Cradle stove (STOVE.json) of a published release, open8 or later, by the shared game-port gate."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import verify_gameport_stove as gate
    try:
        release, archive, why = gate.verify(stove, minimum=MINIMUM)
    except gate.GateError as exc:
        raise ValueError(f"AstroMenace requires a verified GCC 16.2.0-open8 or later stove: {exc}") from exc
    print(f"ASTROMENACE_STOVE_PASS: {release} (archive {archive}): " + "; ".join(why))
    return {"schema": 1, "release": release, "archive_sha256": archive, "source": "STOVE.json"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_open8_stove.py /path/to/stove (open8 or later)")
    try:
        verify(Path(sys.argv[1]))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"ASTROMENACE_OPEN8_STOVE_FAIL: {exc}") from exc
