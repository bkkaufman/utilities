# Brad's utilities

# HEIC to PDF Converter

Convert HEIC image files (iPhone photos) into a single compressed, searchable PDF document with built-in OCR.

## Requirements

- Python 3.7 or higher
- macOS (tested on MacBook Pro)
- Tesseract OCR (for text recognition)

## Installation

1. Install Tesseract OCR:
```bash
brew install tesseract
```

2. Install the required Python packages:
```bash
pip install pillow pillow-heif ocrmypdf
```

## Usage

### Basic Usage

1. Place all your HEIC files in a single folder
2. Copy `convert_heic_to_pdf.py` into that folder
3. Run the script:
```bash
python convert_heic_to_pdf.py
```

The script will create a searchable `presentation.pdf` in the same folder.

### Configuration

You can adjust these constants at the top of the script:

**Image Quality Settings:**
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

**OCR Settings:**
- **ENABLE_OCR**: Enable text recognition (default: True)
  - Set to False if you don't need searchable text
- **OCR_LANGUAGE**: Language for OCR (default: "eng")
  - Options: "eng" (English), "spa" (Spanish), "fra" (French), "deu" (German), etc.
  - For multiple languages, use: "eng+spa"

### Additional OCR Languages

To install additional language packs:
```bash
# Spanish
brew install tesseract-lang

# Or install specific languages
brew install tesseract-lang --with-spanish
```

## Expected Output

For 150 HEIC files (2-4 MB each):
- Input total: ~300-600 MB
- Output PDF: ~15-30 MB (approximately 100-200 KB per page)
- Processing time: 5-10 minutes depending on your Mac (OCR adds extra time)

## Features

- **Automatic compression**: Reduces file size by 90%+ while maintaining readability
- **OCR text layer**: Makes PDF searchable and allows text copying
- **Batch processing**: Handles hundreds of images automatically
- **Smart resizing**: Maintains aspect ratios while reducing resolution
- **Progress tracking**: Shows real-time progress during conversion

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

**OCR is taking too long**
- Set ENABLE_OCR = False to skip OCR and create PDF faster
- OCR typically adds 2-5 seconds per page

**OCR "lots of diacritics" warning**
- This is normal if your slides contain foreign language text with accents
- For English-only slides, this may indicate image quality issues but OCR should still work
- The warning doesn't affect the final result

**"Tesseract not found" error**
- Run: `brew install tesseract`
- Verify installation: `tesseract --version`

## License

MIT License - feel free to modify and use as needed.