# DeepAgents (Project Atlas) Project Brief

## Project Summary
DeepAgents (codenamed "Atlas") is an autonomous multi-agent studio system designed to produce commercial video assets from high-level concepts. It simulates a real-world production team with specialized agents (Director, Researcher, Editor, Cinematographer, Composer) collaborating to create a final output.

## Core Objectives
1.  **Autonomous Production**: Transform a text prompt (e.g., "Coffee commercial") into a structured shot list, validated research facts, and generated AV assets (Voice, Music, Video, Image) without human micro-management.
2.  **Epistemic Integrity**: Ensure all claims made in the creative content are fact-checked by a dedicated "Confidence Agent" using a "Trust-But-Verify" ontology.
3.  **Enterprise-Grade Architecture**: Implement robust state management (OLTP), deep observability (OTLP), and hybrid persistence (Vector + Relational) to support long-running, interruptible workflows.
4.  **Zero-Touch Usability**: Provide a Streamlit GUI that auto-configures the environment and locks down upon failure, ensuring a stable user experience.

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

