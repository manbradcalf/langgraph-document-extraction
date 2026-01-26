"""Command-line interface for document extraction."""

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from docextract.config import get_settings, load_document_type
from docextract.graph import extract_document

app = typer.Typer(
    name="docextract",
    help="Extract structured data from documents using LangGraph and LLMs.",
    add_completion=False,
)
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@app.command()
def extract(
    document: Path = typer.Argument(
        ...,
        help="Path to the document to extract",
        exists=True,
        readable=True,
    ),
    document_type: str = typer.Option(
        "settlement_statement",
        "--type",
        "-t",
        help="Document type for schema and prompt selection",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Extract structured data from a document.

    Processes the document through the extraction pipeline:
    1. Extract text from PDF
    2. Parse with LLM using structured output
    3. Validate against schema
    4. Interpret extracted data with AI analysis
    5. Generate HTML report
    """
    setup_logging(verbose)

    console.print(
        Panel.fit(
            f"[bold blue]Document Extraction[/bold blue]\n"
            f"File: {document.name}\n"
            f"Type: {document_type}",
            border_style="blue",
        )
    )

    try:
        config = load_document_type(document_type)
        console.print(f"[dim]Using model: {config.llm.model}[/dim]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    with console.status("[bold green]Processing document..."):
        result = extract_document(str(document), document_type)

    # Display results
    _display_results(result)


def _display_results(result: dict) -> None:
    """Display extraction results."""
    table = Table(title="Extraction Results", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Document", result.get("document_path", ""))
    table.add_row("Extraction Method", result.get("extraction_method", ""))
    table.add_row("Extraction Model", result.get("model_used", ""))
    table.add_row(
        "Valid",
        "[green]Yes[/green]" if result.get("is_valid") else "[yellow]No[/yellow]",
    )

    # Interpretation status
    if result.get("interpretation"):
        interp_model = result.get("interpretation_model", "")
        table.add_row("Interpretation", f"[green]Generated[/green] ({interp_model})")
    else:
        table.add_row("Interpretation", "[dim]None[/dim]")

    if result.get("validation_errors"):
        errors = "\n".join(result["validation_errors"])
        table.add_row("Validation Errors", f"[red]{errors}[/red]")

    if result.get("error"):
        table.add_row("Error", f"[red]{result['error']}[/red]")

    if result.get("report_path"):
        table.add_row("Report", f"[green]{result['report_path']}[/green]")

    console.print(table)

    if result.get("is_valid"):
        console.print("\n[bold green]Extraction completed successfully![/bold green]")
    elif result.get("parsed_extraction_data"):
        console.print(
            "\n[bold yellow]Extraction completed with validation warnings.[/bold yellow]"
        )
    else:
        console.print("\n[bold red]Extraction failed.[/bold red]")
        raise typer.Exit(1)


@app.command()
def list_types() -> None:
    """List available document types."""
    settings = get_settings()
    types_dir = Path(settings.document_types_dir)

    table = Table(title="Available Document Types", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Source", style="dim")

    # Built-in types
    builtins = ["settlement_statement"]
    for name in builtins:
        try:
            config = load_document_type(name)
            source = "yaml" if (types_dir / f"{name}.yaml").exists() else "built-in"
            table.add_row(name, config.description, source)
        except Exception:
            pass

    # YAML types not in builtins
    if types_dir.exists():
        for yaml_file in types_dir.glob("*.yaml"):
            name = yaml_file.stem
            if name not in builtins:
                try:
                    config = load_document_type(name)
                    table.add_row(name, config.description, "yaml")
                except Exception:
                    pass

    console.print(table)


@app.command()
def info(
    document_type: str = typer.Argument(
        ...,
        help="Document type to show info for",
    ),
) -> None:
    """Show detailed info about a document type."""
    try:
        config = load_document_type(document_type)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    interp_status = (
        "[green]Enabled[/green]"
        if config.interpretation.enabled
        else "[dim]Disabled[/dim]"
    )

    console.print(
        Panel.fit(
            f"[bold]{config.name}[/bold]\n"
            f"{config.description}\n\n"
            f"[dim]Schema:[/dim] {config.schema_path}\n"
            f"[dim]Extraction Model:[/dim] {config.llm.model}\n"
            f"[dim]Temperature:[/dim] {config.llm.temperature}\n"
            f"[dim]Max Retries:[/dim] {config.llm.max_retries}\n\n"
            f"[dim]Interpretation:[/dim] {interp_status}\n"
            f"[dim]Interpretation Model:[/dim] {config.interpretation.model}",
            title="Document Type Info",
            border_style="blue",
        )
    )

    if config.validation.required_fields:
        console.print("\n[bold]Required Fields:[/bold]")
        for field in config.validation.required_fields:
            console.print(f"  - {field}")

    if config.validation.custom_validators:
        console.print("\n[bold]Custom Validators:[/bold]")
        for validator in config.validation.custom_validators:
            console.print(f"  - {validator}")


if __name__ == "__main__":
    app()
