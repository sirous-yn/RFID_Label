from pathlib import Path
from datetime import date as system_date
import os
import sys
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
FONT_DIR = PROJECT_DIR / "fonts"
LOGO_PATH = PROJECT_DIR / "UR_Logo.jpg"
LABEL_PATH = PROJECT_DIR / "label.png"

# Defaults match the tested Brother QL-1100 setup. Environment variables let
# another Linux computer override the device path without editing the code.
PRINTER_MODEL = os.environ.get("LABEL_PRINTER_MODEL", "QL-1100")
PRINTER_DEVICE = os.environ.get("LABEL_PRINTER_DEVICE", "/dev/usb/lp0")
PRINTER_BACKEND = os.environ.get("LABEL_PRINTER_BACKEND", "linux_kernel")
LABEL_TYPE = os.environ.get("LABEL_MEDIA_TYPE", "103")  # DK-2246 continuous roll

# Keep the existing print width. The label height is calculated
# from the content so the printer cuts off unused blank space.
LABEL_WIDTH = 1164

LEFT_MARGIN = 50
RIGHT_MARGIN = 50
BOTTOM_MARGIN = 25

LOGO_MAX_WIDTH = 230
LOGO_MAX_HEIGHT = 125
LOGO_RIGHT_MARGIN = 40
LOGO_TOP_MARGIN = 20
LOGO_TITLE_GAP = 18

TITLE_FONT_SIZE = 42
MIN_TITLE_FONT_SIZE = 18
TEXT_FONT_SIZE = 45
LINE_SPACING = 58
SECTION_SPACING = 12

MAX_TEXT_WIDTH = LABEL_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


# ============================================================
# FONT LOADING
# ============================================================

def load_font(filename: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font stored in this project's fonts directory."""
    path = FONT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Font file not found: {path}\n"
            "Make sure the fonts folder contains DejaVuSans.ttf and "
            "DejaVuSans-Bold.ttf."
        )
    return ImageFont.truetype(str(path), size)


def load_fonts():
    """Load the default title and identification text fonts."""
    title_font = load_font("DejaVuSans-Bold.ttf", TITLE_FONT_SIZE)
    text_font = load_font("DejaVuSans.ttf", TEXT_FONT_SIZE)
    return title_font, text_font


# ============================================================
# UNIVERSITY LOGO
# ============================================================

def load_university_logo():
    """Load the logo, trim pale margins, and resize for thermal printing."""
    if not LOGO_PATH.exists():
        return None

    try:
        with Image.open(LOGO_PATH) as logo_file:
            logo = logo_file.convert("RGB")

        gray = ImageOps.grayscale(logo)
        mask = gray.point(lambda pixel: 255 if pixel < 230 else 0)
        content_box = mask.getbbox()

        if content_box:
            logo = logo.crop(content_box)
            padding = 6
            padded = Image.new(
                "RGB",
                (logo.width + 2 * padding, logo.height + 2 * padding),
                "white",
            )
            padded.paste(logo, (padding, padding))
            logo = padded

        logo = ImageOps.grayscale(logo)
        logo = ImageOps.autocontrast(logo).convert("RGB")
        logo.thumbnail(
            (LOGO_MAX_WIDTH, LOGO_MAX_HEIGHT),
            Image.Resampling.LANCZOS,
        )
        return logo

    except Exception as exc:
        print(f"Warning: Could not load university logo: {exc}")
        return None


# ============================================================
# PID FORMATTING
# ============================================================

def shorten_pid(pid):
    """Keep at most three trailing zeros in the displayed PID."""
    pid = str(pid).strip()
    if not pid:
        return ""

    trailing_zeros = len(pid) - len(pid.rstrip("0"))
    if trailing_zeros > 3:
        pid = pid[:-(trailing_zeros - 3)]
    return pid


def group_pid(pid):
    """Group PID characters in blocks of four."""
    pid = str(pid).replace(" ", "").strip()
    return " ".join(pid[index:index + 4] for index in range(0, len(pid), 4))


def wrap_pid(pid, font, draw, max_width):
    """Wrap a grouped PID into lines that fit the available width."""
    groups = group_pid(pid).split()
    lines = []
    current_line = ""

    for group in groups:
        candidate = f"{current_line} {group}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current_line:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = group

    if current_line:
        lines.append(current_line)
    return lines


# ============================================================
# GENERAL TEXT WRAPPING
# ============================================================

def wrap_text_by_width(text, font, draw, max_width):
    """Wrap text to fit the available label width."""
    text = str(text).strip()
    if not text:
        return []

    lines = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width or not current_line:
                current_line = candidate
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

    return lines


def wrap_pid_groups_on_lines(groups, font, draw, max_width):
    """Group a list of PID blocks into lines, preserving the block order."""
    lines = []
    while groups:
        current_groups = []
        while groups:
            candidate_groups = current_groups + [groups[0]]
            candidate = " ".join(candidate_groups)
            if draw.textlength(candidate, font=font) <= max_width:
                current_groups.append(groups.pop(0))
            elif not current_groups:
                # Prevent a loop for an unusually wide single group.
                current_groups.append(groups.pop(0))
                break
            else:
                break
        lines.append(" ".join(current_groups))
    return lines


# ============================================================
# LABEL RENDERING
# ============================================================

def render_label(
    run_id="",
    pid="",
    board_type="",
    extra_info="",
    title="BOARD IDENTIFICATION",
    include_logo=True,
    date=None,
):
    """Render a label as a PIL image, without sending it to the printer.

    Empty fields are omitted. The title is editable and may be an empty
    string. The university logo is placed at the upper right. The image
    height is trimmed to the content.
    """
    run_id = str(run_id).strip()
    pid = str(pid).strip()
    board_type = str(board_type).strip().upper()
    extra_info = str(extra_info).strip()
    title = str(title).strip()
    # None means use today's date; an empty string deliberately omits it.
    date = system_date.today().strftime("%Y-%m-%d") if date is None else str(date).strip()

    title_font, text_font = load_fonts()
    logo = load_university_logo() if include_logo else None

    # Large temporary canvas; crop it to the content before returning.
    canvas = Image.new("RGB", (LABEL_WIDTH, 3000), "white")
    draw = ImageDraw.Draw(canvas)

    logo_x = None
    logo_bottom = 0
    if logo is not None:
        logo_x = LABEL_WIDTH - LOGO_RIGHT_MARGIN - logo.width
        logo_y = LOGO_TOP_MARGIN
        canvas.paste(logo, (logo_x, logo_y))
        logo_bottom = logo_y + logo.height
        draw = ImageDraw.Draw(canvas)

    # Keep an editable title centered. Reduce the font size when needed
    # so the title does not collide with the logo on the right.
    title_lines = []
    if title:
        available_title_width = LABEL_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
        if logo_x is not None:
            # The centered title's right edge must stay left of the logo.
            available_title_width = min(
                available_title_width,
                max(300, int(2 * (logo_x - LABEL_WIDTH / 2 - LOGO_TITLE_GAP))),
            )

        title_size = TITLE_FONT_SIZE
        while title_size > MIN_TITLE_FONT_SIZE:
            title_font = load_font("DejaVuSans-Bold.ttf", title_size)
            if draw.textlength(title, font=title_font) <= available_title_width:
                break
            title_size -= 1

        title_lines = wrap_text_by_width(
            title, title_font, draw, available_title_width
        )

        title_y = 35
        for line in title_lines:
            text_width = draw.textlength(line, font=title_font)
            x = (LABEL_WIDTH - text_width) / 2
            draw.text((int(x), title_y), line, font=title_font, fill="black")
            bbox = draw.textbbox((int(x), title_y), line, font=title_font)
            title_y = bbox[3] + 5

        title_bottom = title_y - 5
    else:
        title_bottom = 0

    # Place content below both title and logo to avoid overlapping them.
    y = max(title_bottom, logo_bottom) + (15 if title or logo is not None else 35)

    # Date
    if date:
        for line in wrap_text_by_width(
            f"Date: {date}", text_font, draw, MAX_TEXT_WIDTH
        ):
            draw.text((LEFT_MARGIN, y), line, font=text_font, fill="black")
            y += LINE_SPACING
        y += SECTION_SPACING

    # Run ID
    if run_id:
        for line in wrap_text_by_width(
            f"Run ID: {run_id}", text_font, draw, MAX_TEXT_WIDTH
        ):
            draw.text((LEFT_MARGIN, y), line, font=text_font, fill="black")
            y += LINE_SPACING
        y += SECTION_SPACING

    # Board type is relevant only to labels that identify a board by PID.
    if pid and board_type in {"A", "B"}:
        draw.text((LEFT_MARGIN, y), f"Board Type: {board_type}", font=text_font, fill="black")
        y += LINE_SPACING + SECTION_SPACING

    # PID: put as much as possible after "PID:" on the first line.
    if pid:
        displayed_pid = shorten_pid(pid)
        groups = [
            displayed_pid[index:index + 4]
            for index in range(0, len(displayed_pid), 4)
        ]

        first_line_groups = []
        while groups:
            candidate = "PID: " + " ".join(first_line_groups + [groups[0]])
            if draw.textlength(candidate, font=text_font) <= MAX_TEXT_WIDTH:
                first_line_groups.append(groups.pop(0))
            else:
                break

        first_line = "PID:" + (
            " " + " ".join(first_line_groups) if first_line_groups else ""
        )
        draw.text((LEFT_MARGIN, y), first_line, font=text_font, fill="black")
        y += LINE_SPACING

        for line in wrap_pid_groups_on_lines(groups, text_font, draw, MAX_TEXT_WIDTH):
            draw.text((LEFT_MARGIN, y), line, font=text_font, fill="black")
            y += LINE_SPACING

        y += SECTION_SPACING

    # Optional extra information
    if extra_info:
        for line in wrap_text_by_width(
            extra_info, text_font, draw, MAX_TEXT_WIDTH
        ):
            draw.text((LEFT_MARGIN, y), line, font=text_font, fill="black")
            y += LINE_SPACING

    # Calculate a tight crop around all content, leaving a small bottom margin.
    bottom = max(y, logo_bottom, title_bottom) + BOTTOM_MARGIN
    bottom = max(1, min(bottom, canvas.height))
    return canvas.crop((0, 0, LABEL_WIDTH, bottom))


def create_label(
    run_id="",
    pid="",
    board_type="",
    extra_info="",
    title="BOARD IDENTIFICATION",
    include_logo=True,
    date=None,
):
    """Render and save a label image; does not print it."""
    image = render_label(
        run_id=run_id,
        pid=pid,
        board_type=board_type,
        extra_info=extra_info,
        title=title,
        include_logo=include_logo,
        date=date,
    )
    image.save(LABEL_PATH)
    return LABEL_PATH


# ============================================================
# LABEL PRINTING
# ============================================================

def print_label(
    run_id="",
    pid="",
    board_type="",
    extra_info="",
    title="BOARD IDENTIFICATION",
    include_logo=True,
    date=None,
):
    """Create and print a label using the Brother QL-1100.

    Existing calls remain compatible, for example:
        print_label(run_id="0001", pid="PMT-0042")

    A custom title can be supplied by name:
        print_label(title="DETECTOR CALIBRATION", run_id="0015", pid="PMT-0042")
    """
    pid = str(pid).strip()
    board_type = str(board_type).strip().upper()
    if pid and board_type not in {"A", "B"}:
        raise ValueError("Board type A or B is required when a PID is provided.")

    label_path = create_label(
        run_id=run_id,
        pid=pid,
        board_type=board_type,
        extra_info=extra_info,
        title=title,
        include_logo=include_logo,
        date=date,
    )

    # Resolve the CLI inside the active Python environment.
    # Do not resolve sys.executable: on Linux the venv Python symlink
    # can resolve outside .venv/bin.
    scripts_dir = Path(sys.prefix) / (
        "Scripts" if os.name == "nt" else "bin"
    )
    venv_cli = scripts_dir / (
        "brother_ql.exe" if os.name == "nt" else "brother_ql"
    )

    if venv_cli.is_file():
        brother_ql_command = str(venv_cli)
    else:
        import shutil
        brother_ql_command = shutil.which("brother_ql")

    if not brother_ql_command:
        raise RuntimeError(
            "The Brother QL command-line tool was not found in the "
            "active Python environment. Run setup_linux.sh and try again."
        )

    command = [
        brother_ql_command,
        "-b", PRINTER_BACKEND,
        "-m", PRINTER_MODEL,
        "-p", PRINTER_DEVICE,
        "print",
        "-l", LABEL_TYPE,
        str(label_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Printing failed:\n" + result.stderr)

    return True
