"""Report generation node."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from docextract.state import ExtractionState

logger = logging.getLogger(__name__)


def generate_report(state: ExtractionState) -> ExtractionState:
    """Generate an HTML report of the extraction results.

    Args:
        state: Current state with parsed_data, interpretation, and metadata.

    Returns:
        Updated state with report_path.
    """
    document_path = Path(state["document_path"])
    parsed_data = state.get("parsed_data")
    extracted_text = state.get("extracted_text", "")
    model_used = state.get("model_used", "unknown")
    validation_errors = state.get("validation_errors", [])
    interpretation = state.get("interpretation", "")
    interpretation_model = state.get("interpretation_model", "")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Set up output directories
    output_dir = Path("outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy PDF to outputs for embedding
    pdf_filename = document_path.name
    output_pdf_path = output_dir / f"report_{pdf_filename}"
    try:
        shutil.copy(document_path, output_pdf_path)
    except Exception as e:
        logger.warning(f"Could not copy PDF: {e}")

    # Load benchmark for comparison if available
    benchmark_json = _load_benchmark()

    # Format parsed data as JSON
    if parsed_data:
        contract_json = json.dumps(parsed_data, indent=2, default=str)
    else:
        contract_json = json.dumps({"error": state.get("error", "No data parsed")})

    # Generate HTML report
    html_content = _generate_html(
        pdf_filename=pdf_filename,
        contract_json=contract_json,
        benchmark_json=benchmark_json,
        extracted_text=extracted_text,
        model_used=model_used,
        timestamp=timestamp,
        validation_errors=validation_errors,
        interpretation=interpretation or "",
        interpretation_model=interpretation_model or "",
    )

    # Write report
    report_filename = f"pdf_analysis_report-{timestamp}-{model_used}.html"
    report_path = output_dir / report_filename

    report_path.write_text(html_content)
    logger.info(f"Report generated: {report_path}")

    return {
        **state,
        "report_path": str(report_path),
    }


def _load_benchmark() -> str:
    """Load benchmark JSON for comparison."""
    benchmark_path = Path("benchmark.json")
    if benchmark_path.exists():
        try:
            with open(benchmark_path) as f:
                return json.dumps(json.load(f), indent=2)
        except Exception as e:
            return f"Error loading benchmark: {e}"
    return "Benchmark file not found"


def _generate_html(
    pdf_filename: str,
    contract_json: str,
    benchmark_json: str,
    extracted_text: str,
    model_used: str,
    timestamp: str,
    validation_errors: list[str],
    interpretation: str,
    interpretation_model: str,
) -> str:
    """Generate HTML report content."""
    validation_section = ""
    if validation_errors:
        errors_html = "".join(f"<li>{e}</li>" for e in validation_errors)
        validation_section = f"""
        <div class="validation-errors">
            <h4>Validation Errors</h4>
            <ul>{errors_html}</ul>
        </div>
        """

    # Format interpretation with markdown-like rendering
    interpretation_html = _format_interpretation(interpretation) if interpretation else "No interpretation available"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Extraction Report - {pdf_filename}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .header p {{ margin: 0; opacity: 0.8; }}
        .content {{
            display: flex;
            min-height: 800px;
        }}
        .pdf-section {{
            flex: 1;
            padding: 20px;
            border-right: 2px solid #ecf0f1;
        }}
        .data-section {{
            flex: 1;
            padding: 20px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        .pdf-embed {{
            width: 100%;
            height: 700px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .metadata {{
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 15px;
            font-size: 13px;
        }}
        .validation-errors {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 15px;
        }}
        .validation-errors h4 {{ margin: 0 0 10px 0; color: #721c24; }}
        .validation-errors ul {{ margin: 0; padding-left: 20px; }}
        .validation-errors li {{ color: #721c24; }}
        .tabs {{
            display: flex;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 15px;
        }}
        .tab {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-bottom: none;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            margin-right: 5px;
            border-radius: 4px 4px 0 0;
        }}
        .tab.active {{
            background: #3498db;
            color: white;
            border-color: #3498db;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .json-view {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            white-space: pre-wrap;
            overflow-y: auto;
            max-height: 600px;
        }}
        .benchmark-view {{
            background: #f0f8f0;
            border: 1px solid #d4edda;
        }}
        .text-view {{
            background: #fff3cd;
            border: 1px solid #ffeeba;
        }}
        .diff-view {{
            max-height: 600px;
            overflow-y: auto;
        }}
        .interpretation-view {{
            background: #e8f5e9;
            border: 1px solid #c8e6c9;
            padding: 20px;
            border-radius: 4px;
            line-height: 1.6;
            max-height: 600px;
            overflow-y: auto;
        }}
        .interpretation-view h1, .interpretation-view h2, .interpretation-view h3, .interpretation-view h4 {{
            color: #2e7d32;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }}
        .interpretation-view h1 {{ font-size: 1.4em; }}
        .interpretation-view h2 {{ font-size: 1.2em; }}
        .interpretation-view h3 {{ font-size: 1.1em; }}
        .interpretation-view ul, .interpretation-view ol {{
            margin: 0.5em 0;
            padding-left: 1.5em;
        }}
        .interpretation-view li {{ margin: 0.3em 0; }}
        .interpretation-view strong {{ color: #1b5e20; }}
        .interpretation-view table, .pub551-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin: 0;
        }}
        .interpretation-view th, .pub551-table th {{
            background: #2e7d32;
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
        }}
        .interpretation-view td, .pub551-table td {{
            padding: 8px;
            border-bottom: 1px solid #c8e6c9;
            vertical-align: top;
        }}
        .interpretation-view tbody tr:hover, .pub551-table tbody tr:hover {{
            background: #f1f8e9;
        }}
        .interpretation-view tfoot, .pub551-table tfoot {{
            background: #e8f5e9;
            font-weight: 600;
        }}
        .interpretation-view tfoot td, .pub551-table tfoot td {{
            padding: 10px 8px;
            border-top: 2px solid #2e7d32;
        }}
        .interpretation-model {{
            font-size: 11px;
            color: #666;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #c8e6c9;
        }}
        @media (max-width: 768px) {{
            .content {{ flex-direction: column; }}
            .pdf-section {{ border-right: none; border-bottom: 2px solid #ecf0f1; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Document Extraction Report</h1>
            <p>Generated {timestamp}</p>
        </div>
        <div class="content">
            <div class="pdf-section">
                <div class="section-title">Original PDF</div>
                <div class="metadata">
                    <strong>File:</strong> {pdf_filename}<br>
                    <strong>Model:</strong> {model_used}<br>
                    <strong>Processed:</strong> {timestamp}
                </div>
                <iframe src="report_{pdf_filename}" class="pdf-embed"></iframe>
            </div>
            <div class="data-section">
                <div class="section-title">Extraction Results</div>
                {validation_section}
                <div class="tabs">
                    <div class="tab active" onclick="showTab('interpretation')">Interpretation</div>
                    <div class="tab" onclick="showTab('generated')">Extracted Data</div>
                    <div class="tab" onclick="showTab('benchmark')">Benchmark</div>
                    <div class="tab" onclick="showTab('diff')">Diff</div>
                    <div class="tab" onclick="showTab('text')">Raw Text</div>
                </div>
                <div id="interpretation" class="tab-content active">
                    <div class="interpretation-view">
                        <div class="interpretation-model">Generated by {interpretation_model}</div>
                        {interpretation_html}
                    </div>
                </div>
                <div id="generated" class="tab-content">
                    <div class="json-view">{_escape_html(contract_json)}</div>
                </div>
                <div id="benchmark" class="tab-content">
                    <div class="json-view benchmark-view">{_escape_html(benchmark_json)}</div>
                </div>
                <div id="diff" class="tab-content">
                    <div class="diff-view" id="diff-viewer">Loading...</div>
                </div>
                <div id="text" class="tab-content">
                    <div class="json-view text-view">{_escape_html(extracted_text)}</div>
                </div>
            </div>
        </div>
    </div>
    <script>
        function showTab(name) {{
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(name).classList.add('active');
            event.target.classList.add('active');
            if (name === 'diff') generateDiff();
        }}
        function generateDiff() {{
            const gen = {json.dumps(contract_json)};
            const bench = {json.dumps(benchmark_json)};
            if (bench.includes('not found') || bench.includes('Error')) {{
                document.getElementById('diff-viewer').innerHTML = '<p>No benchmark available</p>';
                return;
            }}
            const genLines = gen.split('\\n');
            const benchLines = bench.split('\\n');
            let html = '<div style="font-family:monospace;font-size:12px;">';
            const maxLen = Math.max(genLines.length, benchLines.length);
            for (let i = 0; i < maxLen; i++) {{
                const g = genLines[i] || '';
                const b = benchLines[i] || '';
                if (g === b) {{
                    html += `<div style="background:#f8f9fa;padding:2px 5px;border-left:3px solid #6c757d;">${{escapeHtml(g)}}</div>`;
                }} else {{
                    if (b) html += `<div style="background:#f8d7da;padding:2px 5px;border-left:3px solid #dc3545;">- ${{escapeHtml(b)}}</div>`;
                    if (g) html += `<div style="background:#d1ecf1;padding:2px 5px;border-left:3px solid #0ea5e9;">+ ${{escapeHtml(g)}}</div>`;
                }}
            }}
            html += '</div>';
            document.getElementById('diff-viewer').innerHTML = html;
        }}
        function escapeHtml(t) {{
            const d = document.createElement('div');
            d.textContent = t;
            return d.innerHTML;
        }}
    </script>
</body>
</html>"""


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _format_interpretation(text: str) -> str:
    """Format interpretation text - pass through HTML or convert markdown."""
    import re

    stripped = text.strip()

    # Strip markdown code fences if present (```html ... ``` or ``` ... ```)
    code_fence_pattern = r"^```(?:html)?\s*\n?(.*?)\n?```$"
    match = re.match(code_fence_pattern, stripped, re.DOTALL | re.IGNORECASE)
    if match:
        stripped = match.group(1).strip()

    # If interpretation is already HTML (starts with a tag), return as-is
    if stripped.startswith("<table") or stripped.startswith("<div") or stripped.startswith("<html"):
        return stripped

    # Otherwise, convert markdown to HTML
    # Escape HTML first
    text = _escape_html(text)

    # Convert markdown headers to HTML
    text = re.sub(r"^\*\*\*(.+?)\*\*\*$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\*(.+?)\*\*$", r"<h4>\1</h4>", text, flags=re.MULTILINE)
    text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$", r"<h1>\1</h1>", text, flags=re.MULTILINE)

    # Convert numbered headers like "1. **Title**" to headers
    text = re.sub(
        r"^(\d+)\.\s+\*\*(.+?)\*\*", r"<h4>\1. \2</h4>", text, flags=re.MULTILINE
    )

    # Convert inline bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # Convert bullet points
    lines = text.split("\n")
    in_list = False
    result = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{stripped[2:]}</li>")
        elif re.match(r"^\d+\.\s", stripped) and not stripped.startswith("<h"):
            if not in_list:
                result.append("<ol>")
                in_list = True
            content = re.sub(r"^\d+\.\s+", "", stripped)
            result.append(f"<li>{content}</li>")
        else:
            if in_list:
                result.append("</ul>" if result[-2].startswith("<ul>") else "</ol>")
                in_list = False
            if stripped:
                result.append(f"<p>{line}</p>" if not line.startswith("<") else line)
            else:
                result.append("")

    if in_list:
        result.append("</ul>")

    return "\n".join(result)
