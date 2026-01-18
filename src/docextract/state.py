"""Graph state definition for document extraction pipeline."""

from typing import TypedDict


class ExtractionState(TypedDict, total=False):
    """State that flows through the LangGraph extraction pipeline.

    Attributes:
        document_path: Path to the input document.
        document_type: Type of document being processed (e.g., "settlement_statement").
        extracted_text: Raw text extracted from the document.
        extraction_method: Method used for extraction ("pdfplumber" or "ocr").
        parsed_data: Structured data extracted by the LLM.
        model_used: LLM model identifier used for parsing.
        validation_errors: List of validation error messages.
        is_valid: Whether the parsed data passed validation.
        retry_count: Number of parsing retries attempted.
        interpretation: AI-generated interpretation of the extracted data.
        interpretation_model: LLM model used for interpretation.
        report_path: Path to the generated HTML report.
        error: Error message if processing failed.
    """

    # Inputs
    document_path: str
    document_type: str

    # Processing
    extracted_text: str | None
    extraction_method: str | None

    # LLM Output
    parsed_data: dict | None
    model_used: str | None

    # Validation
    validation_errors: list[str]
    is_valid: bool
    retry_count: int

    # Interpretation
    interpretation: str | None
    interpretation_model: str | None

    # Output
    report_path: str | None
    error: str | None
