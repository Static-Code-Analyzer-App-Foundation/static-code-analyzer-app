from __future__ import annotations

import inspect
import math
import re
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Iterable, Iterator, Optional

from ...rules import RuleFinding

try:
    from PIL import ImageColor
except Exception:  # pragma: no cover
    ImageColor = None

from tinycss2 import parse_declaration_list, parse_rule_list, parse_stylesheet, serialize
from tinycss2.ast import AtRule, Declaration, ParseError, QualifiedRule

DECLARATION_AT_RULES = {"font-face", "page", "property", "counter-style"}
KEYFRAME_AT_RULES = {"keyframes", "-webkit-keyframes"}

COMMON_CSS_PROPERTIES = {
    "accent-color", "align-content", "align-items", "align-self", "all",
    "animation", "animation-delay", "animation-direction", "animation-duration",
    "animation-fill-mode", "animation-iteration-count", "animation-name",
    "animation-play-state", "animation-timing-function", "appearance",
    "aspect-ratio", "backface-visibility", "backdrop-filter", "background",
    "background-attachment", "background-blend-mode", "background-clip",
    "background-color", "background-image", "background-origin",
    "background-position", "background-repeat", "background-size", "border",
    "border-bottom", "border-bottom-color", "border-bottom-left-radius",
    "border-bottom-right-radius", "border-bottom-style", "border-bottom-width",
    "border-collapse", "border-color", "border-image", "border-image-outset",
    "border-image-repeat", "border-image-slice", "border-image-source",
    "border-image-width", "border-left", "border-left-color", "border-left-style",
    "border-left-width", "border-radius", "border-right", "border-right-color",
    "border-right-style", "border-right-width", "border-spacing", "border-style",
    "border-top", "border-top-color", "border-top-left-radius",
    "border-top-right-radius", "border-top-style", "border-top-width",
    "border-width", "bottom", "box-decoration-break", "box-shadow", "box-sizing",
    "break-after", "break-before", "break-inside", "caption-side", "caret-color",
    "clear", "clip", "clip-path", "color", "column-count", "column-fill",
    "column-gap", "column-rule", "column-rule-color", "column-rule-style",
    "column-rule-width", "column-span", "column-width", "columns", "content",
    "counter-increment", "counter-reset", "cursor", "direction", "display",
    "empty-cells", "filter", "flex", "flex-basis", "flex-direction", "flex-flow",
    "flex-grow", "flex-shrink", "flex-wrap", "float", "font", "font-family",
    "font-feature-settings", "font-kerning", "font-optical-sizing", "font-size",
    "font-size-adjust", "font-stretch", "font-style", "font-variant",
    "font-variant-caps", "font-variant-ligatures", "font-variant-numeric",
    "font-variation-settings", "font-weight", "gap", "grid", "grid-area",
    "grid-auto-columns", "grid-auto-flow", "grid-auto-rows", "grid-column",
    "grid-column-end", "grid-column-gap", "grid-column-start", "grid-row",
    "grid-row-end", "grid-row-gap", "grid-row-start", "grid-template",
    "grid-template-areas", "grid-template-columns", "grid-template-rows",
    "height", "hyphens", "isolation", "justify-content", "justify-items",
    "justify-self", "left", "letter-spacing", "line-height", "list-style",
    "list-style-image", "list-style-position", "list-style-type", "margin",
    "margin-bottom", "margin-left", "margin-right", "margin-top", "max-height",
    "max-width", "min-height", "min-width", "mix-blend-mode", "object-fit",
    "object-position", "opacity", "order", "outline", "outline-color",
    "outline-offset", "outline-style", "outline-width", "overflow",
    "overflow-anchor", "overflow-wrap", "overflow-x", "overflow-y", "padding",
    "padding-bottom", "padding-left", "padding-right", "padding-top",
    "perspective", "perspective-origin", "place-content", "place-items",
    "place-self", "pointer-events", "position", "resize", "right",
    "scroll-behavior", "scroll-margin", "scroll-padding", "scroll-snap-align",
    "scroll-snap-stop", "scroll-snap-type", "shape-image-threshold",
    "shape-margin", "shape-outside", "tab-size", "table-layout", "text-align",
    "text-align-last", "text-decoration", "text-decoration-color",
    "text-decoration-line", "text-decoration-style", "text-decoration-thickness",
    "text-indent", "text-overflow", "text-rendering", "text-shadow",
    "text-transform", "text-underline-offset", "text-underline-position",
    "top", "transform", "transform-origin", "transform-style", "transition",
    "transition-delay", "transition-duration", "transition-property",
    "transition-timing-function", "unicode-bidi", "user-select",
    "vertical-align", "visibility", "white-space", "widows", "width",
    "will-change", "word-break", "word-spacing", "writing-mode", "z-index",
    "content-visibility", "contain", "inset", "inset-block",
    "inset-block-end", "inset-block-start", "inset-inline",
    "inset-inline-end", "inset-inline-start", "mask", "mask-image",
    "mask-mode", "mask-position", "mask-repeat", "mask-size", "offset",
    "offset-anchor", "offset-distance", "offset-path", "offset-rotate",
    "overscroll-behavior", "overscroll-behavior-x", "overscroll-behavior-y",
    "scrollbar-color", "scrollbar-gutter", "scrollbar-width", "touch-action",
}

_LENGTH_RE = re.compile(r"^\s*(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(px|rem|em|ch|ex|vh|vw|vmin|vmax|svh|dvh|lvh|cqw|cqh|%)\s*$", re.I)
_HEX_COLOR_RE = re.compile(r"^#([0-9a-f]{3,8})$", re.I)
_RGB_RE = re.compile(r"rgba?\(\s*([^)]+)\s*\)$", re.I)
_HSL_RE = re.compile(r"hsla?\(\s*([^)]+)\s*\)$", re.I)

def make_finding(
    category: str,
    severity: str,
    points: int,
    message: str,
    *,
    line: int | None = None,
    snippet: str | None = None,
    confidence: float | None = None,
    fix: str | None = None,
    autofix: str | None = None,
) -> RuleFinding:
    payload = {"category": category, "severity": severity, "points": points, "message": message}
    extras = {
        "line": line,
        "snippet": snippet,
        "confidence": confidence,
        "fix": fix,
        "autofix": autofix,
    }
    extras = {k: v for k, v in extras.items() if v is not None}

    try:
        sig = inspect.signature(RuleFinding)
        candidate = {**payload, **{k: v for k, v in extras.items() if k in sig.parameters}}
        return RuleFinding(**candidate)
    except Exception:
        extra_bits: list[str] = []
        if line is not None:
            extra_bits.append(f"line {line}")
        if snippet:
            extra_bits.append(f"snippet: {snippet}")
        if confidence is not None:
            extra_bits.append(f"confidence {confidence:.2f}")
        if fix:
            extra_bits.append(f"fix: {fix}")
        if autofix:
            extra_bits.append(f"auto-fix: {autofix}")
        text = message if not extra_bits else f"{message} ({'; '.join(extra_bits)})"
        try:
            return RuleFinding(category, severity, points, text)
        except Exception:
            return RuleFinding(**payload)

def line_for_index(text: str, index: int) -> int:
    return text.count("\n", 0, max(0, index)) + 1

def line_text(text: str, line: int) -> str:
    if line <= 0:
        return ""
    parts = text.splitlines()
    if 1 <= line <= len(parts):
        return parts[line - 1]
    return ""

def snippet_for_index(text: str, index: int) -> str:
    return line_text(text, line_for_index(text, index)).strip()

def snippet_for_line(text: str, line: int) -> str:
    return line_text(text, line).strip()

def normalize_value(value: str) -> str:
    return " ".join(value.split()).lower()

def parse_length(value: str) -> tuple[float, str] | None:
    m = _LENGTH_RE.match(value)
    if not m:
        return None
    return float(m.group(1)), m.group(2).lower()

def _parse_rgb_channel(token: str) -> int | float | None:
    token = token.strip()
    if token.endswith("%"):
        try:
            return max(0.0, min(100.0, float(token[:-1])))
        except Exception:
            return None
    try:
        return float(token)
    except Exception:
        return None

def parse_css_color(value: str) -> tuple[int, int, int, float] | None:
    text = value.strip().lower()
    if text in {"transparent", "none", "currentcolor"}:
        return None

    m = _HEX_COLOR_RE.match(text)
    if m:
        h = m.group(1)
        if len(h) == 3:
            r, g, b = [int(ch * 2, 16) for ch in h]
            return (r, g, b, 1.0)
        if len(h) == 4:
            r, g, b, a = [int(ch * 2, 16) for ch in h]
            return (r, g, b, a / 255.0)
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
        if len(h) == 8:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255.0)

    m = _RGB_RE.match(text)
    if m:
        body = m.group(1).replace("/", ",")
        parts = [p.strip() for p in body.split(",") if p.strip()]
        if len(parts) in {3, 4}:
            channels = [_parse_rgb_channel(p) for p in parts[:3]]
            if any(v is None for v in channels):
                return None
            rgb: list[int] = []
            for ch in channels:
                assert ch is not None
                if isinstance(ch, float) and 0.0 <= ch <= 100.0 and "%" in parts[len(rgb)]:
                    rgb.append(int(round((ch / 100.0) * 255)))
                else:
                    rgb.append(int(max(0, min(255, round(float(ch))))))
            alpha = 1.0
            if len(parts) == 4:
                a = _parse_rgb_channel(parts[3])
                if a is None:
                    return None
                alpha = float(a)
                if alpha > 1:
                    alpha = max(0.0, min(1.0, alpha / 100.0))
            return (rgb[0], rgb[1], rgb[2], alpha)

    m = _HSL_RE.match(text)
    if m:
        body = m.group(1).replace("/", ",")
        parts = [p.strip() for p in body.split(",") if p.strip()]
        if len(parts) in {3, 4}:
            try:
                h = float(parts[0].rstrip("deg")) % 360.0
                s = float(parts[1].rstrip("%")) / 100.0
                l = float(parts[2].rstrip("%")) / 100.0
            except Exception:
                return None
            c = (1 - abs(2 * l - 1)) * s
            x = c * (1 - abs((h / 60.0) % 2 - 1))
            m0 = l - c / 2
            if h < 60:
                r, g, b = c, x, 0
            elif h < 120:
                r, g, b = x, c, 0
            elif h < 180:
                r, g, b = 0, c, x
            elif h < 240:
                r, g, b = 0, x, c
            elif h < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            alpha = 1.0
            if len(parts) == 4:
                try:
                    alpha = float(parts[3].rstrip("%"))
                    if alpha > 1:
                        alpha /= 100.0
                except Exception:
                    return None
            return (
                int(round((r + m0) * 255)),
                int(round((g + m0) * 255)),
                int(round((b + m0) * 255)),
                max(0.0, min(1.0, alpha)),
            )

    if ImageColor is not None:
        try:
            r, g, b = ImageColor.getrgb(text)
            return (int(r), int(g), int(b), 1.0)
        except Exception:
            return None

    return None

def _linearize(channel: float) -> float:
    channel /= 255.0
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4

def contrast_ratio(fg: tuple[int, int, int, float], bg: tuple[int, int, int, float]) -> float | None:
    if fg[3] < 1.0 or bg[3] < 1.0:
        return None
    l1 = 0.2126 * _linearize(fg[0]) + 0.7152 * _linearize(fg[1]) + 0.0722 * _linearize(fg[2])
    l2 = 0.2126 * _linearize(bg[0]) + 0.7152 * _linearize(bg[1]) + 0.0722 * _linearize(bg[2])
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)

def css_properties_close_match(name: str) -> str | None:
    matches = get_close_matches(name, COMMON_CSS_PROPERTIES, n=1, cutoff=0.86)
    return matches[0] if matches else None

def is_vendor_or_custom_property(name: str) -> bool:
    return name.startswith("--") or name.startswith("-webkit-") or name.startswith("-moz-") or name.startswith("-ms-") or name.startswith("-o-")

def iter_css_nodes(text: str):
    """
    Yield (node, absolute_line, in_keyframes) for the stylesheet, recursively.
    """
    def _walk(nodes, line_offset: int = 0, in_keyframes: bool = False):
        for node in nodes:
            source_line = getattr(node, "source_line", 1) or 1
            abs_line = line_offset + source_line
            yield node, abs_line, in_keyframes

            if isinstance(node, AtRule) and getattr(node, "content", None):
                at_name = (getattr(node, "at_keyword", "") or "").lower()
                if at_name in DECLARATION_AT_RULES:
                    continue
                inner_text = serialize(node.content)
                inner_nodes = parse_rule_list(inner_text, skip_whitespace=True, skip_comments=True)
                next_line_offset = line_offset + source_line - 1
                next_keyframes = in_keyframes or at_name in KEYFRAME_AT_RULES
                yield from _walk(inner_nodes, next_line_offset, next_keyframes)

    top = parse_stylesheet(text, skip_whitespace=True, skip_comments=True)
    yield from _walk(top, 0, False)
