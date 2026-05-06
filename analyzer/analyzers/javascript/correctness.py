from __future__ import annotations

import re
from pathlib import Path

from ...rules import RuleFinding

JS_KEYWORDS = {
    "break", "case", "catch", "class", "const", "continue", "debugger", "default",
    "delete", "do", "else", "export", "extends", "false", "finally", "for",
    "function", "if", "import", "in", "instanceof", "let", "new", "null",
    "return", "super", "switch", "this", "throw", "true", "try", "typeof",
    "var", "void", "while", "with", "yield", "async", "await",
}

JS_GLOBALS = {
    "Array", "ArrayBuffer", "Boolean", "Date", "Error", "EvalError", "Function",
    "Infinity", "JSON", "Map", "Math", "NaN", "Number", "Object", "Promise",
    "Proxy", "RangeError", "ReferenceError", "Reflect", "RegExp", "Set", "String",
    "Symbol", "SyntaxError", "TypeError", "URIError", "WeakMap", "WeakSet",
    "console", "document", "window", "globalThis", "navigator", "location",
    "history", "localStorage", "sessionStorage", "fetch", "URL", "URLSearchParams",
    "setTimeout", "setInterval", "clearTimeout", "clearInterval",
    "setImmediate", "clearImmediate", "queueMicrotask",
}

IDENT_RE = re.compile(r"\b[A-Za-z_$][\w$]*\b")


def _strip_js(text: str) -> str:
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r"//.*?$", "", text, flags=re.M)
    text = re.sub(r"'(?:\\.|[^'\\])*'", "''", text)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"`(?:\\.|[^`\\])*`", "``", text)
    return text


def _extract_declarations(lines: list[str]) -> dict[str, tuple[int, str]]:
    decls: dict[str, tuple[int, str]] = {}

    for lineno, line in enumerate(lines, 1):
        for m in re.finditer(r"\b(let|const|var)\s+([A-Za-z_$][\w$]*)", line):
            kind = m.group(1)
            name = m.group(2)
            decls.setdefault(name, (lineno, kind))

        for m in re.finditer(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", line):
            name = m.group(1)
            decls.setdefault(name, (lineno, "function"))

    return decls


def analyze(path: Path, text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    stripped = _strip_js(text)

    if (
        stripped.count("(") != stripped.count(")")
        or stripped.count("{") != stripped.count("}")
        or stripped.count("[") != stripped.count("]")
    ):
        findings.append(
            RuleFinding(
                "correctness",
                "high",
                18,
                "Possible syntax error: unmatched brackets, braces, or parentheses.",
            )
        )

    for m in re.finditer(r"\b(if|while)\s*\(([\s\S]{0,200}?)\)", stripped):
        condition = m.group(2)
        if re.search(r"(?<![!<>=+\-*/%&|^])=(?!=)", condition):
            findings.append(
                RuleFinding(
                    "correctness",
                    "high",
                    15,
                    "Assignment found inside a condition; this is usually a bug.",
                )
            )
            break

    lines = text.splitlines()
    decls = _extract_declarations(lines)

    for name, (decl_line, kind) in decls.items():
        if kind not in {"let", "const"}:
            continue

        pattern = rf"(?<![\.\w$])\b{re.escape(name)}\b"
        for lineno, line in enumerate(lines, 1):
            if lineno >= decl_line:
                break
            if re.search(pattern, line):
                findings.append(
                    RuleFinding(
                        "correctness",
                        "medium",
                        9,
                        f"'{name}' is used before its {kind} declaration; hoisting or TDZ bugs may occur.",
                    )
                )
                break

    nullish_names: set[str] = set()
    for m in re.finditer(
        r"\b(?:let|const|var)?\s*([A-Za-z_$][\w$]*)\s*=\s*(?:null|undefined)\b",
        stripped,
    ):
        nullish_names.add(m.group(1))

    for name in sorted(nullish_names):
        if re.search(rf"(?<!\?)\b{re.escape(name)}\.(?!\?)", stripped):
            findings.append(
                RuleFinding(
                    "correctness",
                    "medium",
                    8,
                    f"'{name}' may be null or undefined before property access.",
                )
            )

    for name in sorted(decls):
        if name in JS_KEYWORDS or name in JS_GLOBALS:
            continue

        kind = decls[name][1]
        if kind == "function":
            continue

        pattern = rf"(?<![\.\w$])\b{re.escape(name)}\b"
        first_decl_line = decls[name][0]
        for lineno, line in enumerate(lines, 1):
            if lineno >= first_decl_line:
                break
            if re.search(pattern, line):
                findings.append(
                    RuleFinding(
                        "correctness",
                        "low" if kind == "var" else "medium",
                        6 if kind == "var" else 9,
                        f"'{name}' appears before its declaration; check for scope or initialization bugs.",
                    )
                )
                break

    return findings
