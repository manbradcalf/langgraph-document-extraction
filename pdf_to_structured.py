import json
import os
from datetime import datetime
from config import openai_client
from inputs.openai_models import models
from models.settlement_statement import SettlementStatement
from pdf_reader import read_pdf
from template import html_template

# Setup
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
pdf_path = "/Users/benmedcalf/code/segtax/python-poc/Executed Closing Statement (1).pdf"
extracted_text = read_pdf(pdf_path)
openai_model = models[1]
system_prompt = """
    You are an expert at structured data extraction from real estate settlement statements.

    You will be given unstructured text from a Settlement Statement and should convert it into the given structure.

    Key instructions:
    1. Extract all financial amounts as precise decimal values
    2. Parse dates in the format they appear (e.g., "May 29, 2025" -> "2025-05-29")
    3. Identify parties correctly with their entity types (LLC, LP, etc.)
    4. Categorize line items into appropriate sections (commissions, taxes, fees, etc.)
    5. Determine whether each cost is a debit to seller or buyer
    6. For tax items, extract both the basis amount and the tax amount
    7. For adjustments, extract period information and daily rates when available
    8. Calculate totals accurately for both buyer and seller sides

    Pay special attention to:
    - Property addresses (may be multiple properties)
    - Loan details (principal amount, draws, balances)
    - Tax calculations and who pays them
    - Prorations and adjustments with date ranges
    - Commission structures and percentages
    """

# Execution
result = openai_client.beta.chat.completions.parse(
    model=openai_model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": extracted_text},
    ],
    response_format=SettlementStatement,
    temperature=0,
)


def generate_html_report(contract_data, pdf_path, extracted_text):
    """Generate HTML report showing parsed data alongside original PDF"""

    # Get PDF filename and create relative path
    pdf_filename = os.path.basename(pdf_path)

    # Copy PDF to same directory as HTML for relative linking
    import shutil

    local_pdf_path = f"./outputs/reports/report_{pdf_filename}"
    shutil.copy2(pdf_path, local_pdf_path)

    # Convert contract data to readable format
    if contract_data:
        # Use model_dump with serialization mode to handle dates properly
        contract_dict = contract_data.model_dump(mode="json")
        contract_json = json.dumps(contract_dict, indent=2, default=str)
    else:
        contract_json = "Unable to parse PDF"

    # Load benchmark JSON for comparison
    benchmark_json = "Benchmark file not found"
    try:
        with open("benchmark.json", "r", encoding="utf-8") as f:
            benchmark_data = json.load(f)
            benchmark_json = json.dumps(benchmark_data, indent=2, default=str)
    except FileNotFoundError:
        benchmark_json = "Benchmark file not found"
    except Exception as e:
        benchmark_json = f"Error loading benchmark: {str(e)}"

    return html_template(
        pdf_filename,
        contract_json,
        benchmark_json,
        extracted_text,
        openai_model,
        local_pdf_path,
        timestamp,
    )


if result.choices[0].message.parsed is not None:
    contract: SettlementStatement = result.choices[0].message.parsed

    # Validate JSON matches the Pydantic class
    contract_dict = contract.model_dump(mode="json")
    contract_json = json.dumps(contract_dict, indent=2, default=str)

    contract.model_validate_json(contract_json, strict=True)

    # Generate HTML report
    html_content = generate_html_report(contract, pdf_path, extracted_text)

    # Save HTML file
    output_path = f"outputs/reports/pdf_analysis_report-{timestamp}-{openai_model}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML report generated: {output_path}")
    print("Open the file in your browser to view the analysis results.")
else:
    # Generate HTML report even if parsing failed
    html_content = generate_html_report(None, pdf_path, extracted_text)
    output_path = "pdf_analysis_report.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML report generated: {output_path}")
    print("Unable to parse PDF, but extracted text is available in the report.")


# TODO: scoring
# score = benchmark(result,expected)
# return score, system_prompt, openai_model
