#!/usr/bin/env python3
"""Streamable-HTTP adapter for the Transit Atlas MCP server.

This is a small single-user adapter for local clients such as Open WebUI.
The stdio server remains the canonical implementation; this process forwards
JSON-RPC requests to it in-process.

Hardening (RT-4): every POST must carry a per-install bearer token
(``Authorization: Bearer <token>``). The token comes from the
``ATLAS_MCP_TOKEN`` environment variable when set, otherwise from a token
file in the data dir (``mcp_http_token``, created with mode 0600 on first
use). There is no wildcard CORS, the ``Host`` header must name this machine,
and request bodies are capped at 1 MiB.
"""
import argparse
import json
import os
import pathlib
import secrets
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from . import atlas_mcp
except ImportError:  # direct execution as scripts/atlas_mcp_http.py
    import atlas_mcp


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_BODY = 1024 * 1024
SESSION = secrets.token_urlsafe(18)


def data_dir():
    return pathlib.Path(os.environ.get("ATLAS_DATA_DIR", ROOT / "data"))


def token_file():
    return data_dir() / "mcp_http_token"


def expected_token():
    override = os.environ.get("ATLAS_MCP_TOKEN")
    if override:
        return override
    path = token_file()
    try:
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    except OSError:
        pass
    value = secrets.token_urlsafe(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:  # another process created it first; read theirs
        return path.read_text(encoding="utf-8").strip()
    try:
        os.write(fd, (value + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    return value


def allowed_hosts(bind_host, port):
    names = {"localhost", "127.0.0.1", "::1", socket.gethostname()}
    if bind_host not in ("", "0.0.0.0", "::"):
        names.add(bind_host)
    else:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                names.add(info[4][0])
        except OSError:
            pass
    allowed = set()
    for name in names:
        allowed.add(name.lower())
        allowed.add("%s:%s" % (name.lower(), port))
    allowed.add("[::1]:%s" % port)
    return allowed


def response_for(payload):
    result = atlas_mcp.dispatch(payload)
    return result


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _headers(self, content_type="application/json", length=None):
        self.send_header("Content-Type", content_type)
        self.send_header("Mcp-Session-Id", SESSION)
        if length is not None:
            self.send_header("Content-Length", str(length))

    def _fail(self, status, message):
        body = (message + "\n").encode("utf-8")
        self.send_response(status)
        if status == 401:
            self.send_header("WWW-Authenticate", "Bearer")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _host_ok(self):
        host = (self.headers.get("Host") or "").strip().lower()
        return bool(host) and host in self.server.allowed_hosts

    def do_OPTIONS(self):
        # No CORS grants: browsers get no Access-Control-Allow-* headers.
        self.send_response(204)
        self._headers(length=0)
        self.end_headers()

    def do_GET(self):
        self.send_response(405)
        self._headers(length=0)
        self.send_header("Allow", "POST, OPTIONS")
        self.end_headers()

    def do_DELETE(self):
        self.send_response(405)
        self._headers(length=0)
        self.send_header("Allow", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self):
        if self.path != "/mcp":
            self.send_response(404)
            self._headers(length=0)
            self.end_headers()
            return
        if not self._host_ok():
            self._fail(403, "Forbidden: Host header does not match this server.")
            return
        authorization = self.headers.get("Authorization", "")
        token = authorization[7:] if authorization.startswith("Bearer ") else ""
        if not token or not secrets.compare_digest(token, expected_token()):
            self._fail(401, "Unauthorized: a valid MCP bearer token is required.")
            return
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            size = -1
        if size < 0:
            self._fail(400, "Bad Request: a valid Content-Length is required.")
            return
        if size > MAX_BODY:
            self._fail(413, "Request body exceeds the 1 MiB limit.")
            return
        try:
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            result = response_for(payload)
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            result = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Invalid JSON-RPC request: " + str(exc)}}
        if result is None:
            self.send_response(202)
            self._headers(length=0)
            self.end_headers()
            return
        data = json.dumps(result, separators=(",", ":")).encode("utf-8")
        accepts = self.headers.get("Accept", "")
        if "text/event-stream" in accepts:
            event = b"event: message\ndata: " + data + b"\n\n"
            self.send_response(200)
            self._headers("text/event-stream", len(event))
            self.end_headers()
            self.wfile.write(event)
        else:
            self.send_response(200)
            self._headers(length=len(data))
            self.end_headers()
            self.wfile.write(data)

    def log_message(self, fmt, *args):
        # Keep stdout clean for clients and make logs readable on stderr.
        super().log_message(fmt, *args)


def make_server(host, port):
    server = ThreadingHTTPServer((host, port), Handler)
    server.allowed_hosts = allowed_hosts(host, server.server_address[1])
    return server


def main():
    parser = argparse.ArgumentParser(description="Serve Transit Atlas MCP over local Streamable HTTP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    token = expected_token()
    source = "ATLAS_MCP_TOKEN" if os.environ.get("ATLAS_MCP_TOKEN") else str(token_file())
    print("Transit Atlas MCP HTTP: http://%s:%s/mcp" % (args.host, args.port), flush=True)
    print("MCP bearer token: %s" % token, flush=True)
    print("Token source: %s — clients must send 'Authorization: Bearer <token>'." % source, flush=True)
    make_server(args.host, args.port).serve_forever()


if __name__ == "__main__":
    main()
