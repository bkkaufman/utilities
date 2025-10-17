## Brad's utilities


# HEIC to PDF Converter

Convert HEIC image files (iPhone photos) into a single compressed PDF document.

## Requirements

- Python 3.7 or higher
- macOS (tested on MacBook Pro)

## Installation

1. Install the required Python packages:
```bash
pip install pillow pillow-heif
```

## Usage

### Basic Usage

1. Place all your HEIC files in a single folder
2. Copy `convert_heic_to_pdf.py` into that folder
3. Run the script:
```bash
python convert_heic_to_pdf.py
```

The script will create `presentation.pdf` in the same folder.

### Configuration

You can adjust these constants at the top of the script to control output quality and file size:

- **INPUT_FOLDER**: Folder containing HEIC files (default: current directory)
- **OUTPUT_PDF**: Name of the output PDF file (default: "presentation.pdf")
- **MAX_WIDTH**: Maximum image width in pixels (default: 1400)
  - Lower values = smaller file size but lower quality
  - Recommended range: 1200-1600
- **JPEG_QUALITY**: JPEG compression quality from 1-100 (default: 80)
  - Lower values = smaller file size but lower quality
  - Recommended range: 75-85
- **OPTIMIZE**: Enable image optimization (default: True)
  - Keep this as True for best compression

### Adding OCR (Making PDF Searchable)

To make the PDF searchable with text recognition:

1. Install OCRmyPDF:
```bash
brew install ocrmypdf
```

2. Run OCR on your PDF:
```bash
ocrmypdf presentation.pdf presentation_searchable.pdf --optimize 3 --jpeg-quality 80
```

This creates a new PDF where you can search and copy text from the slides.

## Expected Output

For 150 HEIC files (2-4 MB each):
- Input total: ~300-600 MB
- Output PDF: ~15-25 MB (approximately 100-170 KB per page)
- Processing time: 2-5 minutes depending on your Mac

## Troubleshooting

**"No HEIC files found!"**
- Ensure your files have .HEIC or .heic extension
- Check that you're running the script in the correct folder

**PDF is too large**
- Lower MAX_WIDTH to 1200 or 1000
- Lower JPEG_QUALITY to 75 or 70
- These changes will reduce quality but significantly decrease file size

**Images are blurry or hard to read**
- Increase MAX_WIDTH to 1600 or 1800
- Increase JPEG_QUALITY to 85 or 90
- Note: this will increase the file size

**OCR "lots of diacritics" warning**
- This is normal if your slides contain foreign language text with accents
- For English-only slides, this may indicate image quality issues but OCR should still work

## License

MIT License - feel free to modify and use as needed.