from __future__ import annotations

import re
from collections import Counter

from cssselect2.parser import SelectorError, parse as parse_selector
from tinycss2 import parse_declaration_list, serialize
from tinycss2.ast import AtRule, Declaration, ParseError, QualifiedRule

from ...rules import RuleFinding
from .css_common import (
    COMMON_CSS_PROPERTIES,
    css_properties_close_match,
    iter_css_nodes,
    line_for_index,
    make_finding,
    normalize_value,
    parse_length,
    snippet_for_line,
    is_vendor_or_custom_property,
)

_KEYFRAME_SELECTOR_RE = re.compile(r"^(?:from|to|\d{1,3}%)(?:\s*,\s*(?:from|to|\d{1,3}%))*$", re.I)
_COMBINATOR_RE = re.compile(r"\s+|[>+~]")
_UNSAFE_FOCUS_RE = re.compile(r"outline\s*:\s*(none|0)\b|outline-style\s*:\s*none\b|box-shadow\s*:\s*none\b", re.I)
_FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([^;]+)", re.I)
_LINE_HEIGHT_RE = re.compile(r"line-height\s*:\s*([^;]+)", re.I)

def _rule_line(node, abs_line: int, text: str) -> int:
    return abs_line

def _analyze_declarations(text: str, decl_text: str, abs_line: int, selector: str, findings: list[RuleFinding], in_keyframes: bool) -> None:
    decls = parse_declaration_list(decl_text, skip_whitespace=True, skip_comments=True)
    seen: dict[str, list[str]] = {}
    properties = []
    important_count = 0

    for decl in decls:
        if isinstance(decl, ParseError):
            line = abs_line + getattr(decl, "source_line", 1) - 1
            findings.append(
                make_finding(
                    "style",
                    "error",
                    18,
                    f"Invalid CSS declaration syntax: {getattr(decl, 'message', 'parse error')}",
                    line=line,
                    snippet=snippet_for_line(text, line),
                    confidence=0.97,
                    fix="Check missing colons, semicolons, braces, or stray characters.",
                )
            )
            continue

        if not isinstance(decl, Declaration):
            continue

        name = decl.name.lower()
        value = normalize_value(serialize(decl.value).strip())
        line = abs_line + decl.source_line - 1
        snippet = snippet_for_line(text, line)
        properties.append(name)

        if decl.important:
            important_count += 1

        if not (is_vendor_or_custom_property(name) or name in COMMON_CSS_PROPERTIES):
            close = css_properties_close_match(name)
            if close:
                findings.append(
                    make_finding(
                        "style",
                        "warning",
                        10,
                        f"Possible invalid CSS property `{name}`; did you mean `{close}`?",
                        line=line,
                        snippet=snippet,
                        confidence=0.91,
                        fix=f"Rename `{name}` to `{close}`.",
                    )
                )
            else:
                findings.append(
                    make_finding(
                        "style",
                        "info",
                        4,
                        f"Unrecognized CSS property `{name}`.",
                        line=line,
                        snippet=snippet,
                        confidence=0.68,
                    )
                )

        seen.setdefault(name, []).append(value)

        if name == "font-size":
            size = parse_length(value)
            if size and size[1] == "px" and size[0] < 14:
                findings.append(
                    make_finding(
                        "accessibility",
                        "warning",
                        9,
                        f"Font size `{value}` may be too small for comfortable reading.",
                        line=line,
                        snippet=snippet,
                        confidence=0.86,
                        fix="Use at least 14px for body text or use a responsive scale.",
                    )
                )

        if name == "line-height":
            try:
                if re.fullmatch(r"\d*\.?\d+", value) and float(value) < 1.2:
                    findings.append(
                        make_finding(
                            "accessibility",
                            "warning",
                            8,
                            f"Line height `{value}` is very tight.",
                            line=line,
                            snippet=snippet,
                            confidence=0.82,
                            fix="Increase line-height to around 1.4–1.6 for body text.",
                        )
                    )
            except Exception:
                pass

        if name in {"width", "min-width", "max-width"}:
            size = parse_length(value)
            if size and size[1] == "px" and size[0] >= 600:
                findings.append(
                    make_finding(
                        "layout",
                        "warning",
                        10,
                        f"Fixed width `{value}` can trap responsive layouts.",
                        line=line,
                        snippet=snippet,
                        confidence=0.84,
                        fix="Use fluid units, max-width, or responsive breakpoints.",
                    )
                )
            if "100vw" in value:
                findings.append(
                    make_finding(
                        "layout",
                        "warning",
                        8,
                        f"`{name}: {value}` can cause horizontal overflow on mobile.",
                        line=line,
                        snippet=snippet,
                        confidence=0.81,
                        fix="Prefer `width: 100%` with appropriate max-width and box sizing.",
                    )
                )

        if name == "height" and "100vh" in value:
            findings.append(
                make_finding(
                    "layout",
                    "info",
                    5,
                    "`100vh` can behave badly on mobile browser chrome.",
                    line=line,
                    snippet=snippet,
                    confidence=0.75,
                    fix="Consider `100dvh` or a safer responsive container height.",
                )
            )

        if name in {"overflow", "overflow-x"} and "hidden" in value:
            if any(token in selector.lower() for token in ("html", "body", "#app", "#root")):
                findings.append(
                    make_finding(
                        "layout",
                        "warning",
                        8,
                        f"`{name}: hidden` on a root container can clip content.",
                        line=line,
                        snippet=snippet,
                        confidence=0.84,
                        fix="Use overflow clipping only where the clipping is intentional.",
                    )
                )

        if name == "outline" and ("none" in value or value == "0"):
            findings.append(
                make_finding(
                    "accessibility",
                    "error",
                    15,
                    "Focus outline is removed without a visible replacement.",
                    line=line,
                    snippet=snippet,
                    confidence=0.96,
                    fix="Add a visible focus style using `:focus-visible` or an accessible outline.",
                )
            )

        if name == "box-shadow" and value == "none" and ":focus" in selector.lower():
            findings.append(
                make_finding(
                    "accessibility",
                    "warning",
                    8,
                    "Focus state appears visually muted.",
                    line=line,
                    snippet=snippet,
                    confidence=0.82,
                    fix="Add a clear focus ring or outline for keyboard users.",
                )
            )

    if len(seen) != len(properties):
        for prop, vals in seen.items():
            if len(vals) > 1:
                unique_vals = list(dict.fromkeys(vals))
                if len(unique_vals) > 1:
                    findings.append(
                        make_finding(
                            "maintenance",
                            "warning",
                            9,
                            f"Duplicate declaration `{prop}` with conflicting values in the same rule.",
                            line=abs_line,
                            snippet=snippet_for_line(text, abs_line),
                            confidence=0.92,
                            fix="Keep one declaration per property unless the override is deliberate.",
                        )
                    )
                else:
                    findings.append(
                        make_finding(
                            "maintenance",
                            "info",
                            3,
                            f"Duplicate declaration `{prop}` repeated in the same rule.",
                            line=abs_line,
                            snippet=snippet_for_line(text, abs_line),
                            confidence=0.88,
                            fix="Remove the duplicate declaration.",
                        )
                    )

    if important_count >= 3:
        findings.append(
            make_finding(
                "maintenance",
                "warning",
                9,
                f"`!important` appears {important_count} times in one rule.",
                line=abs_line,
                snippet=snippet_for_line(text, abs_line),
                confidence=0.88,
                fix="Reduce `!important` usage and refactor specificity instead.",
            )
        )

    if selector.lower().find(":focus") >= 0 and _UNSAFE_FOCUS_RE.search(decl_text):
        findings.append(
            make_finding(
                "accessibility",
                "error",
                15,
                "Focusable element removes visible focus styling.",
                line=abs_line,
                snippet=snippet_for_line(text, abs_line),
                confidence=0.97,
                fix="Keep a clear `:focus-visible` treatment with outline or ring.",
            )
        )

    if ("color" in seen or "background-color" in seen or "background" in seen) and len(seen) >= 2:
        fg = None
        bg = None
        if "color" in seen:
            fg = seen["color"][-1]
        if "background-color" in seen:
            bg = seen["background-color"][-1]
        elif "background" in seen:
            bg = seen["background"][-1]
        if fg and bg:
            from .css_common import parse_css_color, contrast_ratio

            fg_color = parse_css_color(fg)
            bg_color = parse_css_color(bg)
            if fg_color and bg_color:
                ratio = contrast_ratio(fg_color, bg_color)
                if ratio is not None and ratio < 4.5:
                    findings.append(
                        make_finding(
                            "accessibility",
                            "warning",
                            12,
                            f"Low contrast risk detected ({ratio:.2f}:1).",
                            line=abs_line,
                            snippet=snippet_for_line(text, abs_line),
                            confidence=0.91,
                            fix="Increase the contrast ratio to at least 4.5:1 for normal text.",
                        )
                    )

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if "\t" in text:
        findings.append(
            make_finding(
                "style",
                "low",
                2,
                "Tabs are used in CSS indentation.",
                line=text.find("\t") + 1,
                snippet=text.splitlines()[line_for_index(text, text.find("\t")) - 1].strip() if "\n" in text else text.strip(),
                confidence=0.9,
                fix="Use spaces for consistent indentation.",
            )
        )

    for node, abs_line, in_keyframes in iter_css_nodes(text):
        if isinstance(node, ParseError):
            findings.append(
                make_finding(
                    "style",
                    "error",
                    18,
                    f"CSS parse error: {getattr(node, 'message', 'invalid syntax')}",
                    line=abs_line,
                    snippet=snippet_for_line(text, abs_line),
                    confidence=0.97,
                    fix="Fix malformed syntax around the reported line.",
                )
            )
            continue

        if isinstance(node, QualifiedRule):
            selector = serialize(node.prelude).strip()
            if not selector:
                findings.append(
                    make_finding(
                        "style",
                        "error",
                        18,
                        "Empty selector block.",
                        line=abs_line,
                        snippet=snippet_for_line(text, abs_line),
                        confidence=0.98,
                        fix="Add a valid selector before the opening brace.",
                    )
                )
            else:
                if in_keyframes:
                    if not _KEYFRAME_SELECTOR_RE.fullmatch(selector):
                        findings.append(
                            make_finding(
                                "style",
                                "error",
                                15,
                                f"Invalid keyframe selector `{selector}`.",
                                line=abs_line,
                                snippet=snippet_for_line(text, abs_line),
                                confidence=0.95,
                                fix="Use `from`, `to`, or percentage stops like `50%`.",
                            )
                        )
                else:
                    try:
                        parsed = list(parse_selector(selector))
                        if not parsed:
                            raise SelectorError(selector)
                        max_specificity = max((s.specificity for s in parsed), default=(0, 0, 0))
                        chain_depth = max((len(_COMBINATOR_RE.findall(str(s))) for s in parsed), default=0)
                        if max_specificity[0] > 1 or (max_specificity[0] > 0 and max_specificity[1] > 3):
                            findings.append(
                                make_finding(
                                    "maintenance",
                                    "warning",
                                    10,
                                    f"High specificity selector `{selector}` may cause override wars.",
                                    line=abs_line,
                                    snippet=snippet_for_line(text, abs_line),
                                    confidence=0.9,
                                    fix="Prefer lower-specificity selectors or component scoping.",
                                )
                            )
                        if chain_depth > 4:
                            findings.append(
                                make_finding(
                                    "performance",
                                    "warning",
                                    9,
                                    f"Deep selector chain detected in `{selector}`.",
                                    line=abs_line,
                                    snippet=snippet_for_line(text, abs_line),
                                    confidence=0.87,
                                    fix="Flatten the selector structure where possible.",
                                )
                            )
                    except Exception:
                        findings.append(
                            make_finding(
                                "style",
                                "error",
                                18,
                                f"Invalid selector `{selector}`.",
                                line=abs_line,
                                snippet=snippet_for_line(text, abs_line),
                                confidence=0.98,
                                fix="Fix selector syntax, brackets, combinators, or pseudo-class usage.",
                            )
                        )

            decl_text = serialize(node.content)
            _analyze_declarations(text, decl_text, abs_line, selector, findings, in_keyframes)

        elif isinstance(node, AtRule) and getattr(node, "content", None):
            at_name = (getattr(node, "at_keyword", "") or "").lower()
            if at_name in {"font-face", "page", "property", "counter-style"}:
                decl_text = serialize(node.content)
                _analyze_declarations(text, decl_text, abs_line, f"@{at_name}", findings, False)

    return findings
