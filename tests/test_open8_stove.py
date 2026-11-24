"""AstroMenace Open8 fail-closed build provenance regressions."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astro_open8", ROOT / "scripts/verify_open8_stove.py")
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


class Open8StoveTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        exe = self.root / "prefix/bin/m68k-amigaos-g++"
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b"correct-artifact")
        self.file = exe
        self.receipt = {
            "schema": 1, "release": guard.RELEASE,
            "archive_sha256": guard.ARCHIVE_SHA256,
            "compiler_runtime_sha256": {
                "bin/m68k-amigaos-g++": hashlib.sha256(exe.read_bytes()).hexdigest()
            },
        }
        self.save()

    def save(self):
        (self.root / "provenance.json").write_text(json.dumps(self.receipt))

    def test_good_stove_receipt(self):
        self.assertEqual(guard.verify(self.root, check_version=False)["release"], guard.RELEASE)

    def test_rejects_old_compiler_release(self):
        self.receipt["release"] = "16.2.0-open3"
        self.save()
        with self.assertRaisesRegex(ValueError, "requires verified"):
            guard.verify(self.root, check_version=False)

    def test_rejects_wrong_published_archive(self):
        self.receipt["archive_sha256"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "requires verified"):
            guard.verify(self.root, check_version=False)

    def test_rejects_tampered_compiler_runtime(self):
        self.file.write_bytes(b"compromised")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            guard.verify(self.root, check_version=False)

    def test_rejects_empty_receipt_or_path_escape(self):
        self.receipt["compiler_runtime_sha256"] = {}
        self.save()
        with self.assertRaisesRegex(ValueError, "Missing compiler/runtime"):
            guard.verify(self.root, check_version=False)
        self.receipt["compiler_runtime_sha256"] = {"../escape": "a" * 64}
        self.save()
        with self.assertRaisesRegex(ValueError, "Invalid compiler/runtime"):
            guard.verify(self.root, check_version=False)

    def test_release_builder_requires_explicit_stove(self):
        for script in ("build-amigaos3-runtime-fixed.sh", "build-amigaos3.sh"):
            with self.subTest(script=script):
                text = (ROOT / script).read_text()
                self.assertIn('python3 "$HERE/scripts/verify_open8_stove.py" "$STOVE"', text)
                self.assertIn("Set STOVE to a verified GCC 16.2.0-open8 or later", text)


class CradleStoveTests(unittest.TestCase):
    """A Cradle stove (STOVE.json, no provenance.json) goes through the shared game-port gate, open8 or later."""
    def stove(self, release, archive="9" * 64, said=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        cc = root / "prefix/bin/m68k-amigaos-gcc"
        cc.parent.mkdir(parents=True)
        cc.write_text(f"#!/bin/sh\necho 'm68k-amigaos-gcc (GFOpenAmigaGCC {said or release}) 16.2.0b'\n")
        cc.chmod(0o755)
        info = {"release": f"GFOpenAmigaGCC {release}"}
        if archive:
            info["compilerArchive"] = {"sha256": archive}
        (root / "STOVE.json").write_text(json.dumps(info))
        return root

    def test_open9_cradle_stove_accepted(self):
        self.assertEqual(guard.verify(self.stove("16.2.0-open9"))["release"], "16.2.0-open9")

    def test_open8_cradle_stove_accepted(self):
        self.assertEqual(guard.verify(self.stove("16.2.0-open8"))["release"], "16.2.0-open8")

    def test_open7_refused(self):
        with self.assertRaisesRegex(ValueError, "open8 or later"):
            guard.verify(self.stove("16.2.0-open7"))

    def test_unpublished_stove_refused(self):
        with self.assertRaisesRegex(ValueError, "open8 or later"):
            guard.verify(self.stove("16.2.0-open9", archive=None))

    def test_mislabelled_compiler_refused(self):
        with self.assertRaisesRegex(ValueError, "open8 or later"):
            guard.verify(self.stove("16.2.0-open9", said="16.2.0-open6"))


if __name__ == "__main__":
    unittest.main()
