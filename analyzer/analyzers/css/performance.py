from __future__ import annotations

import re

from cssselect2.parser import SelectorError, parse as parse_selector
from tinycss2 import parse_declaration_list, serialize
from tinycss2.ast import AtRule, Declaration, ParseError, QualifiedRule

from ...rules import RuleFinding
from .css_common import iter_css_nodes, make_finding, normalize_value, snippet_for_line

_HEAVY_EFFECT_RE = re.compile(r"(backdrop-filter|filter)\s*:", re.I)
_TRANSITION_ALL_RE = re.compile(r"transition(?:-property)?\s*:\s*all\b", re.I)
_WILL_CHANGE_RE = re.compile(r"will-change\s*:\s*[^;]+", re.I)
_LAYOUT_ANIM_RE = re.compile(r"\b(?:top|left|right|bottom|width|height|margin|padding|inset|font-size|line-height)\b", re.I)
_BOX_SHADOW_SPLIT_RE = re.compile(r"box-shadow\s*:\s*([^;]+)", re.I)
_UNIVERSAL_SELECTOR_RE = re.compile(r"(^|[,\s>+~])\*(?=($|[,\s>+~.:#\[]))")

def _selector_depth(selector: str) -> int:
    selector = re.sub(r"\[[^\]]*\]", "", selector)
    selector = re.sub(r"\([^)]*\)", "", selector)
    return len(re.findall(r"\s+|[>+~]", selector))

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    for node, abs_line, _ in iter_css_nodes(text):
        if isinstance(node, ParseError):
            continue

        if isinstance(node, QualifiedRule):
            selector = serialize(node.prelude).strip()
            if _UNIVERSAL_SELECTOR_RE.search(selector):
                findings.append(
                    make_finding(
                        "performance",
                        "low",
                        4,
                        "Universal selector can be expensive on large DOMs.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.9,
                        fix="Target a narrower selector when possible.",
                    )
                )

            if ":has(" in selector.lower():
                findings.append(
                    make_finding(
                        "performance",
                        "warning",
                        9,
                        "`:has()` selectors can be expensive.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.88,
                        fix="Use `:has()` sparingly and only where the payoff is clear.",
                    )
                )

            depth = _selector_depth(selector)
            if depth > 4:
                findings.append(
                    make_finding(
                        "performance",
                        "warning",
                        9,
                        "Deep selector chains can slow matching and make styles brittle.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.88,
                        fix="Flatten the selector structure and favor component-scoped classes.",
                    )
                )

            decl_text = serialize(node.content)

            if _HEAVY_EFFECT_RE.search(decl_text):
                findings.append(
                    make_finding(
                        "performance",
                        "warning",
                        10,
                        "Filter/backdrop-filter can be expensive to render.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.91,
                        fix="Avoid large blurred or backdrop-filtered surfaces unless necessary.",
                    )
                )

            if _TRANSITION_ALL_RE.search(decl_text):
                findings.append(
                    make_finding(
                        "performance",
                        "warning",
                        8,
                        "`transition: all` can trigger extra repaints and make intent unclear.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.93,
                        fix="Animate only the properties that need to change.",
                    )
                )

            if _WILL_CHANGE_RE.search(decl_text):
                findings.append(
                    make_finding(
                        "performance",
                        "info",
                        4,
                        "`will-change` should be used sparingly.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.88,
                        fix="Remove `will-change` unless it is measured and temporary.",
                    )
                )

            m = _BOX_SHADOW_SPLIT_RE.search(decl_text)
            if m:
                value = normalize_value(m.group(1))
                if value.count(",") >= 2:
                    findings.append(
                        make_finding(
                            "performance",
                            "low",
                            4,
                            "Stacked box-shadows can be expensive to paint.",
                            line=abs_line,
                            snippet=snippet_for_line(text, abs_line),
                            confidence=0.84,
                            fix="Reduce the number and blur radius of shadows.",
                        )
                    )
                if re.search(r"(\d+)(px|rem|em)\s+(\d+)(px|rem|em)\s+(\d+)(px|rem|em)", value):
                    try:
                        blur = float(re.findall(r"(\d+(?:\.\d+)?)px", value)[2])
                        if blur >= 32:
                            findings.append(
                                make_finding(
                                    "performance",
                                    "info",
                                    4,
                                    "Large blur radii can increase paint cost.",
                                    line=abs_line,
                                    snippet=snippet_for_line(text, abs_line),
                                    confidence=0.78,
                                    fix="Use smaller blur radii where the design allows.",
                                )
                            )
                    except Exception:
                        pass

            if _LAYOUT_ANIM_RE.search(decl_text) and ("transition:" in decl_text.lower() or "animation:" in decl_text.lower()):
                findings.append(
                    make_finding(
                        "performance",
                        "warning",
                        9,
                        "Animating layout-affecting properties can force reflow.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.89,
                        fix="Animate transform and opacity instead of geometry when possible.",
                    )
                )

    return findings
