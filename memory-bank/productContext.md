# Product Context

## Project Description

DeepAgents ("Atlas") is a commercial-grade, multi-agent automated production studio. It allows users to input high-level creative concepts and receive fully realized audiovisual assets.
Originally focused on commercials, the studio has expanded to support:

- **Music Production**: Complete songs with lyrics and instrumentals (via Minimax 1.5 "High Density" strategy).
- **Narrative Video**: Short films, YouTube content, and storytelling.
- **Synthetic Personas**: High-fidelity, believable artificial personalities for content creation.

The system is designed for "Zero Touch" operation, handling research, creative direction, asset generation, and quality assurance autonomously.
Current Brain: Anthropic Claude 3 Haiku (Cost/Availability optimized).

## Core Features

- **The Nervous System (Hybrid Persistence)**: Combines Semantic Memory (LanceDB for knowledge) and State Persistence (Postgres for workflow checkpointing).
- **Orchestra GUI**: A centralized Streamlit dashboard for controlling agents, monitoring system health (OTLP diagnostics), and reviewing generated assets.
- **Ontology-Driven Agents**:
  - **Director (Apollo)**: Creative Lead.
  - **Researcher (Delphi)**: Truth verification.
  - **Confidence (The Editor)**: Quality assurance.
  - **Cinematographer (Lumiere)**: Visual synthesis (Google Imagen 4 Fast / Replicate).
  - **Composer (Orpheus)**: Audio synthesis (Minimax Music-1.5).
- **MemoriPilot**: Self-referential memory for the developer (Copilot) to maintain context across sessions.

## Architecture

# DeepAgents Architecture

## Core Components

- **Framework**: LangGraph (Orchestration), Streamlit (UI).
- **Communication (AgentComms)**: PostgreSQL based message passing.
- **Memory (AgentMemory)**: PostgreSQL based short-term memory (checkpoints).
- **Knowledge (KnowledgeStore)**: LanceDB (Vector Store) for long-term recall.
- **Hub**: LangChain Hub (Prompt versioning). **Status**: Fixed & Stable (v2 Auth).

## Models & Providers

- **Intelligence**: **Anthropic** (Strict Constraint: **Haiku** `claude-3-haiku-20240307` only).
- **Vision/Media**: **Replicate** (Flux for Image, Zeroscope for Video, XTTS for Voice).
- **Comms/Music**: Replicate (Minimax Music-1.5 default).

## Deployment

- **Local (Windows)**: `python -m langgraph_cli dev --allow-blocking`.
- **Environment**: Python 3.10+ VENV.
- **Secrets**: Managed via `.env` and `st.secrets` (implied).

The system follows a **Hub-and-Spoke** architecture managed by the `orchestrator.py` core.

- **Frontend**: Streamlit (Sync) with an `asyncio` bridge.
- **Backend Orchestration**: LangGraph (Async) managing stateful agent threads.
- **Data Layer**:
  - **OLTP**: `psycopg` (v3) connection pool.
  - **Vector**: LanceDB for semantic search.
- **Observability**: OpenTelemetry (OTLP) exporting traces to LangSmith.

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

- langchain
- langgraph
- streamlit
- anthropic
- google-genai
- replicate
- lancedb
- psycopg

- langgraph
- langsmith
- streamlit
- asyncpg
- lancedb
- anthropic

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
- Streamlit
- LangChain
- Replicate

- Intelligence: Anthropic Claude 3 Haiku (Primary).
- Visuals: Replicate Flux/Zeroscope.
- Voice: Replicate XTTS-v2.
- Infrastructure: Postgres + LanceDB + OTLP.

- Anthropic Claude 3 Haiku
- Google Vertex AI (Fallback)
- Replicate (Visuals/Voice)
- OpenTelemetry

- Anthropic Claude 3 Haiku
- Google Vertex AI (Fallback)
- Replicate (Visuals/Voice)
- OpenTelemetry
