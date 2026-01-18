import * as vscode from 'vscode';
import { MemoryExtractor, ExtractedLearning } from './extractor';
import { FileWriter } from './fileWriter';
import { Statistics } from './statistics';

interface KeeperResult extends vscode.ChatResult {
    metadata?: {
        command?: string;
        extracted?: boolean;
        learnings?: ExtractedLearning[];
        conversationContext?: ConversationContext;
    };
}

interface ConversationContext {
    history: Array<{
        role: 'user' | 'assistant';
        content: string;
    }>;
    timestamp: number;
}

export class KeeperParticipant {
    constructor(
        private extractor: MemoryExtractor,
        private fileWriter: FileWriter,
        private statistics: Statistics
    ) {}

    async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<KeeperResult> {
        // Build conversation context from history
        const conversationContext = this.buildConversationContext(context);

        // Handle commands
        if (request.command === 'save') {
            return this.handleSaveCommand(request, context, stream, token, conversationContext);
        } else if (request.command === 'review') {
            return this.handleReviewCommand(request, context, stream, token, conversationContext);
        } else if (request.command === 'status') {
            return this.handleStatusCommand(stream);
        }

        // Default: explain what CanonKeeper does
        return this.handleDefaultRequest(request, stream, conversationContext);
    }

    private buildConversationContext(context: vscode.ChatContext): ConversationContext {
        const history: Array<{ role: 'user' | 'assistant'; content: string }> = [];

        for (const turn of context.history) {
            if (turn instanceof vscode.ChatRequestTurn) {
                history.push({
                    role: 'user',
                    content: turn.prompt
                });
            } else if (turn instanceof vscode.ChatResponseTurn) {
                // Extract text content from response parts
                const content = turn.response
                    .filter((part): part is vscode.ChatResponseMarkdownPart => 
                        part instanceof vscode.ChatResponseMarkdownPart)
                    .map(part => part.value.value)
                    .join('\n');
                
                if (content) {
                    history.push({
                        role: 'assistant',
                        content
                    });
                }
            }
        }

        return {
            history,
            timestamp: Date.now()
        };
    }

    private async handleSaveCommand(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken,
        conversationContext: ConversationContext
    ): Promise<KeeperResult> {
        stream.progress('Analyzing conversation for learnings...');

        if (conversationContext.history.length === 0) {
            stream.markdown('No conversation history found to extract learnings from.\n\n');
            stream.markdown('Start a conversation with Copilot first, then use `@keeper /save` to extract and save learnings.');
            return { metadata: { command: 'save', extracted: false } };
        }

        try {
            // Extract learnings using LLM
            const learnings = await this.extractor.extractLearnings(
                conversationContext,
                request.model,
                token
            );

            if (learnings.length === 0) {
                stream.markdown('**No significant learnings detected** in this conversation.\n\n');
                stream.markdown('Learnings are extracted when conversations contain:\n');
                stream.markdown('- Technical decisions or architecture choices\n');
                stream.markdown('- Bug fixes with root cause analysis\n');
                stream.markdown('- Configuration or setup patterns\n');
                stream.markdown('- Code patterns or best practices\n');
                return { metadata: { command: 'save', extracted: false } };
            }

            stream.markdown(`**Found ${learnings.length} learning(s):**\n\n`);

            // Display each learning
            for (const learning of learnings) {
                const confidenceIcon = learning.confidence >= 0.8 ? '🟢' : 
                                       learning.confidence >= 0.6 ? '🟡' : '🔴';
                
                stream.markdown(`### ${confidenceIcon} ${learning.title}\n`);
                stream.markdown(`**Target:** \`${learning.targetFile}\`\n`);
                stream.markdown(`**Category:** ${learning.category}\n`);
                stream.markdown(`**Confidence:** ${(learning.confidence * 100).toFixed(0)}%\n\n`);
                stream.markdown(`${learning.content}\n\n`);
                stream.markdown('---\n\n');
            }

            // Check if confirmation is required
            const config = vscode.workspace.getConfiguration('canonKeeper');
            const requireConfirmation = config.get<boolean>('requireConfirmation', true);
            const minConfidence = config.get<number>('minimumConfidence', 0.7);

            // Filter by confidence
            const qualifiedLearnings = learnings.filter(l => l.confidence >= minConfidence);

            if (qualifiedLearnings.length === 0) {
                stream.markdown(`*No learnings met the minimum confidence threshold (${(minConfidence * 100).toFixed(0)}%).*\n`);
                return { metadata: { command: 'save', extracted: false, learnings } };
            }

            if (requireConfirmation) {
                stream.markdown('**Ready to save.** Click the button below to write these learnings:\n\n');
                stream.button({
                    command: 'canonKeeper.confirmSave',
                    title: vscode.l10n.t(`Save ${qualifiedLearnings.length} Learning(s)`),
                    arguments: [qualifiedLearnings]
                });
            } else {
                // Auto-save without confirmation
                await this.saveLearnings(qualifiedLearnings, stream);
            }

            this.statistics.incrementExtractionCount();
            return { 
                metadata: { 
                    command: 'save', 
                    extracted: true, 
                    learnings: qualifiedLearnings 
                } 
            };

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            stream.markdown(`**Error extracting learnings:** ${errorMessage}\n`);
            return { metadata: { command: 'save', extracted: false } };
        }
    }

    private async handleReviewCommand(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken,
        conversationContext: ConversationContext
    ): Promise<KeeperResult> {
        stream.progress('Analyzing conversation for potential learnings...');

        if (conversationContext.history.length === 0) {
            stream.markdown('No conversation history to review.\n\n');
            stream.markdown('Start a conversation with Copilot first, then use `@keeper /review` to see what learnings could be extracted.');
            return { metadata: { command: 'review' } };
        }

        stream.markdown('## Review: Potential Learnings\n\n');
        stream.markdown(`Analyzing ${conversationContext.history.length} message(s)...\n\n`);

        try {
            // Extract learnings using LLM (same as /save but without saving)
            const learnings = await this.extractor.extractLearnings(
                conversationContext,
                request.model,
                token
            );

            if (learnings.length === 0) {
                stream.markdown('**No significant learnings detected** in this conversation.\n\n');
                stream.markdown('Learnings are extracted when conversations contain:\n');
                stream.markdown('- Technical decisions or architecture choices\n');
                stream.markdown('- Bug fixes with root cause analysis\n');
                stream.markdown('- Configuration or setup patterns\n');
                stream.markdown('- Code patterns or best practices\n');
                return { metadata: { command: 'review', learnings: [] } };
            }

            const config = vscode.workspace.getConfiguration('canonKeeper');
            const minConfidence = config.get<number>('minimumConfidence', 0.7);

            stream.markdown(`**Found ${learnings.length} potential learning(s):**\n\n`);

            // Display each learning with confidence indicator
            for (const learning of learnings) {
                const confidenceIcon = learning.confidence >= 0.8 ? '🟢' : 
                                       learning.confidence >= 0.6 ? '🟡' : '🔴';
                const wouldSave = learning.confidence >= minConfidence;
                const saveIndicator = wouldSave ? '✅ Would save' : '⏭️ Below threshold';
                
                stream.markdown(`### ${confidenceIcon} ${learning.title}\n`);
                stream.markdown(`**Target:** \`${learning.targetFile}\`\n`);
                stream.markdown(`**Category:** ${learning.category}\n`);
                stream.markdown(`**Confidence:** ${(learning.confidence * 100).toFixed(0)}% - ${saveIndicator}\n\n`);
                stream.markdown(`${learning.content}\n\n`);
                stream.markdown('---\n\n');
            }

            const qualifiedCount = learnings.filter(l => l.confidence >= minConfidence).length;
            stream.markdown(`\n**Summary:** ${qualifiedCount} of ${learnings.length} learning(s) meet the ${(minConfidence * 100).toFixed(0)}% confidence threshold.\n\n`);
            stream.markdown('*Use `/save` to extract and persist these learnings.*');
            
            return { metadata: { command: 'review', learnings, conversationContext } };

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            stream.markdown(`**Error analyzing conversation:** ${errorMessage}\n`);
            return { metadata: { command: 'review' } };
        }
    }

    private async handleStatusCommand(
        stream: vscode.ChatResponseStream
    ): Promise<KeeperResult> {
        const config = vscode.workspace.getConfiguration('canonKeeper');
        const stats = this.statistics.getStats();

        stream.markdown('## CanonKeeper Status\n\n');
        
        stream.markdown('### Configuration\n');
        stream.markdown(`- **Copilot instructions path:** \`${config.get('copilotInstructionsPath')}\`\n`);
        stream.markdown(`- **Agent canon path:** \`${config.get('agentCanonPath')}\`\n`);
        stream.markdown(`- **Minimum confidence:** ${((config.get('minimumConfidence') as number) * 100).toFixed(0)}%\n`);
        stream.markdown(`- **Require confirmation:** ${config.get('requireConfirmation') ? 'Yes' : 'No'}\n\n`);

        stream.markdown('### Statistics\n');
        stream.markdown(`- **Total extractions:** ${stats.totalExtractions}\n`);
        stream.markdown(`- **Learnings saved:** ${stats.totalLearningsSaved}\n`);

        const instructionsPath = await this.fileWriter.getInstructionsPath();
        if (instructionsPath) {
            stream.markdown('\n### Target Files\n');
            stream.anchor(instructionsPath, 'copilot-instructions.md');
        }

        return { metadata: { command: 'status' } };
    }

    private async handleDefaultRequest(
        request: vscode.ChatRequest,
        stream: vscode.ChatResponseStream,
        conversationContext: ConversationContext
    ): Promise<KeeperResult> {
        stream.markdown('# CanonKeeper\n\n');
        stream.markdown('I help you **automatically extract and persist learnings** from your Copilot conversations.\n\n');
        
        stream.markdown('## Commands\n\n');
        stream.markdown('- `/save` - Extract learnings from this conversation and save to your knowledge base\n');
        stream.markdown('- `/review` - Preview what would be extracted without saving\n');
        stream.markdown('- `/status` - Show current settings and statistics\n\n');

        stream.markdown('## How It Works\n\n');
        stream.markdown('1. **Have a conversation** with Copilot about code, architecture, or problems\n');
        stream.markdown('2. **Press `Ctrl+Shift+K`** (or `Cmd+Shift+K` on Mac) to save learnings\n');
        stream.markdown('3. **Or use `/save`** to manually trigger extraction\n');
        stream.markdown('4. **Learnings are written** to your `copilot-instructions.md` or agent-specific files\n\n');

        stream.markdown('## What I Extract\n\n');
        stream.markdown('- Technical decisions and rationale\n');
        stream.markdown('- Bug fixes with root cause analysis\n');
        stream.markdown('- Architecture patterns\n');
        stream.markdown('- Configuration discoveries\n');
        stream.markdown('- Code patterns and best practices\n\n');

        if (request.prompt) {
            stream.markdown('*You said: "' + request.prompt + '"* - Did you want me to \\`/save\\` or \\`/review\\`?');
        }

        // Store context for potential future extraction
        return { 
            metadata: { 
                conversationContext 
            } 
        };
    }

    private async saveLearnings(
        learnings: ExtractedLearning[],
        stream: vscode.ChatResponseStream
    ): Promise<void> {
        stream.progress('Saving learnings...');

        for (const learning of learnings) {
            try {
                await this.fileWriter.writeLearning(learning);
                stream.markdown(`✅ Saved: **${learning.title}** to \`${learning.targetFile}\`\n`);
                this.statistics.incrementSavedCount();
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Unknown error';
                stream.markdown(`❌ Failed to save **${learning.title}**: ${errorMessage}\n`);
            }
        }
    }
}
