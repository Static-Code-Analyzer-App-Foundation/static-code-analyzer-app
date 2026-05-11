from __future__ import annotations

import ast

from ...rules import RuleFinding

HEAVY_CALLS = {
    "open",
    "time.sleep",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "requests.request",
}


def _expr_text(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_expr_text(node.value)}.{node.attr}"
    return ""


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.loop_depth = 0
            self.async_depth = 0

        def visit_For(self, node: ast.For) -> None:
            self.loop_depth += 1
            if self.loop_depth >= 2:
                findings.append(RuleFinding("efficiency", "medium", 12, "Nested loops may create quadratic cost."))
            self.generic_visit(node)
            self.loop_depth -= 1

        def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
            self.visit_For(node)  # type: ignore[misc]

        def visit_While(self, node: ast.While) -> None:
            self.loop_depth += 1
            self.generic_visit(node)
            self.loop_depth -= 1

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.async_depth += 1
            self.generic_visit(node)
            self.async_depth -= 1

        def visit_Call(self, node: ast.Call) -> None:
            name = _call_name(node.func)

            if self.loop_depth > 0 and name in HEAVY_CALLS:
                findings.append(RuleFinding("efficiency", "medium", 10, "Repeated I/O or external calls inside a loop can be expensive."))

            if self.async_depth > 0 and name in {"time.sleep", "open", "subprocess.run", "subprocess.call", "subprocess.Popen"}:
                findings.append(RuleFinding("efficiency", "high", 16, f"Blocking call '{name}' inside async code can stall the event loop."))

            if self.loop_depth > 0 and name.endswith(".execute"):
                findings.append(RuleFinding("efficiency", "medium", 10, "Repeated DB calls inside a loop can create an N+1 pattern."))

            self.generic_visit(node)

        def visit_BinOp(self, node: ast.BinOp) -> None:
            if self.loop_depth > 0 and isinstance(node.op, ast.Add):
                findings.append(RuleFinding("efficiency", "medium", 10, "List/dict concatenation inside a loop can be slow; prefer append or extend."))
            self.generic_visit(node)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            if self.loop_depth > 0 and isinstance(node.op, ast.Add):
                findings.append(RuleFinding("efficiency", "low", 6, "Repeated collection growth in a loop may be inefficient."))
            self.generic_visit(node)

    Visitor().visit(tree)

    if text.count("open(") > 3:
        findings.append(RuleFinding("efficiency", "low", 5, "Repeated file opening may hurt performance."))
    if text.count(".execute(") > 5:
        findings.append(RuleFinding("efficiency", "medium", 10, "Many DB calls may indicate an N+1 query pattern."))
    if text.count("time.sleep(") > 1:
        findings.append(RuleFinding("efficiency", "medium", 8, "Multiple sleep calls can throttle throughput."))

    return findings
