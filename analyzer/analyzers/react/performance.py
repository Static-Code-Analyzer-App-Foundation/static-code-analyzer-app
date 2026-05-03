from __future__ import annotations

import re
from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    # list key issues
    if re.search(r"\.map\s*\([\s\S]{0,400}?\bkey\s*=\s*\{\s*(index|i|idx)\s*\}", text, re.S):
        findings.append(
            RuleFinding(
                "performance",
                "medium",
                10,
                "Using an index as a list key can break reconciliation and cause extra rerenders.",
            )
        )

    # missing memoization hints
    large_component = len(text.splitlines()) > 250 or len(re.findall(r"<[A-Z][A-Za-z0-9_]*\b", text)) > 20
    expensive_render = re.search(r"\.map\s*\(", text) or re.search(r"\.filter\s*\(", text) or re.search(r"\.reduce\s*\(", text)

    has_memo = bool(re.search(r"\bReact\.memo\b|\bmemo\s*\(", text))
    has_memo_hooks = bool(re.search(r"\buseMemo\s*\(|\buseCallback\s*\(", text))

    if large_component and expensive_render and not (has_memo or has_memo_hooks):
        findings.append(
            RuleFinding(
                "performance",
                "low",
                6,
                "This render looks large and expensive. Memoization may help if the component rerenders often.",
            )
        )

    # inline object / function props
    if re.search(r"\bstyle\s*=\s*\{\s*\{", text) or re.search(r"\bon[A-Z][A-Za-z0-9_]*\s*=\s*\{\s*\(?.*?=>", text, re.S):
        findings.append(
            RuleFinding(
                "performance",
                "low",
                5,
                "Inline object or function props can trigger extra rerenders in child components.",
            )
        )

    # very heavy JSX block
    if len(text.splitlines()) > 400:
        findings.append(
            RuleFinding(
                "performance",
                "medium",
                8,
                "Very large React files often hide expensive renders and repeated work.",
            )
        )

    return findings
