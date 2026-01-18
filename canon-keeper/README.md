# CanonKeeper 🏛️

**Automatically extract and persist learnings from your Copilot conversations.**

CanonKeeper watches your conversations with GitHub Copilot and intelligently extracts durable knowledge—architecture decisions, bug fixes, configuration patterns—and saves them to your project's knowledge base.

## Features

### 🧠 Intelligent Extraction

Uses LLM-as-Judge to classify conversation content and identify what's worth remembering:

- Technical decisions and rationale
- Bug fixes with root cause analysis  
- Architecture patterns
- Configuration discoveries
- Code patterns and best practices

### 📝 Automatic Persistence

Learnings are automatically written to:

- **`.github/copilot-instructions.md`** - Project-wide knowledge that Copilot loads every session
- **`DeepAgents/Canon/*.md`** - Agent-specific knowledge files

### ⌨️ Keyboard Shortcut

Press **`Ctrl+Shift+K`** (or **`Cmd+Shift+K`** on Mac) anytime to save learnings from your current chat session.

## Usage

### Chat Commands

Invoke CanonKeeper in chat using `@keeper`:

| Command | Description |
| :------ | :---------- |
| `@keeper /save` | Extract learnings from current conversation and save to knowledge base |
| `@keeper /review` | Preview what would be extracted without saving |
| `@keeper /status` | Show current settings and statistics |

### Example Workflow

1. **Have a conversation** with Copilot about a technical problem
2. **Resolve the issue** with Copilot's help
3. **Press `Ctrl+Shift+K`** or use `@keeper /save` to extract the learning
4. **Review and confirm** the extracted knowledge
5. **Next session**, Copilot automatically knows about this decision!

```
User: @copilot Why is my LangGraph server taking 60 seconds to start?

Copilot: The slow startup is caused by Google SDK's `packages_distributions()` 
call scanning all installed packages. This is cached after first import...

User: @keeper /save

CanonKeeper: Found 1 learning:
### 🟢 LangGraph Server Startup Delay
**Target:** `.github/copilot-instructions.md`
**Category:** Configuration
**Confidence:** 85%

Google SDK `packages_distributions()` scans all packages on first import, 
causing ~50-65 second startup. This is unavoidable but cached after first run.

[Save Learning]
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `canonKeeper.copilotInstructionsPath` | `.github/copilot-instructions.md` | Path to Copilot instructions file |
| `canonKeeper.agentCanonPath` | `DeepAgents/Canon` | Path to agent-specific canon folder |
| `canonKeeper.minimumConfidence` | `0.7` | Minimum confidence (0-1) to auto-save |
| `canonKeeper.requireConfirmation` | `true` | Ask before writing to files |

## What Gets Extracted?

CanonKeeper only saves learnings that are:

✅ **Durable** - Will remain true for weeks or months  
✅ **Specific** - Contains concrete details  
✅ **Actionable** - Someone can apply it immediately  
✅ **Non-obvious** - Not easily found in documentation  

It filters out:

❌ Generic coding advice  
❌ Temporary workarounds  
❌ Session-specific debugging info  
❌ Common knowledge  

## Learning Categories

| Category | Description | Typical Target |
|----------|-------------|----------------|
| `architecture-decision` | System design choices | copilot-instructions |
| `bug-fix` | Root cause + solution | copilot-instructions |
| `configuration` | Settings, env vars | copilot-instructions |
| `code-pattern` | Reusable patterns | copilot-instructions |
| `tool-usage` | External tool knowledge | agent-specific |
| `model-knowledge` | AI model specifics | agent-specific |
| `workflow` | Process improvements | copilot-instructions |

## Privacy & Security

- **Local only** - All processing happens locally in VS Code
- **No telemetry** - No data is sent to external services (except the LLM call)
- **You control saves** - Confirmation required before writing files
- **Workspace-scoped** - Only writes to your current workspace

## Requirements

- VS Code 1.95.0 or later
- GitHub Copilot extension
- Active Copilot subscription (for LLM access)

## Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "CanonKeeper"
4. Click Install

Or install from VSIX:

```bash
code --install-extension canon-keeper-0.1.0.vsix
```

## Development

```bash
# Clone the repo
git clone https://github.com/langchain-ai/deepagents-quickstarts
cd deepagents-quickstarts/canon-keeper

# Install dependencies
npm install

# Compile
npm run compile

# Run in development
# Press F5 in VS Code to launch Extension Development Host
```

## Contributing

Contributions welcome! Please read our contributing guidelines first.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**CanonKeeper** - *Because good ideas deserve to be remembered.* 🏛️
