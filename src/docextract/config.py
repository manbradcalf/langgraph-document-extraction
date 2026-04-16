"""Configuration management for document extraction."""

import importlib
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """LLM configuration."""

    model: str = "gpt-4o"
    temperature: float = 0.0
    max_retries: int = 2


class PromptsConfig(BaseModel):
    """Prompt configuration."""

    system: str
    user: str


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
{{ parsed_extraction_data }}

Provide a clear interpretation of this data."""
    model: str = "gpt-4o"
    temperature: float = 0.3


class DocumentTypeConfig(BaseModel):
    """Configuration for a document type."""

    name: str
    description: str = ""
    schema_path: str  # Fully qualified class path
    prompts: PromptsConfig
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

    config = _load_yaml_config(yaml_path)

    _config_cache[name] = config
    return config


def _load_yaml_config(path: Path) -> DocumentTypeConfig:
    """Load configuration from YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return DocumentTypeConfig(**data)


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
