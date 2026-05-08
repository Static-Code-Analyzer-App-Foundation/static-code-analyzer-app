from __future__ import annotations

import re

from tinycss2 import serialize
from tinycss2.ast import AtRule, Declaration, ParseError, QualifiedRule

from ...rules import RuleFinding
from .css_common import iter_css_nodes, make_finding, snippet_for_line, line_for_index

_JS_URL_RE = re.compile(r"url\s*\(\s*['\"]?\s*(?:javascript|vbscript)\s*:", re.I)
_DATA_HTML_RE = re.compile(r"url\s*\(\s*['\"]?\s*data\s*:\s*text/html", re.I)
_EXPRESSION_RE = re.compile(r"\bexpression\s*\(", re.I)
_IMPORT_HTTP_RE = re.compile(r"@import\s+(?:url\()?\s*['\"]?https?://", re.I)
_IMPORT_REMOTE_RE = re.compile(r"@import\s+(?:url\()?\s*['\"]?//", re.I)
_MOZ_BINDING_RE = re.compile(r"-moz-binding\s*:", re.I)
_BEHAVIOR_RE = re.compile(r"\bbehavior\s*:", re.I)

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    for node, abs_line, _ in iter_css_nodes(text):
        if isinstance(node, ParseError):
            continue

        if isinstance(node, AtRule):
            at_name = (getattr(node, "at_keyword", "") or "").lower()
            prelude = serialize(node.prelude).strip()
            if at_name == "import" and (_IMPORT_HTTP_RE.search(prelude) or _IMPORT_REMOTE_RE.search(prelude)):
                findings.append(
                    make_finding(
                        "security",
                        "warning",
                        12,
                        "Remote `@import` can create performance and supply-chain risk.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.9,
                        fix="Prefer local bundling or explicit trusted sources.",
                    )
                )

        if isinstance(node, QualifiedRule):
            decl_text = serialize(node.content)
            selector = serialize(node.prelude).strip()

            if _EXPRESSION_RE.search(decl_text):
                findings.append(
                    make_finding(
                        "security",
                        "error",
                        20,
                        "Legacy CSS `expression()` is unsafe and obsolete.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.99,
                        fix="Remove `expression()` and replace it with safe CSS or JavaScript logic.",
                    )
                )

            if _JS_URL_RE.search(decl_text) or _DATA_HTML_RE.search(decl_text):
                findings.append(
                    make_finding(
                        "security",
                        "error",
                        20,
                        "Unsafe URL scheme detected in CSS.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.98,
                        fix="Remove `javascript:` or `data:text/html` URLs from CSS.",
                    )
                )

            if _MOZ_BINDING_RE.search(decl_text) or _BEHAVIOR_RE.search(decl_text):
                findings.append(
                    make_finding(
                        "security",
                        "warning",
                        12,
                        "Legacy browser binding behavior can be abused or break compatibility.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.93,
                        fix="Remove obsolete browser-specific behavior rules.",
                    )
                )

            if "url(" in decl_text.lower() and "javascript:" in decl_text.lower():
                findings.append(
                    make_finding(
                        "security",
                        "error",
                        20,
                        "Potential JavaScript URL injection inside `url()`.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.98,
                        fix="Sanitize any user-controlled URL inputs before they reach CSS.",
                    )
                )

    if "@import" in text and re.search(r"@import\s+url\(\s*['\"]?https?://", text, re.I):
        line = line_for_index(text, re.search(r"@import", text, re.I).start())
        findings.append(
            make_finding(
                "security",
                "warning",
                10,
                "External stylesheet imports can expand the attack surface.",
                line=line,
                snippet=snippet_for_line(text, line),
                confidence=0.86,
                fix="Bundle trusted CSS locally whenever possible.",
            )
        )

    return findings
