"""Validation node for parsed data."""

import logging

from docextract.config import load_document_type
from docextract.state import ExtractionState

logger = logging.getLogger(__name__)


def validate(state: ExtractionState) -> ExtractionState:
    """Validate the parsed data against schema and custom rules.

    Args:
        state: Current state with parsed_extraction_data.

    Returns:
        Updated state with validation_errors and is_valid.
    """
    if state.get("error"):
        return {**state, "is_valid": False, "validation_errors": [state["error"]]}

    parsed_extraction_data = state.get("parsed_extraction_data")
    if not parsed_extraction_data:
        return {
            **state,
            "is_valid": False,
            "validation_errors": ["No parsed data to validate"],
        }

    document_type = state["document_type"]
    validation_errors: list[str] = []

    try:
        config = load_document_type(document_type)
    except Exception as e:
        return {
            **state,
            "is_valid": False,
            "validation_errors": [f"Failed to load config: {e}"],
        }

    # Check required fields
    for field in config.validation.required_fields:
        if field not in parsed_extraction_data or parsed_extraction_data[field] is None:
            validation_errors.append(f"Missing required field: {field}")

    # Run custom validators
    for validator_name in config.validation.custom_validators:
        validator_func = _get_custom_validator(validator_name)
        if validator_func:
            errors = validator_func(parsed_extraction_data)
            validation_errors.extend(errors)

    is_valid = len(validation_errors) == 0

    if is_valid:
        logger.info("Validation passed")
    else:
        logger.warning(f"Validation failed with {len(validation_errors)} errors")

    return {
        **state,
        "validation_errors": validation_errors,
        "is_valid": is_valid,
    }


def _get_custom_validator(name: str):
    """Get a custom validator function by name."""
    return _CUSTOM_VALIDATORS.get(name)


def _validate_totals_balance(data: dict) -> list[str]:
    """Validate that settlement statement financial totals balance."""
    errors: list[str] = []
    for party in ("seller", "buyer"):
        debits = data.get(f"{party}_total_debits")
        credits = data.get(f"{party}_total_credits")
        if debits is not None and credits is not None:
            if abs(float(debits) - float(credits)) > 0.01:
                errors.append(
                    f"{party.title()} totals do not balance: "
                    f"debits={debits}, credits={credits}"
                )
    return errors


_CUSTOM_VALIDATORS = {
    "totals_balance": _validate_totals_balance,
}
