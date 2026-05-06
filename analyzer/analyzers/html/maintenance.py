from __future__ import annotations
import re
from ...rules import RuleFinding

_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.I | re.S)
_COMMENTED_BLOCK_RE = re.compile(r'<!--.*?-->', re.S)

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    script_blocks = _SCRIPT_RE.findall(text)
    style_blocks = _STYLE_RE.findall(text)
    total_inline = sum(len(block) for block in script_blocks) + sum(len(block) for block in style_blocks)

    if script_blocks and style_blocks and len(text) > 1500:
        findings.append(RuleFinding("maintenance", "medium", 8, "This file is mixing markup, style, and behavior in one place."))

    if len(script_blocks) >= 2:
        findings.append(RuleFinding("maintenance", "medium", 8, "Multiple inline scripts make reuse and testing harder."))
    if len(style_blocks) >= 2:
        findings.append(RuleFinding("maintenance", "medium", 8, "Multiple inline style blocks make design changes harder to manage."))

    if total_inline > 2500:
        findings.append(RuleFinding("maintenance", "medium", 8, "Large inline code blocks suggest the page should be split into modules."))

    if len(text.splitlines()) > 700:
        findings.append(RuleFinding("maintenance", "medium", 8, "Very large HTML files are difficult to maintain safely."))

    if _COMMENTED_BLOCK_RE.search(text) and re.search(r'<!--\s*(?:TODO|FIXME|HACK)\b', text, re.I):
        findings.append(RuleFinding("maintenance", "low", 4, "Commented-out TODO/FIXME/HACK blocks should be cleaned up."))

    if re.search(r'\b(?:box1|box2|temp\d+|newDiv|data1|item1|stuff|test\d*)\b', text, re.I):
        findings.append(RuleFinding("maintenance", "low", 4, "Naming looks vague in places; descriptive names scale better."))

    if len(re.findall(r'\b(?:function|const|let|var)\b', text)) >= 15 and len(text) > 2000:
        findings.append(RuleFinding("maintenance", "medium", 8, "This file contains a lot of logic and should be split into smaller units."))

    return findings
