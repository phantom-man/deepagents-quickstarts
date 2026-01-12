# DeepAgents (Project Atlas)

## Project Summary

DeepAgents ("Atlas") is an autonomous multi-agent studio system that transforms concepts into high-fidelity audiovisual content using a strict 'Hub-and-Spoke' architecture where Intelligence (Anthropic) directs Media (Replicate) with rigid state management (Postgres).



DeepAgents (codenamed "Atlas") is an autonomous multi-agent studio system designed to produce high-fidelity audiovisual content (Commercials, Music Videos, Narratives, Synthetic Personas) from high-level concepts. It simulates a real-world production team with specialized agents collaborating to create a final output.

## Core Objectives

1. **Autonomous Production**: Transform a text prompt (e.g., "Coffee commercial", "Cyberpunk Synthwave Music Video", "Tech YouTuber Personality") into a structured content plan, validated research facts, and generated AV assets (Voice, Music, Video, Image) without human micro-management.
2. **Epistemic Integrity**: Ensure all claims made in the creative content are fact-checked by a dedicated "Confidence Agent" using a "Trust-But-Verify" ontology.
3. **Enterprise-Grade Architecture**: Implement robust state management (OLTP), deep observability (OTLP), and hybrid persistence (Vector + Relational) to support long-running, interruptible workflows.
4. **Zero-Touch Usability**: Provide a Streamlit GUI that auto-configures the environment and locks down upon failure, ensuring a stable user experience.

## Target Audience

- **Creative Agencies**: For rapid storyboarding and animatic generation.
- **Developers**: As a reference implementation for complex LangGraph multi-agent architectures.

## Architecture Highlights

- **Orchestration**: LangGraph (Async) with Postgres Checkpointing (OLTP).
- **Communication**: Streamlit GUI with Asyncio Bridge to backend agents.
- **Memory**:
  - **LanceDB**: Semantic storage (Documents, Learnings).
  - **Postgres**: State persistence ("The Nervous System").
- **Observation**: OpenTelemetry (OTLP) tracing to LangSmith.

## Critical Constraints

- **Model**: Google Gemini (Primary), XTTS-v2 (Voice), Veo/Imagen (Visuals).
- **Standards**: All agents must adhere to strict JSON/Markdown Ontologies.
- **Quality**: "The Jewel Standard" - Code must be linted and type-checked; mediocrity is considered a bug.
- **Handle**: LangChain Hub Handle must be strictly configured (`damienfosborn`).

## Current Status

- **Phase**: System Evaluation & Optimization.
- **Modules**: Director, Researcher, Confidence, Composer, Cinematographer (Active).
- **Infrastructure**: Fully instrumented (Postgres + OTLP).


## Goals

- Autonomous Production: zero-touch creation of AV assets.
- Epistemic Integrity: Fact-checking via Confidence Agent.
- Enterprise Architecture: LangGraph (Async) + Postgres (OLTP).
- Strict Observability: Full OTLP Tracing + Hub Prompt Management.



## Constraints

- Model: Anthropic (Intelligence), Replicate (Media).
- Prompts: Must sync with LangSmith Hub (No Local Failover).
- Quality: 'The Jewel Standard' - 10/10 Linting.
- Standards: Strict JSON/Markdown Ontologies.



## Stakeholders

- Creative Agencies
- Developers

