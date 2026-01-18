"""Interpretation node for analyzing extracted data."""

import json
import logging

from langchain_openai import ChatOpenAI

from docextract.config import load_document_type
from docextract.prompts.templates import render_prompt
from docextract.state import ExtractionState

logger = logging.getLogger(__name__)


def interpret(state: ExtractionState) -> ExtractionState:
    """Interpret extracted data using configurable AI analysis.

    Takes the structured data from extraction and generates insights,
    summaries, or analysis based on the configured interpretation prompt.

    Args:
        state: Current state with parsed_data from extraction.

    Returns:
        Updated state with interpretation results.
    """
    if state.get("error"):
        return state

    parsed_data = state.get("parsed_data")
    if not parsed_data:
        logger.warning("No parsed data available for interpretation")
        return {
            **state,
            "interpretation": None,
            "interpretation_model": None,
        }

    document_type = state["document_type"]

    try:
        config = load_document_type(document_type)
    except Exception as e:
        logger.error(f"Failed to load config for interpretation: {e}")
        return {
            **state,
            "interpretation": None,
            "interpretation_model": None,
        }

    # Check if interpretation is enabled
    if not config.interpretation.enabled:
        logger.info("Interpretation disabled for this document type")
        return {
            **state,
            "interpretation": None,
            "interpretation_model": None,
        }

    # Format parsed data as JSON for the prompt
    parsed_data_json = json.dumps(parsed_data, indent=2, default=str)

    # Render the interpretation prompt with the extracted data
    interpretation_prompt = render_prompt(
        config.interpretation.prompt,
        parsed_data=parsed_data_json,
    )

    logger.info(f"Running interpretation with model {config.interpretation.model}")

    try:
        llm = ChatOpenAI(
            model=config.interpretation.model,
            temperature=config.interpretation.temperature,
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert analyst. Provide clear, actionable insights.",
            },
            {"role": "user", "content": interpretation_prompt},
        ]

        response = llm.invoke(messages)
        interpretation = response.content

        logger.info("Interpretation completed successfully")

        return {
            **state,
            "interpretation": interpretation,
            "interpretation_model": config.interpretation.model,
        }

    except Exception as e:
        logger.error(f"Interpretation failed: {e}")
        return {
            **state,
            "interpretation": f"Interpretation failed: {e}",
            "interpretation_model": config.interpretation.model,
        }
