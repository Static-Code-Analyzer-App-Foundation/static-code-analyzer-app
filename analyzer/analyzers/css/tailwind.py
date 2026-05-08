from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from ...rules import RuleFinding
from .css_common import make_finding, line_for_index, snippet_for_line

CLASS_ATTR_RE = re.compile(
    r'(?P<attr>\bclassName\b|\bclass\b|\bngClass\b|\bclass:list\b|\bclass:\w+\b|\[[^\]]*class[^\]]*\]|\:class\b|\bv-bind:class\b)\s*=\s*(?P<value>"[^"]*"|\'[^\']*\'|`[^`]*`|\{[^{}]*\})',
    re.I | re.S,
)

TAILWIND_CONFIG_FILE_RE = re.compile(r"tailwind\.config\.(?:js|cjs|mjs|ts)$", re.I)
PURGE_RE = re.compile(r"\bpurge\s*:", re.I)
CONTENT_RE = re.compile(r"\bcontent\s*:", re.I)
JIT_RE = re.compile(r"\bmode\s*:\s*['\"]jit['\"]", re.I)
SAFELIST_RE = re.compile(r"\bsafelist\s*:\s*\[", re.I)

KNOWN_BREAKPOINTS = {"sm", "md", "lg", "xl", "2xl"}
KNOWN_VARIANTS = {
    "hover", "focus", "focus-visible", "focus-within", "active", "visited", "disabled",
    "checked", "indeterminate", "required", "invalid", "valid", "placeholder-shown",
    "read-only", "first", "last", "odd", "even", "only", "only-of-type", "empty", "open",
    "default", "autofill", "group-hover", "group-focus", "group-active", "peer-hover",
    "peer-focus", "peer-checked", "dark", "motion-safe", "motion-reduce", "ltr", "rtl",
    "print", "before", "after", "marker", "selection", "file", "placeholder", "backdrop",
}
STATE_VARIANTS = {"hover", "focus", "focus-visible", "focus-within", "active", "visited", "disabled"}
STANDALONE_BASES = {
    "block", "inline-block", "inline", "inline-flex", "flex", "grid", "hidden", "contents",
    "table", "table-row", "table-cell", "absolute", "relative", "fixed", "sticky", "static",
    "container", "sr-only", "not-sr-only", "truncate", "antialiased", "subpixel-antialiased",
    "italic", "not-italic", "underline", "line-through", "no-underline", "capitalize",
    "uppercase", "lowercase", "normal-case", "isolate", "isolation-auto", "overflow-hidden",
    "overflow-auto", "overflow-scroll", "overflow-visible", "pointer-events-none",
    "pointer-events-auto", "select-none", "select-text", "select-all", "select-auto",
}
BASE_PREFIXES = (
    "p-", "px-", "py-", "pt-", "pr-", "pb-", "pl-",
    "m-", "mx-", "my-", "mt-", "mr-", "mb-", "ml-",
    "w-", "h-", "min-w-", "max-w-", "min-h-", "max-h-",
    "text-", "bg-", "border-", "rounded-", "ring-", "outline-", "shadow-",
    "gap-", "space-x-", "space-y-", "top-", "right-", "bottom-", "left-", "inset-",
    "translate-", "scale-", "rotate-", "skew-", "origin-",
    "font-", "leading-", "tracking-", "opacity-", "z-", "order-",
    "grow", "shrink", "basis-", "flex-", "grid-", "col-", "row-",
    "justify-", "items-", "content-", "self-", "place-",
    "overflow-", "overscroll-", "object-", "mix-blend-", "from-", "via-", "to-",
    "accent-", "caret-", "fill-", "stroke-", "blur-", "brightness-", "contrast-",
    "drop-shadow-", "grayscale", "hue-rotate-", "invert", "saturate-", "sepia",
    "backdrop-", "transition-", "duration-", "ease-", "delay-", "animate-",
    "cursor-", "align-", "whitespace-", "break-", "line-clamp-", "columns-",
    "content-", "list-", "appearance-", "will-change", "scroll-", "touch-",
)

def _split_variants(token: str) -> list[str]:
    parts = []
    buf = []
    depth = 0
    for ch in token:
        if ch == "[":
            depth += 1
        elif ch == "]" and depth:
            depth -= 1
        elif ch == ":" and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    parts.append("".join(buf))
    return parts

def _strip_dynamic(text: str) -> str:
    text = re.sub(r"\$\{[^}]*\}", " ", text)
    text = re.sub(r"\{\{[^}]*\}\}", " ", text)
    text = text.replace("+", " ")
    return text

def _base_utility(token: str) -> tuple[list[str], str]:
    token = token.strip()
    if token.startswith("!"):
        token = token[1:]
    parts = _split_variants(token)
    if len(parts) == 1:
        return [], parts[0]
    return parts[:-1], parts[-1]

def _is_known_base(base: str) -> bool:
    if base in STANDALONE_BASES:
        return True
    if base.startswith("[") and base.endswith("]"):
        return True
    if base.startswith(BASE_PREFIXES):
        return True
    if re.fullmatch(r"(?:sm|md|lg|xl|2xl):?.*", base):
        return True
    if re.fullmatch(r"[a-z0-9][a-z0-9\-\/\[\]\(\)%#:.]*", base):
        return True
    return False

def _utility_group(base: str) -> str:
    base = base.lstrip("!")
    core = base.split("/", 1)[0]

    if core in {"block", "inline-block", "inline", "inline-flex", "flex", "grid", "hidden", "contents", "table", "table-row", "table-cell"}:
        return "display"
    if core in {"absolute", "relative", "fixed", "sticky", "static"}:
        return "position"
    if core.startswith(("p-", "px-", "py-", "pt-", "pr-", "pb-", "pl-", "m-", "mx-", "my-", "mt-", "mr-", "mb-", "ml-", "space-x-", "space-y-")):
        return "spacing"
    if re.fullmatch(r"text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl|\[.*\])", core) or core.startswith("leading-") or core.startswith("tracking-") or core.startswith("font-"):
        return "typography"
    if core.startswith(("text-", "bg-", "from-", "via-", "to-")):
        return "color"
    if core.startswith(("border-", "rounded-", "ring-", "outline-")):
        return "border"
    if core.startswith(("w-", "h-", "min-w-", "max-w-", "min-h-", "max-h-", "basis-", "aspect-")):
        return "size"
    if core.startswith(("grid", "col-", "row-", "gap-", "place-")):
        return "grid"
    if core.startswith(("justify-", "items-", "content-", "self-", "flex-", "grow", "shrink", "order-")):
        return "flex"
    if core.startswith(("shadow-", "blur-", "brightness-", "contrast-", "drop-shadow-", "grayscale", "hue-rotate-", "invert", "saturate-", "sepia", "backdrop-")):
        return "effects"
    if core.startswith(("overflow-", "overscroll-", "scroll-")):
        return "overflow"
    if core.startswith(("transition-", "duration-", "ease-", "delay-", "animate-", "transform", "translate-", "scale-", "rotate-", "skew-")):
        return "motion"
    return "other"

def _looks_like_arbitrary_value(base: str) -> bool:
    return "[" in base or "]" in base

def _is_valid_arbitrary(base: str) -> bool:
    if base.count("[") != base.count("]"):
        return False
    if "[" not in base:
        return True
    inner = base[base.find("[") + 1 : base.rfind("]")]
    if not inner.strip():
        return False
    if "${" in inner or "{{" in inner or "}}" in inner:
        return False
    if inner.count("(") != inner.count(")"):
        return False
    return True

def _extract_class_values(text: str):
    for m in CLASS_ATTR_RE.finditer(text):
        raw = m.group("value")
        line = line_for_index(text, m.start())
        snippet = snippet_for_line(text, line)
        yield raw, line, snippet, m.group("attr")

def analyze(text: str, path: Path | None = None) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    bundles = Counter()
    arbitrary_values = Counter()
    dynamic_markers = 0

    file_name = (path.name.lower() if path else "")
    is_tailwind_config = bool(path and TAILWIND_CONFIG_FILE_RE.search(file_name))

    if is_tailwind_config:
        if PURGE_RE.search(text):
            findings.append(
                make_finding(
                    "tailwind-config",
                    "warning",
                    10,
                    "`purge:` is deprecated in modern Tailwind config.",
                    line=line_for_index(text, PURGE_RE.search(text).start()),
                    snippet=snippet_for_line(text, line_for_index(text, PURGE_RE.search(text).start())),
                    confidence=0.97,
                    fix="Replace `purge:` with `content:`.",
                )
            )
        if JIT_RE.search(text):
            findings.append(
                make_finding(
                    "tailwind-config",
                    "info",
                    3,
                    "Explicit `mode: 'jit'` is obsolete in Tailwind v3+.",
                    line=line_for_index(text, JIT_RE.search(text).start()),
                    snippet=snippet_for_line(text, line_for_index(text, JIT_RE.search(text).start())),
                    confidence=0.95,
                    fix="Remove the `mode: 'jit'` setting unless you are on an older stack.",
                )
            )
        if SAFELIST_RE.search(text) and text.count("safelist") > 1:
            findings.append(
                make_finding(
                    "performance",
                    "info",
                    4,
                    "Large safelists can inflate generated CSS.",
                    line=line_for_index(text, SAFELIST_RE.search(text).start()),
                    snippet=snippet_for_line(text, line_for_index(text, SAFELIST_RE.search(text).start())),
                    confidence=0.84,
                    fix="Keep the safelist narrow and intentional.",
                )
            )

    for raw, line, snippet, attr in _extract_class_values(text):
        cleaned = raw[1:-1] if raw[:1] in {'"', "'", "`", "{"} and raw[-1:] in {'"', "'", "`", "}"} else raw
        dynamic = False
        if "${" in cleaned or "{{" in cleaned or "}}" in cleaned or "clsx(" in cleaned or "cn(" in cleaned or "classnames(" in cleaned.lower():
            dynamic = True
            dynamic_markers += 1
            findings.append(
                make_finding(
                    "security",
                    "warning",
                    10,
                    "Dynamic class construction can hide user-controlled styling.",
                    line=line,
                    snippet=snippet,
                    confidence=0.9,
                    fix="Constrain class inputs to a safe allowlist instead of concatenating raw user input.",
                )
            )
            if "${" in cleaned or "{{" in cleaned or "}}" in cleaned:
                findings.append(
                    make_finding(
                        "framework",
                        "warning",
                        8,
                        "Template interpolation appears inside a class string.",
                        line=line,
                        snippet=snippet,
                        confidence=0.88,
                        fix="Keep class strings static where possible, or precompute class names safely.",
                    )
                )

        static_text = _strip_dynamic(cleaned)
        tokens = [t for t in re.split(r"\s+", static_text.strip()) if t]
        if not tokens:
            continue

        bundles[tuple(sorted(set(tokens)))] += 1

        if len(tokens) >= 18:
            findings.append(
                make_finding(
                    "maintainability",
                    "info",
                    4,
                    "Very long utility string.",
                    line=line,
                    snippet=snippet,
                    confidence=0.86,
                    fix="Extract a component class or reusable variant bundle.",
                )
            )

        group_map: dict[tuple[tuple[str, ...], str], set[str]] = defaultdict(set)
        variant_groups: dict[str, set[str]] = defaultdict(set)
        hover_seen = False
        focus_seen = False
        motion_reduce_seen = False
        hidden_seen = False
        breakpoint_display_seen = False
        has_focus_ring_removal = False

        for token in tokens:
            original = token
            important = token.startswith("!")
            if important:
                token = token[1:]

            if token.count("[") != token.count("]"):
                findings.append(
                    make_finding(
                        "syntax",
                        "error",
                        18,
                        f"Malformed arbitrary value in `{original}`.",
                        line=line,
                        snippet=snippet,
                        confidence=0.98,
                        fix="Balance the square brackets and keep the arbitrary value syntax valid.",
                    )
                )
                continue

            variants, base = _base_utility(token)
            if not base:
                findings.append(
                    make_finding(
                        "syntax",
                        "error",
                        18,
                        f"Broken variant chain in `{original}`.",
                        line=line,
                        snippet=snippet,
                        confidence=0.98,
                        fix="Add a real utility after the variant chain, for example `sm:hover:bg-blue-500`.",
                    )
                )
                continue

            if token.endswith(":") or "::" in token or token.startswith(":"):
                findings.append(
                    make_finding(
                        "syntax",
                        "error",
                        18,
                        f"Broken variant syntax in `{original}`.",
                        line=line,
                        snippet=snippet,
                        confidence=0.98,
                        fix="Remove the trailing colon or malformed separator.",
                    )
                )
                continue

            if not _is_valid_arbitrary(base):
                findings.append(
                    make_finding(
                        "syntax",
                        "error",
                        18,
                        f"Malformed arbitrary value in `{original}`.",
                        line=line,
                        snippet=snippet,
                        confidence=0.98,
                        fix="Fix the bracketed value, quotes, and parentheses.",
                    )
                )
                continue

            variant_key = tuple(sorted(v for v in variants if v))
            for variant in variants:
                if variant == "hover":
                    hover_seen = True
                if variant in {"focus", "focus-visible"}:
                    focus_seen = True
                if variant == "motion-reduce":
                    motion_reduce_seen = True
                if variant in KNOWN_BREAKPOINTS:
                    breakpoint_display_seen = True
                if variant not in KNOWN_VARIANTS and not variant.startswith(("aria-", "data-", "group-", "peer-", "supports-")) and not variant.startswith("["):
                    findings.append(
                        make_finding(
                            "config",
                            "info",
                            4,
                            f"Unknown or custom variant `{variant}`; verify Tailwind config support.",
                            line=line,
                            snippet=snippet,
                            confidence=0.76,
                            fix="Check whether the breakpoint, plugin variant, or screen name is defined in your Tailwind config.",
                        )
                    )

            group = _utility_group(base)
            group_map[(variant_key, group)].add(original)
            variant_groups["|".join(variants)].add(original)

            if important:
                findings.append(
                    make_finding(
                        "maintainability",
                        "info",
                        4,
                        f"Important utility `{original}` reduces clarity.",
                        line=line,
                        snippet=snippet,
                        confidence=0.86,
                        fix="Avoid `!` utilities unless they are truly the last resort.",
                    )
                )

            if _looks_like_arbitrary_value(base):
                arbitrary_values[base] += 1
                findings.append(
                    make_finding(
                        "design-system",
                        "info",
                        4,
                        f"Arbitrary value utility `{original}` may drift from design tokens.",
                        line=line,
                        snippet=snippet,
                        confidence=0.84,
                        fix="Prefer approved design tokens or extend the Tailwind theme.",
                    )
                )

            if not _is_known_base(base) and not base.startswith("["):
                findings.append(
                    make_finding(
                        "config",
                        "info",
                        3,
                        f"Unknown or custom utility `{base}`; verify it exists in Tailwind config.",
                        line=line,
                        snippet=snippet,
                        confidence=0.7,
                        fix="Confirm that this utility comes from core Tailwind, a plugin, or your theme extensions.",
                    )
                )

            if base.startswith("focus:outline-none") or base in {"outline-none", "focus:ring-0", "focus-visible:ring-0"}:
                has_focus_ring_removal = True

            if base.startswith("text-") and re.fullmatch(r"text-(?:xs|sm|\[.*\])", base):
                findings.append(
                    make_finding(
                        "accessibility",
                        "warning",
                        8,
                        f"Small text utility `{original}` may be hard to read.",
                        line=line,
                        snippet=snippet,
                        confidence=0.82,
                        fix="Use a larger text size or a better responsive scale.",
                    )
                )

            if base.startswith("animate-") or base == "transition-all":
                if not motion_reduce_seen:
                    findings.append(
                        make_finding(
                            "accessibility",
                            "info",
                            4,
                            f"Motion-heavy utility `{original}` should have a reduced-motion fallback.",
                            line=line,
                            snippet=snippet,
                            confidence=0.79,
                            fix="Add `motion-reduce:` alternatives for users who prefer less motion.",
                        )
                    )

            if base == "hidden":
                hidden_seen = True

        # Conflicts inside the same class list.
        for (variant_key, group), values in group_map.items():
            if len(values) > 1 and group != "other":
                findings.append(
                    make_finding(
                        "conflict",
                        "warning",
                        9,
                        f"Conflicting `{group}` utilities in the same class list: {', '.join(sorted(values)[:3])}.",
                        line=line,
                        snippet=snippet,
                        confidence=0.92,
                        fix="Keep only the utility that expresses the final intent for that state/breakpoint.",
                    )
                )

        # State coverage.
        if hover_seen and not focus_seen:
            findings.append(
                make_finding(
                    "accessibility",
                    "info",
                    4,
                    "Hover styling exists without a focus counterpart.",
                    line=line,
                    snippet=snippet,
                    confidence=0.82,
                    fix="Add `focus:` or `focus-visible:` styles for keyboard users.",
                )
            )

        # Hidden content patterns that deserve a second look.
        if hidden_seen and breakpoint_display_seen:
            findings.append(
                make_finding(
                    "responsive",
                    "info",
                    4,
                    "Content is hidden by default and only revealed at breakpoints.",
                    line=line,
                    snippet=snippet,
                    confidence=0.8,
                    fix="Verify that the mobile experience still exposes the needed content or controls.",
                )
            )

        if has_focus_ring_removal:
            findings.append(
                make_finding(
                    "accessibility",
                    "warning",
                    10,
                    "Focus ring removal detected.",
                    line=line,
                    snippet=snippet,
                    confidence=0.93,
                    fix="Replace the removed ring with a visible, accessible focus treatment.",
                )
            )

        if sum(1 for t in tokens if "[" in t and "]" in t) >= 4:
            findings.append(
                make_finding(
                    "performance",
                    "info",
                    4,
                    "Many arbitrary utilities reduce reuse and can bloat styling patterns.",
                    line=line,
                    snippet=snippet,
                    confidence=0.81,
                    fix="Promote repeated arbitrary values into theme tokens.",
                )
            )

    for bundle, count in bundles.items():
        if count > 4 and len(bundle) > 4:
            findings.append(
                make_finding(
                    "maintenance",
                    "info",
                    4,
                    "Repeated utility bundle found across multiple elements.",
                    line=1,
                    snippet=snippet_for_line(text, 1),
                    confidence=0.78,
                    fix="Extract a reusable component or class recipe.",
                )
            )
            break

    if dynamic_markers >= 3:
        findings.append(
            make_finding(
                "security",
                "warning",
                10,
                "Multiple dynamic class expressions were detected.",
                line=1,
                snippet=snippet_for_line(text, 1),
                confidence=0.84,
                fix="Constrain dynamic style inputs to safe presets instead of free-form strings.",
            )
        )

    if arbitrary_values and len(arbitrary_values) >= 6:
        findings.append(
            make_finding(
                "design-system",
                "warning",
                9,
                "Excessive arbitrary value usage suggests token drift.",
                line=1,
                snippet=snippet_for_line(text, 1),
                confidence=0.9,
                fix="Move those values into the Tailwind theme or a shared design token set.",
            )
        )

    return findings
