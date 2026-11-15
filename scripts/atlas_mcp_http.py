#!/usr/bin/env python3
"""Loopback Streamable-HTTP adapter for the Transit Atlas MCP server.

This is intentionally a small single-user adapter for local clients such as
Open WebUI. The stdio server remains the canonical implementation; this
process forwards JSON-RPC requests to it in-process and never binds beyond
loopback by default.
"""
import argparse
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from . import atlas_mcp
except ImportError:  # direct execution as scripts/atlas_mcp_http.py
    import atlas_mcp


SESSION = secrets.token_urlsafe(18)


def response_for(payload):
    result = atlas_mcp.dispatch(payload)
    return result


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _headers(self, content_type="application/json", length=None):
        self.send_header("Content-Type", content_type)
        self.send_header("Mcp-Session-Id", SESSION)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Mcp-Session-Id")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        if length is not None:
            self.send_header("Content-Length", str(length))

    def do_OPTIONS(self):
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
        try:
            size = int(self.headers.get("Content-Length", "0"))
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


def main():
    parser = argparse.ArgumentParser(description="Serve Transit Atlas MCP over local Streamable HTTP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print("Transit Atlas MCP HTTP: http://%s:%s/mcp" % (args.host, args.port), flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
