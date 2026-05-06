from __future__ import annotations

import json
import re
from pathlib import Path

from ...rules import RuleFinding


def _manifest_findings(data: dict) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    sections = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")

    for section in sections:
        deps = data.get(section, {})
        if not isinstance(deps, dict):
            continue

        for pkg, version in deps.items():
            if not isinstance(version, str):
                continue

            v = version.strip()

            if v in {"*", "latest"}:
                findings.append(
                    RuleFinding(
                        "dependency",
                        "medium",
                        8,
                        f"'{pkg}' uses an unpinned version range ({v}); this makes builds less predictable.",
                    )
                )
                continue

            if v.startswith(("file:", "link:", "git+", "github:", "http://", "https://")):
                findings.append(
                    RuleFinding(
                        "dependency",
                        "medium",
                        9,
                        f"'{pkg}' is sourced from a non-registry reference; review supply-chain risk.",
                    )
                )
                continue

            if v.startswith("0.") or v.startswith("^0.") or v.startswith("~0."):
                findings.append(
                    RuleFinding(
                        "dependency",
                        "low",
                        5,
                        f"'{pkg}' is on a 0.x version line; verify maturity and compatibility carefully.",
                    )
                )

            if re.search(r"[<>]=?", v):
                findings.append(
                    RuleFinding(
                        "dependency",
                        "medium",
                        7,
                        f"'{pkg}' uses a version constraint that may hide old or incompatible releases.",
                    )
                )

    if not data.get("packageManager"):
        findings.append(
            RuleFinding(
                "dependency",
                "low",
                3,
                "No packageManager field found; pinning the package manager can reduce install drift.",
            )
        )

    return findings


def analyze(path: Path, text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    name = path.name.lower()

    if name == "package.json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            findings.append(
                RuleFinding(
                    "dependency",
                    "medium",
                    8,
                    "package.json is not valid JSON, so dependency checks cannot be trusted.",
                )
            )
            return findings

        if isinstance(data, dict):
            findings.extend(_manifest_findings(data))

    elif name in {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml"}:
        if re.search(r"\bhttp://", text):
            findings.append(
                RuleFinding(
                    "dependency",
                    "medium",
                    8,
                    "Lockfile references an insecure HTTP source; prefer HTTPS-based registries.",
                )
            )

        if name.endswith(".json") and "\"integrity\"" not in text:
            findings.append(
                RuleFinding(
                    "dependency",
                    "low",
                    4,
                    "Lockfile does not appear to contain integrity data; verify package provenance.",
                )
            )

    else:
        if re.search(r"(?:import\s+.*?from\s+|require\s*\(|import\s*\()\s*['\"]https?://", text):
            findings.append(
                RuleFinding(
                    "dependency",
                    "medium",
                    9,
                    "Remote URL imports or requires are risky and should be reviewed carefully.",
                )
            )

        if re.search(r"require\s*\(\s*['\"].*\/\.\./", text):
            findings.append(
                RuleFinding(
                    "dependency",
                    "low",
                    4,
                    "Relative dependency paths are fragile; prefer managed package imports where possible.",
                )
            )

    return findings
