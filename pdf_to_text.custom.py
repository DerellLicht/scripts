#!/usr/bin/env python3
"""
pdf_to_text.py

Converts a scanned PDF (image-only pages, no text layer) into a single
plain-text file using OCR. Built for a scanned-PDF -> epub pipeline.

Usage:
    python pdf_to_text.py my_scanned_pdf_book.pdf
    python pdf_to_text.py my_scanned_pdf_book.pdf -o output_name.txt
    python pdf_to_text.py my_scanned_pdf_book.pdf --dpi 300 --lang eng

Requires (installed separately, not via pip):
    - Poppler   (provides pdftoppm, used by pdf2image to rasterize pages)
    - Tesseract (the actual OCR engine, used by pytesseract)

Requires (pip install pdf2image pytesseract pillow):
    - pdf2image
    - pytesseract
    - Pillow (pulled in automatically as a dependency)

If Poppler or Tesseract are not on PATH, set POPPLER_PATH / TESSERACT_PATH
below, or pass --poppler-path / --tesseract-cmd on the command line.
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
from pdf2image.pdf2image import pdfinfo_from_path
import pytesseract

# --- Optional manual paths (leave as None if both tools are on PATH) ---
POPPLER_PATH = None     # e.g. r"D:\Tools\poppler\Library\bin"
TESSERACT_PATH = None   # e.g. r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_threshold(
    pil_image: Image.Image, block_size: int, c: int, denoise: int, illum_blur: int
) -> Image.Image:
    """
    Convert a page image to clean black-and-white using illumination
    normalization, denoising, and adaptive thresholding.

    This is a blunt, all-or-nothing approach: every pixel gets forced to
    pure black or pure white. Effective on some scans, but risky to tune --
    testing showed it can degrade already-good regions of a page while
    fixing a problem area. Kept available via --mode threshold, but
    --mode clahe (below) is gentler and the current default.
    """
    gray = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)

    if illum_blur > 0:
        if illum_blur % 2 == 0:
            illum_blur += 1
        background = cv2.GaussianBlur(gray, (illum_blur, illum_blur), 0)
        gray = cv2.divide(gray, background, scale=255)

    if denoise > 0:
        # medianBlur requires an odd kernel size.
        if denoise % 2 == 0:
            denoise += 1
        gray = cv2.medianBlur(gray, denoise)

    # block_size must be odd; adaptiveThreshold requires it.
    if block_size % 2 == 0:
        block_size += 1

    thresholded = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        c,
    )
    return Image.fromarray(thresholded)


def preprocess_clahe(pil_image: Image.Image, clip_limit: float, tile_size: int) -> Image.Image:
    """
    Boost local contrast using CLAHE (Contrast Limited Adaptive Histogram
    Equalization), without ever committing pixels to pure black/white.

    The image is divided into small tiles; contrast within each tile is
    stretched independently, so a shadowed tile gets brightened/sharpened
    on its own terms while an already well-lit tile is left alone. Tesseract
    reads grayscale images fine, so there's no need to force a hard
    threshold decision -- this only nudges contrast, leaving far more of
    the original detail (and far less room for damage) than binarizing.
    """
    gray = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    enhanced = clahe.apply(gray)
    return Image.fromarray(enhanced)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OCR a scanned PDF into a single plain-text file."
    )
    parser.add_argument("pdf_path", type=Path, help="Path to the scanned PDF file.")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output .txt path (default: same name as PDF, .txt extension).",
    )
    parser.add_argument(
        "--dpi", type=int, default=300,
        help="Rasterization resolution. 300 is a good balance of speed/accuracy (default: 300).",
    )
    parser.add_argument(
        "--lang", default="eng",
        help="Tesseract language code, e.g. 'eng', 'deu', 'eng+deu' (default: eng).",
    )
    parser.add_argument(
        "--poppler-path", default=POPPLER_PATH,
        help="Override path to Poppler's bin folder, if not on PATH.",
    )
    parser.add_argument(
        "--tesseract-cmd", default=TESSERACT_PATH,
        help="Override path to tesseract.exe, if not on PATH.",
    )
    parser.add_argument(
        "--mode", choices=["none", "clahe", "threshold"], default="none",
        help="Preprocessing mode (default: none). 'none' OCRs the raw scan as-is -- "
             "testing showed this beats both processed modes on well-lit pages. "
             "'clahe' gently boosts local contrast without forcing pixels to black/white "
             "-- try this first for shadowed pages. 'threshold' is the older, more "
             "aggressive black-and-white conversion; higher risk of damaging good text.",
    )
    parser.add_argument(
        "--clahe-clip", type=float, default=2.0,
        help="CLAHE contrast boost strength (default: 2.0). Higher = more aggressive "
             "contrast enhancement; try 3-4 if shadowed text is still too faint.",
    )
    parser.add_argument(
        "--clahe-tile", type=int, default=8,
        help="CLAHE tile grid size (default: 8, meaning an 8x8 grid of local regions). "
             "Smaller tiles react more locally to shadows but can look patchy.",
    )
    parser.add_argument(
        "--block-size", type=int, default=35,
        help="[--mode threshold] Adaptive threshold neighborhood size in pixels, must be "
             "odd (default: 35). Larger = smoother, better for big shadow gradients.",
    )
    parser.add_argument(
        "--c", type=int, default=15,
        help="[--mode threshold] Adaptive threshold constant subtracted from the local "
             "mean (default: 15). Raise it if text is too thin/broken; lower it if shadow "
             "noise remains.",
    )
    parser.add_argument(
        "--denoise", type=int, default=3,
        help="[--mode threshold] Median blur kernel size in pixels, must be odd (default: "
             "3). Strips speckle/grain noise before thresholding. Set to 0 to disable.",
    )
    parser.add_argument(
        "--illum-blur", type=int, default=51,
        help="[--mode threshold] Gaussian blur size used to estimate and remove broad "
             "shading gradients before thresholding (default: 51, must be odd). "
             "Set to 0 to disable.",
    )
    parser.add_argument(
        "--preview", type=int, default=None, metavar="PAGE_NUM",
        help="Also save a preprocessed PNG of one page (1-indexed) next to the output, "
             "so you can eyeball it alongside the OCR text. Combine with --pages to run "
             "OCR on the same page; if --pages is omitted, it defaults to this page.",
    )
    parser.add_argument(
        "--pages", default=None, metavar="RANGE",
        help="Run full OCR on just a page or range, instead of the whole book, e.g. "
             "'18' or '18-19' or '18,20,25'. Useful for testing preprocessing settings "
             "against real OCR output before committing to a full run. Can be combined "
             "with --preview to inspect a different page's image at the same time.",
    )
    return parser.parse_args()


def parse_page_range(spec: str, total: int) -> list[int]:
    """Parse a page spec like '18', '18-19', or '18,20,25' into a sorted page list."""
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str), int(end_str)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    for p in pages:
        if not (1 <= p <= total):
            raise ValueError(f"page {p} out of range (1-{total})")
    return sorted(pages)


def main() -> int:
    args = parse_args()

    if not args.pdf_path.is_file():
        print(f"Error: file not found: {args.pdf_path}", file=sys.stderr)
        return 1

    if args.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd

    output_path = args.output or args.pdf_path.with_suffix(".txt")

    print(f"Reading page count from: {args.pdf_path.name}")
    try:
        info = pdfinfo_from_path(str(args.pdf_path), poppler_path=args.poppler_path)
        total = info["Pages"]
    except PDFInfoNotInstalledError:
        print(
            "Error: Poppler not found. Install it and add its 'bin' folder to "
            "PATH, or pass --poppler-path.",
            file=sys.stderr,
        )
        return 1
    except (PDFPageCountError, PDFSyntaxError) as e:
        print(f"Error reading PDF: {e}", file=sys.stderr)
        return 1

    def get_page(page_num: int) -> Image.Image:
        """Rasterize a single page (1-indexed) on demand."""
        result = convert_from_path(
            str(args.pdf_path),
            dpi=args.dpi,
            poppler_path=args.poppler_path,
            first_page=page_num,
            last_page=page_num,
        )
        return result[0]

    def apply_preprocessing(page_image: Image.Image) -> Image.Image:
        """Dispatch to the selected preprocessing mode."""
        if args.mode == "clahe":
            return preprocess_clahe(page_image, args.clahe_clip, args.clahe_tile)
        elif args.mode == "threshold":
            return preprocess_threshold(
                page_image, args.block_size, args.c, args.denoise, args.illum_blur
            )
        return page_image  # mode == "none"

    # --preview: rasterize + preprocess one page, save as PNG for visual inspection.
    # Falls through to the normal OCR step below rather than exiting, so you can
    # look at the preprocessed image AND the OCR text from the same run. If
    # --pages wasn't given, default it to the preview page so OCR runs on that
    # same page rather than the whole book.
    if args.preview is not None:
        if not (1 <= args.preview <= total):
            print(f"Error: --preview page {args.preview} out of range (1-{total}).", file=sys.stderr)
            return 1
        page_image = apply_preprocessing(get_page(args.preview))
        preview_path = output_path.with_name(f"{output_path.stem}_preview_p{args.preview}.png")
        page_image.save(preview_path)
        print(f"Saved preprocessed ({args.mode}) preview of page {args.preview} to: {preview_path}")
        if args.pages is None:
            args.pages = str(args.preview)

    print(f"Found {total} page(s). Starting OCR (lang={args.lang}, mode={args.mode})...")

    if args.pages:
        try:
            page_numbers = parse_page_range(args.pages, total)
        except ValueError as e:
            print(f"Error in --pages: {e}", file=sys.stderr)
            return 1
        # Test runs get their own filename so they never overwrite the real output.
        pages_tag = args.pages.replace(",", "_").replace("-", "to")
        output_path = output_path.with_name(f"{output_path.stem}_pages{pages_tag}.txt")
        print(f"Running OCR on page(s): {args.pages}")
    else:
        page_numbers = list(range(1, total + 1))

    run_total = len(page_numbers)
    ocr_text_parts = []
    for idx, page_num in enumerate(page_numbers, start=1):
        print(f"  OCR page {page_num} ({idx}/{run_total})...", end="\r")
        page_image = apply_preprocessing(get_page(page_num))
        try:
            text = pytesseract.image_to_string(page_image, lang=args.lang)
        except pytesseract.TesseractNotFoundError:
            print(
                "\nError: Tesseract not found. Install it and add it to PATH, "
                "or pass --tesseract-cmd.",
                file=sys.stderr,
            )
            return 1
        ocr_text_parts.append(text.strip())

    print(f"  OCR page {page_numbers[-1]} ({run_total}/{run_total})... done.")

    full_text = "\n\n".join(ocr_text_parts)
    output_path.write_text(full_text, encoding="utf-8")

    print(f"Wrote {len(full_text):,} characters to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
