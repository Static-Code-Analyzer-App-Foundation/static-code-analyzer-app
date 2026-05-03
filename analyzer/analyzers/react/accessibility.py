from __future__ import annotations

import re
from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    # Missing alt text on images
    for match in re.finditer(r"<img\b([^<>]*?)(/?)>", text, re.S | re.I):
        attrs = match.group(1)
        if not re.search(r"\balt\s*=", attrs, re.I):
            findings.append(
                RuleFinding(
                    "accessibility",
                    "medium",
                    8,
                    "Image elements should include alt text.",
                )
            )

    # Missing labels on form controls
    for match in re.finditer(r"<(input|textarea|select)\b([^<>]*?)(/?)>", text, re.S | re.I):
        tag = match.group(1).lower()
        attrs = match.group(2)

        has_label_attr = bool(re.search(r"\b(aria-label|aria-labelledby|title)\s*=", attrs, re.I))
        has_id = bool(re.search(r"\bid\s*=", attrs, re.I))
        if not has_label_attr and not has_id:
            findings.append(
                RuleFinding(
                    "accessibility",
                    "medium",
                    8,
                    f"<{tag}> may be missing an accessible label.",
                )
            )

    # Clickable non-interactive elements without keyboard support
    for match in re.finditer(r"<(div|span|li|section|article|p)\b([^<>]*?)(/?)>", text, re.S | re.I):
        tag = match.group(1).lower()
        attrs = match.group(2)

        clickable = bool(re.search(r"\bonClick\s*=", attrs))
        has_role = bool(re.search(r"\brole\s*=\s*['\"]", attrs))
        has_keyboard = bool(re.search(r"\bon(KeyDown|KeyUp|KeyPress)\s*=", attrs))
        has_tabindex = bool(re.search(r"\btabIndex\s*=", attrs))

        if clickable and not (has_role and has_keyboard and has_tabindex):
            findings.append(
                RuleFinding(
                    "accessibility",
                    "high",
                    14,
                    f"<{tag}> is clickable but lacks keyboard and role support.",
                )
            )

    # Anchors used like buttons
    for match in re.finditer(r"<a\b([^<>]*?)(/?)>", text, re.S | re.I):
        attrs = match.group(1)
        if re.search(r"\bonClick\s*=", attrs) and not re.search(r"\bhref\s*=", attrs):
            findings.append(
                RuleFinding(
                    "accessibility",
                    "medium",
                    10,
                    "<a> with onClick but no href is not accessible by default.",
                )
            )

    # Button label issues
    if re.search(r"<button\b[^>]*>\s*<svg\b", text, re.S | re.I) and not re.search(r"\baria-label\s*=", text, re.I):
        findings.append(
            RuleFinding(
                "accessibility",
                "medium",
                10,
                "Icon-only buttons should have an accessible label.",
            )
        )

    return findings
