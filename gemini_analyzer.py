import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def analyze_code(code_input):
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set. Please add it to your .env file."
    
    prompt = f"""
Analyze the following Python code for sustainability, performance, and efficiency.
Provide a report with the following sections in Markdown format:
## Issues Found
## Sustainability Score (out of 100)
## Optimization Suggestions
## Estimated Improvements
## Green Coding Recommendation

Code to analyze:
```python
{code_input}
```
"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini API: {e}"

def optimize_code(code_input):
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set. Please add it to your .env file."
    
    prompt = f"""
Optimize the following Python code for sustainability, performance, and memory efficiency.
Return ONLY the optimized Python code (with ```python ... ``` block if needed), followed by a brief summary of the improvements in Markdown format under the heading '## Improvements'.
Do not include any other conversational text.

Code to optimize:
```python
{code_input}
```
"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini API: {e}"
