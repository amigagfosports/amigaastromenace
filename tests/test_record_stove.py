"""record_stove.py: names the compiler, writes build-info.json, refuses no stove (BL-144)."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("record_stove", ROOT / "scripts/record_stove.py")
assert SPEC and SPEC.loader
rs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rs)


def fake_stove(root: Path, line: str, stove_json: dict | None = None) -> Path:
    gcc = root / "prefix/bin/m68k-amigaos-gcc"
    gcc.parent.mkdir(parents=True)
    gcc.write_text(f"#!/bin/sh\necho '{line}'\necho 'Copyright'\n")
    os.chmod(gcc, 0o755)
    if stove_json is not None:
        (root / "STOVE.json").write_text(json.dumps(stove_json))
    return root


class RecordStoveTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.tmp = Path(t.name)

    def test_any_stove_builds_and_is_recorded(self):
        # an open6 stove with no archive SHA-256 was refused by the old gate
        s = fake_stove(self.tmp / "os32-gcc16-open6", "m68k-amigaos-gcc (GFOpenAmigaGCC 16.2.0-open6) 16.2.0",
                       {"release": "16.2.0-open6"})
        info = rs.record(s, self.tmp / "out")
        self.assertEqual(info["compiler"], "m68k-amigaos-gcc (GFOpenAmigaGCC 16.2.0-open6) 16.2.0")
        self.assertEqual(info["release"], "16.2.0-open6")
        saved = json.loads((self.tmp / "out/build-info.json").read_text())
        self.assertEqual(saved["stove"], "os32-gcc16-open6")
        self.assertEqual(saved["compiler"], info["compiler"])

    def test_locally_built_stove_without_receipts(self):
        s = fake_stove(self.tmp / "local", "m68k-amigaos-gcc (local) 16.2.0")
        info = rs.record(s)
        self.assertIsNone(info["release"])
        self.assertIn("local", info["compiler"])

    def test_no_compiler_is_the_only_failure(self):
        (self.tmp / "empty").mkdir()
        r = subprocess.run([sys.executable, str(ROOT / "scripts/record_stove.py"), str(self.tmp / "empty")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_build_scripts_no_longer_call_the_gate(self):
        for f in ("build-amigaos3.sh", "build-amigaos3-runtime-fixed.sh", "package/build-amiga.sh"):
            text = (ROOT / f).read_text()
            self.assertNotIn("verify_open8_stove", text, f)
            self.assertNotIn("verify_gameport_stove", text, f)
        self.assertFalse((ROOT / "scripts/verify_open8_stove.py").exists())
        self.assertFalse((ROOT / "scripts/verify_gameport_stove.py").exists())


if __name__ == "__main__":
    unittest.main()
