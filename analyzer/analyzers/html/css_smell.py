from __future__ import annotations
import re
from collections import Counter
from ...rules import RuleFinding

_STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.I | re.S)
_STYLE_ATTR_RE = re.compile(r'\sstyle\s*=\s*(["\'])(.*?)\1', re.I | re.S)
_RULE_RE = re.compile(r'([^{]+)\{([^{}]*)\}', re.S)
_DECL_RE = re.compile(r'([-\w]+)\s*:\s*([^;]+);?')
_ID_OR_CLASS_FROM_HTML_RE = re.compile(r'\b(?:id|class)\s*=\s*["\']([^"\']+)["\']', re.I)
_SELECTOR_SPLIT_RE = re.compile(r'\s*,\s*')
_SELECTOR_TOKEN_RE = re.compile(r'(?:[#.][\w-]+|\[[^\]]+\]|::?[\w-]+|[a-zA-Z][\w-]*)')
_COLOR_RE = re.compile(r'(?:#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\))')
_LENGTH_RE = re.compile(r'\b\d+(?:\.\d+)?(?:px|pt|cm|mm|in|pc)\b', re.I)
_RESPONSIVE_UNIT_RE = re.compile(r'\b\d+(?:\.\d+)?(?:rem|em|%|vw|vh|vmin|vmax|ch)\b|\bclamp\s*\(', re.I)
_MEDIA_QUERY_RE = re.compile(r'@media\b', re.I)

def _extract_css(text: str) -> str:
    blocks = _STYLE_BLOCK_RE.findall(text)
    inline_styles = [m.group(2) for m in _STYLE_ATTR_RE.finditer(text)]
    parts = []
    if blocks:
        parts.extend(blocks)
    if inline_styles:
        parts.extend(inline_styles)
    return "\n".join(parts)

def _extract_html_ids_classes(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in _ID_OR_CLASS_FROM_HTML_RE.findall(text):
        for item in raw.split():
            if item:
                tokens.add(item)
    return tokens

def _selector_specificity(selector: str) -> tuple[int, int, int]:
    ids = len(re.findall(r'#[\w-]+', selector))
    classes = len(re.findall(r'\.[\w-]+|\[[^\]]+\]|:[\w-]+', selector))
    elements = len([t for t in _SELECTOR_TOKEN_RE.findall(selector) if not t.startswith(('#', '.', '[', ':'))])
    return ids, classes, elements

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    css = _extract_css(text)
    if not css:
        return findings

    style_blocks = _STYLE_BLOCK_RE.findall(text)
    if len(style_blocks) >= 2 or sum(len(block) for block in style_blocks) > 1200:
        findings.append(RuleFinding("style", "medium", 8, "Heavy inline <style> usage makes the file harder to maintain."))

    inline_styles = list(_STYLE_ATTR_RE.finditer(text))
    if len(inline_styles) >= 6:
        findings.append(RuleFinding("style", "medium", 8, "Too many inline style attributes reduce reuse and consistency."))

    rules = []
    for selector_part, body in _RULE_RE.findall(css):
        selectors = [s.strip() for s in _SELECTOR_SPLIT_RE.split(selector_part.strip()) if s.strip()]
        decls = _DECL_RE.findall(body)
        if not selectors or not decls:
            continue
        rules.append((selectors, decls, body))

    normalized_rules = []
    for selectors, decls, body in rules:
        normalized = tuple(sorted((prop.strip().lower(), " ".join(value.split())) for prop, value in decls))
        normalized_rules.append(normalized)
    dup_rules = [rule for rule, count in Counter(normalized_rules).items() if count >= 2]
    if dup_rules:
        findings.append(RuleFinding("style", "medium", 8, "Duplicate CSS rule bodies were found."))

    prop_counts = Counter()
    for _, decls, _ in rules:
        for prop, value in decls:
            prop_counts[(prop.strip().lower(), " ".join(value.split()))] += 1
    repeated_props = [f"{prop}: {value}" for (prop, value), count in prop_counts.items() if count >= 4]
    if repeated_props:
        findings.append(RuleFinding("style", "low", 4, "Repeated CSS property/value pairs suggest missing variables or shared utility classes."))

    complex_selectors = []
    for selectors, _, _ in rules:
        for selector in selectors:
            ids, classes, elements = _selector_specificity(selector)
            combinators = len(re.findall(r'\s+|>|\+|~', selector))
            if ids >= 2 or classes >= 4 or elements >= 4 or combinators >= 4:
                complex_selectors.append(selector)
    if complex_selectors:
        findings.append(RuleFinding("style", "medium", 8, "Overly specific selectors make overrides and refactors brittle."))

    important_count = len(re.findall(r'!\s*important\b', css, re.I))
    if important_count >= 3:
        findings.append(RuleFinding("style", "medium", 8, "Excessive !important usage usually signals a specificity war."))

    length_count = len(_LENGTH_RE.findall(css))
    responsive_count = len(_RESPONSIVE_UNIT_RE.findall(css))
    if length_count >= 10 and responsive_count <= 2:
        findings.append(RuleFinding("style", "medium", 8, "CSS leans too much on fixed pixel sizes instead of responsive units."))

    has_float = re.search(r'\bfloat\s*:', css, re.I) is not None
    has_flex = re.search(r'\bdisplay\s*:\s*flex\b|\bflex-(?:direction|wrap|grow|shrink|basis)\s*:', css, re.I) is not None
    has_grid = re.search(r'\bdisplay\s*:\s*grid\b|\bgrid-(?:template|auto|area|column|row)\s*:', css, re.I) is not None
    has_absolute = re.search(r'\bposition\s*:\s*absolute\b', css, re.I) is not None
    if sum([has_float, has_flex, has_grid, has_absolute]) >= 3:
        findings.append(RuleFinding("style", "medium", 8, "Mixed layout systems are fighting each other (float/flex/grid/absolute)."))

    color_count = len(_COLOR_RE.findall(css))
    has_vars = re.search(r'--[\w-]+\s*:', css) is not None
    if color_count >= 6 and not has_vars:
        findings.append(RuleFinding("style", "low", 4, "Repeated magic colors without CSS variables reduce consistency."))

    if len(re.findall(r'\b(?:margin|padding|gap)\s*:\s*[^;]+', css, re.I)) >= 8 and not has_vars:
        findings.append(RuleFinding("style", "low", 4, "Repeated spacing values suggest the design system is not centralized."))

    html_tokens = _extract_html_ids_classes(text)
    dead_selectors = []
    for selectors, _, _ in rules:
        for selector in selectors:
            tokens = set(re.findall(r'[#.]([\w-]+)', selector))
            if tokens and tokens.isdisjoint(html_tokens):
                if selector.count(" ") <= 2 and selector.count(">") <= 1:
                    dead_selectors.append(selector)
    if dead_selectors:
        findings.append(RuleFinding("style", "low", 4, "Some CSS selectors do not appear to match any HTML ids/classes in this file."))

    has_media = _MEDIA_QUERY_RE.search(css) is not None
    fixed_widths = len(re.findall(r'\b(?:width|max-width|min-width|height|min-height|max-height)\s*:\s*\d+px\b', css, re.I))
    overflow_hints = len(re.findall(r'\boverflow(?:-x|-y)?\s*:\s*(?:hidden|scroll)\b', css, re.I))
    if fixed_widths >= 4 and not has_media:
        findings.append(RuleFinding("style", "medium", 8, "Fixed-width CSS without media queries is likely to break on smaller screens."))
    if overflow_hints >= 2 and not has_media:
        findings.append(RuleFinding("style", "low", 4, "Overflow handling looks brittle for responsive layouts."))

    if re.search(r':focus(?:-visible)?\b', css, re.I) is None and re.search(r'\b(?:button|a|input|select|textarea)\b', text, re.I):
        findings.append(RuleFinding("accessibility", "low", 4, "No visible focus styles were detected for interactive controls."))

    return findings
