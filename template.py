def html_template(
    pdf_filename,
    contract_json,
    benchmark_json,
    extracted_text,
    openai_model,
    local_pdf_path,
    timestamp,
):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Analysis Report - {pdf_filename}</title>
        <script src="https://cdn.jsdelivr.net/npm/diff2html@3.4.47/bundles/js/diff2html-ui.min.js"></script>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/diff2html@3.4.47/bundles/css/diff2html.min.css" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
            }}
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
            .tabs {{
                display: flex;
                border-bottom: 2px solid #e9ecef;
                margin-bottom: 15px;
            }}
            .tab {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-bottom: none;
                padding: 10px 20px;
                cursor: pointer;
                font-weight: bold;
                margin-right: 5px;
                border-radius: 4px 4px 0 0;
            }}
            .tab.active {{
                background-color: #3498db;
                color: white;
                border-color: #3498db;
            }}
            .tab-content {{
                display: none;
            }}
            .tab-content.active {{
                display: block;
            }}
            .parsed-data {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                overflow-y: auto;
                max-height: 600px;
            }}
            .diff-container {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 10px;
                max-height: 600px;
                overflow-y: auto;
            }}
            .extracted-text {{
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                white-space: pre-wrap;
                overflow-y: auto;
                max-height: 300px;
                margin-top: 20px;
            }}
            .metadata {{
                background-color: #e8f4fd;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 20px;
                font-size: 12px;
            }}
            .benchmark-data {{
                background-color: #f0f8f0;
                border: 1px solid #d4edda;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                overflow-y: auto;
                max-height: 600px;
            }}
            @media (max-width: 768px) {{
                .content {{
                    flex-direction: column;
                }}
                .pdf-section {{
                    border-right: none;
                    border-bottom: 2px solid #ecf0f1;
                }}
                .tabs {{
                    flex-wrap: wrap;
                }}
                .tab {{
                    margin-bottom: 5px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>PDF Analysis Report</h1>
                <p>Generated on {timestamp}</p>
            </div>

            <div class="content">
                <div class="pdf-section">
                    <div class="section-title">📄 Original PDF</div>
                    <div class="metadata">
                        <strong>File:</strong> {pdf_filename}<br>
                        <strong>Model:</strong> {openai_model}<br>
                        <strong>Processing Date:</strong> {timestamp}
                    </div>
                    <iframe src="{local_pdf_path}"
                            class="pdf-embed"
                            type="application/pdf">
                        <p>Your browser does not support PDFs.
                           <a href="{local_pdf_path}">Download the PDF</a> to view it.</p>
                    </iframe>
                </div>

                <div class="data-section">
                    <div class="section-title">📊 Analysis Results</div>

                    <div class="tabs">
                        <div class="tab active" onclick="showTab('generated')">Generated JSON</div>
                        <div class="tab" onclick="showTab('benchmark')">Benchmark JSON</div>
                        <div class="tab" onclick="showTab('diff')">JSON Diff</div>
                        <div class="tab" onclick="showTab('text')">Extracted Text</div>
                    </div>

                    <div id="generated" class="tab-content active">
                        <div class="parsed-data">{contract_json}</div>
                    </div>

                    <div id="benchmark" class="tab-content">
                        <div class="benchmark-data">{benchmark_json}</div>
                    </div>

                    <div id="diff" class="tab-content">
                        <div class="diff-container" id="diff-viewer">
                            <p>Loading diff...</p>
                        </div>
                    </div>

                    <div id="text" class="tab-content">
                        <div class="extracted-text">{extracted_text}</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function showTab(tabName) {{
                // Hide all tab contents
                const contents = document.querySelectorAll('.tab-content');
                contents.forEach(content => content.classList.remove('active'));

                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => tab.classList.remove('active'));

                // Show selected tab content
                document.getElementById(tabName).classList.add('active');

                // Add active class to clicked tab
                event.target.classList.add('active');

                // Generate diff when diff tab is clicked
                if (tabName === 'diff') {{
                    generateDiff();
                }}
            }}

            function generateDiff() {{
                const generated = `{contract_json.replace("`", "\\`")}`;
                const benchmark = `{benchmark_json.replace("`", "\\`")}`;

                if (benchmark === "Benchmark file not found" || benchmark.startsWith("Error loading benchmark")) {{
                    document.getElementById('diff-viewer').innerHTML = '<p style="color: #dc3545; padding: 20px;">Benchmark file not available for comparison.</p>';
                    return;
                }}

                // Create unified diff format
                const generatedLines = generated.split('\\n');
                const benchmarkLines = benchmark.split('\\n');

                // Simple line-by-line comparison
                let diffHtml = '<div style="font-family: monospace; font-size: 12px;">';
                const maxLines = Math.max(generatedLines.length, benchmarkLines.length);

                for (let i = 0; i < maxLines; i++) {{
                    const genLine = generatedLines[i] || '';
                    const benchLine = benchmarkLines[i] || '';

                    if (genLine === benchLine) {{
                        diffHtml += `<div style="background-color: #f8f9fa; padding: 2px 5px; border-left: 3px solid #6c757d;">${{escapeHtml(genLine)}}</div>`;
                    }} else {{
                        if (benchLine) {{
                            diffHtml += `<div style="background-color: #f8d7da; padding: 2px 5px; border-left: 3px solid #dc3545;">- ${{escapeHtml(benchLine)}}</div>`;
                        }}
                        if (genLine) {{
                            diffHtml += `<div style="background-color: #d1ecf1; padding: 2px 5px; border-left: 3px solid #0ea5e9;">+ ${{escapeHtml(genLine)}}</div>`;
                        }}
                    }}
                }}

                diffHtml += '</div>';
                document.getElementById('diff-viewer').innerHTML = diffHtml;
            }}

            function escapeHtml(text) {{
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }}
        </script>
    </body>
    </html>
    """
