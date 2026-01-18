import * as vscode from 'vscode';

export interface ExtractedLearning {
    title: string;
    content: string;
    category: LearningCategory;
    targetFile: string;
    confidence: number;
    timestamp: number;
}

export type LearningCategory = 
    | 'architecture-decision'
    | 'bug-fix'
    | 'configuration'
    | 'code-pattern'
    | 'tool-usage'
    | 'model-knowledge'
    | 'workflow'
    | 'other';

interface ConversationContext {
    history: Array<{
        role: 'user' | 'assistant';
        content: string;
    }>;
    timestamp: number;
}

const CLASSIFICATION_PROMPT = `You are CanonKeeper, an expert at identifying durable, reusable knowledge from conversations.

Analyze the following conversation and extract ONLY learnings that are:
1. **Durable** - Will remain true/useful for weeks or months (not temporary fixes)
2. **Specific** - Contains concrete details, not vague generalities
3. **Actionable** - Someone reading this can apply it immediately
4. **Non-obvious** - Not something easily found in documentation

DO NOT extract:
- Generic coding advice ("use meaningful variable names")
- Temporary workarounds that should be removed later
- Information specific to a single debugging session
- Common knowledge or basic syntax

For each learning, determine the target file:
- **copilot-instructions** - Project-wide decisions, architecture, technology choices
- **agent-specific** - Knowledge specific to an AI agent (Director, Composer, etc.)
- **skip** - Not worth persisting

OUTPUT FORMAT (JSON array):
[
  {
    "title": "Short descriptive title (3-7 words)",
    "content": "The learning in 1-3 sentences. Include specific values, patterns, or decisions.",
    "category": "architecture-decision|bug-fix|configuration|code-pattern|tool-usage|model-knowledge|workflow|other",
    "targetFile": "copilot-instructions|agent-specific:AgentName|skip",
    "confidence": 0.0-1.0,
    "rationale": "Why this is worth saving (internal use, not persisted)"
  }
]

If no learnings are worth extracting, return an empty array: []

CONVERSATION TO ANALYZE:
`;

export class MemoryExtractor {
    async extractLearnings(
        context: ConversationContext,
        model: vscode.LanguageModelChat,
        token: vscode.CancellationToken
    ): Promise<ExtractedLearning[]> {
        // Build the conversation text
        const conversationText = context.history
            .map(msg => `[${msg.role.toUpperCase()}]: ${msg.content}`)
            .join('\n\n');

        if (conversationText.length < 100) {
            // Too short to contain meaningful learnings
            return [];
        }

        // Prepare messages for the LLM
        const messages = [
            vscode.LanguageModelChatMessage.User(CLASSIFICATION_PROMPT + conversationText)
        ];

        try {
            // Send to LLM
            const response = await model.sendRequest(messages, {}, token);

            // Collect response text
            let responseText = '';
            for await (const chunk of response.text) {
                responseText += chunk;
            }

            // Parse JSON response
            const learnings = this.parseResponse(responseText, context.timestamp);
            return learnings;

        } catch (error) {
            console.error('[CanonKeeper] Error calling LLM for extraction:', error);
            throw error;
        }
    }

    private parseResponse(responseText: string, timestamp: number): ExtractedLearning[] {
        try {
            // Extract JSON from response (might have markdown code blocks)
            let jsonText = responseText;
            
            // Try to extract from code block
            const jsonMatch = responseText.match(/```(?:json)?\s*([\s\S]*?)```/);
            if (jsonMatch) {
                jsonText = jsonMatch[1].trim();
            }

            // Try to find array directly
            const arrayMatch = jsonText.match(/\[[\s\S]*\]/);
            if (arrayMatch) {
                jsonText = arrayMatch[0];
            }

            const parsed = JSON.parse(jsonText);
            
            if (!Array.isArray(parsed)) {
                console.warn('[CanonKeeper] Response is not an array');
                return [];
            }

            // Validate and transform each learning
            const learnings: ExtractedLearning[] = [];
            
            for (const item of parsed) {
                if (this.isValidLearning(item) && item.targetFile !== 'skip') {
                    learnings.push({
                        title: item.title,
                        content: item.content,
                        category: item.category as LearningCategory,
                        targetFile: this.resolveTargetFile(item.targetFile),
                        confidence: Math.min(1, Math.max(0, item.confidence)),
                        timestamp
                    });
                }
            }

            return learnings;

        } catch (error) {
            console.error('[CanonKeeper] Error parsing LLM response:', error);
            console.error('[CanonKeeper] Raw response:', responseText);
            return [];
        }
    }

    private isValidLearning(item: unknown): item is {
        title: string;
        content: string;
        category: string;
        targetFile: string;
        confidence: number;
    } {
        if (typeof item !== 'object' || item === null) {
            return false;
        }

        const obj = item as Record<string, unknown>;
        
        return (
            typeof obj.title === 'string' && obj.title.length > 0 &&
            typeof obj.content === 'string' && obj.content.length > 0 &&
            typeof obj.category === 'string' &&
            typeof obj.targetFile === 'string' &&
            typeof obj.confidence === 'number'
        );
    }

    private resolveTargetFile(targetFile: string): string {
        const config = vscode.workspace.getConfiguration('canonKeeper');
        
        if (targetFile === 'copilot-instructions') {
            return config.get('copilotInstructionsPath', '.github/copilot-instructions.md');
        }
        
        if (targetFile.startsWith('agent-specific:')) {
            const agentName = targetFile.replace('agent-specific:', '');
            const canonPath = config.get('agentCanonPath', 'DeepAgents/Canon');
            return `${canonPath}/${agentName.toUpperCase()}_CANON.md`;
        }

        return targetFile;
    }
}
