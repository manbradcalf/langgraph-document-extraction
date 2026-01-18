"""PDF reader with OCR fallback."""

import logging
from pathlib import Path

import pdfplumber
import pytesseract

logger = logging.getLogger(__name__)


def read_pdf(pdf_path: str | Path) -> tuple[str, str]:
    """Extract text from a PDF file.

    Uses pdfplumber for text extraction, falling back to OCR via
    pytesseract when text extraction fails or returns empty content.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Tuple of (extracted_text, extraction_method).
        extraction_method is either "pdfplumber" or "ocr".

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If the file is not a valid PDF.
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    text_parts: list[str] = []
    used_ocr = False

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()

            if not page_text or len(page_text.strip()) == 0:
                logger.info(f"No text on page {page_num}, using OCR")
                page_image = page.to_image(resolution=300)
                page_text = pytesseract.image_to_string(page_image.original)
                used_ocr = True

            text_parts.append(page_text)

    extracted_text = "\n\n".join(text_parts)
    extraction_method = "ocr" if used_ocr else "pdfplumber"

    logger.info(
        f"Extracted {len(extracted_text)} chars from {len(text_parts)} pages "
        f"using {extraction_method}"
    )

    return extracted_text, extraction_method
