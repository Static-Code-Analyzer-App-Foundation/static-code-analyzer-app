from __future__ import annotations

import ast
import re

from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    lines = text.splitlines()
    if len(lines) > 400:
        findings.append(RuleFinding("maintenance", "medium", 8, "Large Python files are harder to maintain."))

    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if re.search(r"[A-Z-]", node.name):
                    findings.append(RuleFinding("maintenance", "low", 6, f"Function name '{node.name}' is not snake_case."))
            elif isinstance(node, ast.AsyncFunctionDef):
                if re.search(r"[A-Z-]", node.name):
                    findings.append(RuleFinding("maintenance", "low", 6, f"Function name '{node.name}' is not snake_case."))
            elif isinstance(node, ast.ClassDef):
                if not re.fullmatch(r"[A-Z][A-Za-z0-9]+", node.name):
                    findings.append(RuleFinding("maintenance", "low", 5, f"Class name '{node.name}' should use PascalCase."))

    if "print(" in text:
        findings.append(RuleFinding("maintenance", "low", 4, "Debug print statements should be removed or logged properly."))

    if re.search(r"^\s*except\s*:\s*$", text, re.MULTILINE):
        findings.append(RuleFinding("maintenance", "medium", 10, "Bare except blocks make debugging and recovery harder."))

    if re.search(r"\bimport\s+\*", text):
        findings.append(RuleFinding("maintenance", "medium", 8, "Wildcard imports reduce clarity and can cause namespace collisions."))

    return findings
