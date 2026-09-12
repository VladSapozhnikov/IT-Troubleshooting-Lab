"""Local IT troubleshooting exercises. Python standard library only."""
import argparse
from datetime import datetime, timezone
from functools import partial
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import threading

ROOT = Path(__file__).resolve().parent
WORK = ROOT / ".lab"
SERVICE_ID = "IT-Troubleshooting-Lab"
MARKER = "it-troubleshooting-lab-v1\n"
LOG_LOCK = threading.Lock()


def read_json(path):
    # utf-8-sig also accepts files saved with a BOM by Windows PowerShell.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def require_workspace(work):
    if work.is_symlink() or (work / "marker.txt").read_text(encoding="utf-8") != MARKER:
        raise ValueError("Unrecognized lab workspace. Use a fresh project download.")
    for path in work.iterdir():
        if path.is_symlink():
            raise ValueError("Linked files are not supported in the lab workspace.")


def setup(work, port=None):
    if port is not None and not 1024 <= port <= 65535:
        raise ValueError("Choose a port between 1024 and 65535.")
    if work.exists():
        require_workspace(work)
    else:
        work.mkdir()
        (work / "marker.txt").write_text(MARKER, encoding="utf-8")
    if port is not None or not (work / "server.json").exists():
        selected = port or 8765
        write_json(work / "server.json", {"port": selected})
        write_json(work / "client.json", {"port": selected})
    if not (work / "service-state.json").exists():
        write_json(work / "service-state.json", {"maintenance": False})
    print("READY: Lab files are in .lab/. No extra packages are needed.")
    print("Next: py lab.py serve")


def port_from(path):
    value = read_json(path)["port"]
    if type(value) is not int or not 1024 <= value <= 65535:
        raise ValueError("The configured port must be an integer from 1024 to 65535.")
    return value


def event(work, kind, **fields):
    record = {"time_utc": datetime.now(timezone.utc).isoformat(), "event": kind, **fields}
    with LOG_LOCK, (work / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "LocalITLab/1.0"

    def __init__(self, *args, work, **kwargs):
        self.work = work
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        # Only the purpose-built local lab log is used; no host inventory.
        pass

    def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_error(404)
            return
        try:
            maintenance = read_json(self.work / "service-state.json")["maintenance"]
            if type(maintenance) is not bool:
                raise ValueError("maintenance must be true or false")
            status = 503 if maintenance else 200
            state = "maintenance" if maintenance else "healthy"
        except (OSError, ValueError, KeyError):
            status, state = 500, "invalid_service_configuration"
        payload = {"service": SERVICE_ID, "status": state, "synthetic": True}
        event(self.work, "http.response", status=status, state=state)
        if self.path == "/health":
            body = json.dumps(payload).encode("utf-8")
            content_type = "application/json"
        else:
            body = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
                    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                    "<title>IT Troubleshooting Lab</title><style>"
                    "body{font:18px system-ui;max-width:650px;margin:10vh auto;padding:24px;"
                    "background:#f3f5f8;color:#17263a}main{padding:32px;background:white;"
                    "border-radius:12px}code{background:#edf1f6;padding:4px}</style>"
                    "<main><p>LOCAL PRACTICE ENVIRONMENT</p><h1>IT Troubleshooting Lab</h1>"
                    f"<p><strong>HTTP {status}: {state.replace('_', ' ')}</strong></p>"
                    "<p>This page is a synthetic support service running on your own computer.</p>"
                    "<p>Use the terminal exercises to compare connectivity, application health, "
                    "and file access.</p><p><a href='/health'>View health response</a></p></main></html>").encode()
            content_type = "text/html; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def make_server(work, port):
    # Loopback only. No directory serving, file upload, or remote host options.
    return ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, work=work))


def serve(work):
    port = port_from(work / "server.json")
    try:
        server = make_server(work, port)
    except OSError as error:
        raise ValueError(f"Cannot bind port {port}. Stop another lab instance or use the port-conflict steps in docs/START-HERE.md.") from error
    event(work, "server.started", port=port)
    print(f"RUNNING: http://127.0.0.1:{port} (this computer only)", flush=True)
    print("Leave this terminal open. Use a second terminal for checks. Ctrl+C stops it.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSTOPPED: Local lab service.")
    finally:
        server.server_close()


def check(work):
    port = port_from(work / "client.json")
    connection = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request("GET", "/health")
        response = connection.getresponse()
        body = response.read(4096)
        try:
            result = json.loads(body)
        except ValueError:
            result = {}
        if not isinstance(result, dict) or result.get("service") != SERVICE_ID:
            print(f"FAIL: Port {port} answered, but it is not the expected lab health response.")
            return 1
        if response.status != 200 or result.get("status") != "healthy":
            print(f"FAIL: TCP connected to port {port}; application returned HTTP {response.status} ({result.get('status')}).")
            return 1
        print(f"PASS: TCP connected to port {port}; application returned HTTP 200 (healthy).")
        return 0
    except (OSError, HTTPException) as error:
        if isinstance(error, ConnectionRefusedError):
            reason = "connection refused"
        elif isinstance(error, (TimeoutError, socket.timeout)):
            reason = "timed out"
        else:
            reason = type(error).__name__
        print(f"FAIL: Could not get an HTTP response from 127.0.0.1:{port} ({reason}).")
        return 1
    finally:
        connection.close()


def change(work, scenario, broken):
    if scenario == "connection":
        port = port_from(work / "server.json")
        wrong_port = port + 1 if port < 65535 else port - 1
        write_json(work / "client.json", {"port": wrong_port if broken else port})
    else:
        write_json(work / "service-state.json", {"maintenance": broken})
    event(work, "exercise.changed", scenario=scenario, broken=broken)
    print(f"{'INTRODUCED' if broken else 'RESTORED'}: {scenario} exercise. Run py lab.py check to observe the result.")


def diagnose(work):
    for name in ("server.json", "client.json", "service-state.json"):
        print(f"{name}: {json.dumps(read_json(work / name))}")
    log = work / "events.jsonl"
    print("Recent synthetic lab events:")
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines()[-6:]:
            print(line)
    else:
        print("No events yet. Start the service and run a check.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup").add_argument("--port", type=int)
    for name in ("serve", "check", "diagnose"):
        commands.add_parser(name)
    for name in ("break", "fix"):
        commands.add_parser(name).add_argument("scenario", choices=["connection", "service"])
    args = parser.parse_args()
    try:
        if args.command == "setup":
            setup(WORK, args.port)
            return 0
        require_workspace(WORK)
        if args.command == "serve":
            serve(WORK)
        elif args.command == "check":
            return check(WORK)
        elif args.command == "diagnose":
            diagnose(WORK)
        else:
            change(WORK, args.scenario, args.command == "break")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}. If this is a fresh download, run py lab.py setup first.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
