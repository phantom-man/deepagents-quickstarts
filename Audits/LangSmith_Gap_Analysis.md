# LangSmith & LangChain Best Practices: Gap Analysis

**Date:** 2026-01-10
**Author:** Copilot (Atlas)

## 1. Evaluation & Datasets (Critical Gap)

**Current State:**

- We have ad-hoc scripts (`run_director_eval.py`) that run logic.
- We do not use LangSmith's First-Class **Datasets** (KV Pairs) to define ground truth.
- Testing is anecdotal rather than systematic.

**Recommendation:**

- Create a `Create_Dataset.py` script to upload specific test cases (e.g., "Director - Commercial Request") to LangSmith.
- Refactor `run_director_eval.py` to use `run_on_dataset` or the `evaluate` function from `langsmith.evaluation`.

## 2. Tracing Granularity

**Current State:**

- We rely on auto-tracing from `ChatGoogleGenerativeAI`.
- Complex tools (e.g., `_handle_replicate_generation` in Composer) appear as flat "black boxes" or messy spans.
- Sub-agent calls are hard to see in the trace tree.

**Recommendation:**

- Decorate key agent functions (e.g., `run_research_task`, `compose_tool`) with `@traceable`.
- Use `run_tree.name` to explicitly name the spans (e.g., "Research Loop" vs "Tavily Search").

## 3. Human Feedback (RLHF)

**Current State:**

- The CLI (`studio.py`) prints output but offers no way for the user to rate the result.
- We are missing the feedback loop to improve the agents over time.

**Recommendation:**

- Add a simple prompt at the end of `studio.py`: "Rate this reponse (1-5)?".
- Use `client.create_feedback(run_id, ...)` to send this score to LangSmith.

## 4. Prompt Version Management

**Current State:**

- We pull the `latest` version of prompts.
- If a prompt is broken in the Hub, production breaks.

**Recommendation:**

- Pin prompts to specific commit hashes in `prompts.py` (e.g., `client.pull_prompt("director-system-main", version="abc1234")`).
- Use aliases like `prod` and `dev` in the Hub.

## 5. Deployment / Runnable Interfaces

**Current State:**

- We use custom `create_agent` factories.
- We are not fully leveraging `LangGraph` for state management (except in `deep_research`), making the commercial agents harder to orchestrate or deploy as APIs.

**Recommendation:**

- Convert Director and Composer to `LangGraph` StateGraphs.
- This allows for "Time Travel" debugging and better persistence.
