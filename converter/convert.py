# convert.py - Scans data/ folder and converts non-ZIM files to ZIM format

import argparse
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

import fitz  # pymupdf
from PIL import Image
from libzim.writer import Creator, Item, Hint, StringProvider

# -------------------------------------------------------
# LOGGING SETUP
# -------------------------------------------------------

# Delete existing log file and start fresh each run
if os.path.exists("convert.log"):
    os.remove("convert.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("convert.log", encoding="utf-8"),
        logging.StreamHandler()  # also prints to terminal
    ]
)
log = logging.getLogger(__name__)

# -------------------------------------------------------
# ARGUMENT PARSER
# -------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Convert files in data/ to ZIM format")
    parser.add_argument(
        "--quality",
        choices=["text", "standard", "full"],
        default="standard",
        help="Conversion quality: text (no images), standard (compressed images), full (full quality images)"
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        default=False,
        help="Enable OCR for scanned PDFs (requires Tesseract)"
    )
    return parser.parse_args()

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
DATA_FOLDER = Path("../data")
FAILED_FOLDER = DATA_FOLDER / "failed"

# Supported file types for conversion
SUPPORTED_EXTENSIONS = [".pdf"]  # more added later: .epub, .docx, .html

# -------------------------------------------------------
# FOLDER SETUP
# -------------------------------------------------------
def setup_folders():
    """Create data/ and data/failed/ if they don't exist"""
    DATA_FOLDER.mkdir(exist_ok=True)
    FAILED_FOLDER.mkdir(exist_ok=True)
    log.info(f"Data folder: {DATA_FOLDER.resolve()}")
    log.info(f"Failed folder: {FAILED_FOLDER.resolve()}")

# -------------------------------------------------------
# FOLDER SCANNER
# -------------------------------------------------------
def scan_for_files():
    """Scan data/ for non-ZIM files that need conversion"""
    files = []
    for f in DATA_FOLDER.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(f)
            log.info(f"Found: {f.name}")
    if not files:
        log.info("No files found for conversion")
    return files

# -------------------------------------------------------
# IMAGE PROCESSING
# -------------------------------------------------------
def extract_image(page, img_info, doc, quality):
    """Extract and compress an image from a PDF page based on quality setting"""
    try:
        xref = img_info[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]

        # Text only — skip images entirely
        if quality == "text":
            return None, None

        # Open image with Pillow for processing
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))

        # Convert to RGB if necessary (e.g. RGBA, CMYK)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        output = BytesIO()

        if quality == "standard":
            # Resize if too large and compress
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)
            img.save(output, format="JPEG", quality=65)

        elif quality == "full":
            # Keep original size, light compression
            img.save(output, format="JPEG", quality=95)

        return output.getvalue(), "jpg"

    except Exception as e:
        log.warning(f"Image extraction failed: {e}")
        return None, None
    
# -------------------------------------------------------
# PAGE TO HTML CONVERTER
# -------------------------------------------------------
def page_to_html(page, doc, quality, page_num, total_pages, title, use_ocr=False):
    """Convert a single PDF page to an HTML string with embedded images"""

    # -------------------------------------------------------
    # RENDER PAGE AS IMAGE (visual layer)
    # -------------------------------------------------------
    if quality == "text":
        dpi = 0  # skip image rendering for text only
    elif quality == "standard":
        dpi = 150
    else:  # full
        dpi = 300

    page_image_html = ""
    if dpi > 0:
        pix = page.get_pixmap(dpi=dpi)
        from io import BytesIO
        img = Image.open(BytesIO(pix.tobytes("png")))

        output = BytesIO()
        if quality == "standard":
            img.save(output, format="JPEG", quality=65)
        else:
            img.save(output, format="JPEG", quality=95)

        import base64
        b64 = base64.b64encode(output.getvalue()).decode("utf-8")
        page_image_html = f'<img src="data:image/jpeg;base64,{b64}" style="max-width:100%;height:auto;display:block;margin:0 auto;">'

    # -------------------------------------------------------
    # EXTRACT TEXT (hidden search layer)
    # -------------------------------------------------------
    if quality == "text":
        # Text only mode — show text, no image
        text_content = page.get_text()
        hidden_text_html = f"<div style='font-family:sans-serif;line-height:1.6'><pre style='white-space:pre-wrap'>{text_content}</pre></div>"
    else:
        # Hidden text layer for search
        text_content = page.get_text()
        if not text_content.strip() and use_ocr:
            try:
                import pytesseract
                pix_ocr = page.get_pixmap(dpi=300)
                img_ocr = Image.open(BytesIO(pix_ocr.tobytes("png")))
                text_content = pytesseract.image_to_string(img_ocr, lang="hat+fra+eng")
                log.info(f"OCR used on page {page_num}")
            except Exception as e:
                log.warning(f"OCR failed on page {page_num}: {e}")
                text_content = ""
        hidden_text_html = f'<div style="display:none">{text_content}</div>'

    # -------------------------------------------------------
    # NAVIGATION BAR
    # -------------------------------------------------------
    prev_link = f'<a href="page_{page_num - 1}.html">← Previous</a>' if page_num > 1 else ""
    next_link = f'<a href="page_{page_num + 1}.html">Next →</a>' if page_num < total_pages else ""

    nav = f'''
    <div style="position:fixed;bottom:0;left:0;right:0;background:#fff;
    border-top:1px solid #ccc;padding:8px 16px;display:flex;
    justify-content:space-between;font-family:sans-serif;font-size:14px;">
        {prev_link}
        <span>Page {page_num} of {total_pages} — {title}</span>
        {next_link}
    </div>
    '''

    # -------------------------------------------------------
    # FULL HTML PAGE
    # -------------------------------------------------------
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} — Page {page_num}</title>
    <style>
        body {{
            margin: 0;
            padding: 0 0 60px 0;
            background: #f0f0f0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    {page_image_html}
    {hidden_text_html}
    {nav}
</body>
</html>'''

    return html

# -------------------------------------------------------
# ZIM WRITER
# -------------------------------------------------------
class HTMLItem(Item):
    def __init__(self, path, title, html_content):
        super().__init__()
        self._path = path
        self._title = title
        self._content = html_content

    def get_path(self):
        return self._path

    def get_title(self):
        return self._title

    def get_mimetype(self):
        return "text/html"

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: True}

    def get_contentprovider(self):
        return StringProvider(self._content)


def write_zim(pages_html, output_path, title, language):
    """Write a list of HTML pages into a ZIM file"""
    log.info(f"Writing ZIM: {output_path}")
    try:
        with Creator(str(output_path)).config_indexing(True, language) as creator:
            # Set ZIM metadata
            creator.add_metadata("Title", title)
            creator.add_metadata("Language", language)
            creator.add_metadata("Description", "Converted from PDF by Library Catalog converter")
            creator.add_metadata("Creator", "Library Catalog")
            creator.add_metadata("Publisher", "Library Catalog")
            creator.add_metadata("Date", datetime.now().strftime("%Y-%m-%d"))

            # Write each page
            for i, html in enumerate(pages_html, start=1):
                path = f"page_{i}.html"
                item = HTMLItem(path, f"{title} — Page {i}", html)
                creator.add_item(item)
                log.info(f"Written page {i} of {len(pages_html)}")

            # Set main entry to first page
            creator.set_mainpath("page_1.html")

        log.info(f"ZIM file created successfully: {output_path}")
        return True

    except Exception as e:
        log.error(f"Failed to write ZIM: {e}")
        return False

    
# -------------------------------------------------------
# PDF CONVERTER
# -------------------------------------------------------
def convert_pdf(file_path, quality, use_ocr):
    """Convert a PDF file to ZIM format"""
    
    title = file_path.stem  # filename without extension
    language = title.split("_")[-1]  # extract language code from filename
    output_path = file_path.with_suffix(".zim")

    log.info(f"Starting conversion: {file_path.name}")
    log.info(f"Title: {title} | Language: {language} | Quality: {quality}")

    try:
        # Open PDF
        doc = fitz.open(str(file_path))
        total_pages = len(doc)
        log.info(f"PDF has {total_pages} pages")

        if total_pages == 0:
            log.error(f"PDF has no pages: {file_path.name}")
            return False

        # Convert each page to HTML
        pages_html = []
        for page_num in range(1, total_pages + 1):
            page = doc[page_num - 1]
            log.info(f"Converting page {page_num} of {total_pages}")
            html = page_to_html(
                page=page,
                doc=doc,
                quality=quality,
                page_num=page_num,
                total_pages=total_pages,
                title=title,
                use_ocr=use_ocr
            )
            pages_html.append(html)

        doc.close()

        # Write ZIM file
        success = write_zim(
            pages_html=pages_html,
            output_path=output_path,
            title=title.replace("_", " "),
            language=language
        )

        return success

    except Exception as e:
        log.error(f"Conversion failed for {file_path.name}: {e}")
        return False
    
# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    args = parse_args()

    log.info("=" * 50)
    log.info("Library Catalog Converter")
    log.info(f"Quality: {args.quality}")
    log.info(f"OCR: {'enabled' if args.ocr else 'disabled'}")
    log.info("=" * 50)

    # Setup folders
    setup_folders()

    # Scan for files
    files = scan_for_files()

    if not files:
        log.info("Nothing to convert. Exiting.")
        return

    # Track results
    success_count = 0
    failed_count = 0

    # Convert each file
    for file_path in files:
        log.info(f"\n--- Processing: {file_path.name} ---")

        if file_path.suffix.lower() == ".pdf":
            success = convert_pdf(file_path, args.quality, args.ocr)
        else:
            log.warning(f"Unsupported file type: {file_path.suffix} — skipping")
            success = False

        if success:
            # Delete original after successful conversion
            file_path.unlink()
            log.info(f"Deleted original: {file_path.name}")
            success_count += 1
        else:
            # Check for .zim.tmp recovery before declaring failure
            tmp_path = DATA_FOLDER / (file_path.stem + ".zim.tmp")
            if tmp_path.exists():
                recovered_path = DATA_FOLDER / (file_path.stem + ".zim")
                tmp_path.rename(recovered_path)
                log.info(f"Recovered ZIM from .tmp: {recovered_path.name}")
                file_path.unlink()
                log.info(f"Deleted original: {file_path.name}")
                success_count += 1
            else:
                # Move to failed folder
                failed_path = FAILED_FOLDER / file_path.name
                shutil.move(str(file_path), str(failed_path))
                log.warning(f"Moved to failed/: {file_path.name}")
                failed_count += 1

    # Summary
    log.info("\n" + "=" * 50)
    log.info("Conversion Complete!")
    log.info(f"Successful: {success_count}")
    log.info(f"Failed: {failed_count}")
    log.info(f"Total processed: {success_count + failed_count}")
    log.info("=" * 50)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()