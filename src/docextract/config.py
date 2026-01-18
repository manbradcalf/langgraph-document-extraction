"""Configuration management for document extraction."""

import importlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from docextract.prompts.templates import DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT


class LLMConfig(BaseModel):
    """LLM configuration."""

    model: str = "gpt-4o"
    temperature: float = 0.0
    max_retries: int = 2


class PromptsConfig(BaseModel):
    """Prompt configuration."""

    system: str = DEFAULT_SYSTEM_PROMPT
    user: str = DEFAULT_USER_PROMPT


class ValidationConfig(BaseModel):
    """Validation configuration."""

    required_fields: list[str] = Field(default_factory=list)
    custom_validators: list[str] = Field(default_factory=list)


class InterpretationConfig(BaseModel):
    """Configuration for the interpretation step.

    The interpretation node takes extracted structured data and
    produces insights, summaries, or analysis based on the prompt.
    """

    enabled: bool = True
    prompt: str = """Analyze the extracted document data and provide insights.

Extracted data:
{{ parsed_data }}

Provide a clear interpretation of this data."""
    model: str = "gpt-4o"
    temperature: float = 0.3


class DocumentTypeConfig(BaseModel):
    """Configuration for a document type."""

    name: str
    description: str = ""
    schema_path: str  # Fully qualified class path
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    interpretation: InterpretationConfig = Field(default_factory=InterpretationConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def get_schema_class(self) -> type:
        """Dynamically import and return the schema class."""
        module_path, class_name = self.schema_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)


class Settings(BaseSettings):
    """Application settings from environment variables."""

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    document_types_dir: str = "document_types"
    outputs_dir: str = "outputs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Cache for loaded configs
_config_cache: dict[str, DocumentTypeConfig] = {}


def load_document_type(name: str) -> DocumentTypeConfig:
    """Load a document type configuration by name.

    First checks for a YAML file in document_types/, then falls back
    to built-in configurations.

    Args:
        name: Document type identifier (e.g., "settlement_statement").

    Returns:
        DocumentTypeConfig for the requested type.

    Raises:
        ValueError: If the document type is not found.
    """
    if name in _config_cache:
        return _config_cache[name]

    settings = Settings()
    yaml_path = Path(settings.document_types_dir) / f"{name}.yaml"

    if yaml_path.exists():
        config = _load_yaml_config(yaml_path)
    else:
        config = _get_builtin_config(name)

    _config_cache[name] = config
    return config


def _load_yaml_config(path: Path) -> DocumentTypeConfig:
    """Load configuration from YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return DocumentTypeConfig(**data)


def _get_builtin_config(name: str) -> DocumentTypeConfig:
    """Get a built-in document type configuration."""
    builtins = {
        "settlement_statement": DocumentTypeConfig(
            name="settlement_statement",
            description="Real estate settlement/closing statement",
            schema_path="docextract.schemas.settlement_statement.SettlementStatement",
            prompts=PromptsConfig(
                system="""You are a real estate settlement statement parser.
Extract all financial data accurately from the document.

Guidelines:
- Extract amounts as decimal numbers
- Use ISO format for dates (YYYY-MM-DD)
- Categorize line items correctly
- Identify all parties (buyer, seller, lender)
- Extract all property addresses
- Be precise with debit/credit assignments""",
                user="""Parse this settlement statement and extract structured data.

Document text:
{{ extracted_text }}

Extract complete data including header info, parties, properties,
purchase price, loan details, all line items, and financial totals.""",
            ),
            validation=ValidationConfig(
                required_fields=[
                    "settlement_date",
                    "buyer",
                    "seller",
                    "purchase_price",
                ],
                custom_validators=["totals_balance"],
            ),
            interpretation=InterpretationConfig(
                enabled=True,
                prompt="""Categorize all line items from this settlement statement according to IRS Publication 551.

Settlement Data:
{{ parsed_data }}

Categories:
1. Costs Added to Basis - title insurance, recording fees, transfer taxes, survey, legal fees
2. Costs NOT Added to Basis - fire insurance, loan charges, occupancy costs
3. Loan Settlement Fees - points, mortgage insurance, prepaid interest (potentially deductible)
4. Prorations - property taxes, HOA dues, utilities
5. Seller's Costs - commissions, advertising, seller legal fees

For each line item: description, amount, category, buyer/seller, justification.
End with category totals.""",
                model="gpt-4o",
                temperature=0,
            ),
            llm=LLMConfig(model="gpt-4o", temperature=0, max_retries=2),
        ),
    }

    if name not in builtins:
        raise ValueError(
            f"Unknown document type: {name}. "
            f"Available types: {list(builtins.keys())}"
        )

    return builtins[name]


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
