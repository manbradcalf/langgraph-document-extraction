"""Document schemas for structured extraction."""

from docextract.schemas.base import DocumentSchema
from docextract.schemas.resume import Resume
from docextract.schemas.settlement_statement import SettlementStatement

__all__ = ["DocumentSchema", "Resume", "SettlementStatement"]
