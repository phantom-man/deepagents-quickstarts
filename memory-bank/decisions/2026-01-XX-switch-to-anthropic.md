# Architectural Decision Log

## Decision: Switch to Anthropic (Claude 3.5 Sonnet) as Primary LLM

- **Date**: 2026-01-XX
- **Context**: Development flagged by persistent `429 RESOURCE_EXHAUSTED` errors from Google Vertex AI API (Gemini 2.0 Flash/Pro/Lite) across `us-central1` and `global` regions.
- **Decision**: Pivot the "Brain" (Director/Researcher) to use Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-latest`).
- **Rationale**: User has a paid/working Anthropic key. Stability is prioritized over the free tier cost of Google.
- **Implementation**:
  - `langchain-anthropic` added as dependency.
  - `agent_config.json` updated.
  - `Director` and `Researcher` factories refactored to support Provider extraction.
- **Impact**:
  - System is now multi-provider.
  - Google still used for Image (Imagen) and Voice fallback until further notice.
  - Replicate remains for Video/Music.
