"""Cost basis interpretation schema for settlement statements per IRS Publication 551."""

from decimal import Decimal
from enum import Enum

from pydantic import Field

from docextract.schemas.base import DocumentSchema


class CostBasisCategory(str, Enum):
    """IRS Publication 551 categories for settlement statement line items."""

    COSTS_ADDED_TO_BASIS = "Costs Added to Basis"
    COSTS_NOT_ADDED_TO_BASIS = "Costs NOT Added to Basis"
    LOAN_SETTLEMENT_FEES = "Loan Settlement Fees (Potentially Deductible)"
    PRORATIONS = "Prorations"
    SELLERS_COSTS = "Seller's Costs"


class CostBasisLineItem(DocumentSchema):
    """Individual line item categorized per IRS Publication 551."""

    description: str = Field(description="Description of the line item")
    amount: Decimal = Field(description="Dollar amount of the line item")
    category: CostBasisCategory = Field(
        description="IRS Pub 551 category for this line item"
    )
    applies_to: str = Field(
        description="Who this cost applies to (Buyer, Seller, or Both)"
    )
    justification: str = Field(
        description="Brief explanation of why this item falls into the assigned category"
    )

    @classmethod
    def get_document_type(cls) -> str:
        return "cost_basis_line_item"


class CategoryTotal(DocumentSchema):
    """Total amount for a cost basis category."""

    category: CostBasisCategory = Field(description="The IRS Pub 551 category")
    total: Decimal = Field(description="Sum of all line items in this category")

    @classmethod
    def get_document_type(cls) -> str:
        return "category_total"


class CostBasisInterpretation(DocumentSchema):
    """Complete cost basis interpretation of a settlement statement per IRS Publication 551.

    This schema represents the categorization of all settlement statement line items
    according to IRS Publication 551 (Basis of Assets) guidelines.
    """

    line_items: list[CostBasisLineItem] = Field(
        description="All line items from the settlement statement, categorized per IRS Pub 551"
    )
    category_totals: list[CategoryTotal] = Field(
        description="Totals for each IRS Pub 551 category"
    )

    @classmethod
    def get_document_type(cls) -> str:
        return "cost_basis_interpretation"

    def get_total_for_category(self, category: CostBasisCategory) -> Decimal:
        """Get the total amount for a specific category."""
        for ct in self.category_totals:
            if ct.category == category:
                return ct.total
        return Decimal("0")

    def get_buyer_basis_additions(self) -> Decimal:
        """Get total costs that can be added to the buyer's basis."""
        return self.get_total_for_category(CostBasisCategory.COSTS_ADDED_TO_BASIS)
