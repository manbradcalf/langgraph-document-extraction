"""LangGraph workflow definition for document extraction."""

import logging
from typing import cast

from langgraph.graph import END, StateGraph

from docextract.config import load_document_type
from docextract.nodes import (
    extract_text,
    generate_report,
    interpret,
    llm_parse,
    validate,
)
from docextract.state import ExtractionState

logger = logging.getLogger(__name__)


def should_retry(state: ExtractionState) -> str:
    """Determine if parsing should be retried or proceed to interpretation.

    Returns:
        "retry" if more retries available,
        "interpret" if valid and should run interpretation,
        "report" otherwise.
    """
    if state.get("is_valid", False):
        return "interpret"

    document_type = state.get("document_type", "settlement_statement")
    try:
        config = load_document_type(document_type)
        max_retries = config.llm.max_retries
    except Exception:
        max_retries = 2

    retry_count = state.get("retry_count", 0)

    if retry_count < max_retries and state.get("parsed_extraction_data") is None:
        logger.info(f"Retrying parse (attempt {retry_count + 1}/{max_retries})")
        return "retry"

    # Even if not fully valid, proceed to interpretation if we have data
    if state.get("parsed_extraction_data"):
        return "interpret"

    return "report"


def has_error(state: ExtractionState) -> str:
    """Check if there's an error that should skip to report.

    Returns:
        "error" if extraction failed, "continue" otherwise.
    """
    if state.get("error") and state.get("extracted_text") is None:
        return "error"
    return "continue"


def build_extraction_graph():
    """Build the document extraction workflow graph.

    The graph flow:
        START -> extract_text -> llm_parse -> validate -> interpret -> generate_report -> END
                     |               |           |
                     v               v           v
                   (error)        (retry)    (no data)
                     |               |           |
                     +--------> generate_report <-+

    Returns:
        Compiled StateGraph ready for invocation.
    """
    graph = StateGraph(ExtractionState)

    # Add nodes
    graph.add_node("extract_text", extract_text)
    graph.add_node("llm_parse", llm_parse)
    graph.add_node("validate", validate)
    graph.add_node("interpret", interpret)
    graph.add_node("generate_report", generate_report)

    # Set entry point
    graph.set_entry_point("extract_text")

    # Add conditional edge after text extraction
    graph.add_conditional_edges(
        "extract_text",
        has_error,
        {
            "error": "generate_report",
            "continue": "llm_parse",
        },
    )

    # Add edge from parse to validate
    graph.add_edge("llm_parse", "validate")

    # Add conditional edge after validation for retry or interpretation
    graph.add_conditional_edges(
        "validate",
        should_retry,
        {
            "retry": "llm_parse",
            "interpret": "interpret",
            "report": "generate_report",
        },
    )

    # Add edge from interpret to report
    graph.add_edge("interpret", "generate_report")

    # Add edge from report to end
    graph.add_edge("generate_report", END)

    return graph.compile()


def extract_document(
    document_path: str,
    document_type: str = "settlement_statement",
) -> ExtractionState:
    """Run the extraction pipeline on a document.

    Args:
        document_path: Path to the input document.
        document_type: Type of document for schema/prompt selection.

    Returns:
        Final extraction state with results.
    """
    graph = build_extraction_graph()

    initial_state: ExtractionState = {
        "document_path": document_path,
        "document_type": document_type,
        "extracted_text": None,
        "extraction_method": None,
        "parsed_extraction_data": None,
        "model_used": None,
        "validation_errors": [],
        "is_valid": False,
        "retry_count": 0,
        "interpretation": None,
        "interpretation_model": None,
        "report_path": None,
        "error": None,
    }

    logger.info(f"Starting extraction: {document_path} (type: {document_type})")

    result = graph.invoke(initial_state)

    if result.get("is_valid"):
        logger.info(f"Extraction successful: {result.get('report_path')}")
    else:
        logger.warning(
            f"Extraction completed with issues: {result.get('validation_errors')}"
        )

    return cast(ExtractionState, result)
