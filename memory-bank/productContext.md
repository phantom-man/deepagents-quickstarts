# Product Context

## Project Description

DeepAgents ("Atlas") is a commercial-grade, multi-agent automated production studio. It allows users to input high-level creative concepts and receive fully realized audiovisual assets.
Originally focused on commercials, the studio has expanded to support Music Production, Narrative Video, and Synthetic Personas.
Current Brain: Anthropic Claude 3 Haiku.
Infrastructure: Modernized LangGraph implementation.



DeepAgents ("Atlas") is a commercial-grade, multi-agent automated production studio. It allows users to input high-level creative concepts and receive fully realized audiovisual assets.
Originally focused on commercials, the studio has expanded to support Music Production, Narrative Video, and Synthetic Personas.
Current Brain: Anthropic Claude 3 Haiku (Cost/Availability optimized).



DeepAgents ("Atlas") is a commercial-grade, multi-agent automated production studio. It allows users to input high-level creative concepts and receive fully realized audiovisual assets. 
Originally focused on commercials, the studio has expanded to support:
- **Music Production**: Complete songs with lyrics and instrumentals.
- **Narrative Video**: Short films, YouTube content, and storytelling.
- **Synthetic Personas**: High-fidelity, believable artificial personalities for content creation.

The system is designed for "Zero Touch" operation, handling research, creative direction, asset generation, and quality assurance autonomously.

## Core Features


- **The Nervous System (Hybrid Persistence)**: Combines Semantic Memory (LanceDB for knowledge) and State Persistence (Postgres for workflow checkpointing).
- **Orchestra GUI**: A centralized Streamlit dashboard for controlling agents, monitoring system health (OTLP diagnostics), and reviewing generated assets.
- **Ontology-Driven Agents**:
  - **Director (Apollo)**: Creative Lead.
  - **Researcher (Delphi)**: Truth verification.
  - **Confidence (The Editor)**: Quality assurance.
  - **Cinematographer (Lumiere)**: Visual synthesis.
  - **Composer (Orpheus)**: Audio synthesis.
- **MemoriPilot**: Self-referential memory for the developer (Copilot) to maintain context across sessions.

## Architecture

The system follows a **Hub-and-Spoke** architecture managed by the `orchestrator.py` core.

- **Agent Factory**: Standardized on `langgraph.prebuilt.create_react_agent` for all modern models (Claude/Gemini). Retained `agent_factory_legacy.py` for Dumb Models (Replicate).
- **Backend Orchestration**: LangGraph (Async) managing stateful agent threads.
- **Data Layer**: LanceDB (Vector) + Postgres (OLTP).
- **Observability**: OpenTelemetry (OTLP) exporting traces to LangSmith.



The system follows a **Hub-and-Spoke** architecture managed by the `orchestrator.py` core.

- **Frontend**: Streamlit (Sync) with an `asyncio` bridge.
- **Backend Orchestration**: LangGraph (Async) managing stateful agent threads.
- **Data Layer**:
  - **OLTP**: `psycopg` (v3) connection pool.
  - **Vector**: LanceDB for semantic search.
- **Observability**: OpenTelemetry (OTLP) exporting traces to LangSmith.



The system follows a **Hub-and-Spoke** architecture managed by the `orchestrator.py` core (formerly `DeepAgents.py`).

- **Frontend**: Streamlit (Sync) with an `asyncio` bridge (`agent_runner.py`) to the backend.
- **Backend Orchestration**: LangGraph (Async) managing stateful agent threads.
- **Data Layer**:
  - **OLTP**: `psycopg` (v3) connection pool managing LangGraph checkpoints.
  - **Vector**: LanceDB for semantic search.
- **Observability**: OpenTelemetry (OTLP) exporting traces to LangSmith/Jaeger.

## Technical Stack

### Core Frameworks

- **LangChain / LangGraph**: Agent orchestration and state management.
- **Streamlit**: User Interface.
- **Pydantic**: Data validation and schema definition.

### AI & Models

- **Decision Engine (Brain)**:
  - **Primary**: Anthropic `claude-3-5-sonnet-latest`. (Reliable, High Reasoning, Paid Tier).
  - **Fallback**: Google Vertex AI `gemini-1.5-flash` or Replicate `meta/meta-llama-3-70b-instruct`.
- **Visuals (Image)**:
  - **Primary**: Google Vertex AI `imagen-4.0-fast-generate-001`.
  - **Alternate**: `imagen-3.0-generate-002`.
  - **Fallback**: Replicate `black-forest-labs/flux-schnell`.
- **Audio (Music/SFX)**:
  - **Primary**: Replicate `minimax/music-01` or `meta/musicgen`. (Google Lyria blocked by quota).
- **Voice (TTS)**:
  - **Primary**: Replicate `lucataco/xtts-v2`. (Google Audio blocked by quota).
- **Video**:
  - **Primary**: Replicate `zeroscope/v2-xl`. (Google Veo blocked by quota/access).

### Infrastructure

- **Orchestration**: LangGraph (StateGraph).
  - *Note*: Custom `deepagents` middleware is currently DISABLED manually in favor of native implementation.
- **Reflex Storage**: PostgreSQL (Local).
- **Semantic Storage**: LanceDB (Local).
- **Tracing**: OpenTelemetry (OTLP) / LangSmith.

## Libraries & Dependencies

- `langgraph-checkpoint-postgres`
- `asyncpg`, `psycopg-pool`
- `opentelemetry-api`, `opentelemetry-exporter-otlp`
- `streamlit`
- `google-genai`
- `lancedb`

## Libraries and Dependencies

- LangChain
- LangGraph
- Streamlit
- Pydantic
- LanceDB
- Psycopg



- LangChain
- LangGraph
- Streamlit
- Pydantic
- LanceDB
- Psycopg



- langchain
- langsmith
- opentelemetry
- lancedb
- google-genai
- deepagents (middleware)


## Technologies

- Anthropic Claude 3 Haiku
- Google Vertex AI (Fallback)
- Replicate (Visuals/Voice)
- OpenTelemetry



- Anthropic Claude 3 Haiku
- Google Vertex AI (Fallback)
- Replicate (Visuals/Voice)
- OpenTelemetry

