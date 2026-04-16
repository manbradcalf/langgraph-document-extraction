"""Interpretation node for analyzing extracted data."""

import json
import logging

from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from docextract.config import load_document_type
from docextract.prompts.templates import render_prompt
from docextract.schemas.interpretations import (
    CandidateScreening,
    CostBasisInterpretation,
)
from docextract.state import ExtractionState

logger = logging.getLogger(__name__)

# Map document types to their interpretation schema classes
INTERPRETATION_SCHEMAS = {
    "settlement_statement": CostBasisInterpretation,
    "resume": CandidateScreening,
}


def interpret(state: ExtractionState) -> ExtractionState:
    """Interpret extracted data using configurable AI analysis.

    Takes the structured data from extraction and generates insights,
    summaries, or analysis based on the configured interpretation prompt.

    Args:
        state: Current state with parsed_extraction_data from extraction.

    Returns:
        Updated state with interpretation results.
    """
    if state.get("error"):
        return state

    parsed_extraction_data = state.get("parsed_extraction_data")
    if not parsed_extraction_data:
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
    parsed_extraction_data_json = json.dumps(parsed_extraction_data, indent=2, default=str)

    # Render the interpretation prompt with the extracted data
    interpretation_prompt = render_prompt(
        config.interpretation.prompt,
        parsed_extraction_data=parsed_extraction_data_json,
    )

    logger.info(f"interpretation_prompt: {interpretation_prompt}")
    logger.info(f"Running interpretation with model {config.interpretation.model}")

    # Get the interpretation schema for this document type
    interpretation_schema = INTERPRETATION_SCHEMAS.get(document_type)

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

        if interpretation_schema:
            # Use structured output for known document types
            structured_llm = llm.with_structured_output(interpretation_schema)
            result = structured_llm.invoke(messages)

            # Store both the structured data and a text summary
            parsed_interpretation_data = result.model_dump()
            interpretation = json.dumps(parsed_interpretation_data, indent=2, default=str)

            logger.info("Interpretation completed successfully (structured)")

            return {
                **state,
                "interpretation": interpretation,
                "parsed_interpretation_data": parsed_interpretation_data,
                "interpretation_model": config.interpretation.model,
            }
        else:
            # Fall back to plain text for unknown document types
            response = llm.invoke(messages)
            interpretation = response.content

            logger.info("Interpretation completed successfully (unstructured)")

            return {
                **state,
                "interpretation": interpretation,
                "parsed_interpretation_data": None,
                "interpretation_model": config.interpretation.model,
            }

    except ValidationError as e:
        logger.warning(f"Validation error during interpretation: {e}")
        return {
            **state,
            "interpretation": f"Interpretation validation failed: {e}",
            "parsed_interpretation_data": None,
            "interpretation_model": config.interpretation.model,
        }
    except Exception as e:
        logger.error(f"Interpretation failed: {e}")
        return {
            **state,
            "interpretation": f"Interpretation failed: {e}",
            "parsed_interpretation_data": None,
            "interpretation_model": config.interpretation.model,
        }
