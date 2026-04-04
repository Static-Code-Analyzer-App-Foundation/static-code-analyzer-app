from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    img_tags = re.findall(r"<img\b[^>]*>", text, re.I)
    for tag in img_tags:
        if not re.search(r"alt\s*=", tag, re.I):
            findings.append(RuleFinding("accessibility", "high", 15, "Image tag missing alt text."))
            break
    if not re.search(r"<html\b[^>]*lang\s*=", text, re.I):
        findings.append(RuleFinding("accessibility", "medium", 10, "HTML root should declare a lang attribute."))
    if not re.search(r"<meta\b[^>]*name\s*=\s*['\"]viewport['\"]", text, re.I):
        findings.append(RuleFinding("accessibility", "medium", 10, "Viewport meta tag is missing for responsive layout support."))
    return findings
