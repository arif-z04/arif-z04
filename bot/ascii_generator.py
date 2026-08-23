"""
bot.ascii_generator
~~~~~~~~~~~~~~~~~~~
High-detail ASCII art generator. Converts avatar images into expressive, crisp
ASCII line matrices using subcell quadrant analysis, Sobel edge detection,
percentile normalization, and Floyd-Steinberg dithering.
"""

from io import BytesIO
import math
import logging
from PIL import Image
import requests

from bot.config import Config

logger = logging.getLogger(__name__)

# Monospace character aspect ratio (width / height)
CHAR_ASPECT = 0.5

# High-detail character density ramps (from dark/sparse to dense/heavy)
# Denser symbols represent dark ink in light mode, or bright pixels in dark mode.
ASCII_RAMP = r" .'`^\"...,:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

# Directional edge characters
EDGE_CHARS = ["|", "\\", "-", "/"]

# Edge detection sensitivity threshold
EDGE_THRESHOLD = 1.0
EDGE_VOTES_NEEDED = 3


def fetch_avatar_image(avatar_url: str) -> Image.Image:
    """
    Downloads the GitHub avatar image and returns a Pillow Image object.
    Requests higher resolution (s=400) for clean downsampling.
    """
    # Append size parameter for higher resolution source
    url = f"{avatar_url}&s=400" if "?" in avatar_url else f"{avatar_url}?s=400"
    headers = {"User-Agent": Config.USER_AGENT}

    logger.info("Downloading avatar image from %s", avatar_url)
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()

    return Image.open(BytesIO(res.content)).convert("RGBA")


def apply_unsharp_mask(grid: list[list[float]], alpha_grid: list[list[float]]) -> None:
    """
    Applies an adaptive unsharp mask filter to recover fine features (facial features,
    glasses, hair) lost during downsampling. Modifies brightness grid in-place.
    """
    rows = len(grid)
    cols = len(grid[0])
    source = [row[:] for row in grid]

    deviations = []
    dev_sum = 0.0
    dev_count = 0

    for y in range(rows):
        dev_row = []
        for x in range(cols):
            if alpha_grid[y][x] < 0.2:
                dev_row.append(0.0)
                continue

            neighborhood_sum = 0.0
            neighborhood_count = 0

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < rows and 0 <= nx < cols and alpha_grid[ny][nx] >= 0.2:
                        neighborhood_sum += source[ny][nx]
                        neighborhood_count += 1

            if neighborhood_count > 0:
                mean = neighborhood_sum / neighborhood_count
                dev = source[y][x] - mean
                dev_row.append(dev)
                dev_sum += abs(dev)
                dev_count += 1
            else:
                dev_row.append(0.0)

        deviations.append(dev_row)

    if dev_count == 0:
        return

    texture = dev_sum / dev_count
    amount = min(0.9, max(0.0, (texture - 0.03) * 15.0))
    if amount == 0:
        return

    for y in range(rows):
        for x in range(cols):
            if alpha_grid[y][x] >= 0.2:
                grid[y][x] = min(1.0, max(0.0, source[y][x] + amount * deviations[y][x]))


def normalize_brightness(grid: list[list[float]], alpha_grid: list[list[float]], gamma: float = 0.9) -> None:
    """
    Normalizes cell brightness using 2nd to 98th percentile stretching
    and applies gamma correction for balanced midtones.
    """
    values = []
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if alpha_grid[y][x] >= 0.2:
                values.append(grid[y][x])

    if not values:
        return

    values.sort()
    lo = values[int(len(values) * 0.02)]
    hi = values[min(len(values) - 1, int(len(values) * 0.98))]
    span = max(hi - lo, 0.01)

    for y in range(len(grid)):
        for x in range(len(grid[0])):
            stretched = min(1.0, max(0.0, (grid[y][x] - lo) / span))
            grid[y][x] = math.pow(stretched, gamma)


def compute_subcell_edges(grid: list[list[float]], alpha_grid: list[list[float]]) -> list[list[int | None]]:
    r"""
    Applies Sobel operator across subcells to compute edge magnitude and direction angle.
    Returns direction index (0: |, 1: \, 2: -, 3: /) or None.
    """
    rows = len(grid)
    cols = len(grid[0])

    def get_val(x: int, y: int) -> float:
        cy = min(rows - 1, max(0, y))
        cx = min(cols - 1, max(0, x))
        return 0.0 if alpha_grid[cy][cx] < 0.2 else grid[cy][cx]

    edge_grid: list[list[int | None]] = []

    for y in range(rows):
        row_edges: list[int | None] = []
        for x in range(cols):
            gx = (
                -get_val(x - 1, y - 1) - 2 * get_val(x - 1, y) - get_val(x - 1, y + 1)
                + get_val(x + 1, y - 1) + 2 * get_val(x + 1, y) + get_val(x + 1, y + 1)
            )
            gy = (
                (-get_val(x - 1, y - 1) - 2 * get_val(x, y - 1) - get_val(x + 1, y - 1)
                 + get_val(x - 1, y + 1) + 2 * get_val(x, y + 1) + get_val(x + 1, y + 1)) / 2.0
            )

            if math.hypot(gx, gy) < EDGE_THRESHOLD:
                row_edges.append(None)
            else:
                deg = (math.atan2(gy, gx) * 180.0 / math.pi + 180.0) % 180.0
                if deg < 22.5 or deg >= 157.5:
                    row_edges.append(0)  # |
                elif deg < 67.5:
                    row_edges.append(1)  # \
                elif deg < 112.5:
                    row_edges.append(2)  # -
                else:
                    row_edges.append(3)  # /
        edge_grid.append(row_edges)

    return edge_grid


def vote_cell_edge(sub_edges: list[int | None]) -> str | None:
    """Votes dominant direction character among 4 subcells."""
    counts = [0, 0, 0, 0]
    for e in sub_edges:
        if e is not None:
            counts[e] += 1
    winner = counts.index(max(counts))
    if counts[winner] >= EDGE_VOTES_NEEDED:
        return EDGE_CHARS[winner]
    return None


def generate_ascii_art(
    avatar_img: Image.Image,
    theme: str = "dark",
    cols: int = 100
) -> list[str]:
    """
    Main conversion routine: Avatar Image -> Detailed ASCII Lines.

    Parameters:
    - avatar_img: PIL Image object in RGBA mode.
    - theme: 'light' or 'dark'.
    - cols: Number of character columns for the ASCII grid (default: 100).
    """
    img_w, img_h = avatar_img.size
    rows = max(1, round((cols * img_h * CHAR_ASPECT) / img_w))

    # Subcell sampling resolution (2x2 subcells per character cell)
    sub_w = cols * 2
    sub_h = rows * 2

    resized_img = avatar_img.resize((sub_w, sub_h), Image.Resampling.LANCZOS)
    pixels = resized_img.load()

    grid: list[list[float]] = []
    alpha_grid: list[list[float]] = []

    for y in range(sub_h):
        brightness_row = []
        alpha_row = []
        for x in range(sub_w):
            r, g, b, a = pixels[x, y]
            alpha_norm = a / 255.0
            # ITU-R BT.709 relative luminance
            luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0

            # Light mode: darker pixel = denser ASCII character
            # Dark mode : brighter pixel = denser ASCII character
            oriented = 1.0 - luma if theme == "light" else luma
            cell_brightness = oriented * alpha_norm

            brightness_row.append(cell_brightness)
            alpha_row.append(alpha_norm)

        grid.append(brightness_row)
        alpha_grid.append(alpha_row)

    # Image processing passes
    apply_unsharp_mask(grid, alpha_grid)
    normalize_brightness(grid, alpha_grid)
    edge_grid = compute_subcell_edges(grid, alpha_grid)

    # Floyd-Steinberg error diffusion carry grid across character cells
    carry: list[list[float]] = [[0.0] * cols for _ in range(rows)]

    lines: list[str] = []
    ramp_len = len(ASCII_RAMP)

    for y in range(rows):
        line_chars = []
        for x in range(cols):
            quad_y0 = y * 2
            quad_x0 = x * 2

            sub_alphas = [
                alpha_grid[quad_y0][quad_x0],
                alpha_grid[quad_y0][quad_x0 + 1],
                alpha_grid[quad_y0 + 1][quad_x0],
                alpha_grid[quad_y0 + 1][quad_x0 + 1],
            ]

            # Background cells become space
            if all(a < 0.2 for a in sub_alphas):
                line_chars.append(" ")
                continue

            sub_edges = [
                edge_grid[quad_y0][quad_x0],
                edge_grid[quad_y0][quad_x0 + 1],
                edge_grid[quad_y0 + 1][quad_x0],
                edge_grid[quad_y0 + 1][quad_x0 + 1],
            ]

            edge_char = vote_cell_edge(sub_edges)

            # Average cell brightness plus Floyd-Steinberg carry
            sub_bright = [
                grid[quad_y0][quad_x0],
                grid[quad_y0][quad_x0 + 1],
                grid[quad_y0 + 1][quad_x0],
                grid[quad_y0 + 1][quad_x0 + 1],
            ]
            cell_mean = sum(sub_bright) / 4.0 + carry[y][x]
            clamped_mean = min(1.0, max(0.0, cell_mean))

            if edge_char:
                char = edge_char
            else:
                ramp_idx = min(ramp_len - 1, int(round(clamped_mean * (ramp_len - 1))))
                char = ASCII_RAMP[ramp_idx]

            line_chars.append(char)

            # Dithering error calculation
            glyph_val = (ASCII_RAMP.find(char) / (ramp_len - 1)) if char in ASCII_RAMP else clamped_mean
            error = (clamped_mean - glyph_val) * 0.25

            if error != 0:
                if x + 1 < cols:
                    carry[y][x + 1] += (error * 7.0) / 16.0
                if y + 1 < rows:
                    if x > 0:
                        carry[y + 1][x - 1] += (error * 3.0) / 16.0
                    carry[y + 1][x] += (error * 5.0) / 16.0
                    if x + 1 < cols:
                        carry[y + 1][x + 1] += (error * 1.0) / 16.0

        lines.append("".join(line_chars).rstrip())

    # Trim leading/trailing blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return lines
