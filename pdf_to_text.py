# usage: python pdf_to_text.py <my_scanned_pdf_file.pdf>
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

from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
import pytesseract

# --- Optional manual paths (leave as None if both tools are on PATH) ---
POPPLER_PATH = None     # e.g. r"D:\Tools\poppler\Library\bin"
TESSERACT_PATH = None   # e.g. r"C:\Program Files\Tesseract-OCR\tesseract.exe"


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
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.pdf_path.is_file():
        print(f"Error: file not found: {args.pdf_path}", file=sys.stderr)
        return 1

    if args.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd

    output_path = args.output or args.pdf_path.with_suffix(".txt")

    print(f"Rasterizing pages from: {args.pdf_path.name}")
    try:
        pages = convert_from_path(
            str(args.pdf_path),
            dpi=args.dpi,
            poppler_path=args.poppler_path,
        )
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

    total = len(pages)
    print(f"Found {total} page(s). Starting OCR (lang={args.lang})...")

    ocr_text_parts = []
    for i, page_image in enumerate(pages, start=1):
        print(f"  OCR page {i}/{total}...", end="\r")
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

    print(f"  OCR page {total}/{total}... done.")

    full_text = "\n\n".join(ocr_text_parts)
    output_path.write_text(full_text, encoding="utf-8")

    print(f"Wrote {len(full_text):,} characters to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
