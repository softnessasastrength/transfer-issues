"""Regression tests for the extraction path of scripts/setup_ollama.sh.

The pinned Ollama release tarball's top level is bin/ + lib/ (bin/ollama,
lib/ollama/llama-server, lib/ollama/libggml*, ...). The v0.0.1/v0.0.2
packages shipped an extraction using --strip-components=1, which turned
bin/ollama into a regular file named "ollama" in the target root and
made every lib/ollama/* member fail with "Not a directory" — the script
had been digest-verified but never executed end-to-end, so the defect
reached the owner's machine (live run, 2026-11-15; see DECISIONS.md).

These tests build a small synthetic .tar.zst with the real layout shape
and run the script's own extract_ollama function against it, sourced
with SETUP_OLLAMA_FUNCTIONS_ONLY=1 so the install itself does not run.

The script's extraction shells out to `tar --zstd`, which needs a real
zstd binary on PATH (setup_ollama.sh apt-installs zstd on target
machines before extracting). Where zstd is unavailable the tests skip
rather than simulating the decompressor.
"""
import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "setup_ollama.sh"


def build_fixture(members):
    """Build .tar.zst bytes from (arcname, data, mode) file members.
    Like the real tarball, directories are implied by the file paths —
    there are no explicit directory entries."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, data, mode in members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = mode
            tf.addfile(info, io.BytesIO(data))
    proc = subprocess.run(
        ["zstd", "-q", "-f", "-c"], input=buf.getvalue(),
        capture_output=True, check=True)
    return proc.stdout


# Same shape as the real v0.40.16 tarball: bin/ollama executable,
# lib/ollama/ carrying llama-server, the libggml libraries and licenses.
REAL_LAYOUT = [
    ("bin/ollama", b"#!/bin/sh\n# dummy ollama binary\n", 0o755),
    ("lib/ollama/llama-server", b"dummy llama-server\n", 0o755),
    ("lib/ollama/libggml-base.so.0.29.0", b"dummy shared library\n", 0o644),
    ("lib/ollama/GO_LICENSE", b"dummy license\n", 0o644),
]

# A layout the script must refuse: no bin/ or lib/ structure at all.
FLAT_LAYOUT = [
    ("ollama", b"#!/bin/sh\n# flat layout, no bin/ or lib/\n", 0o755),
]


@unittest.skipUnless(shutil.which("zstd"),
                     "zstd binary not on PATH — the extraction under "
                     "test needs it (setup_ollama.sh installs it via "
                     "apt on target machines)")
@unittest.skipUnless(shutil.which("sh"), "POSIX sh not available")
class SetupOllamaExtractionTest(unittest.TestCase):
    def run_extract(self, fixture_bytes):
        tmp = Path(tempfile.mkdtemp(prefix="setup-ollama-test-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        archive = tmp / "ollama.tar.zst"
        archive.write_bytes(fixture_bytes)
        target = tmp / "install"
        env = dict(os.environ, SETUP_OLLAMA_FUNCTIONS_ONLY="1")
        proc = subprocess.run(
            ["sh", "-c", '. "$1"; extract_ollama "$2" "$3"', "sh",
             str(SCRIPT), str(archive), str(target)],
            capture_output=True, text=True, env=env)
        return proc, target

    def test_real_layout_lands_intact(self):
        proc, target = self.run_extract(build_fixture(REAL_LAYOUT))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        binary = target / "bin" / "ollama"
        self.assertTrue(binary.is_file())
        self.assertTrue(os.access(binary, os.X_OK))
        self.assertTrue((target / "lib" / "ollama" / "llama-server").is_file())
        self.assertTrue(
            (target / "lib" / "ollama" / "libggml-base.so.0.29.0").is_file())
        # The shipped defect's signature: a regular file named "ollama"
        # at the target root, with the lib members blocked beneath it.
        self.assertFalse((target / "ollama").is_file())

    def test_unexpected_layout_fails_loudly(self):
        proc, target = self.run_extract(build_fixture(FLAT_LAYOUT))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unexpected Ollama tarball layout", proc.stderr)


if __name__ == "__main__":
    unittest.main()
