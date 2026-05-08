from __future__ import annotations

import re
from collections import Counter, defaultdict

from cssselect2.parser import parse as parse_selector
from tinycss2 import parse_declaration_list, serialize
from tinycss2.ast import AtRule, Declaration, ParseError, QualifiedRule

from ...rules import RuleFinding
from .css_common import (
    iter_css_nodes,
    make_finding,
    normalize_value,
    parse_length,
    snippet_for_line,
    is_vendor_or_custom_property,
    css_properties_close_match,
    COMMON_CSS_PROPERTIES,
)

_HEX_VALUE_RE = re.compile(r"#[0-9a-f]{3,8}\b", re.I)
_RGB_VALUE_RE = re.compile(r"\brgba?\([^)]+\)", re.I)
_SPACE_NUM_RE = re.compile(r"\b\d+(?:\.\d+)?(px|rem|em|vh|vw|vmin|vmax|%)\b", re.I)

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if len(text.splitlines()) > 300:
        findings.append(
            make_finding(
                "maintenance",
                "warning",
                8,
                "Very large CSS files become harder to maintain and review.",
                line=1,
                snippet=snippet_for_line(text, 1),
                confidence=0.95,
                fix="Split the stylesheet into smaller component-scoped files.",
            )
        )

    selector_buckets: dict[str, list[tuple[int, str]]] = defaultdict(list)
    declaration_signatures: Counter[str] = Counter()
    property_value_counter: Counter[str] = Counter()
    raw_literal_count = 0
    var_count = 0
    important_count = 0

    for node, abs_line, in_keyframes in iter_css_nodes(text):
        if isinstance(node, ParseError):
            continue

        if isinstance(node, QualifiedRule):
            selector = serialize(node.prelude).strip()
            selector_buckets[selector].append((abs_line, serialize(node.content)))

            decls = parse_declaration_list(serialize(node.content), skip_whitespace=True, skip_comments=True)
            block_pairs = []
            local_seen: dict[str, str] = {}

            for decl in decls:
                if not isinstance(decl, Declaration):
                    continue

                name = decl.name.lower()
                value = normalize_value(serialize(decl.value).strip())
                local_seen.setdefault(name, value)

                sig = f"{name}:{value}"
                property_value_counter[sig] += 1
                block_pairs.append(sig)

                if decl.important:
                    important_count += 1

                if "var(" in value:
                    var_count += 1

                if _HEX_VALUE_RE.search(value) or _RGB_VALUE_RE.search(value):
                    raw_literal_count += 1

            declaration_signatures[f"{selector}||{'|'.join(sorted(block_pairs))}"] += 1

            for prop, val in local_seen.items():
                if prop in {"color", "background", "background-color", "border-color", "outline-color"}:
                    if _HEX_VALUE_RE.search(val) or _RGB_VALUE_RE.search(val):
                        raw_literal_count += 1

        elif isinstance(node, AtRule) and getattr(node, "content", None):
            at_name = (getattr(node, "at_keyword", "") or "").lower()
            if at_name in {"font-face", "page", "property", "counter-style"}:
                decls = parse_declaration_list(serialize(node.content), skip_whitespace=True, skip_comments=True)
                for decl in decls:
                    if isinstance(decl, Declaration):
                        value = normalize_value(serialize(decl.value).strip())
                        if "var(" in value:
                            var_count += 1
                        if _HEX_VALUE_RE.search(value) or _RGB_VALUE_RE.search(value):
                            raw_literal_count += 1

    for selector, occurrences in selector_buckets.items():
        if len(occurrences) > 1:
            values = {content.strip() for _, content in occurrences}
            if len(values) > 1:
                findings.append(
                    make_finding(
                        "maintenance",
                        "warning",
                        10,
                        f"Selector `{selector}` is defined multiple times with different declarations.",
                        line=occurrences[-1][0],
                        snippet=snippet_for_line(text, occurrences[-1][0]),
                        confidence=0.93,
                        fix="Merge the rules or make the override intentional and obvious.",
                    )
                )
            else:
                findings.append(
                    make_finding(
                        "maintenance",
                        "info",
                        4,
                        f"Selector `{selector}` is duplicated.",
                        line=occurrences[-1][0],
                        snippet=snippet_for_line(text, occurrences[-1][0]),
                        confidence=0.9,
                        fix="Remove repeated copies of the same rule.",
                    )
                )

    for signature, count in declaration_signatures.items():
        if count > 8:
            selector = signature.split("||", 1)[0]
            findings.append(
                make_finding(
                    "maintenance",
                    "info",
                    4,
                    f"Repeated style block detected for `{selector}`.",
                    line=1,
                    snippet=snippet_for_line(text, 1),
                    confidence=0.8,
                    fix="Extract shared styles into reusable classes or tokens.",
                )
            )
            break

    if important_count >= 8:
        findings.append(
            make_finding(
                "maintenance",
                "warning",
                9,
                f"`!important` is used {important_count} times across the stylesheet.",
                line=1,
                snippet=snippet_for_line(text, 1),
                confidence=0.9,
                fix="Reduce `!important` usage and refactor specificity or structure.",
            )
        )

    if raw_literal_count >= 10 and var_count == 0:
        findings.append(
            make_finding(
                "maintenance",
                "warning",
                10,
                "Hardcoded colors and sizes dominate this stylesheet.",
                line=1,
                snippet=snippet_for_line(text, 1),
                confidence=0.89,
                fix="Move repeated values into CSS custom properties or design tokens.",
            )
        )

    if any(count > 10 for count in property_value_counter.values()):
        top = property_value_counter.most_common(1)[0][0]
        findings.append(
            make_finding(
                "maintenance",
                "info",
                4,
                f"Repeated declaration value pattern: `{top}`.",
                line=1,
                snippet=snippet_for_line(text, 1),
                confidence=0.78,
                fix="Consider tokenizing repeated values or abstracting a component class.",
            )
        )

    # Specificity wars: selectors with IDs or too many class/attribute selectors.
    for selector, occurrences in selector_buckets.items():
        try:
            parsed = list(parse_selector(selector))
        except Exception:
            continue
        for s in parsed:
            a, b, c = s.specificity
            if a > 1 or (a > 0 and b > 3):
                findings.append(
                    make_finding(
                        "maintenance",
                        "warning",
                        10,
                        f"High specificity selector `{selector}` can lead to override wars.",
                        line=occurrences[-1][0],
                        snippet=snippet_for_line(text, occurrences[-1][0]),
                        confidence=0.9,
                        fix="Prefer lower-specificity selectors and component-scoped styling.",
                    )
                )
                break

    return findings
