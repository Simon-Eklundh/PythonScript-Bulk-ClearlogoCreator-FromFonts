import random
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR_OK = Fore.GREEN
    COLOR_WARN = Fore.YELLOW
    COLOR_ERR = Fore.RED
    COLOR_INFO = Fore.CYAN
    COLOR_TITLE = Fore.MAGENTA + Style.BRIGHT
    COLOR_RESET = Style.RESET_ALL
except ImportError:
    COLOR_OK = ""
    COLOR_WARN = ""
    COLOR_ERR = ""
    COLOR_INFO = ""
    COLOR_TITLE = ""
    COLOR_RESET = ""

if getattr(sys, "frozen", False):
    PROJECT_PATH = Path(sys.executable).resolve().parent
else:
    PROJECT_PATH = Path(__file__).resolve().parent

FONTS_FOLDER = PROJECT_PATH / "fonts"
PATHS_FILE = PROJECT_PATH / "paths.txt"

IMG_SIZE = (800, 310)
TEXT_FILL = (255, 255, 255, 255)
STROKE_FILL = (0, 0, 0, 255)
STROKE_WIDTH = 1
PADDING = 10
MAX_FONT_SIZE = 500


def draw_text_with_outline(draw, position, text, font):
    x, y = position
    for dx in range(-STROKE_WIDTH, STROKE_WIDTH + 1):
        for dy in range(-STROKE_WIDTH, STROKE_WIDTH + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=STROKE_FILL)
    draw.text((x, y), text, font=font, fill=TEXT_FILL)


def show_menu():
    print(f"{COLOR_TITLE}=========================================")
    print("Clearlogo Creator")
    print(f"========================================={COLOR_RESET}")
    print("1 = Update (create missing logos only)")
    print("2 = Replace (recreate all logos)")
    print("3 = Update (Dry Run)")
    print("4 = Replace (Dry Run)")
    print()

    while True:
        choice = input("Select: ").strip()
        if choice == "1":
            return False, False
        if choice == "2":
            return True, False
        if choice == "3":
            return False, True
        if choice == "4":
            return True, True
        print(f"{COLOR_ERR}Invalid input, please enter 1, 2, 3 or 4.{COLOR_RESET}")


def build_logo(folder_name, font_files):
    fonts_tried = set()
    while len(fonts_tried) < len(font_files):
        font_path = random.choice(font_files)
        if font_path in fonts_tried:
            continue
        fonts_tried.add(font_path)

        try:
            img = Image.new("RGBA", IMG_SIZE, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            min_font = 10
            max_font = MAX_FONT_SIZE
            best_font = min_font

            while min_font <= max_font:
                mid = (min_font + max_font) // 2
                font = ImageFont.truetype(font_path, mid)
                bbox = draw.textbbox((0, 0), folder_name, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]

                if text_w <= IMG_SIZE[0] - 2 * PADDING and text_h <= IMG_SIZE[1] - 2 * PADDING:
                    best_font = mid
                    min_font = mid + 1
                else:
                    max_font = mid - 1

            font = ImageFont.truetype(font_path, best_font)
            bbox = draw.textbbox((0, 0), folder_name, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            x = (IMG_SIZE[0] - text_w) // 2 - bbox[0]
            y = (IMG_SIZE[1] - text_h) // 2 - bbox[1]

            draw_text_with_outline(draw, (x, y), folder_name, font)
            return img, font_path.name, best_font

        except OSError:
            print(f"{COLOR_WARN}Font broken/unusable: {font_path.name} -> trying next{COLOR_RESET}")

    return None, None, None


def format_duration(seconds):
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    REPLACE, DRY_RUN = show_menu()

    font_files = (
        list(FONTS_FOLDER.glob("*.otf"))
        + list(FONTS_FOLDER.glob("*.ttf"))
        + list(FONTS_FOLDER.glob("*.ttc"))
    )
    if not font_files:
        print(f"{COLOR_ERR}No fonts found in fonts folder!{COLOR_RESET}")
        input("Press Enter to exit...")
        return

    if not PATHS_FILE.exists():
        print(f"{COLOR_ERR}paths.txt not found at {PATHS_FILE}{COLOR_RESET}")
        input("Press Enter to exit...")
        return

    with open(PATHS_FILE, "r", encoding="utf-8") as f:
        base_paths = [line.strip() for line in f if line.strip()]

    if not base_paths:
        print(f"{COLOR_ERR}No paths found in paths.txt!{COLOR_RESET}")
        input("Press Enter to exit...")
        return

    stats = {
        "paths_processed": 0,
        "folders_found": 0,
        "created": 0,
        "replaced": 0,
        "skipped": 0,
        "dryrun_create": 0,
        "dryrun_replace": 0,
        "errors": 0,
    }

    start_time = time.time()

    all_jobs = []
    for base_path_str in base_paths:
        BASE_PATH = Path(base_path_str)
        if not BASE_PATH.exists():
            print(f"{COLOR_WARN}Path does not exist: {BASE_PATH}{COLOR_RESET}")
            continue

        subfolders = [d for d in BASE_PATH.iterdir() if d.is_dir()]
        if not subfolders:
            print(f"{COLOR_WARN}No subfolders in: {BASE_PATH}{COLOR_RESET}")
            continue

        stats["paths_processed"] += 1
        stats["folders_found"] += len(subfolders)
        print(f"{COLOR_INFO}Processing {len(subfolders)} subfolders in: {BASE_PATH}{COLOR_RESET}")

        for folder in subfolders:
            all_jobs.append(folder)

    total = len(all_jobs)

    for i, folder in enumerate(all_jobs, start=1):
        output_file = folder / "clearlogo.png"
        folder_name = folder.name
        exists = output_file.exists()

        print(f"[{i}/{total}] {folder_name}")

        if exists and not REPLACE:
            print(f"{COLOR_WARN}Skipped (exists): {output_file}{COLOR_RESET}")
            stats["skipped"] += 1
            continue

        if DRY_RUN:
            if exists:
                stats["dryrun_replace"] += 1
                print(f"{COLOR_INFO}Dry run: would replace {output_file}{COLOR_RESET}")
            else:
                stats["dryrun_create"] += 1
                print(f"{COLOR_INFO}Dry run: would create {output_file}{COLOR_RESET}")
            continue

        img, font_name, font_size = build_logo(folder_name, font_files)

        if img is None:
            print(f"{COLOR_ERR}Could not create logo for: {folder_name}{COLOR_RESET}")
            stats["errors"] += 1
            continue

        img.save(output_file)

        if exists:
            stats["replaced"] += 1
            print(f"{COLOR_OK}Replaced: {output_file} | Font: {font_name} | Size: {font_size}{COLOR_RESET}")
        else:
            stats["created"] += 1
            print(f"{COLOR_OK}Created: {output_file} | Font: {font_name} | Size: {font_size}{COLOR_RESET}")

    elapsed = time.time() - start_time

    print()
    print(f"{COLOR_TITLE}=========================================")
    print("Statistics")
    print(f"========================================={COLOR_RESET}")
    print(f"Paths processed: {stats['paths_processed']}")
    print(f"Folders found: {stats['folders_found']}")
    print(f"Logos created: {stats['created']}")
    print(f"Logos replaced: {stats['replaced']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Dry run 'would create': {stats['dryrun_create']}")
    print(f"Dry run 'would replace': {stats['dryrun_replace']}")
    print(f"Errors: {stats['errors']}")
    print(f"Runtime: {format_duration(elapsed)}")
    print(f"{COLOR_TITLE}========================================={COLOR_RESET}")

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
