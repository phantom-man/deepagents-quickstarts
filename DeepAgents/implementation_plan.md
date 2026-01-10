# DeepAgents Implementation Plan

## Phase 1: Restore Memory Architecture (Immediate)
**Goal:** Reconnect the "Amputated" brains of the agents.
- [ ] **Architecture:** Link `memory_manager.py` to `AgentComms` (Postgres) and `KnowledgeStore` (LanceDB).
- [ ] **Fix:** Update `knowledge_store.py` to point to `DeepAgents/data/lancedb`.
- [ ] **Enhancement:** Ensure `KnowledgeStore` supports auto-embedding (using LangChain integration) so text can be passed directly.
- [ ] **Validation:** Pylint 10/10, Pylance clean, `verify_memory.py` script.

## Phase 2: Prompt Management (LangChain Hub)
**Goal:** Decouple prompts from code.
- [ ] **Refactor:** Identify all hardcoded string prompts in `CommercialAgents`.
- [ ] **Integration:** Implement `langchainhub.pull()` logic.
- [ ] **Fallback:** Ensure local prompt strings exist as fallback if Hub is unreachable.

## Phase 3: Automated Evaluations
**Goal:** Establish quality metric baselines.
- [ ] **Dataset:** Create a standard "Golden Dataset" of inputs/outputs for Director Agent.
- [ ] **Pipeline:** Create `DeepAgents/evaluation/evaluate_director.py` using LangSmith SDK.
- [ ] **Metric:** Implement "Response Relevance" and "Tool Usage" graders.

## Phase 4: LangGraph Migration
**Goal:** Support loops, persistence, and complex state.
- [ ] **Conversion:** Convert `DirectorAgent` class to a `StateGraph`.
- [ ] **State:** Define `AgentState` TypedDict (Messages, Context, Tools).
- [ ] **Server:** Ensure `DeepAgents.py` can serve this graph via LangGraph Cloud standards.
