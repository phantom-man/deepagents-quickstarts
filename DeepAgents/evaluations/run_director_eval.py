import os

# Import Director Agent
# Need to add repo root to path
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_google_vertexai import ChatVertexAI # Deprecated
from langsmith import evaluate
from langsmith.schemas import Example, Run
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Insert at 0 to prioritize local code over installed packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent

# Load env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))

# Initialize Agent
director_app = create_director_agent(model_name="gemini-2.0-flash-001")


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(
        Exception
    ),  # Broad for now, narrow to specific API errors in prod
    reraise=True,
)
def _invoke_agent_safe(user_query: str):
    """
    Invokes the agent with exponential backoff for rate limits.
    """
    return director_app.invoke(
        {"messages": [HumanMessage(content=user_query)]}, config={"tags": ["eval_run"]}
    )


def target(inputs: dict) -> dict:
    """
    Wraps the Director Agent for evaluation.
    Converts dataset input to agent input.
    """
    user_query = inputs["input_text"]

    # Run the agent (with Retry Logic)
    final_state = _invoke_agent_safe(user_query)

    # Extract final response
    # The output of create_react_agent is state. 'messages'[-1] is the AI response.
    messages = final_state["messages"]
    answer = messages[-1].content

    return {"output": answer}


# Evaluator LLM
eval_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001", vertexai=True, temperature=0, location="us-central1"
)


def element_presence_evaluator(run: Run, example: Example) -> dict:
    """
    Checks if reference elements are present in the output.
    """
    prediction = (run.outputs or {}).get("output", "")
    reference_elements = (example.outputs or {}).get("reference_elements", [])

    if not reference_elements:
        return {"key": "accuracy", "score": 1}

    # Ask LLM to grade
    prompt = f"""
    You are a strict grader. 
    Does the following text contain the concepts listed below?
    
    TEXT:
    {prediction}
    
    CONCEPTS:
    {", ".join(reference_elements)}
    
    For each concept, check if it is explicitly mentioned or clearly described.
    Return a score between 0 and 1 representing the percentage of concepts found.
    Return ONLY the number.
    """

    try:
        result = eval_llm.invoke(prompt)
        score_text = result.content
        # Handle potential list output from multimodal models
        if isinstance(score_text, list):
            score_text = "".join([str(item) for item in score_text])

        score_text = score_text.strip()
        score = float(score_text)
        return {"key": "accuracy", "score": score}
    except Exception as e:
        print(f"Eval Error: {e}")
        return {"key": "accuracy", "score": 0}


if __name__ == "__main__":
    print("Running Evaluation on Director Agent...")
    evaluate(
        target,
        data="Director-Commercial-Tests-v1",
        evaluators=[element_presence_evaluator],
        experiment_prefix="director-flash-eval",
        max_concurrency=1,
    )
