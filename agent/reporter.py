import json
import os
from typing import List, Dict, Any
from .violation_fixer import ViolationFixer

class ReportGenerator:
    """Generates an accessibility report from a list of violations."""
    
    def __init__(self):
        """Initialize reporter with violation fixer."""
        self.fixer = ViolationFixer()
    
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
        
        # Save the report - use hierarchical structure for mobile and tablet
        if device_type.startswith('mobile-'):
            platform = device_type.replace('mobile-', '')
            output_dir = os.path.join("results", "mobile", platform)
        elif device_type.startswith('tablet-'):
            platform = device_type.replace('tablet-', '')
            output_dir = os.path.join("results", "tablet", platform)
        else:
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
        pages_with_errors = 0
        auth_failed_pages = 0
        total_violations = 0
        impact_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        
        for result in results:
            if result.get('error'):
                pages_with_errors += 1
                if result.get('authentication_failed'):
                    auth_failed_pages += 1
            elif result.get('violations'):
                pages_with_violations += 1
                total_violations += len(result['violations'])
                for violation in result['violations']:
                    impact = violation.get('impact')
                    if impact in impact_counts:
                        impact_counts[impact] += 1

        # Calculate successfully scanned pages (total - auth failures)
        pages_scanned_successfully = total_pages - auth_failed_pages

        # 2. Build HTML content with device type information
        device_title = device_type.replace("_", " ").title()
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Report ({device_title}) for {base_url}</title>
    <!-- Metadata for parsing by automation tools -->
    <meta name="accessibility-report-total-pages" content="{total_pages}">
    <meta name="accessibility-report-scanned-successfully" content="{pages_scanned_successfully}">
    <meta name="accessibility-report-auth-failures" content="{auth_failed_pages}">
    <meta name="accessibility-report-pages-with-violations" content="{pages_with_violations}">
    <meta name="accessibility-report-pages-with-errors" content="{pages_with_errors}">
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
        
        /* Code Fix Section Styles - Vertical Stacked Layout */
        .code-fix-section {{ margin-top: 25px; padding: 25px; background: linear-gradient(to bottom, #f8f9fa, #ffffff); border-radius: 10px; border: 3px solid #28a745; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        
        .fix-explanation {{ font-size: 1.1rem; color: #155724; background-color: #d4edda; padding: 15px 20px; border-radius: 8px; margin-bottom: 25px; border-left: 5px solid #28a745; font-weight: 500; }}
        
        /* Vertical stacking - one section on top of the other */
        .code-comparison {{ margin: 20px 0; display: block; }}
        
        .code-before, .code-after {{ 
            background: #fff; 
            border-radius: 8px; 
            overflow: hidden; 
            box-shadow: 0 3px 6px rgba(0,0,0,0.12); 
            margin-bottom: 20px;
            border: 2px solid #dee2e6;
        }}
        
        .code-header {{ 
            padding: 15px 20px; 
            font-weight: 700; 
            font-size: 1.1rem; 
            border-bottom: 3px solid #dee2e6;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .code-before .code-header {{ 
            background: linear-gradient(135deg, #f8d7da 0%, #f5c2c7 100%); 
            color: #721c24; 
            border-bottom-color: #dc3545;
        }}
        
        .code-after .code-header {{ 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
            color: #155724; 
            border-bottom-color: #28a745;
        }}
        
        .code-before pre, .code-after pre {{ 
            margin: 0; 
            padding: 20px; 
            background: #f8f9fa; 
            overflow-x: auto; 
            max-height: 500px;
            border-top: 1px solid #e9ecef;
        }}
        
        .code-before code, .code-after code {{ 
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Courier New', monospace; 
            font-size: 0.95rem; 
            line-height: 1.7; 
            display: block;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        
        .copy-button {{ 
            display: block; 
            width: calc(100% - 40px); 
            margin: 0 20px 20px 20px; 
            padding: 14px 20px; 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: 700; 
            font-size: 1.05rem; 
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
        }}
        
        .copy-button:hover {{ 
            background: linear-gradient(135deg, #218838 0%, #1ea87a 100%); 
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(40, 167, 69, 0.4);
        }}
        
        .copy-button:active {{ 
            background: #1e7e34; 
            transform: translateY(0);
        }}
        
        .css-fix {{ 
            margin-top: 20px; 
            background: #fff; 
            border-radius: 8px; 
            overflow: hidden; 
            box-shadow: 0 3px 6px rgba(0,0,0,0.12); 
            border: 2px solid #0d6efd;
        }}
        
        .css-fix .code-header {{ 
            background: linear-gradient(135deg, #cfe2ff 0%, #b6d4fe 100%); 
            color: #084298; 
            border-bottom-color: #0d6efd;
        }}
        
        .css-fix pre {{ 
            margin: 0; 
            padding: 20px; 
            background: #f8f9fa; 
            overflow-x: auto; 
        }}
        
        .fix-steps {{ 
            margin-top: 20px; 
            padding: 20px; 
            background: #ffffff; 
            border-radius: 8px; 
            border-left: 5px solid #0d6efd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }}
        
        .fix-steps strong {{ 
            color: #0d6efd; 
            font-size: 1.05rem; 
        }}
        
        .fix-steps ol {{ 
            margin: 15px 0 0 0; 
            padding-left: 25px; 
        }}
        
        .fix-steps li {{ 
            margin: 12px 0; 
            line-height: 1.7;
            color: #495057;
        }}
        
        .wcag-reference {{ 
            margin-top: 20px; 
            padding: 15px 20px; 
            background: linear-gradient(135deg, #e7f3ff 0%, #d4e9ff 100%); 
            border-radius: 8px; 
            color: #004085; 
            font-size: 1rem; 
            border-left: 5px solid #007bff;
            font-weight: 500;
        }}
        
        .screenshot-wrapper {{ 
            margin-top: 25px; 
            padding: 20px; 
            background: linear-gradient(to bottom, #ffffff, #f8f9fa); 
            border-radius: 10px; 
            border: 3px solid #007bff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .screenshot-wrapper h4 {{ 
            margin-top: 0; 
            margin-bottom: 15px;
            color: #007bff; 
            font-size: 1.15rem;
            font-weight: 700;
        }}
    </style>
    <script>
    // Copy code to clipboard
    function copyCode(button) {{
        const code = button.getAttribute('data-code');
        navigator.clipboard.writeText(code).then(() => {{
            const originalText = button.textContent;
            button.textContent = '✅ Copied!';
            button.style.background = '#218838';
            setTimeout(() => {{
                button.textContent = originalText;
                button.style.background = '#28a745';
            }}, 2000);
        }}).catch(err => {{
            alert('Failed to copy code: ' + err);
        }});
    }}
    </script>
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
            status_icon = "❌" if result.get('error') else ("⚠️" if result.get('violations') else "✅")
            html_content += f'<li><a href="#{page_id}">{status_icon} {url.split("/")[-1] or "Homepage"}</a></li>'
        
        html_content += f"""
            </ul>
        </div>
        <div id="main-content">
            <h1>Accessibility Report <span class="device-badge">{device_title}</span></h1>
            
            {f'''<div class="summary-card" style="background-color: #fff3cd; border-color: #ffc107;">
                <h2 style="color: #856404;">⚠️ Authentication Required</h2>
                <p style="color: #856404; margin: 10px 0;">
                    <strong>{auth_failed_pages}</strong> page(s) require SSO authentication and could not be tested.
                </p>
                <p style="color: #856404; margin: 10px 0;">
                    <strong>Action Required:</strong> Configure SSO credentials in Settings (⚙️ icon) → Test Username & Test Password
                </p>
                <p style="color: #6c757d; font-size: 0.9rem; margin: 10px 0;">
                    Note: Public pages were tested successfully. Re-run the test after configuring credentials to test protected pages.
                </p>
            </div>''' if auth_failed_pages > 0 else ''}
            
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
                        <h4>Failed Pages</h4>
                        <p style="color: #dc3545;">{pages_with_errors}</p>
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

            # Check for errors (e.g., authentication failures)
            if result.get('error'):
                error_msg = result['error']
                error_type = result.get('error_type', 'Error')
                is_auth_error = result.get('authentication_failed', False)
                
                error_style = 'background-color: #fee; border-left: 5px solid #dc3545; padding: 15px; border-radius: 5px; margin-bottom: 10px;'
                html_content += f'<div style="{error_style}">'
                html_content += f'<h3 style="color: #dc3545; margin-top: 0;">❌ {error_type}</h3>'
                html_content += f'<p><strong>Error:</strong> {error_msg}</p>'
                if is_auth_error:
                    html_content += '<p><strong>Action Required:</strong> Please verify your SSO credentials in Settings are correct.</p>'
                    html_content += '<p><em>Note: This page requires authentication. The test failed before analyzing accessibility.</em></p>'
                html_content += '</div>'
            elif not violations:
                html_content += "<p>✅ No accessibility violations found.</p>"
            
            if violations:
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
                        
                        # Generate fix suggestion
                        fix = self.fixer.generate_fix(violation, node)
                        if fix:
                            html_content += self._render_code_fix(fix)
                        
                        # Display screenshot with clear wrapper
                        if node.get('screenshot'):
                            # Make screenshot path relative to the HTML file location
                            screenshot_path = node['screenshot']
                            # Extract just the filename from the full path
                            # Path format: results/desktop/screenshots/screenshot_desktop_default_*.png
                            # HTML location: results/desktop/accessibility_report.html
                            # Relative path needed: screenshots/screenshot_desktop_default_*.png
                            if '/' in screenshot_path or '\\' in screenshot_path:
                                # Get just the filename
                                screenshot_filename = os.path.basename(screenshot_path)
                                relative_path = f"screenshots/{screenshot_filename}"
                            else:
                                # Already just a filename
                                relative_path = f"screenshots/{screenshot_path}"
                            html_content += '<div class="screenshot-wrapper">'
                            html_content += '<h4>📸 Element Screenshot (Highlighted)</h4>'
                            html_content += f"<img src='{relative_path}' alt='Screenshot showing the problematic element highlighted in red' class='screenshot'>"
                            html_content += '</div>'
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
    
    def _render_code_fix(self, fix: Dict[str, Any]) -> str:
        """
        Render before/after code comparison with fix explanation.
        
        Args:
            fix: Dictionary with 'before', 'after', 'explanation', 'steps' keys
            
        Returns:
            HTML string with styled code comparison
        """
        html = '<div class="code-fix-section">'
        
        # Explanation
        html += f'<div class="fix-explanation"><strong>💡 How to Fix:</strong> {fix["explanation"]}</div>'
        
        # Before/After code comparison - Vertically stacked
        html += '<div class="code-comparison">'
        
        # BEFORE code
        html += '<div class="code-before">'
        html += '<div class="code-header">❌ Current Code (With Issue)</div>'
        html += f'<pre><code class="language-html">{self._escape_html(fix["before"])}</code></pre>'
        html += '</div>'
        
        # AFTER code
        html += '<div class="code-after">'
        html += '<div class="code-header">✅ Fixed Code (Copy This)</div>'
        html += f'<pre><code class="language-html">{self._escape_html(fix["after"])}</code></pre>'
        html += f'<button class="copy-button" onclick="copyCode(this)" data-code="{self._escape_attr(fix["after"])}">📋 Copy Fixed Code</button>'
        html += '</div>'
        
        html += '</div>'  # code-comparison
        
        # CSS fix if applicable (for color contrast issues)
        if 'css_fix' in fix:
            html += '<div class="css-fix">'
            html += '<div class="code-header">🎨 CSS Changes Needed</div>'
            html += f'<pre><code class="language-css">{self._escape_html(fix["css_fix"])}</code></pre>'
            html += '</div>'
        
        # Step-by-step instructions
        if fix.get('steps'):
            html += '<div class="fix-steps">'
            html += '<strong>📝 Steps to Apply Fix:</strong>'
            html += '<ol>'
            for step in fix['steps']:
                html += f'<li>{step}</li>'
            html += '</ol>'
            html += '</div>'
        
        # WCAG reference
        html += '<div class="wcag-reference">'
        html += f'<strong>📚 WCAG Criterion:</strong> {fix.get("wcag_criterion", "See violation help URL")}'
        html += '</div>'
        
        html += '</div>'  # code-fix-section
        
        return html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters for display in code blocks."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def _escape_attr(self, text: str) -> str:
        """Escape text for use in HTML attributes."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
                .replace('\n', '&#10;')
                .replace('\r', ''))

    def save_report(self, report_content: str, filename: str):
        """Saves the report to a file."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
