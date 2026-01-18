"""Settlement statement schema for real estate transactions."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from docextract.schemas.base import DocumentSchema


class PropertyAddress(DocumentSchema):
    """Individual property address."""

    street_address: str
    city: str
    state: str
    county: str | None = None

    @classmethod
    def get_document_type(cls) -> str:
        return "property_address"


class Party(DocumentSchema):
    """Party involved in the transaction."""

    name: str
    entity_type: str | None = None  # LLC, LP, Corporation, Individual, etc.
    state_of_formation: str | None = None

    @classmethod
    def get_document_type(cls) -> str:
        return "party"


class LineItem(DocumentSchema):
    """Individual line item in settlement statement."""

    description: str
    amount: Decimal
    debit_to: str | None = None  # "seller" or "buyer"
    credit_to: str | None = None  # "seller" or "buyer"
    category: str | None = None  # e.g., "taxes", "fees", "commissions"

    @classmethod
    def get_document_type(cls) -> str:
        return "line_item"


class TaxItem(DocumentSchema):
    """Specific tax line item."""

    tax_type: str  # e.g., "State Grantee Tax (Deed)"
    basis_amount: Decimal | None = None  # The amount the tax is calculated on
    tax_amount: Decimal
    paid_by: str  # "seller" or "buyer"

    @classmethod
    def get_document_type(cls) -> str:
        return "tax_item"


class AdjustmentItem(DocumentSchema):
    """Adjustments and prorations."""

    description: str
    amount: Decimal
    period_start: date | None = None
    period_end: date | None = None
    daily_rate: Decimal | None = None
    number_of_days: int | None = None
    allocated_to_seller: Decimal | None = None
    allocated_to_buyer: Decimal | None = None

    @classmethod
    def get_document_type(cls) -> str:
        return "adjustment_item"


class LoanDetails(DocumentSchema):
    """Loan information."""

    principal_amount: Decimal
    closing_draw: Decimal | None = None
    remaining_balance: Decimal | None = None
    lender: str
    loan_type: str | None = None

    @classmethod
    def get_document_type(cls) -> str:
        return "loan_details"


class SettlementStatement(DocumentSchema):
    """Complete settlement statement model for real estate transactions."""

    # Header Information
    title_company: str = Field(description="Name of the title insurance company")
    settlement_date: date = Field(description="Date of settlement/closing")
    order_number: str = Field(description="Title company order number")
    escrow_officer: str | None = Field(
        default=None, description="Name of escrow officer"
    )

    # Parties
    buyer: Party = Field(description="Buyer information")
    seller: Party = Field(description="Seller information")
    lender: Party | None = Field(default=None, description="Lender information")

    # Property Information
    properties: list[PropertyAddress] = Field(
        description="List of properties being transferred"
    )

    # Financial Summary
    purchase_price: Decimal = Field(description="Total purchase price")
    deposit: Decimal | None = Field(default=None, description="Earnest money deposit")

    # Loan Information
    loan: LoanDetails | None = Field(
        default=None, description="Loan details if applicable"
    )

    # Payoffs
    payoffs: list[LineItem] = Field(
        default=[], description="Existing loans/liens being paid off"
    )

    # Commissions
    commissions: list[LineItem] = Field(
        default=[], description="Real estate commissions"
    )

    # Adjustments and Prorations
    adjustments: list[AdjustmentItem] = Field(
        default=[],
        description="Prorated items like taxes, rents, etc.",
    )

    # Lender Fees
    lender_fees: list[LineItem] = Field(
        default=[], description="Lender fees and expenses"
    )

    # Title and Escrow Fees
    title_fees: list[LineItem] = Field(
        default=[], description="Title insurance and escrow fees"
    )

    # Recording Fees and Taxes
    recording_taxes: list[TaxItem] = Field(
        default=[], description="Recording fees and transfer taxes"
    )

    # Third Party Consultants
    consultant_fees: list[LineItem] = Field(
        default=[], description="Third party consultant fees"
    )

    # Other Items
    other_items: list[LineItem] = Field(
        default=[], description="Other miscellaneous items"
    )

    # Financial Totals
    seller_total_debits: Decimal = Field(description="Total debits to seller")
    seller_total_credits: Decimal = Field(description="Total credits to seller")
    buyer_total_debits: Decimal = Field(description="Total debits to buyer")
    buyer_total_credits: Decimal = Field(description="Total credits to buyer")

    seller_net_proceeds: Decimal | None = Field(
        default=None, description="Net proceeds to seller"
    )
    buyer_cash_required: Decimal | None = Field(
        default=None, description="Cash required from buyer"
    )

    # Additional Metadata
    page_count: int | None = Field(
        default=None, description="Number of pages in statement"
    )
    print_date: date | None = Field(
        default=None, description="Date statement was printed"
    )

    @classmethod
    def get_document_type(cls) -> str:
        return "settlement_statement"

    def get_total_closing_costs_buyer(self) -> Decimal:
        """Calculate total closing costs for buyer."""
        total = Decimal("0")
        for item in (
            self.lender_fees + self.title_fees + self.consultant_fees + self.other_items
        ):
            if item.debit_to == "buyer":
                total += item.amount
        for tax in self.recording_taxes:
            if tax.paid_by == "buyer":
                total += tax.tax_amount
        return total

    def get_total_closing_costs_seller(self) -> Decimal:
        """Calculate total closing costs for seller."""
        total = Decimal("0")
        for item in (
            self.commissions + self.title_fees + self.consultant_fees + self.other_items
        ):
            if item.debit_to == "seller":
                total += item.amount
        for tax in self.recording_taxes:
            if tax.paid_by == "seller":
                total += tax.tax_amount
        return total
