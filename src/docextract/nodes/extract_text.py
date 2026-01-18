"""Text extraction node for the LangGraph pipeline."""

import logging

from docextract.readers.pdf import read_pdf
from docextract.state import ExtractionState

logger = logging.getLogger(__name__)


def extract_text(state: ExtractionState) -> ExtractionState:
    """Extract text from the input document.

    Args:
        state: Current extraction state with document_path set.

    Returns:
        Updated state with extracted_text and extraction_method.
    """
    document_path = state["document_path"]
    logger.info(f"Extracting text from: {document_path}")

    try:
        extracted_text, extraction_method = read_pdf(document_path)

        return {
            **state,
            "extracted_text": extracted_text,
            "extraction_method": extraction_method,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return {
            **state,
            "extracted_text": None,
            "extraction_method": None,
            "error": f"Text extraction failed: {e}",
        }
