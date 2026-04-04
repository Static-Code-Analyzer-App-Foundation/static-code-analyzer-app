from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"<style\b", text, re.I):
        findings.append(RuleFinding("maintenance", "medium", 8, "Inline style blocks are harder to maintain at scale."))
    if re.search(r"<script\b", text, re.I):
        findings.append(RuleFinding("maintenance", "medium", 8, "Inline scripts are harder to reuse and test."))
    if len(text.splitlines()) > 500:
        findings.append(RuleFinding("maintenance", "medium", 8, "Very large HTML files are difficult to manage."))
    return findings
