#!/usr/bin/env python3
"""Interactive Ollama chat with the local Transit Atlas MCP server."""
import argparse
import json
import os
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
PERSONALITY_PATH = os.path.join(ROOT, "personality.md")


class McpProcess:
    def __init__(self):
        self.proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "scripts", "atlas_mcp.py")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.next_id = 1

    def request(self, method, params=None):
        request_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("Atlas MCP server exited unexpectedly")
            response = json.loads(line)
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(response["error"].get("message", "MCP request failed"))
                return response.get("result", {})

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=3)


def ollama_chat(model, messages, tools, think=False):
    body = {"model": model, "messages": messages, "stream": False, "tools": tools, "think": think}
    request = Request(OLLAMA_URL + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        raise RuntimeError("Ollama API %s: %s" % (exc.code, exc.read().decode(errors="replace")[:500]))
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Ollama is unavailable at %s: %s" % (OLLAMA_URL, exc))


def ollama_tools(mcp_tools):
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["inputSchema"]}} for t in mcp_tools]


def run_turn(mcp, model, messages, prompt, think=False):
    verified_context = []
    route_numbers = re.findall(r"\b(?:route|line|bus)\s*(?:number\s*)?(\d{2,4})\b|\b(\d{3})\b", prompt, re.IGNORECASE)
    for match in route_numbers:
        route_query = next(value for value in match if value)
        lookup = mcp.request("tools/call", {"name": "atlas_search_routes", "arguments": {"query": route_query, "limit": 20}})
        text = "\n".join(item.get("text", "") for item in lookup.get("content", []) if item.get("type") == "text")
        verified_context.append("Verified Atlas route lookup for %s:\n%s" % (route_query, text))
    if verified_context:
        prompt = "\n\n".join(verified_context) + "\n\nAnswer the user's request using this verified route data; do not invent route facts.\n" + prompt
    messages.append({"role": "user", "content": prompt})
    for _ in range(6):
        response = ollama_chat(model, messages, ollama_tools(mcp.tools), think=think)
        assistant = response.get("message", {})
        messages.append(assistant)
        calls = assistant.get("tool_calls") or []
        if not calls:
            return assistant.get("content", "").strip()
        for call in calls:
            function = call.get("function", {})
            result = mcp.request("tools/call", {"name": function.get("name", ""), "arguments": function.get("arguments") or {}})
            text = "\n".join(item.get("text", "") for item in result.get("content", []) if item.get("type") == "text")
            messages.append({"role": "tool", "content": text})
    raise RuntimeError("Tool-call limit reached; the model did not finish the turn")


def main():
    parser = argparse.ArgumentParser(description="Chat with Ollama using Transit Atlas MCP tools")
    parser.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "qwen3:1.7b"))
    parser.add_argument("--think", action="store_true", help="Enable Qwen3 reasoning; slower but potentially better for complex requests")
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()
    mcp = McpProcess()
    try:
        mcp.request("initialize")
        mcp.tools = mcp.request("tools/list").get("tools", [])
        personality = open(PERSONALITY_PATH, encoding="utf-8").read() if os.path.exists(PERSONALITY_PATH) else "You are Percival, a local transit assistant."
        personality += "\n\nOperational rule: for every transit fact, use Atlas tools before answering. For route descriptions, call atlas_route_report and report the matched identity, operator/feed, source status, date coverage and limitations. For a visit or 'come to me' request, call atlas_come_to_me and protect the return journey; never imply that a message, booking or purchase occurred. If a date or departure time is missing, ask a concise follow-up instead of guessing. Format answers as Known, Estimated, Unknown, then Next step when useful."
        messages = [{"role": "system", "content": personality}]
        if args.prompt:
            print(run_turn(mcp, args.model, messages, " ".join(args.prompt), think=args.think))
            return
        print("Percival — local transit companion. Type 'quit' to exit.")
        while True:
            try:
                prompt = input("you> ").strip()
            except EOFError:
                break
            if prompt.lower() in {"quit", "exit"}:
                break
            if prompt:
                print("atlas> " + run_turn(mcp, args.model, messages, prompt, think=args.think))
    finally:
        mcp.close()


if __name__ == "__main__":
    main()
