"""
bot.svg_renderer
~~~~~~~~~~~~~~~~
SVG card layout renderer. Converts GitHub stats and ASCII art lines into
clean, pixel-aligned SVG vector cards for both light and dark GitHub themes.
"""

from dataclasses import dataclass
import html
import logging

from bot.github_api import GitHubStats, account_uptime

logger = logging.getLogger(__name__)

# SVG Layout Metrics
FONT_SIZE = 16
LINE_HEIGHT = 20
CHAR_WIDTH = FONT_SIZE * 0.6  # 9.6px

ASCII_FONT_SIZE = 8
ASCII_CHAR_WIDTH = 4.8
ASCII_LINE_HEIGHT = 9.6

PAD = 28
GAP = 32
INFO_COLS = 58


@dataclass
class ThemePalette:
    bg: str
    border: str
    ascii: str
    header: str
    rule: str
    key: str
    dots: str
    value: str
    number: str


PALETTES: dict[str, ThemePalette] = {
    "light": ThemePalette(
        bg="#ffffff",
        border="#d0d7de",
        ascii="#24292f",
        header="#0969da",
        rule="#d0d7de",
        key="#953800",
        dots="#8c959f",
        value="#24292f",
        number="#0550ae",
    ),
    "dark": ThemePalette(
        bg="#0d1117",
        border="#30363d",
        ascii="#c9d1d9",
        header="#58a6ff",
        rule="#3d444d",
        key="#ffa657",
        dots="#484f58",
        value="#c9d1d9",
        number="#79c0ff",
    ),
}


@dataclass
class TextSpan:
    text: str
    color: str


Line = list[TextSpan]


def escape_xml(text: str) -> str:
    """Escapes special XML characters (&, <, >, ")."""
    return html.escape(text, quote=True)


def truncate_text(text: str, max_len: int) -> str:
    """Truncates text with ellipsis if exceeding max length."""
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def build_info_lines(stats: GitHubStats, palette: ThemePalette) -> list[Line]:
    """
    Constructs the formatted neofetch-style text lines for the right-hand panel.
    """
    lines: list[Line] = []

    def add_header(title: str) -> None:
        label = f" {title} "
        fill_count = max(0, INFO_COLS - len(label) - 1)
        fill = "─" * fill_count
        lines.append([
            TextSpan("─", palette.rule),
            TextSpan(label, palette.header),
            TextSpan(fill, palette.rule),
        ])

    def add_kv(key: str, val: str, val_color: str = palette.value) -> None:
        clean_val = truncate_text(val, INFO_COLS - len(key) - 8)
        dot_count = max(2, INFO_COLS - len(key) - len(clean_val) - 6)
        lines.append([
            TextSpan(f". {key}: ", palette.key),
            TextSpan("." * dot_count, palette.dots),
            TextSpan(f" {clean_val}", val_color),
        ])

    def add_kv2(k1: str, v1: str, k2: str, v2: str) -> None:
        half = (INFO_COLS - 3) // 2

        def make_part(k: str, v: str) -> Line:
            dots = max(2, half - len(k) - len(v) - 6)
            return [
                TextSpan(f". {k}: ", palette.key),
                TextSpan("." * dots, palette.dots),
                TextSpan(f" {v}", palette.number),
            ]

        lines.append([
            *make_part(k1, v1),
            TextSpan(" | ", palette.rule),
            *make_part(k2, v2),
        ])

    def add_blank() -> None:
        lines.append([])

    # Header Section
    add_header(f"{stats.login}@github")
    add_kv("Uptime", account_uptime(stats.created_at))
    if stats.location:
        add_kv("Location", stats.location)
    if stats.company:
        add_kv("Company", stats.company)
    if stats.languages:
        add_kv("Languages", ", ".join(stats.languages))

    # Contact Section
    add_blank()
    add_header("Contact")
    if stats.email:
        add_kv("Email", stats.email)
    if stats.blog:
        add_kv("Website", stats.blog)
    if stats.twitter:
        add_kv("Twitter", f"@{stats.twitter}")
    add_kv("GitHub", f"github.com/{stats.login}")

    # GitHub Stats Section
    add_blank()
    add_header("GitHub Stats")
    n = lambda num: f"{num:,}"
    add_kv2("Repos", n(stats.public_repos), "Stars", n(stats.stars))

    if stats.commits is not None:
        add_kv2("Commits", n(stats.commits), "Followers", n(stats.followers))
    else:
        add_kv("Followers", n(stats.followers), palette.number)

    return lines


def render_svg_card(
    stats: GitHubStats,
    ascii_lines: list[str],
    theme: str = "dark"
) -> str:
    """
    Renders complete SVG document for the given profile stats and ASCII art lines.

    Parameters:
    - stats: GitHubStats object containing fetched metrics.
    - ascii_lines: Array of generated ASCII text strings.
    - theme: 'light' or 'dark'.
    """
    palette = PALETTES.get(theme, PALETTES["dark"])
    info_lines = build_info_lines(stats, palette)

    ascii_cols = max((len(line) for line in ascii_lines), default=1)
    info_x = PAD + ascii_cols * ASCII_CHAR_WIDTH + GAP
    width = round(info_x + INFO_COLS * CHAR_WIDTH + PAD)

    ascii_height = len(ascii_lines) * ASCII_LINE_HEIGHT
    info_height = len(info_lines) * LINE_HEIGHT
    content_height = max(ascii_height, info_height)
    height = PAD * 2 + content_height

    # Vertically align shorter panel
    ascii_top = PAD + (content_height - ascii_height) / 2.0
    info_top = PAD + (content_height - info_height) / 2.0

    font_family = """font-family="'Consolas', 'Menlo', 'DejaVu Sans Mono', monospace" xml:space="preserve" """
    ascii_attrs = f'{font_family} font-size="{ASCII_FONT_SIZE}"'
    info_attrs = f'{font_family} font-size="{FONT_SIZE}"'

    # Render ASCII SVG lines
    ascii_elements = []
    for i, line in enumerate(ascii_lines):
        if not line:
            continue
        y = ascii_top + (i + 1) * ASCII_LINE_HEIGHT - 3.0
        ascii_elements.append(
            f'<text x="{PAD}" y="{y:.1f}" fill="{palette.ascii}" {ascii_attrs}>{escape_xml(line)}</text>'
        )

    # Render Info SVG lines
    info_elements = []
    for i, spans in enumerate(info_lines):
        if not spans:
            continue
        y = info_top + (i + 1) * LINE_HEIGHT - 5.0
        tspan_xml = "".join(
            f'<tspan fill="{span.color}">{escape_xml(span.text)}</tspan>'
            for span in spans
        )
        info_elements.append(
            f'<text x="{info_x:.1f}" y="{y:.1f}" {info_attrs}>{tspan_xml}</text>'
        )

    ascii_body = "\n  ".join(ascii_elements)
    info_body = "\n  ".join(info_elements)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="ASCII GitHub profile card for {escape_xml(stats.login)}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{palette.bg}" stroke="{palette.border}"/>
  {ascii_body}
  {info_body}
</svg>"""

    return svg_content
