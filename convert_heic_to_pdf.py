# !/usr/bin/env python3
"""
Convert HEIC images to a single compressed, searchable PDF
"""

import os
import glob
from PIL import Image
import pillow_heif
from pathlib import Path
import ocrmypdf

# Register HEIC opener with Pillow
pillow_heif.register_heif_opener()

# CONFIGURATION CONSTANTS
INPUT_FOLDER = "/Users/brad/Desktop/Input for PDF"  # Current directory
OUTPUT_PDF = "/Users/brad/Desktop/PDF Output/presentation.pdf"
MAX_WIDTH = 1400  # Maximum image width in pixels (smaller = smaller file)
JPEG_QUALITY = 80  # JPEG quality 1-100 (lower = smaller file, try 75-85)
OPTIMIZE = True  # Enable image optimization
ENABLE_OCR = True  # Enable OCR to make PDF searchable
OCR_LANGUAGE = "eng"  # OCR language (eng, spa, fra, deu, etc.)


def convert_heic_to_pdf(input_folder, output_pdf, max_width, jpeg_quality, optimize, enable_ocr, ocr_language):
    """
    Convert HEIC files to a compressed PDF with optional OCR

    Args:
        input_folder: Path to folder containing HEIC files
        output_pdf: Output PDF filename
        max_width: Maximum width for images (maintains aspect ratio)
        jpeg_quality: JPEG compression quality (1-100)
        optimize: Enable optimization for smaller file size
        enable_ocr: Enable OCR to make PDF searchable
        ocr_language: Language for OCR (eng, spa, fra, etc.)
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

    # Create temporary PDF from images
    temp_pdf = output_pdf if not enable_ocr else output_pdf.replace('.pdf', '_temp.pdf')

    images = [Image.open(img_path) for img_path in image_list]
    images[0].save(
        temp_pdf,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=images[1:],
        optimize=optimize
    )

    # Clean up temporary image files
    for img_path in image_list:
        os.remove(img_path)
    temp_folder.rmdir()

    # Apply OCR if enabled
    if enable_ocr:
        print(f"\nApplying OCR (language: {ocr_language})...")
        print("This may take a few minutes...")

        try:
            ocrmypdf.ocr(
                temp_pdf,
                output_pdf,
                language=ocr_language,
                optimize=3,
                jpeg_quality=jpeg_quality,
                progress_bar=True,
                skip_text=True  # Skip pages that already have text
            )

            # Remove temporary PDF
            os.remove(temp_pdf)
            print("OCR completed successfully!")

        except Exception as e:
            print(f"OCR failed: {e}")
            print(f"Keeping non-OCR PDF as {temp_pdf}")
            if os.path.exists(output_pdf):
                os.remove(output_pdf)
            os.rename(temp_pdf, output_pdf)

    # Get final file size
    size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
    print(f"\nDone! PDF created: {output_pdf}")
    print(f"File size: {size_mb:.2f} MB")
    print(f"Average per page: {size_mb / len(heic_files):.2f} MB")
    if enable_ocr:
        print("PDF is now searchable with OCR text layer")


if __name__ == "__main__":
    convert_heic_to_pdf(
        INPUT_FOLDER,
        OUTPUT_PDF,
        MAX_WIDTH,
        JPEG_QUALITY,
        OPTIMIZE,
        ENABLE_OCR,
        OCR_LANGUAGE
    )
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