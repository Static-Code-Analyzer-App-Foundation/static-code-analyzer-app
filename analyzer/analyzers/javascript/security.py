from __future__ import annotations

import re

from ...rules import RuleFinding

CHECKS = [
    (r"\beval\s*\(", 25, "eval can execute arbitrary code."),
    (r"\bnew Function\s*\(", 25, "new Function can execute arbitrary code."),
    (r"\bset(?:Timeout|Interval)\s*\(\s*['\"]", 20, "String-based timers behave like dynamic code execution."),
    (r"\bdocument\.write\s*\(", 15, "document.write is brittle and unsafe in modern code."),
    (r"\binnerHTML\s*=", 20, "innerHTML assignments can create XSS risk."),
    (r"\bouterHTML\s*=", 20, "outerHTML assignments can create XSS risk."),
    (r"\binsertAdjacentHTML\s*\(", 20, "insertAdjacentHTML can create XSS risk if the input is not sanitized."),
    (r"\bDOMParser\s*\(", 8, "DOMParser output should be treated as untrusted until sanitized."),
]

UNTRUSTED_SOURCE_RE = re.compile(
    r"(location\.search|location\.hash|document\.cookie|localStorage\.|sessionStorage\.|"
    r"req\.(?:body|query|params)|event\.target\.value|\binput\.value\b|\bformData\.get\s*\()"
)

SINK_RE = re.compile(
    r"(innerHTML\s*=|outerHTML\s*=|insertAdjacentHTML\s*\(|document\.write\s*\(|"
    r"querySelector(?:All)?\s*\(|fetch\s*\(|axios\.)"
)

SANITIZER_RE = re.compile(
    r"(DOMPurify|sanitize|escapeHTML|encodeURIComponent|encodeURI|textContent|createTextNode|URLSearchParams)"
)

PROTOTYPE_MERGE_RE = re.compile(
    r"(?:Object\.assign\s*\(|\.\.\.\s*(?:req\.(?:body|query|params)|body|query|params|data|payload)|"
    r"\b(?:merge|extend)\s*\(|\b_.merge\s*\()"
)


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    for pattern, impact, msg in CHECKS:
        for _ in re.finditer(pattern, text):
            findings.append(
                RuleFinding(
                    "security",
                    "high" if impact >= 20 else "medium",
                    impact,
                    msg,
                )
            )

    if UNTRUSTED_SOURCE_RE.search(text) and SINK_RE.search(text) and not SANITIZER_RE.search(text):
        findings.append(
            RuleFinding(
                "security",
                "high",
                18,
                "Untrusted input appears to flow into DOM, query, or API sinks without visible sanitization.",
            )
        )

    if re.search(r"\b__proto__\b|\bprototype\b|\bconstructor\b", text) and PROTOTYPE_MERGE_RE.search(text):
        findings.append(
            RuleFinding(
                "security",
                "high",
                18,
                "Unsafe object merging can create prototype pollution risk.",
            )
        )

    if re.search(r"\bcreateElement\s*\(\s*['\"]script['\"]\s*\)", text) and re.search(r"\b(?:src|text|textContent)\s*=", text):
        findings.append(
            RuleFinding(
                "security",
                "high",
                16,
                "Dynamic script creation should be tightly controlled and validated.",
            )
        )

    if re.search(r"\bsetAttribute\s*\(\s*['\"](?:src|href|action|formAction|style|on\w+)['\"]", text):
        findings.append(
            RuleFinding(
                "security",
                "medium",
                10,
                "Attribute assignment can become dangerous when it is fed by user-controlled data.",
            )
        )

    return findings
