"""Base schema for document extraction."""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DocumentSchema(BaseModel, ABC):
    """Base class for all document schemas.

    All document types should inherit from this class and implement
    the get_document_type class method.
    """

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat(),
        }
    )

    @classmethod
    @abstractmethod
    def get_document_type(cls) -> str:
        """Return the document type identifier.

        Returns:
            String identifier for this document type (e.g., "settlement_statement").
        """
        pass
