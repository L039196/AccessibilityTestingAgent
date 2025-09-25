import google.generativeai as genai
from PIL import Image
import io

class MultimodalAnalyzer:
    """Analyzes website data using a multi-modal AI model."""
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.foundation_model = genai.GenerativeModel("gemini-pro-vision")

    async def find_contextual_issues(self, page_data: dict):
        """Analyzes page data to find accessibility issues."""
        screenshot_image = Image.open(io.BytesIO(page_data['screenshot']))
        dom_html = page_data['dom']
        
        prompt = f"""
        Analyze the provided website data for accessibility issues based on WCAG 2.1 AA standards.
        You are an expert accessibility tester. Reason across the image and DOM.

        1.  **Visual Analysis**: Look at the screenshot.
            - Is there any text with low color contrast?
            - Are interactive elements (buttons, links) visually distinct?
            - Is the focus indicator clearly visible on interactive elements?
        2.  **Structural Analysis**: Look at the DOM.
            - Do images have descriptive alt attributes?
            - Are headings (h1-h6) used in a logical order?
            - Do form inputs have associated labels?
        3.  **Holistic Finding**: Synthesize your findings. For each issue, provide:
            - A description of the issue.
            - The HTML snippet of the problematic element.
            - A suggestion for how to fix it.

        DOM: ```html\n{dom_html}\n```
        """
        
        response = await self.foundation_model.generate_content_async([prompt, screenshot_image])
        return response.text
