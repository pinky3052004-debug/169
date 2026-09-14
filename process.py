#!/usr/bin/env python3
"""
Google Drive Video Processor
- Downloads videos from a Google Drive folder (via rclone)
- Adds a blurred vertical background (9:16) using ffmpeg
- Uploads the processed video to another Drive folder
- Tracks completed files so nothing is processed twice
"""

import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# ----------------------------
# CONFIG — adjust as needed
# ----------------------------
SOURCE_REMOTE = "mydrive:NanNanIphone"
DEST_REMOTE = "mydrive:NanNanIphone2"
INPUT_DIR = Path("input_folder")
PROCESSED_LOG = Path("processed.txt")
VIDEO_EXTS = {".mp4", ".mov", ".mkv"}
BATCH_SIZE = 10
LOG_FILE = Path("process_log.txt")

# ----------------------------
# LOGGING SETUP
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def check_dependencies():
    """Make sure rclone and ffmpeg are installed before doing anything."""
    for tool in ("rclone", "ffmpeg"):
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            log.error(f"'{tool}' ကို ဒီစက်ပေါ်မှာ ရှာမတွေ့ပါ။ ကျေးဇူးပြု၍ install လုပ်ပါ။")
            raise SystemExit(1)


def load_processed() -> set:
    if not PROCESSED_LOG.exists():
        PROCESSED_LOG.touch()
    return set(PROCESSED_LOG.read_text(encoding="utf-8").splitlines())


def mark_processed(filename: str):
    with PROCESSED_LOG.open("a", encoding="utf-8") as f:
        f.write(filename + "\n")


def download_source_files():
    log.info("Google Drive မှ ဗီဒီယိုဖိုင်များကို ဆွဲထုတ်နေပါသည်...")
    INPUT_DIR.mkdir(exist_ok=True)
    result = subprocess.run(
        ["rclone", "copy", SOURCE_REMOTE, str(INPUT_DIR), "--max-depth", "1"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error(f"rclone download မအောင်မြင်ပါ: {result.stderr.strip()}")
        raise SystemExit(1)


def get_unprocessed_files(processed: set) -> list:
    all_files = sorted(
        f.name for f in INPUT_DIR.iterdir()
        if f.suffix.lower() in VIDEO_EXTS
    )
    return [f for f in all_files if f not in processed][:BATCH_SIZE]


def process_video(input_path: Path, output_path: Path) -> bool:
    """Blur-background vertical reformat via ffmpeg. Returns True on success."""
    filter_complex = (
        "[0:v]scale=ih*16/9:ih,gblur=sigma=20,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2[bg];"
        "[0:v]scale=-1:1080,scale=trunc(iw/2)*2:trunc(ih/2)*2[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-c:a", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"ffmpeg conversion မအောင်မြင်ပါ ({input_path.name}): {result.stderr[-500:]}")
        return False
    return True


def upload_file(path: Path) -> bool:
    result = subprocess.run(
        ["rclone", "copy", str(path), DEST_REMOTE],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error(f"rclone upload မအောင်မြင်ပါ ({path.name}): {result.stderr.strip()}")
        return False
    return True


def main():
    start = datetime.now()
    check_dependencies()
    download_source_files()

    processed = load_processed()
    todo = get_unprocessed_files(processed)

    if not todo:
        log.info("လုပ်ဆောင်ရန် ဗီဒီယိုအသစ် မရှိတော့ပါ။")
        return

    log.info(f"ဗီဒီယို {len(todo)} ခု ကို ဒီအကြိမ်တွင် လုပ်ဆောင်မည်...")
    success_count = 0

    for i, filename in enumerate(todo, start=1):
        input_path = INPUT_DIR / filename
        output_path = Path(f"output_{filename}")
        log.info(f"[{i}/{len(todo)}] Converting: {filename}")

        ok = process_video(input_path, output_path)
        if ok:
            log.info(f"[{i}/{len(todo)}] Uploading: {output_path.name} -> {DEST_REMOTE}")
            ok = upload_file(output_path)

        if ok:
            mark_processed(filename)
            success_count += 1
        else:
            log.warning(f"{filename} ကို skip လုပ်လိုက်ပါသည် (error ရှိသဖြင့် processed.txt ထဲ မထည့်ပါ)")

        # Clean up local copies regardless of success, to save disk space
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)

    elapsed = (datetime.now() - start).total_seconds()
    log.info(f"ပြီးဆုံးပါပြီ — {success_count}/{len(todo)} ဗီဒီယို အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ "
              f"({elapsed:.1f} စက္ကန့်)")


if __name__ == "__main__":
    main()
