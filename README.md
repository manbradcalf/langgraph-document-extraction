# DocExtract

A LangGraph-powered document extraction pipeline for converting PDFs to structured data.

## Features

- **LangGraph workflow** - Robust extraction pipeline with retry logic and validation
- **Configurable document types** - YAML-based configuration for different document schemas
- **Structured LLM output** - Type-safe extraction using Pydantic schemas and OpenAI
- **AI interpretation** - Configurable analysis of extracted data with custom prompts
- **OCR fallback** - Automatic OCR for scanned documents
- **HTML reports** - Visual comparison with benchmark data and AI interpretation

## Installation

Requires Python 3.12+, [uv](https://github.com/astral-sh/uv) and tesseract and an OpenAI API Key.

```bash
# Install dependencies
uv sync

# Set OpenAI API key
export OPENAI_API_KEY=your-key-here
```

## Usage

### Extract a document

```bash
uv run docextract extract "example_settlement_statement.pdf" --type settlement_statement
```

### List available document types

```bash
uv run docextract list-types # where does list-types come from?
```

### Show document type info

```bash
uv run docextract info settlement_statement # where does info come from
```

### Verbose mode

```bash
uv run docextract extract "example_settlemenet_statement.pdf" -v
```

## Architecture

```
[START]
    │
    ▼
[extract_text] ── error ──▶ [generate_report] ──▶ [END]
    │
    ▼
[llm_parse]
    │
    ▼
[validate]
    │
    ├── invalid (retry available) ──▶ [llm_parse]
    │
    └── valid/has data ──▶ [interpret] ──▶ [generate_report] ──▶ [END]
```

The pipeline:

1. **extract_text** - Extract text from PDF (with OCR fallback)
2. **llm_parse** - Parse text into structured data using LLM
3. **validate** - Validate against schema and custom rules
4. **interpret** - Generate AI analysis of extracted data
5. **generate_report** - Create HTML report with all results

### Components

| Component   | Purpose                       |
| ----------- | ----------------------------- |
| `state.py`  | Graph state definition        |
| `graph.py`  | LangGraph workflow            |
| `config.py` | Document type loader          |
| `nodes/`    | Pipeline node implementations |
| `schemas/`  | Pydantic document schemas     |
| `readers/`  | Document readers (PDF)        |
| `prompts/`  | Jinja2 prompt templates       |

## Adding Document Types

Create a YAML file in `document_types/`:

```yaml
name: invoice
description: Invoice document

schema_path: docextract.schemas.invoice.Invoice

prompts:
  system: |
    You are an invoice parser...

  user: |
    Parse this invoice:
    {{ extracted_text }}

validation:
  required_fields:
    - invoice_number
    - total_amount

interpretation:
  enabled: true
  model: gpt-4o
  temperature: 0.3
  prompt: |
    Analyze this invoice and provide insights.

    Invoice Data:
    {{ parsed_data }}

    Summarize key details and flag any concerns.

llm:
  model: gpt-4o
  temperature: 0
  max_retries: 2
```

Then create the corresponding schema in `src/docextract/schemas/invoice.py`.

### Interpretation Configuration

The `interpretation` section is optional but powerful:

- **enabled** - Set to `false` to skip interpretation
- **model** - LLM model for analysis (can differ from extraction model)
- **temperature** - Higher values (0.3-0.7) allow more creative analysis
- **prompt** - Jinja2 template with access to `{{ parsed_data }}` (JSON)

## Output

Reports are generated in `outputs/reports/` with:

- **Interpretation** - AI-generated analysis and insights (default tab)
- **Extracted Data** - Parsed JSON from structured extraction
- **Benchmark** - Comparison with expected output
- **Diff** - Visual diff between extracted and benchmark
- **Raw Text** - Original OCR/extracted text
- Embedded PDF viewer (side-by-side)

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Format code
uv run ruff format src/
```

## Project Structure

```
python-poc/
├── pyproject.toml
├── README.md
├── src/
│   └── docextract/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── graph.py
│       ├── state.py
│       ├── nodes/
│       ├── schemas/
│       ├── prompts/
│       └── readers/
├── document_types/
│   └── settlement_statement.yaml
└── outputs/
    └── reports/
```
