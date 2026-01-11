# Product Context

## Project Description
DeepAgents ("Atlas") is a commercial-grade, multi-agent automated production studio. It allows users to input high-level creative concepts (e.g., commercials, mood boards) and receive fully realized audiovisual assets. The system is designed for "Zero Touch" operation, handling research, creative direction, asset generation, and quality assurance autonomously.

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
The system follows a **Hub-and-Spoke** architecture managed by the `orchestrator.py` core (formerly `DeepAgents.py`).
- **Frontend**: Streamlit (Sync) with an `asyncio` bridge (`agent_runner.py`) to the backend.
- **Backend Orchestration**: LangGraph (Async) managing stateful agent threads.
- **Data Layer**: 
    - **OLTP**: `asyncpg` connection pool managing LangGraph checkpoints.
    - **Vector**: LanceDB for semantic search.
- **Observability**: OpenTelemetry (OTLP) exporting traces to LangSmith/Jaeger.

## Technical Stack

### Core Frameworks
- **LangChain / LangGraph**: Agent orchestration and state management.
- **Streamlit**: User Interface.
- **Pydantic**: Data validation and schema definition.

### AI & Models
- **Decision Engine**: Google Gemini (Pro/Flash).
- **Voice**: XTTS-v2 (via Replicate).
- **Visuals**: Stable Video Diffusion / Google Veo / Imagen 3.
- **Audio**: MusicGen / Minimax (via Replicate).

### Infrastructure
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
- langsmith
- opentelemetry
- lancedb
- google-genai
- deepagents (middleware)

