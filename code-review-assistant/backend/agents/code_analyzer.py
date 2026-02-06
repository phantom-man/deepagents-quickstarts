"""
Code Analysis Agent using LangChain
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict, Any
import os

class CodeAnalysisAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        self.analysis_prompt = PromptTemplate(
            input_variables=["code", "language", "context"],
            template="""
You are an expert code reviewer. Analyze the following code for:

1. Bugs and logical errors
2. Security vulnerabilities
3. Code style and best practices
4. Performance issues
5. Maintainability concerns

Code to analyze:
Language: {language}
Context: {context}

```{language}
{code}
```

Provide your analysis in the following JSON format:
{{
    "comments": [
        {{
            "line": <line_number>,
            "type": "bug|security|style|performance|maintainability",
            "message": "<detailed_feedback>",
            "severity": "low|medium|high"
        }}
    ],
    "summary": "<overall_summary>",
    "score": <0-100_score>
}}

Only return valid JSON, no additional text.
"""
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.analysis_prompt)

    def analyze_code(self, code: str, language: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze code and return review results
        """
        try:
            result = self.chain.run(
                code=code,
                language=language,
                context=context
            )

            # Parse JSON response
            import json
            return json.loads(result.strip())

        except Exception as e:
            print(f"Error analyzing code: {e}")
            return {
                "comments": [],
                "summary": "Analysis failed due to technical error",
                "score": 50
            }

# Example usage
if __name__ == "__main__":
    agent = CodeAnalysisAgent()

    sample_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
"""

    result = agent.analyze_code(sample_code, "python", "Simple math utility")
    print(result)</content>
<parameter name="filePath">c:\Users\User\source\repos\deepagents-quickstarts\code-review-assistant\backend\agents\code_analyzer.py