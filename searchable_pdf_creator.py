#!/usr/bin/env python3
"""
Searchable PDF Creator (searchable_pdf_creator.py)
formerly OCR PDF Utility (ocr_pdf.py)

Description:
    This script takes an image-only PDF (e.g., a scanned slide deck or document),
    runs OCR (Optical Character Recognition) on each page using Tesseract, and
    outputs a new text-enabled, searchable PDF.
    - Keeps the original PDF untouched
    - Produces a new <filename>-ocr.pdf with an invisible text layer
    - Cleans up all intermediate PNGs and per-page PDFs automatically

Dependencies:
    - Tesseract OCR (install via Homebrew: brew install tesseract)
    - Poppler utilities (for pdftoppm and pdfunite: brew install poppler)

Setup (recommended virtual environment):
    python3 -m venv .venv
    source .venv/bin/activate
    # (dependencies are system-installed, so no pip packages needed)

Usage:
    python3 searchable_pdf_creator.py input.pdf
        → Creates input-ocr.pdf in the same directory

    python3 searchable_pdf_creator.py input.pdf output.pdf
        → Creates a text-enabled PDF with a custom name (output.pdf)

Notes:
    - Language is set to English ("eng") by default, but you can change the 'lang' parameter in the code
    - Requires macOS or Linux with Tesseract and Poppler installed
"""
import os
import sys
import subprocess
import tempfile
import shutil

def ocr_pdf(input_pdf, output_pdf=None, lang="eng"):
    if output_pdf is None:
        base, _ = os.path.splitext(input_pdf)
        output_pdf = f"{base}-ocr.pdf"

    # Create temporary working dir
    workdir = tempfile.mkdtemp()
    try:
        print(f"[INFO] Working in {workdir}")

        # Step 1: Convert PDF to images
        print("[INFO] Converting PDF to images...")
        subprocess.run(
            ["pdftoppm", input_pdf, os.path.join(workdir, "page"), "-png"],
            check=True
        )

        # Step 2: Run OCR on each page
        page_pdfs = []
        for f in sorted(os.listdir(workdir)):
            if f.endswith(".png"):
                img_path = os.path.join(workdir, f)
                page_pdf = img_path.replace(".png", ".pdf")
                subprocess.run(
                    ["tesseract", img_path, img_path.replace(".png", ""), "-l", lang, "pdf"],
                    check=True
                )
                page_pdfs.append(page_pdf)

        # Step 3: Merge into single PDF
        print(f"[INFO] Merging into {output_pdf}...")
        subprocess.run(["pdfunite"] + page_pdfs + [output_pdf], check=True)

        print(f"[SUCCESS] OCR complete: {output_pdf}")
        return output_pdf

    finally:
        shutil.rmtree(workdir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input.pdf [output.pdf]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    ocr_pdf(input_pdf, output_pdf)
