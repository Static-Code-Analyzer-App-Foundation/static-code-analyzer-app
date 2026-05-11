from __future__ import annotations

import ast
import re
from collections.abc import Iterable

from ...rules import RuleFinding

SUSPICIOUS_SECRET_NAMES = ("password", "passwd", "pwd", "secret", "token", "apikey", "api_key", "private_key")
BLOCKING_SHELL_NAMES = {"eval", "exec", "os.system"}
SENSITIVE_LOG_FUNCS = {"print", "logging.debug", "logging.info", "logging.warning", "logging.error", "logging.critical"}


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


def _target_names(target: ast.AST) -> Iterable[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            yield from _target_names(elt)


def _is_taint_source(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        name = _call_name(node.func)
        if name == "input":
            return True
        if name in {"request.get_json", "request.json", "request.form.get", "request.args.get", "request.headers.get"}:
            return True
    if isinstance(node, ast.Attribute):
        text = _expr_text(node)
        if text in {"sys.argv", "os.environ"}:
            return True
    if isinstance(node, ast.Subscript):
        text = _expr_text(node.value)
        if text in {"sys.argv", "os.environ"}:
            return True
        if text.startswith("request."):
            return True
    return False


def _contains_tainted_name(node: ast.AST, tainted: set[str]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in tainted:
            return True
    return False


def _is_shelly_string(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return any(tok in node.value for tok in (";", "&&", "|", "`", "$(", ">", "<"))
    return False


def _secrets_in_text(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    patterns = [
        (r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key)\s*=\s*['\"][^'\"]{8,}['\"]", 18),
        (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", 30),
    ]
    for pattern, impact in patterns:
        if re.search(pattern, text):
            findings.append(RuleFinding("security", "high" if impact >= 25 else "medium", impact, "Possible secret exposure in source code."))

    if re.search(r"(?i)\b(password|secret|token|api[_-]?key)\b.*\b(print|logger\.)", text):
        findings.append(RuleFinding("security", "medium", 12, "Sensitive values may be logged or printed."))

    return findings


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    findings.extend(_secrets_in_text(text))

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings

    tainted: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            if _is_taint_source(node.value):
                for target in node.targets:
                    for name in _target_names(target):
                        tainted.add(name)
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if node.value is not None and _is_taint_source(node.value):
                for name in _target_names(node.target):
                    tainted.add(name)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            name = _call_name(node.func)

            if name == "eval":
                findings.append(RuleFinding("security", "high", 30, "Use of eval can execute arbitrary code."))
            elif name == "exec":
                findings.append(RuleFinding("security", "high", 30, "Use of exec can execute arbitrary code."))
            elif name in {"pickle.load", "pickle.loads"}:
                findings.append(RuleFinding("security", "high", 25, "Unsafe pickle deserialization can lead to code execution."))
            elif name == "yaml.load":
                findings.append(RuleFinding("security", "high", 20, "yaml.load without SafeLoader is risky."))
            elif name in {"os.system", "subprocess.run", "subprocess.call", "subprocess.Popen"}:
                if name == "os.system" or any(kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in node.keywords):
                    findings.append(RuleFinding("security", "high", 35, "shell=True or os.system can enable command injection."))
                if node.args and _contains_tainted_name(node.args[0], tainted):
                    findings.append(RuleFinding("security", "high", 28, "Tainted input reaches a shell command."))
                if node.args and _is_shelly_string(node.args[0]):
                    findings.append(RuleFinding("security", "medium", 16, "Suspicious shell command string detected."))
            elif name == "open" or name.endswith(".write_text") or name.endswith(".write_bytes") or name.endswith(".unlink") or name.endswith(".rename") or name.endswith(".replace"):
                if node.args and _contains_tainted_name(node.args[0], tainted):
                    findings.append(RuleFinding("security", "high", 20, "Untrusted file path used in file operation."))
            elif name.endswith(".execute") or name.endswith(".executemany") or name.endswith(".query"):
                if any(_contains_tainted_name(arg, tainted) for arg in node.args):
                    findings.append(RuleFinding("security", "high", 22, "Tainted input reaches a database call without validation."))
            elif name.startswith("requests.") or name in {"urllib.request.urlopen", "http.client.HTTPConnection.request"}:
                if any(_contains_tainted_name(arg, tainted) for arg in node.args):
                    findings.append(RuleFinding("security", "medium", 16, "Unvalidated input reaches a network call."))

            if name in SENSITIVE_LOG_FUNCS or name.startswith("logger."):
                text_repr = " ".join(_expr_text(arg) for arg in node.args)
                if re.search(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\b", text_repr):
                    findings.append(RuleFinding("security", "medium", 12, "Sensitive data may be logged or printed."))
                if any(_contains_tainted_name(arg, tainted) for arg in node.args):
                    findings.append(RuleFinding("security", "low", 6, "Potentially sensitive user input is being logged."))

            self.generic_visit(node)

        def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
            text_repr = _expr_text(node)
            if re.search(r"(?i)\b(password|secret|token|api[_-]?key)\b", text_repr):
                findings.append(RuleFinding("security", "low", 4, "Sensitive-looking value may be interpolated into a string."))
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            text_repr = _expr_text(node)
            if re.search(r"(?i)\b(password|secret|token|api[_-]?key)\b", text_repr):
                findings.append(RuleFinding("security", "low", 4, "Sensitive-looking credential access found in code."))
            self.generic_visit(node)

    Visitor().visit(tree)

    # Path traversal heuristic for joins
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            call = _call_name(node.func)
            if call in {"os.path.join", "pathlib.Path.joinpath", "Path.joinpath"}:
                args_text = " ".join(_expr_text(arg) for arg in node.args)
                if ".." in args_text or any(name in args_text for name in ("input", "request", "argv", "form", "json")):
                    findings.append(RuleFinding("security", "high", 20, "Unsafe path join may allow path traversal."))

    return findings
