#!/usr/bin/env python3
"""
Convert HEIC images to a single compressed PDF
"""

import os
import glob
from PIL import Image
import pillow_heif
from pathlib import Path

# Register HEIC opener with Pillow
pillow_heif.register_heif_opener()

# CONFIGURATION CONSTANTS
INPUT_FOLDER = "."  # Current directory
OUTPUT_PDF = "presentation.pdf"
MAX_WIDTH = 1400  # Maximum image width in pixels (smaller = smaller file)
JPEG_QUALITY = 80  # JPEG quality 1-100 (lower = smaller file, try 75-85)
OPTIMIZE = True  # Enable image optimization


def convert_heic_to_pdf(input_folder, output_pdf, max_width, jpeg_quality, optimize):
    """
    Convert HEIC files to a compressed PDF

    Args:
        input_folder: Path to folder containing HEIC files
        output_pdf: Output PDF filename
        max_width: Maximum width for images (maintains aspect ratio)
        jpeg_quality: JPEG compression quality (1-100)
        optimize: Enable optimization for smaller file size
    """

    # Find all HEIC files
    heic_files = sorted(glob.glob(os.path.join(input_folder, "*.HEIC")) +
                        glob.glob(os.path.join(input_folder, "*.heic")))

    if not heic_files:
        print("No HEIC files found!")
        return

    print(f"Found {len(heic_files)} HEIC files")

    # Convert images and store temporarily
    image_list = []
    temp_folder = Path(input_folder) / "temp_converted"
    temp_folder.mkdir(exist_ok=True)

    for i, heic_path in enumerate(heic_files, 1):
        print(f"Processing {i}/{len(heic_files)}: {Path(heic_path).name}")

        # Open and convert HEIC
        img = Image.open(heic_path)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize to reduce file size
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save as compressed JPEG
        temp_jpg = temp_folder / f"temp_{i:03d}.jpg"
        img.save(temp_jpg, "JPEG", quality=jpeg_quality, optimize=optimize)
        image_list.append(str(temp_jpg))

    print(f"\nCreating PDF: {output_pdf}")

    # Create PDF from images
    images = [Image.open(img_path) for img_path in image_list]
    images[0].save(
        output_pdf,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=images[1:],
        optimize=optimize
    )

    # Clean up temporary files
    for img_path in image_list:
        os.remove(img_path)
    temp_folder.rmdir()

    # Get file size
    size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
    print(f"\nDone! PDF created: {output_pdf}")
    print(f"File size: {size_mb:.2f} MB")
    print(f"Average per page: {size_mb / len(heic_files):.2f} MB")


if __name__ == "__main__":
    convert_heic_to_pdf(INPUT_FOLDER, OUTPUT_PDF, MAX_WIDTH, JPEG_QUALITY, OPTIMIZE)