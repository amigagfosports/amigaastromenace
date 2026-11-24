#!/usr/bin/env python3
"""Record which compiler built this port; never refuse a stove.

    python3 scripts/record_stove.py STOVE [OUT_DIR]

Prints one line naming the compiler (the first line of the stove's own
prefix/bin/m68k-amigaos-gcc --version) and, when OUT_DIR is given, writes
OUT_DIR/build-info.json with the stove's folder, that line and the release
STOVE.json or provenance.json names, if either is there. Exits 2 only when
the stove has no compiler at all. It replaces the old certificate gate
(verify_open8_stove.py, verify_gameport_stove.py): the port builds with the
stove it is given (BL-144).
MIT, Copyright (c) 2026 AmiCradle Team.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def compiler_line(stove: Path) -> str:
    gcc = stove / "prefix/bin/m68k-amigaos-gcc"
    if not gcc.is_file():
        raise FileNotFoundError(f"no compiler in the stove: {gcc}")
    try:
        out = subprocess.run([str(gcc), "--version"], text=True, capture_output=True,
                             timeout=20).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        return f"unknown ({exc})"
    return (out.splitlines() or ["unknown"])[0].strip()


def stove_release(stove: Path) -> str | None:
    for name in ("STOVE.json", "provenance.json"):
        try:
            data = json.loads((stove / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and isinstance(data.get("release"), str):
            return data["release"]
    return None


def record(stove: Path, out: Path | None = None) -> dict:
    info = {"schema": 1, "stove": stove.name, "stove_path": str(stove),
            "compiler": compiler_line(stove), "release": stove_release(stove),
            "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        (out / "build-info.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    return info


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: record_stove.py STOVE [OUT_DIR]")
    try:
        i = record(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else None)
    except FileNotFoundError as exc:
        print(f"record_stove: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(f"compiler: {i['compiler']} (stove {i['stove']}, release {i['release'] or 'not named'})")
