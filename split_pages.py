"""
split_pages.py

Splits scanned images that contain two book pages side-by-side into
separate left/right image files, cutting exactly down the vertical center.

Usage:
    python split_pages.py <input_folder> [output_folder]

If output_folder is omitted, a "split" subfolder is created inside
the input folder.

Requires: Pillow
    pip install Pillow
"""

import sys
from pathlib import Path
from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def split_image(image_path: Path, output_folder: Path) -> None:
    with Image.open(image_path) as img:
        width, height = img.size
        mid = width // 2

        left_half = img.crop((0, 0, mid, height))
        right_half = img.crop((mid, 0, width, height))

        stem = image_path.stem
        ext = image_path.suffix

        left_path = output_folder / f"{stem}_left{ext}"
        right_path = output_folder / f"{stem}_right{ext}"

        left_half.save(left_path)
        right_half.save(right_path)

        print(f"  {image_path.name} -> {left_path.name}, {right_path.name}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python split_pages.py <input_folder> [output_folder]")
        sys.exit(1)

    input_folder = Path(sys.argv[1])
    if not input_folder.is_dir():
        print(f"Error: '{input_folder}' is not a valid folder.")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_folder = Path(sys.argv[2])
    else:
        output_folder = input_folder / "split"

    output_folder.mkdir(parents=True, exist_ok=True)

    image_files = sorted(
        p for p in input_folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_files:
        print(f"No image files found in '{input_folder}'.")
        sys.exit(0)

    print(f"Found {len(image_files)} image(s). Splitting into '{output_folder}'...\n")

    for image_path in image_files:
        split_image(image_path, output_folder)

    print("\nDone.")


if __name__ == "__main__":
    main()
