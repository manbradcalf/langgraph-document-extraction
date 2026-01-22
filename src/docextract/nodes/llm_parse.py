"""LLM parsing node for structured extraction."""

import logging

from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from docextract.config import DocumentTypeConfig, load_document_type
from docextract.prompts.templates import render_prompt
from docextract.state import ExtractionState

logger = logging.getLogger(__name__)


def llm_parse(state: ExtractionState) -> ExtractionState:
    """Parse extracted text using LLM with structured output.

    Args:
        state: Current state with extracted_text and document_type.

    Returns:
        Updated state with parsed_data or error.
    """
    # Only bail on upstream errors (e.g., text extraction failed), not previous parse errors
    if state.get("error") and state.get("extracted_text") is None:
        return state

    extracted_text = state.get("extracted_text")
    if not extracted_text:
        return {**state, "error": "No extracted text available for parsing"}

    document_type = state["document_type"]
    retry_count = state.get("retry_count", 0)

    try:
        config = load_document_type(document_type)
    except Exception as e:
        return {**state, "error": f"Failed to load document type config: {e}"}

    # Render prompts with extracted text
    system_prompt = render_prompt(config.prompts.system, extracted_text=extracted_text)
    user_prompt = render_prompt(config.prompts.user, extracted_text=extracted_text)

    logger.info(
        f"Parsing with model {config.llm.model} "
        f"(attempt {retry_count + 1}/{config.llm.max_retries + 1})"
    )

    try:
        # Create LLM with structured output
        llm = ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature,
        )

        # Get the schema class for structured output
        schema_class = config.get_schema_class()

        # Use with_structured_output for type-safe parsing
        structured_llm = llm.with_structured_output(schema_class)

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Invoke and get structured result
        result = structured_llm.invoke(messages)

        # Convert to dict for state storage
        parsed_data = result.model_dump()

        logger.info("Successfully parsed document")

        return {
            **state,
            "parsed_data": parsed_data,
            "model_used": config.llm.model,
            "error": None,
        }

    except ValidationError as e:
        logger.warning(f"Validation error during parsing: {e}")
        return {
            **state,
            "parsed_data": None,
            "model_used": config.llm.model,
            "error": f"Validation error: {e}",
            "retry_count": retry_count + 1,
        }
    except Exception as e:
        logger.error(f"LLM parsing failed: {e}")
        return {
            **state,
            "parsed_data": None,
            "model_used": config.llm.model,
            "error": f"LLM parsing failed: {e}",
            "retry_count": retry_count + 1,
        }
