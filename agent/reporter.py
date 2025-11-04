import json
import os
from typing import List, Dict, Any

class ReportGenerator:
    """Generates an accessibility report from a list of violations."""
    
    def generate_report(self, results: List[Dict[str, Any]], base_url: str, report_format: str, device_type: str = "desktop") -> str:
        """
        Generates and saves a report in the specified format from a list of page results.
        Each result is a dictionary containing the 'url' and 'violations'.
        """
        # Generate report content
        if report_format == "md":
            content = self._to_markdown(results, base_url, device_type)
            extension = "md"
        elif report_format == "json":
            content = self._to_json(results, base_url, device_type)
            extension = "json"
        elif report_format == "html":
            content = self._to_html(results, base_url, device_type)
            extension = "html"
        else:
            content = str(results)
            extension = "txt"
        
        # Save the report
        output_dir = f"results/{device_type}"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/accessibility_report.{extension}"
        self.save_report(content, filename)
        
        return content

    def _to_markdown(self, results: List[Dict[str, Any]], base_url: str, device_type: str = "desktop") -> str:
        """Formats the report as Markdown."""
        device_title = device_type.replace("_", " ").title()
        md_content = f"# Accessibility Report ({device_title}) for {base_url}\n\n"
        for result in results:
            url = result['url']
            violations = result['violations']
            device_info = ""
            if result.get('device_name') and result.get('browser'):
                device_info = f" ({result['device_name']} - {result['browser']})"
            md_content += f"## Page: {url}{device_info}\n\n"
            if not violations:
                md_content += "No accessibility violations found.\n\n"
                continue
            
            for violation in violations:
                md_content += f"- **Violation:** {violation['id']} ({violation['impact']})\n"
                md_content += f"  - **Description:** {violation['description']}\n"
                md_content += f"  - **Help:** {violation['helpUrl']}\n"
                md_content += "  - **Nodes:**\n"
                for node in violation['nodes']:
                    md_content += f"    - ` {node['html']} `\n"
            md_content += "\n"
        return md_content

    def _to_json(self, results: List[Dict[str, Any]], base_url: str, device_type: str = "desktop") -> str:
        """Formats the report as JSON."""
        report_data = {
            "baseUrl": base_url,
            "deviceType": device_type,
            "results": results
        }
        return json.dumps(report_data, indent=4)

    def _to_html(self, results: List[Dict[str, Any]], base_url: str, device_type: str = "desktop") -> str:
        """Formats the report as a detailed HTML document."""
        
        # 1. Calculate summary statistics
        total_pages = len(results)
        pages_with_violations = 0
        total_violations = 0
        impact_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        
        for result in results:
            if result.get('violations'):
                pages_with_violations += 1
                total_violations += len(result['violations'])
                for violation in result['violations']:
                    impact = violation.get('impact')
                    if impact in impact_counts:
                        impact_counts[impact] += 1

        # 2. Build HTML content with device type information
        device_title = device_type.replace("_", " ").title()
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Report ({device_title}) for {base_url}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background-color: #f8f9fa; color: #212529; }}
        .container {{ display: flex; }}
        #sidebar {{ width: 250px; background-color: #fff; border-right: 1px solid #dee2e6; padding: 20px; height: 100vh; position: fixed; overflow-y: auto; }}
        #main-content {{ margin-left: 270px; padding: 20px; width: calc(100% - 270px); }}
        h1, h2, h3, h4 {{ color: #343a40; }}
        h1 {{ font-size: 2rem; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; margin-top: 0; }}
        h2 {{ font-size: 1.5rem; }}
        h3 {{ font-size: 1.25rem; }}
        #sidebar h2 {{ font-size: 1.2rem; margin-top: 0; }}
        #sidebar ul {{ list-style: none; padding: 0; }}
        #sidebar li a {{ text-decoration: none; color: #007bff; display: block; padding: 8px 10px; border-radius: 5px; }}
        #sidebar li a:hover {{ background-color: #e9ecef; }}
        .summary-card {{ background-color: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; }}
        .summary-item {{ text-align: center; padding: 15px; border-radius: 5px; background-color: #f8f9fa; }}
        .summary-item h4 {{ margin: 0 0 5px 0; font-size: 1rem; color: #6c757d; }}
        .summary-item p {{ margin: 0; font-size: 1.5rem; font-weight: bold; }}
        .device-badge {{ display: inline-block; background-color: #007bff; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; margin-left: 10px; }}
        .page-report {{ background-color: #fff; border: 1px solid #dee2e6; border-radius: 8px; margin-bottom: 20px; scroll-margin-top: 20px; }}
        .page-header {{ padding: 15px 20px; border-bottom: 1px solid #dee2e6; background-color: #f8f9fa; border-radius: 8px 8px 0 0; }}
        .page-header h2 {{ margin: 0; font-size: 1.3rem; }}
        .page-header a {{ color: #0056b3; text-decoration: none; }}
        .page-header a:hover {{ text-decoration: underline; }}
        .page-content {{ padding: 20px; }}
        .violation-details {{ border: 1px solid #e9ecef; border-radius: 5px; margin-bottom: 15px; }}
        .violation-summary {{ padding: 15px; cursor: pointer; background-color: #f8f9fa; display: flex; justify-content: space-between; align-items: center; }}
        .violation-summary:hover {{ background-color: #e9ecef; }}
        .violation-summary h3 {{ margin: 0; font-size: 1.1rem; }}
        .violation-body {{ padding: 15px; border-top: 1px solid #e9ecef; display: none; }}
        details[open] .violation-body {{ display: block; }}
        .impact-critical {{ border-left: 5px solid #dc3545; }}
        .impact-serious {{ border-left: 5px solid #fd7e14; }}
        .impact-moderate {{ border-left: 5px solid #ffc107; }}
        .impact-minor {{ border-left: 5px solid #0d6efd; }}
        .impact-tag {{ display: inline-block; padding: 4px 8px; font-size: 0.8rem; font-weight: bold; color: #fff; border-radius: 4px; text-transform: capitalize; }}
        .tag-critical {{ background-color: #dc3545; }}
        .tag-serious {{ background-color: #fd7e14; }}
        .tag-moderate {{ background-color: #ffc107; color: #000; }}
        .tag-minor {{ background-color: #0d6efd; }}
        code {{ background-color: #e9ecef; padding: 2px 5px; border-radius: 3px; font-size: 0.9rem; display: block; white-space: pre-wrap; word-break: break-all;}}
        .node-details {{ padding: 10px; border: 1px solid #e9ecef; border-radius: 4px; margin-top: 10px; }}
        .screenshot {{ max-width: 100%; height: auto; border: 1px solid #dee2e6; border-radius: 5px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div id="sidebar">
            <h2>Pages Scanned</h2>
            <ul>
"""
        for i, result in enumerate(results):
            page_id = f"page-{i}"
            url = result['url']
            status_icon = "❌" if result.get('violations') else "✅"
            html_content += f'<li><a href="#{page_id}">{status_icon} {url.split("/")[-1] or "Homepage"}</a></li>'
        
        html_content += f"""
            </ul>
        </div>
        <div id="main-content">
            <h1>Accessibility Report <span class="device-badge">{device_title}</span></h1>
            <div class="summary-card">
                <h2>Executive Summary ({device_title})</h2>
                <div class="summary-grid">
                    <div class="summary-item">
                        <h4>Total Pages</h4>
                        <p>{total_pages}</p>
                    </div>
                    <div class="summary-item">
                        <h4>Pages with Violations</h4>
                        <p>{pages_with_violations}</p>
                    </div>
                    <div class="summary-item">
                        <h4>Total Violations</h4>
                        <p>{total_violations}</p>
                    </div>
                </div>
                <h3 style="margin-top: 20px;">Violations by Severity</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <h4 style="color: #dc3545;">Critical</h4>
                        <p>{impact_counts['critical']}</p>
                    </div>
                    <div class="summary-item">
                        <h4 style="color: #fd7e14;">Serious</h4>
                        <p>{impact_counts['serious']}</p>
                    </div>
                    <div class="summary-item">
                        <h4 style="color: #ffc107;">Moderate</h4>
                        <p>{impact_counts['moderate']}</p>
                    </div>
                    <div class="summary-item">
                        <h4 style="color: #0d6efd;">Minor</h4>
                        <p>{impact_counts['minor']}</p>
                    </div>
                </div>
            </div>
"""

        for i, result in enumerate(results):
            page_id = f"page-{i}"
            url = result['url']
            violations = result.get('violations', [])
            
            # Extract device and browser info if available
            device_info = ""
            if result.get('device_name') and result.get('browser'):
                device_info = f" <small>({result['device_name']} - {result['browser']})</small>"
            
            html_content += f'<div id="{page_id}" class="page-report"><div class="page-header"><h2><a href="{url}" target="_blank">{url}</a>{device_info}</h2></div>'
            html_content += '<div class="page-content">'

            if not violations:
                html_content += "<p>✅ No accessibility violations found.</p>"
            else:
                for violation in violations:
                    impact = violation.get('impact', 'unknown')
                    html_content += f'<details class="violation-details impact-{impact}">'
                    html_content += f'<summary class="violation-summary"><h3>{violation["id"]}</h3><span class="impact-tag tag-{impact}">{impact}</span></summary>'
                    html_content += '<div class="violation-body">'
                    html_content += f"<p><strong>Description:</strong> {violation['description']}</p>"
                    html_content += f'<p><strong>Help:</strong> <a href="{violation["helpUrl"]}" target="_blank">Learn more</a></p>'
                    html_content += "<h4>Affected Nodes:</h4>"
                    for node in violation['nodes']:
                        html_content += '<div class="node-details">'
                        html_content += f"<code>{node['html']}</code>"
                        if node.get('screenshot'):
                            # Make screenshot path relative to the HTML file location
                            screenshot_path = node['screenshot']
                            # If path contains 'results/', make it relative to the device folder
                            if 'results/' in screenshot_path and device_type != "all_devices":
                                # Extract just the filename from the full path
                                screenshot_filename = screenshot_path.split('/')[-1]
                                relative_path = f"screenshots/{screenshot_filename}"
                            else:
                                relative_path = screenshot_path
                            html_content += f"<img src='{relative_path}' alt='Screenshot of the accessibility issue' class='screenshot'>"
                        html_content += '</div>'
                    html_content += "</div></details>"
            
            html_content += "</div></div>"

        html_content += """
        </div>
    </div>
</body>
</html>
"""
        return html_content

    def save_report(self, report_content: str, filename: str):
        """Saves the report to a file."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
