"""scripts/nightly.sh and autobuild.md: open9 picked from STOVES, an .lha needed, the entry well formed."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NightlyTests(unittest.TestCase):
    def run_nightly(self, make_lha: bool):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        t = Path(tmp.name)
        (t / "stoves/os32-gcc16-open9").mkdir(parents=True)
        fake = t / "fake.sh"
        fake.write_text('echo "$STOVE" > "$T/seen"\nmkdir -p "$OUT"\n'
                        + ('touch "$OUT/AstroMenace-1-68040.lha"\n' if make_lha else ''))
        env = dict(os.environ, T=str(t), STOVES=str(t / "stoves"), STOVE="other",
                   NIGHTLY_OUT=str(t / "out"), NIGHTLY_PACKAGE=str(fake))
        r = subprocess.run(["sh", str(ROOT / "scripts/nightly.sh")], env=env, capture_output=True, text=True)
        return r, t

    def test_open9_from_stoves_and_good_with_lha(self):
        r, t = self.run_nightly(True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((t / "seen").read_text().strip(), str(t / "stoves/os32-gcc16-open9"))

    def test_no_lha_is_a_failure(self):
        r, _ = self.run_nightly(False)
        self.assertNotEqual(r.returncode, 0)

    def test_autobuild_entry(self):
        text = (ROOT / "autobuild.md").read_text()
        for line in ("- frequency: nightly", "- script: scripts/nightly.sh", "- minutes: 120"):
            self.assertIn(line, text)
        self.assertIn("out/build-info.json", text)
        self.assertTrue((ROOT / "scripts/nightly.sh").is_file())

    def test_package_keeps_build_info(self):
        self.assertIn('cp "$BUILD/out/build-info.json" "$OUT/"', (ROOT / "package/build-amiga.sh").read_text())


if __name__ == "__main__":
    unittest.main()
