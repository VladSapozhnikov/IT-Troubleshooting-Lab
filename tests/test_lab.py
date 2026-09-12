"""Behavioral checks for the synthetic local service, using temporary folders."""
from contextlib import redirect_stdout
from http.client import HTTPConnection
import io
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

import lab


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name) / ".lab"
        with redirect_stdout(io.StringIO()):
            lab.setup(self.work)
        self.server = lab.make_server(self.work, 0)
        self.port = self.server.server_address[1]
        with redirect_stdout(io.StringIO()):
            lab.setup(self.work, self.port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def check_output(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = lab.check(self.work)
        return code, output.getvalue()

    def request(self, path):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            return response.status, response.read().decode()
        finally:
            connection.close()

    def test_healthy_service(self):
        code, output = self.check_output()
        self.assertEqual(code, 0)
        self.assertIn("HTTP 200", output)
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_wrong_port_then_fix(self):
        # Reserve a non-listening port so the test never contacts another service.
        with socket.socket() as unused:
            unused.bind(("127.0.0.1", 0))
            wrong = unused.getsockname()[1]
            lab.write_json(self.work / "client.json", {"port": wrong})
            self.assertEqual(self.check_output()[0], 1)
        with redirect_stdout(io.StringIO()):
            lab.change(self.work, "connection", False)
        self.assertEqual(self.check_output()[0], 0)

    def test_introduced_port_mismatch_changes_only_client(self):
        before = (self.work / "server.json").read_text()
        with redirect_stdout(io.StringIO()):
            lab.change(self.work, "connection", True)
        self.assertNotEqual(lab.port_from(self.work / "client.json"), self.port)
        self.assertEqual((self.work / "server.json").read_text(), before)

    def test_service_failure_and_recovery(self):
        with redirect_stdout(io.StringIO()):
            lab.change(self.work, "service", True)
        self.assertEqual(self.request("/health")[0], 503)
        code, output = self.check_output()
        self.assertEqual(code, 1)
        self.assertIn("TCP connected", output)
        self.assertIn("HTTP 503", output)
        self.assertIn('"status": 503', (self.work / "events.jsonl").read_text())
        with redirect_stdout(io.StringIO()):
            lab.change(self.work, "service", False)
        self.assertEqual(self.check_output()[0], 0)

    def test_malformed_service_config_returns_controlled_error(self):
        (self.work / "service-state.json").write_text("not-json", encoding="utf-8")
        self.assertEqual(self.request("/health")[0], 500)

    def test_server_does_not_serve_project_files(self):
        for path in ("/lab.py", "/.lab/server.json", "/../../README.md"):
            self.assertEqual(self.request(path)[0], 404)

    def test_setup_preserves_existing_exercise_state(self):
        with redirect_stdout(io.StringIO()):
            lab.change(self.work, "service", True)
            lab.setup(self.work)
        self.assertEqual(self.request("/health")[0], 503)

    def test_bad_port_does_not_replace_config(self):
        before = (self.work / "server.json").read_text()
        with self.assertRaises(ValueError):
            lab.setup(self.work, 80)
        self.assertEqual((self.work / "server.json").read_text(), before)

    def test_setup_refuses_unrelated_folder(self):
        unrelated = Path(self.temp.name) / "existing"
        unrelated.mkdir()
        note = unrelated / "note.txt"
        note.write_text("keep me")
        with self.assertRaises((OSError, ValueError)):
            lab.setup(unrelated)
        self.assertEqual(note.read_text(), "keep me")

    def test_cli_uses_its_own_project_folder(self):
        folder = Path(self.temp.name) / "project with spaces"
        folder.mkdir()
        script = folder / "lab.py"
        shutil.copyfile(lab.__file__, script)
        result = subprocess.run([sys.executable, str(script), "setup"],
                                cwd=self.temp.name, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((folder / ".lab" / "client.json").exists())


if __name__ == "__main__":
    unittest.main()
