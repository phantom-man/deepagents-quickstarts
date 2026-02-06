"""
AI Code Review Assistant - Backend API
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from agents.code_analyzer import CodeAnalysisAgent

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Code Review Assistant",
    description="Intelligent code review and analysis API",
    version="0.1.0"
)

# Initialize the code analysis agent
code_agent = CodeAnalysisAgent()

class CodeReviewRequest(BaseModel):
    code: str
    language: str
    context: Optional[str] = None

class ReviewComment(BaseModel):
    line: int
    type: str  # 'bug', 'style', 'security', 'suggestion'
    message: str
    severity: str  # 'low', 'medium', 'high'

class CodeReviewResponse(BaseModel):
    comments: List[ReviewComment]
    summary: str
    score: int  # 0-100

@app.get("/")
async def root():
    return {"message": "AI Code Review Assistant API", "status": "running"}

@app.post("/api/review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest):
    """
    Analyze code and provide review comments
    """
    try:
        # Use the AI agent to analyze the code
        analysis_result = code_agent.analyze_code(
            code=request.code,
            language=request.language,
            context=request.context or ""
        )

        # Convert to response format
        comments = [
            ReviewComment(
                line=comment.get("line", 0),
                type=comment.get("type", "suggestion"),
                message=comment.get("message", ""),
                severity=comment.get("severity", "medium")
            )
            for comment in analysis_result.get("comments", [])
        ]

        return CodeReviewResponse(
            comments=comments,
            summary=analysis_result.get("summary", "Analysis completed"),
            score=analysis_result.get("score", 75)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)</content>
<parameter name="filePath">c:\Users\User\source\repos\deepagents-quickstarts\code-review-assistant\backend\main.py