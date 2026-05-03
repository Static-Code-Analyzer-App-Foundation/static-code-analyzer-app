from __future__ import annotations

import re
from ...rules import RuleFinding


def _collect_state_pairs(text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    pattern = re.compile(
        r"\bconst\s*\[\s*([A-Za-z_$][\w$]*)\s*,\s*([A-Za-z_$][\w$]*)\s*\]\s*=\s*useState\s*\((.*?)\)",
        re.S,
    )
    for match in pattern.finditer(text):
        state_var = match.group(1)
        setter = match.group(2)
        initializer = match.group(3).strip()
        pairs[state_var] = setter
    return pairs


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    state_pairs = _collect_state_pairs(text)

    # Derived state misuse
    derived_patterns = [
        r"useState\s*\(\s*props\.[^)]+\)",
        r"useState\s*\(\s*.*\b(filter|map|reduce|sort|slice)\s*\(",
        r"useState\s*\(\s*.*\bJSON\.stringify\s*\(",
    ]
    for pattern in derived_patterns:
        if re.search(pattern, text, re.S):
            findings.append(
                RuleFinding(
                    "state",
                    "medium",
                    10,
                    "State looks derived from props or computed data. Derived state often causes sync bugs.",
                )
            )
            break

    # More specific: derived state from props assignment
    if re.search(r"const\s*\[\s*[A-Za-z_$][\w$]*\s*,\s*[A-Za-z_$][\w$]*\s*\]\s*=\s*useState\s*\(\s*props\.", text, re.S):
        findings.append(
            RuleFinding(
                "state",
                "high",
                14,
                "State is initialized directly from props. That can drift out of sync.",
            )
        )

    # Stale state patterns
    for state_var, setter in state_pairs.items():
        if re.search(rf"\b{re.escape(setter)}\s*\(\s*{re.escape(state_var)}\s*[\+\-]\s*1\s*\)", text):
            findings.append(
                RuleFinding(
                    "state",
                    "medium",
                    12,
                    f"{setter} updates {state_var} from a captured value. Use a functional update instead.",
                )
            )
        if re.search(rf"\b{re.escape(setter)}\s*\(\s*!\s*{re.escape(state_var)}\s*\)", text):
            findings.append(
                RuleFinding(
                    "state",
                    "low",
                    5,
                    f"{setter} toggles {state_var} directly. Confirm it is not stale inside async logic.",
                )
            )

    # Unnecessary rerender clues
    if re.search(r"\bset[A-Z][A-Za-z0-9_]*\s*\(", text) and re.search(r"return\s*\(", text, re.S):
        if re.search(r"\bset[A-Z][A-Za-z0-9_]*\s*\(", text.split("return", 1)[0]):
            findings.append(
                RuleFinding(
                    "state",
                    "low",
                    6,
                    "State update appears before render return. Check for render-loop or unnecessary rerender risk.",
                )
            )

    return findings
