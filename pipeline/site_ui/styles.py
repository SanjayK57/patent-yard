"""The stylesheet: web/styles/site.css and the files it @imports, bundled into the one file the site serves.

Two small jobs besides inlining:
- Dark mode is written once, as rules under :root[data-theme="dark"]. Each such rule is followed by a copy for
  visitors whose system is dark and who haven't picked a theme, so the dark colors live in one place.
- Comments and blank lines are dropped.
The browser-chrome colors (<meta name="theme-color">, the web app manifest) are read from tokens.css too.
"""
import re
from pathlib import Path

STYLES = Path(__file__).resolve().parents[2] / "web" / "styles"
DARK, SYSTEM_DARK = ':root[data-theme="dark"]', ':root:not([data-theme="light"])'


def _inline(path, seen):
    css = path.read_text()
    def sub(m):
        child = (path.parent / m.group(1)).resolve()
        assert child not in seen, f"{child} imported twice"
        seen.add(child)
        return _inline(child, seen)
    return re.sub(r'@import\s+"([^"]+)";', sub, css)


def _top_level_rules(css):
    """Splits CSS into top-level chunks: whole rules and at-rule blocks, with their braces balanced."""
    out, depth, start = [], 0, 0
    for i, ch in enumerate(css):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append(css[start:i + 1].strip())
                start = i + 1
    assert depth == 0, "unbalanced braces in web/styles"
    return [c for c in out if c]


def bundle_css():
    css = re.sub(r"/\*.*?\*/", "", _inline(STYLES / "site.css", set()), flags=re.S)
    out = []
    for rule in _top_level_rules(css):
        rule = re.sub(r"\n\s*", "\n", rule)
        out.append(rule)
        prelude = rule.split("{", 1)[0]
        if DARK in prelude and not prelude.lstrip().startswith("@"):
            out.append("@media (prefers-color-scheme:dark){" + rule.replace(DARK, SYSTEM_DARK) + "}")
    return "\n".join(out) + "\n"


def theme_colors():
    """{"light": hex, "dark": hex}: the page background in each theme, for the browser's own chrome."""
    css = (STYLES / "tokens.css").read_text()
    light = re.search(r":root\{[^}]*?--bg:(#[0-9A-Fa-f]{6})", css).group(1)
    dark = re.search(r':root\[data-theme="dark"\]\{[^}]*?--bg:(#[0-9A-Fa-f]{6})', css).group(1)
    return {"light": light, "dark": dark}


if __name__ == "__main__":  # a quick self-check: python3 site_ui/styles.py
    b = bundle_css()
    assert "@import" not in b and "/*" not in b
    assert re.search(r"@media \(prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{\s*--bg:", b), "dark tokens not copied"
    print(f"{len(b):,} bytes, theme colors {theme_colors()}")
