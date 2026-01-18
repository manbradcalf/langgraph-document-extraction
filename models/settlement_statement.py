from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date


class PropertyAddress(BaseModel):
    """Individual property address"""

    street_address: str
    city: str
    state: str
    county: Optional[str] = None


class Party(BaseModel):
    """Party involved in the transaction"""

    name: str
    entity_type: Optional[str] = None  # LLC, LP, Corporation, Individual, etc.
    state_of_formation: Optional[str] = None


class LineItem(BaseModel):
    """Individual line item in settlement statement"""

    description: str
    amount: Decimal
    debit_to: Optional[str] = None  # "seller" or "buyer"
    credit_to: Optional[str] = None  # "seller" or "buyer"
    category: Optional[str] = None  # e.g., "taxes", "fees", "commissions"


class TaxItem(BaseModel):
    """Specific tax line item"""

    tax_type: str  # e.g., "State Grantee Tax (Deed)"
    basis_amount: Optional[Decimal] = None  # The amount the tax is calculated on
    tax_amount: Decimal
    paid_by: str  # "seller" or "buyer"


class AdjustmentItem(BaseModel):
    """Adjustments and prorations"""

    description: str
    amount: Decimal
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    daily_rate: Optional[Decimal] = None
    number_of_days: Optional[int] = None
    allocated_to_seller: Optional[Decimal] = None
    allocated_to_buyer: Optional[Decimal] = None


class LoanDetails(BaseModel):
    """Loan information"""

    principal_amount: Decimal
    closing_draw: Optional[Decimal] = None
    remaining_balance: Optional[Decimal] = None
    lender: str
    loan_type: Optional[str] = None


class SettlementStatement(BaseModel):
    """Complete settlement statement model for real estate transactions"""

    # Header Information
    title_company: str = Field(description="Name of the title insurance company")
    settlement_date: date = Field(description="Date of settlement/closing")
    order_number: str = Field(description="Title company order number")
    escrow_officer: Optional[str] = Field(
        default=None, description="Name of escrow officer"
    )

    # Parties
    buyer: Party = Field(description="Buyer information")
    seller: Party = Field(description="Seller information")
    lender: Optional[Party] = Field(default=None, description="Lender information")

    # Property Information
    properties: List[PropertyAddress] = Field(
        description="List of properties being transferred"
    )

    # Financial Summary
    purchase_price: Decimal = Field(description="Total purchase price")
    deposit: Optional[Decimal] = Field(
        default=None, description="Earnest money deposit"
    )

    # Loan Information
    loan: Optional[LoanDetails] = Field(
        default=None, description="Loan details if applicable"
    )

    # Payoffs
    payoffs: List[LineItem] = Field(
        default=[], description="Existing loans/liens being paid off"
    )

    # Commissions
    commissions: List[LineItem] = Field(
        default=[], description="Real estate commissions"
    )

    # Adjustments and Prorations
    adjustments: List[AdjustmentItem] = Field(
        default=[],
        description="Prorated items like taxes, rents, etc. These are broken out by credits and debits for both seller and buyer.",
    )

    # Lender Fees
    lender_fees: List[LineItem] = Field(
        default=[], description="Lender fees and expenses"
    )

    # Title and Escrow Fees
    title_fees: List[LineItem] = Field(
        default=[], description="Title insurance and escrow fees"
    )

    # Recording Fees and Taxes
    recording_taxes: List[TaxItem] = Field(
        default=[], description="Recording fees and transfer taxes"
    )

    # Third Party Consultants
    consultant_fees: List[LineItem] = Field(
        default=[], description="Third party consultant fees"
    )

    # Other Items
    other_items: List[LineItem] = Field(
        default=[], description="Other miscellaneous items"
    )

    # Financial Totals
    seller_total_debits: Decimal = Field(description="Total debits to seller")
    seller_total_credits: Decimal = Field(description="Total credits to seller")
    buyer_total_debits: Decimal = Field(description="Total debits to buyer")
    buyer_total_credits: Decimal = Field(description="Total credits to buyer")

    seller_net_proceeds: Optional[Decimal] = Field(
        default=None, description="Net proceeds to seller"
    )
    buyer_cash_required: Optional[Decimal] = Field(
        default=None, description="Cash required from buyer"
    )

    # Additional Metadata
    page_count: Optional[int] = Field(
        default=None, description="Number of pages in statement"
    )
    print_date: Optional[date] = Field(
        default=None, description="Date statement was printed"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v), date: lambda v: v.isoformat()}

    def get_total_closing_costs_buyer(self) -> Decimal:
        """Calculate total closing costs for buyer (excluding purchase price and loan proceeds)"""
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
        """Calculate total closing costs for seller"""
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
