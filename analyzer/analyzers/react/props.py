from __future__ import annotations

import re
from ...rules import RuleFinding


def _extract_balanced(text: str, open_index: int, open_char: str = "{", close_char: str = "}") -> tuple[str | None, int]:
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


def _collect_required_props(text: str) -> dict[str, set[str]]:
    required: dict[str, set[str]] = {}
    start_pattern = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\.propTypes\s*=\s*\{", re.M)

    for match in start_pattern.finditer(text):
        component = match.group(1)
        open_index = match.end() - 1  # points to "{"
        block, _end = _extract_balanced(text, open_index, "{", "}")
        if block is None:
            continue

        props: set[str] = set()
        for prop_match in re.finditer(r"\b([A-Za-z_$][\w$]*)\s*:\s*[^,\n]+?\.isRequired\b", block, re.S):
            props.add(prop_match.group(1))

        if props:
            required[component] = props

    return required


def _iter_jsx_tags(text: str):
    tag_pattern = re.compile(r"<([A-Z][A-Za-z0-9_]*)\b([^<>]*?)(/?)>", re.S)
    for match in tag_pattern.finditer(text):
        yield match.group(1), match.group(2), match.start()


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    required_props = _collect_required_props(text)

    # Required props missing in JSX usage
    for component, props in required_props.items():
        for tag_name, attrs, _pos in _iter_jsx_tags(text):
            if tag_name != component:
                continue
            if "..." in attrs:
                continue

            for prop in props:
                if not re.search(rf"\b{re.escape(prop)}\s*=", attrs):
                    findings.append(
                        RuleFinding(
                            "props",
                            "medium",
                            10,
                            f"<{component}> is missing required prop '{prop}'.",
                        )
                    )

    # Obvious wrong-type prop usage
    wrong_type_patterns = [
        (r"\b(title|alt|placeholder|aria-label|aria-labelledby|name|id|className)\s*=\s*\{\s*(true|false)\s*\}", "boolean"),
        (r"\b(title|alt|placeholder|aria-label|aria-labelledby|name|id|className)\s*=\s*\{\s*\d+(?:\.\d+)?\s*\}", "numeric"),
    ]
    for pattern, kind in wrong_type_patterns:
        if re.search(pattern, text):
            findings.append(
                RuleFinding(
                    "props",
                    "low",
                    5,
                    f"A {kind} value is being passed to a text-like prop. Double-check the JSX prop type.",
                )
            )
            break

    # Controlled / uncontrolled component problems
    control_tag_pattern = re.compile(r"<(input|textarea|select)\b([^<>]*?)(/?)>", re.S)
    for match in control_tag_pattern.finditer(text):
        tag = match.group(1)
        attrs = match.group(2)

        has_value = bool(re.search(r"\b(value|checked)\s*=\s*\{", attrs))
        has_on_change = bool(re.search(r"\bonChange\s*=", attrs))
        has_read_only = bool(re.search(r"\breadOnly\s*=", attrs))

        if has_value and not has_on_change and not has_read_only:
            findings.append(
                RuleFinding(
                    "props",
                    "medium",
                    10,
                    f"<{tag}> looks controlled but has no onChange or readOnly handler.",
                )
            )

    # Wrong component prop shapes from obvious inline literals
    if re.search(r"<[A-Z][A-Za-z0-9_]*\b[^>]*\b(className|id|name|title|alt|placeholder)\s*=\s*\{\s*(\{|\[)\s*", text, re.S):
        findings.append(
            RuleFinding(
                "props",
                "low",
                4,
                "A text-like prop receives an object or array literal. That is probably the wrong type.",
            )
        )

    return findings
