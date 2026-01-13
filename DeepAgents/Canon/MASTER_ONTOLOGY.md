# MASTER ONTOLOGY INDEX

**Status:** ACTIVE
**Philosophy:** Zero Touch / Configuration-Driven
**Source of Truth:** [LangSmith Hub](https://smith.langchain.com/hub)

## Overview

This index supersedes previous local "Ontology MD" files. The cognitive definitions, behaviors, and constraints for all Agents are now managed centrally in the **LangSmith Prompt Hub**.

This ensures that changes to agent behavior (e.g., swapping a model, disabling a tool) can be deployed instantly without code changes, adhering to the "Zero Touch" initiative.

## Global Directives (Applied to All Agents)

1.  **Read Protocol:** You MUST read every new prompt from beginning to end before taking action or planning development.
2.  **Cognitive Engine:** Default LLM is **Anthropic Claude 3 Haiku** (unless overridden by `deepagents-system-config`).
3.  **Context Awareness:** Always check `SystemConfiguration` before assuming tool availability.

## Agent Definitions (Hub Repositories)

| Agent | Hub Repo Name | Key Constraints |
| :--- | :--- | :--- |
| **Director** | `director-system-prompt` | Polymorphic structure. Orchestrates others. |
| **Cinematographer** | `cinematographer-system-prompt` | **Google Veo strictly FORBIDDEN**. Use SVD/Zeroscope. |
| **Composer** | `composer-system-prompt` | Handles Music/Audio. |
| **Researcher** | `researcher-system-prompt` | Uses SIFT method for truth verification. |

## Legacy File Status

The following local files are retained for **Human Reference Only**. They are NOT read by the runtime agents.

- `Director_Ontology.md` -> References `director-system-prompt`.
- `Cinematographer_Ontology.md` -> References `cinematographer-system-prompt`.
- `Composer_Ontology.md` -> References `composer-system-prompt`.

**MemoriPilot** (`MemoriPilot.md`) remains the ACTIVE local protocol for the Copilot (Developer) but is separate from the Runtime Agents.
