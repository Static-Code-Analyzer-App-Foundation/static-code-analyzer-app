from __future__ import annotations

import re
from ...rules import RuleFinding


HOOKS_WITH_DEPS = ("useEffect", "useLayoutEffect", "useMemo", "useCallback")
CONTROL_FLOW_PATTERN = re.compile(r"\b(if|for|while|switch|catch|try)\b", re.I)


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


def _collect_state_vars(text: str) -> dict[str, str]:
    state_pairs: dict[str, str] = {}
    pattern = re.compile(
        r"\bconst\s*\[\s*([A-Za-z_$][\w$]*)\s*,\s*([A-Za-z_$][\w$]*)\s*\]\s*=\s*useState\s*\(",
        re.M,
    )
    for match in pattern.finditer(text):
        state_var = match.group(1)
        setter = match.group(2)
        state_pairs[state_var] = setter
    return state_pairs


def _collect_destructured_props(text: str) -> set[str]:
    props: set[str] = set()

    patterns = [
        re.compile(r"function\s+[A-Z][A-Za-z0-9_]*\s*\(\s*\{([^}]*)\}\s*\)", re.S),
        re.compile(r"const\s+[A-Z][A-Za-z0-9_]*\s*=\s*\(\s*\{([^}]*)\}\s*\)\s*=>", re.S),
        re.compile(r"export\s+default\s+function\s+[A-Z][A-Za-z0-9_]*\s*\(\s*\{([^}]*)\}\s*\)", re.S),
    ]

    for pattern in patterns:
        for match in pattern.finditer(text):
            raw = match.group(1)
            for part in raw.split(","):
                name = part.strip()
                if not name or name.startswith("..."):
                    continue
                if "=" in name:
                    name = name.split("=", 1)[0].strip()
                if ":" in name:
                    name = name.split(":", 1)[0].strip()
                if re.match(r"^[A-Za-z_$][\w$]*$", name):
                    props.add(name)

    return props


def _find_hook_calls(text: str, hook_name: str) -> list[tuple[int, str]]:
    calls: list[tuple[int, str]] = []
    start = 0

    while True:
        pos = text.find(f"{hook_name}(", start)
        if pos == -1:
            break

        open_index = pos + len(hook_name)
        body, end = _extract_balanced(text, open_index)
        if body is not None and end != -1:
            calls.append((pos, body))
            start = end + 1
        else:
            start = pos + len(hook_name) + 1

    return calls


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    state_pairs = _collect_state_vars(text)
    prop_names = _collect_destructured_props(text)

    # Conditional / unstable hook order
    for hook_name in ("useState", "useReducer", "useEffect", "useLayoutEffect", "useMemo", "useCallback", "useRef", "useContext"):
        for pos, _body in _find_hook_calls(text, hook_name):
            prefix = text[max(0, pos - 180) : pos]
            if CONTROL_FLOW_PATTERN.search(prefix):
                findings.append(
                    RuleFinding(
                        "hooks",
                        "high",
                        18,
                        f"{hook_name} appears inside control flow. Hooks must keep a stable call order.",
                    )
                )
                break

    # Dependency arrays and stale closures
    for hook_name in HOOKS_WITH_DEPS:
        for pos, body in _find_hook_calls(text, hook_name):
            args = _split_top_level_args(body)
            if not args:
                continue

            callback = args[0]
            deps = args[1] if len(args) > 1 else None

            if deps is None:
                findings.append(
                    RuleFinding(
                        "hooks",
                        "medium",
                        10,
                        f"{hook_name} is missing a dependency array.",
                    )
                )
                continue

            deps_clean = deps.strip()
            referenced: list[str] = []

            for name in sorted(state_pairs):
                if re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", callback):
                    referenced.append(name)

            for name in sorted(prop_names):
                if re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", callback):
                    referenced.append(name)

            if "props." in callback and "props." not in deps_clean:
                findings.append(
                    RuleFinding(
                        "hooks",
                        "medium",
                        12,
                        f"{hook_name} reads props but the dependency array looks incomplete.",
                    )
                )

            missing = [name for name in referenced if not re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", deps_clean)]
            if missing:
                findings.append(
                    RuleFinding(
                        "hooks",
                        "medium",
                        12,
                        f"{hook_name} dependency array may be missing: {', '.join(missing[:5])}.",
                    )
                )

            if deps_clean == "[]":
                if re.search(r"\b(props\.|useState|useReducer|useRef|set[A-Z][A-Za-z0-9_]*)", callback):
                    findings.append(
                        RuleFinding(
                            "hooks",
                            "low",
                            5,
                            f"Empty dependency array in {hook_name} may be stale if it reads props or state.",
                        )
                    )

    # Stale state updates
    for state_var, setter in state_pairs.items():
        if re.search(rf"\b{re.escape(setter)}\s*\(\s*{re.escape(state_var)}\s*[\+\-]\s*\d+", text):
            findings.append(
                RuleFinding(
                    "state",
                    "medium",
                    12,
                    f"{setter} uses {state_var} directly; prefer functional updates to avoid stale state.",
                )
            )
        if re.search(rf"\b{re.escape(setter)}\s*\(\s*[\[\{{].*\b{re.escape(state_var)}\b", text, re.S):
            findings.append(
                RuleFinding(
                    "state",
                    "low",
                    6,
                    f"{setter} appears to rebuild from captured {state_var}; check for stale closure risk.",
                )
            )

    return findings
