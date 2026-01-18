"""Jinja2 prompt templates for document extraction."""

from jinja2 import Template


def render_prompt(template_str: str, **context) -> str:
    """Render a Jinja2 template string with the given context.

    Args:
        template_str: Jinja2 template string.
        **context: Variables to inject into the template.

    Returns:
        Rendered prompt string.
    """
    template = Template(template_str)
    return template.render(**context)


# Default prompts for settlement statements
DEFAULT_SYSTEM_PROMPT = """You are a real estate settlement statement parser.
Your task is to extract structured data from settlement statements accurately.

Guidelines:
- Extract all financial amounts as decimal numbers
- Use ISO format for dates (YYYY-MM-DD)
- Categorize line items correctly (payoffs, commissions, fees, taxes, etc.)
- Identify all parties involved (buyer, seller, lender)
- Extract all property addresses
- Be precise with debits and credits assignments
"""

DEFAULT_USER_PROMPT = """Parse the following settlement statement and extract all relevant data.

Document text:
{{ extracted_text }}

Extract the complete settlement statement data including:
- Header information (title company, settlement date, order number)
- All parties (buyer, seller, lender)
- Property addresses
- Purchase price and deposits
- Loan details if applicable
- All line items categorized appropriately
- Financial totals and summaries
"""
