from __future__ import annotations

import ast
import builtins
from collections.abc import Iterable
from io import StringIO
import tokenize
from typing import Optional

from ...rules import RuleFinding

BUILTINS = set(dir(builtins))
MUTABLE_LITERAL_NODES = (ast.List, ast.Dict, ast.Set)
BLOCKING_CALLS_IN_ASYNC = {
    "time.sleep",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "os.system",
    "open",
}


def _expr_text(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def _iter_target_names(target: ast.AST) -> Iterable[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            yield from _iter_target_names(elt)


def _is_mutable_default(node: ast.AST) -> bool:
    if isinstance(node, MUTABLE_LITERAL_NODES):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in {"list", "dict", "set"}
    return False


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_expr_text(node.value)}.{node.attr}"
    return ""


def _is_bare_or_broad_except(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    exc_name = _expr_text(handler.type)
    return exc_name in {"Exception", "BaseException"}


def _looks_swallowed(handler: ast.ExceptHandler) -> bool:
    if not handler.body:
        return True
    if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
        return True
    has_raise = any(isinstance(node, ast.Raise) for node in ast.walk(ast.Module(body=handler.body, type_ignores=[])))
    return not has_raise


def _has_cleanup_keywords(node: ast.Try) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in {"open", "close", "release", "connect", "acquire", "lock"}:
            return True
        if isinstance(sub, ast.Attribute) and sub.attr in {"close", "release", "connect", "acquire"}:
            return True
    return False


def _parse(text: str) -> tuple[Optional[ast.AST], list[RuleFinding]]:
    findings: list[RuleFinding] = []
    try:
        tree = ast.parse(text)
    except IndentationError as exc:
        findings.append(RuleFinding("correctness", "high", 25, f"Indentation error: {exc.msg}"))
        return None, findings
    except SyntaxError as exc:
        findings.append(RuleFinding("correctness", "high", 25, f"Syntax error: {exc.msg or 'invalid Python syntax'}"))
        return None, findings

    try:
        list(tokenize.generate_tokens(StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        findings.append(RuleFinding("correctness", "high", 20, f"Tokenization or indentation issue: {exc}"))

    return tree, findings


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    tree, parse_findings = _parse(text)
    findings.extend(parse_findings)
    if tree is None:
        return findings

    imported: set[str] = set()
    used: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scope_stack: list[set[str]] = [set()]
            self.function_returns: list[str | None] = []
            self.current_async_depth = 0

        @property
        def current_scope(self) -> set[str]:
            return self.scope_stack[-1]

        def _lookup(self, name: str) -> bool:
            if name in BUILTINS:
                return True
            for scope in reversed(self.scope_stack):
                if name in scope:
                    return True
            return False

        def _bind(self, name: str) -> None:
            if not name or name == "_":
                return
            if name in BUILTINS:
                findings.append(RuleFinding("maintenance", "low", 6, f"Name '{name}' shadows a Python builtin."))
            if name in self.current_scope:
                findings.append(RuleFinding("maintenance", "low", 5, f"Name '{name}' is redefined in the same scope."))
            else:
                outer = set().union(*self.scope_stack[:-1]) if len(self.scope_stack) > 1 else set()
                if name in outer:
                    findings.append(RuleFinding("maintenance", "low", 5, f"Name '{name}' shadows an outer name."))
            self.current_scope.add(name)

        def _bind_target(self, target: ast.AST) -> None:
            for name in _iter_target_names(target):
                self._bind(name)

        def visit_Module(self, node: ast.Module) -> None:
            for stmt in node.body:
                self.visit(stmt)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imported.add(name)
                self._bind(name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if any(alias.name == "*" for alias in node.names):
                findings.append(RuleFinding("style", "medium", 8, "Wildcard imports reduce clarity and safety."))
                return
            for alias in node.names:
                name = alias.asname or alias.name
                imported.add(name)
                self._bind(name)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Load):
                used.add(node.id)
                if not self._lookup(node.id):
                    findings.append(RuleFinding("correctness", "medium", 10, f"Undefined or unresolved name '{node.id}'."))
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            self.visit(node.value)
            for target in node.targets:
                self._bind_target(target)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if node.value is not None:
                self.visit(node.value)
            self._bind_target(node.target)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            if isinstance(node.target, ast.Name) and not self._lookup(node.target.id):
                findings.append(RuleFinding("correctness", "medium", 10, f"Augmented assignment uses undefined name '{node.target.id}'."))
            self.visit(node.value)
            self._bind_target(node.target)

        def visit_For(self, node: ast.For) -> None:
            self.visit(node.iter)
            self._bind_target(node.target)
            for stmt in node.body:
                self.visit(stmt)
            for stmt in node.orelse:
                self.visit(stmt)

        def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
            self.visit_For(node)  # type: ignore[misc]

        def visit_With(self, node: ast.With) -> None:
            for item in node.items:
                self.visit(item.context_expr)
                if item.optional_vars is not None:
                    self._bind_target(item.optional_vars)
            for stmt in node.body:
                self.visit(stmt)

        def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
            self.visit_With(node)  # type: ignore[misc]

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name and isinstance(node.name, str):
                self._bind(node.name)
            for stmt in node.body:
                self.visit(stmt)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._bind(node.name)
            self.scope_stack.append({arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)})
            if node.args.vararg:
                self._bind(node.args.vararg.arg)
            if node.args.kwarg:
                self._bind(node.args.kwarg.arg)

            for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
                self._bind(arg.arg)

            for default in node.args.defaults + node.args.kw_defaults:
                if default is not None:
                    self.visit(default)

            if node.returns is not None:
                self.visit(node.returns)

            self.function_returns.append(_expr_text(node.returns) if node.returns else None)
            for stmt in node.body:
                self.visit(stmt)
            self.function_returns.pop()
            self.scope_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._bind(node.name)
            self.current_async_depth += 1
            self.visit_FunctionDef(node)  # type: ignore[misc]
            self.current_async_depth -= 1

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self._bind(node.name)
            self.scope_stack.append(set())
            for base in node.bases:
                self.visit(base)
            for keyword in node.keywords:
                if keyword.value is not None:
                    self.visit(keyword.value)
            for stmt in node.body:
                self.visit(stmt)
            self.scope_stack.pop()

        def visit_Return(self, node: ast.Return) -> None:
            ann = self.function_returns[-1] if self.function_returns else None
            if ann in {"None", "NoneType"} and node.value is not None:
                findings.append(RuleFinding("correctness", "medium", 8, "Function annotated to return None returns a value."))
            if ann not in {None, "None", "NoneType"} and node.value is None:
                findings.append(RuleFinding("correctness", "medium", 8, "Function annotated to return a value has a bare return."))
            if node.value is not None:
                self.visit(node.value)

        def visit_Call(self, node: ast.Call) -> None:
            name = _call_name(node.func)

            if name == "assert":
                findings.append(RuleFinding("correctness", "low", 4, "assert is not a runtime validation strategy."))

            if self.current_async_depth > 0 and name in BLOCKING_CALLS_IN_ASYNC:
                findings.append(RuleFinding("correctness", "high", 18, f"Blocking call '{name}' inside async code can stall the event loop."))

            self.generic_visit(node)

        def visit_Compare(self, node: ast.Compare) -> None:
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(comparator, ast.Constant) and comparator.value is None:
                    findings.append(RuleFinding("correctness", "low", 3, "Use 'is None' or 'is not None' instead of '== None'."))
            self.generic_visit(node)

        def visit_Try(self, node: ast.Try) -> None:
            if node.handlers:
                for handler in node.handlers:
                    if _is_bare_or_broad_except(handler):
                        findings.append(RuleFinding("correctness", "high", 20, "Broad exception handling can hide real bugs."))
                    if _looks_swallowed(handler):
                        findings.append(RuleFinding("correctness", "medium", 10, "Exception appears to be swallowed silently."))
            if not node.finalbody and _has_cleanup_keywords(node):
                findings.append(RuleFinding("correctness", "low", 6, "Try block suggests cleanup, but there is no finally clause."))
            for stmt in node.body:
                self.visit(stmt)
            for handler in node.handlers:
                if handler.type is not None:
                    self.visit(handler.type)
                for stmt in handler.body:
                    self.visit(stmt)
            for stmt in node.orelse:
                self.visit(stmt)
            for stmt in node.finalbody:
                self.visit(stmt)

        def visit_Assert(self, node: ast.Assert) -> None:
            findings.append(RuleFinding("correctness", "low", 4, "assert is not a runtime validation strategy."))
            self.generic_visit(node)

        def visit_Match(self, node: ast.Match) -> None:
            self.generic_visit(node)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            self.scope_stack.append(set())
            for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
                self._bind(arg.arg)
            if node.args.vararg:
                self._bind(node.args.vararg.arg)
            if node.args.kwarg:
                self._bind(node.args.kwarg.arg)
            self.visit(node.body)
            self.scope_stack.pop()

    Visitor().visit(tree)

    for name in sorted(imported - used):
        findings.append(RuleFinding("correctness", "low", 3, f"Imported name '{name}' appears unused."))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for default in list(node.args.defaults) + list(node.args.kw_defaults):
                if default is not None and _is_mutable_default(default):
                    findings.append(RuleFinding("correctness", "high", 18, "Mutable default argument can cause shared-state bugs."))
        elif isinstance(node, ast.AsyncFunctionDef):
            for default in list(node.args.defaults) + list(node.args.kw_defaults):
                if default is not None and _is_mutable_default(default):
                    findings.append(RuleFinding("correctness", "high", 18, "Mutable default argument can cause shared-state bugs."))

    return findings
