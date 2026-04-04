from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    patterns = [
        (r"\beval\s*\(", "Use of eval can execute arbitrary code.", 30),
        (r"\bexec\s*\(", "Use of exec can execute arbitrary code.", 30),
        (r"subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True", "shell=True can enable command injection.", 35),
        (r"pickle\.(load|loads)\s*\(", "Unsafe pickle deserialization can lead to code execution.", 25),
        (r"yaml\.load\s*\(", "yaml.load without safe loader is risky.", 20),
        (r"os\.system\s*\(", "os.system can be dangerous with untrusted input.", 20),
    ]
    for pattern, message, impact in patterns:
        for _ in re.finditer(pattern, text):
            findings.append(RuleFinding("security", "high" if impact >= 25 else "medium", impact, message))
    return findings
