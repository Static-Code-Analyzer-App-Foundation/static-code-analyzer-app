from __future__ import annotations

import re
from ...rules import RuleFinding


def _extract_balanced(text: str, open_index: int, open_char: str = "(", close_char: str = ")") -> tuple[str | None, int]:
    depth = 0
    quote = None
    escape = False

    for i in range(open_index, len(text)):
        ch = text[i]

        if quote:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == quote:
                quote = None
            continue

        if ch in ("'", '"', "`"):
            quote = ch
            continue

        if ch == open_char:
            depth += 1
            continue

        if ch == close_char:
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : i], i

    return None, -1


def _split_top_level_args(text: str) -> list[str]:
    args: list[str] = []
    start = 0
    depth_paren = 0
    depth_brace = 0
    depth_bracket = 0
    quote = None
    escape = False

    for i, ch in enumerate(text):
        if quote:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == quote:
                quote = None
            continue

        if ch in ("'", '"', "`"):
            quote = ch
            continue

        if ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren = max(0, depth_paren - 1)
        elif ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace = max(0, depth_brace - 1)
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket = max(0, depth_bracket - 1)
        elif ch == "," and depth_paren == 0 and depth_brace == 0 and depth_bracket == 0:
            part = text[start:i].strip()
            if part:
                args.append(part)
            start = i + 1

    tail = text[start:].strip()
    if tail:
        args.append(tail)
    return args


def _find_use_effect_calls(text: str) -> list[str]:
    calls: list[str] = []
    start = 0
    hook = "useEffect("

    while True:
        pos = text.find(hook, start)
        if pos == -1:
            break

        body, end = _extract_balanced(text, pos + len("useEffect"))
        if body is not None and end != -1:
            calls.append(body)
            start = end + 1
        else:
            start = pos + len(hook)

    return calls


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    for call in _find_use_effect_calls(text):
        args = _split_top_level_args(call)
        if not args:
            continue

        callback = args[0]
        has_cleanup = bool(re.search(r"\breturn\s*\(\s*\)\s*=>|\breturn\s+function\b", callback, re.S))

        if re.search(r"\basync\s*\(", callback) or re.search(r"\basync\s+(\w+|\()", callback):
            findings.append(
                RuleFinding(
                    "lifecycle",
                    "medium",
                    12,
                    "Avoid async useEffect callbacks. Use an inner async function with cleanup/abort logic.",
                )
            )

        resource_usage = {
            "setInterval": "clearInterval",
            "setTimeout": "clearTimeout",
            "addEventListener": "removeEventListener",
            "subscribe": "unsubscribe",
            "fetch(": "AbortController",
            "new WebSocket": "close",
        }

        for needle, cleanup in resource_usage.items():
            if needle in callback:
                if not has_cleanup:
                    findings.append(
                        RuleFinding(
                            "lifecycle",
                            "high",
                            18,
                            f"useEffect uses {needle.rstrip('(')} without an obvious cleanup. That can leak resources.",
                        )
                    )
                elif cleanup not in callback:
                    findings.append(
                        RuleFinding(
                            "lifecycle",
                            "medium",
                            10,
                            f"useEffect uses {needle.rstrip('(')}. Check that cleanup via {cleanup} is implemented.",
                        )
                    )

    # Classic leak clues outside useEffect parsing
    if re.search(r"\bsetInterval\s*\(", text) and not re.search(r"\bclearInterval\s*\(", text):
        findings.append(
            RuleFinding(
                "lifecycle",
                "high",
                16,
                "setInterval is used without clearInterval. That is a memory leak risk.",
            )
        )

    if re.search(r"\baddEventListener\s*\(", text) and not re.search(r"\bremoveEventListener\s*\(", text):
        findings.append(
            RuleFinding(
                "lifecycle",
                "high",
                16,
                "addEventListener is used without removeEventListener. That can leak listeners.",
            )
        )

    if re.search(r"\bfetch\s*\(", text) and not re.search(r"\bAbortController\b", text):
        findings.append(
            RuleFinding(
                "lifecycle",
                "low",
                6,
                "Fetch calls in effects should usually support abort/cleanup to avoid stale updates.",
            )
        )

    return findings
