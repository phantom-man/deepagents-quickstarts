import * as vscode from 'vscode';
import { KeeperParticipant } from './participant';
import { MemoryExtractor } from './extractor';
import { FileWriter } from './fileWriter';
import { Statistics } from './statistics';
import { InstructionsInitializer } from './initializer';

let keeperParticipant: KeeperParticipant;
let statistics: Statistics;
let initializer: InstructionsInitializer;

export function activate(context: vscode.ExtensionContext) {
    console.log('[CanonKeeper] Activating extension...');

    // Initialize components
    statistics = new Statistics(context);
    const fileWriter = new FileWriter();
    const extractor = new MemoryExtractor();
    initializer = new InstructionsInitializer();

    // Run initialization check for copilot-instructions.md
    checkAndInitializeInstructions(context).catch(err => {
        console.error('[CanonKeeper] Initialization check failed:', err);
    });

    // Create chat participant
    keeperParticipant = new KeeperParticipant(extractor, fileWriter, statistics);
    const participant = vscode.chat.createChatParticipant(
        'canon-keeper.keeper',
        keeperParticipant.handleRequest.bind(keeperParticipant)
    );

    // Set participant properties
    participant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'images', 'icon.png');

    // Register follow-up provider
    participant.followupProvider = {
        provideFollowups(result, context, token) {
            if (result.metadata?.extracted) {
                return [
                    {
                        prompt: 'Show me what was saved',
                        label: vscode.l10n.t('View saved learnings')
                    }
                ];
            }
            return [
                {
                    prompt: '@keeper /save',
                    label: vscode.l10n.t('Save learnings from this conversation')
                }
            ];
        }
    };

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('canonKeeper.extractNow', async () => {
            // Open chat panel and insert @keeper /save command
            await vscode.commands.executeCommand('workbench.action.chat.open');
            // Small delay to ensure chat is open, then insert the command
            setTimeout(async () => {
                await vscode.commands.executeCommand('workbench.action.chat.insertIntoInput', '@keeper /save');
            }, 100);
        }),

        vscode.commands.registerCommand('canonKeeper.confirmSave', async (learnings: any[]) => {
            if (!learnings || learnings.length === 0) {
                vscode.window.showWarningMessage('No learnings to save.');
                return;
            }
            
            for (const learning of learnings) {
                try {
                    await fileWriter.writeLearning(learning);
                    statistics.incrementSavedCount();
                } catch (error) {
                    const msg = error instanceof Error ? error.message : 'Unknown error';
                    vscode.window.showErrorMessage(`Failed to save "${learning.title}": ${msg}`);
                }
            }
            
            vscode.window.showInformationMessage(
                `CanonKeeper: Saved ${learnings.length} learning(s) to your knowledge base.`
            );
        }),

        vscode.commands.registerCommand('canonKeeper.showStats', () => {
            const stats = statistics.getStats();
            vscode.window.showInformationMessage(
                `CanonKeeper Stats: ${stats.totalExtractions} extractions, ` +
                `${stats.totalLearningsSaved} learnings saved`
            );
        }),

        vscode.commands.registerCommand('canonKeeper.openInstructions', async () => {
            const instructionsPath = await fileWriter.getInstructionsPath();
            if (instructionsPath) {
                const doc = await vscode.workspace.openTextDocument(instructionsPath);
                await vscode.window.showTextDocument(doc);
            } else {
                vscode.window.showWarningMessage('No copilot-instructions.md found in workspace.');
            }
        }),

        vscode.commands.registerCommand('canonKeeper.initializeInstructions', async () => {
            await runInitializationWithPrompt(true);
        }),

        participant
    );

    console.log('[CanonKeeper] Extension activated successfully');
}

/**
 * Check and initialize copilot-instructions.md on extension activation
 */
async function checkAndInitializeInstructions(context: vscode.ExtensionContext): Promise<void> {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        return;
    }

    const config = vscode.workspace.getConfiguration('canonKeeper');
    const autoInitialize = config.get<boolean>('autoInitialize', true);
    const hasShownPrompt = context.globalState.get<boolean>('initPromptShown', false);

    if (!autoInitialize || hasShownPrompt) {
        return;
    }

    // Preview what changes would be made
    const workspaceRoot = workspaceFolders[0].uri;
    const instructionsPath = '.github/copilot-instructions.md';
    
    const preview = await initializer.previewChanges(workspaceRoot, instructionsPath);
    
    // Determine if we should prompt the user
    const needsChanges = !preview.exists || preview.isDefault || 
                         preview.missingSection || preview.missingPractices.length > 0;
    
    if (!needsChanges) {
        return;
    }

    // Build message based on what's needed
    let message: string;
    if (!preview.exists) {
        message = 'CanonKeeper: No copilot-instructions.md found. Create one with best practices?';
    } else if (preview.isDefault) {
        message = 'CanonKeeper: Default copilot-instructions.md detected. Replace with best practice template?';
    } else {
        const parts: string[] = [];
        if (preview.missingSection) {
            parts.push('Session Learnings Log section');
        }
        if (preview.missingPractices.length > 0) {
            parts.push(`${preview.missingPractices.length} best practice(s)`);
        }
        message = `CanonKeeper: Your instructions file is missing: ${parts.join(' and ')}. Add them?`;
    }

    // Show prompt
    const choice = await vscode.window.showInformationMessage(
        message,
        'Yes, update it',
        'Show preview',
        'Not now',
        "Don't ask again"
    );

    if (choice === 'Yes, update it') {
        await runInitializationWithPrompt(false);
    } else if (choice === 'Show preview') {
        await showInitializationPreview(preview);
    } else if (choice === "Don't ask again") {
        await context.globalState.update('initPromptShown', true);
    }
}

/**
 * Run initialization with optional confirmation
 */
async function runInitializationWithPrompt(showConfirmation: boolean): Promise<void> {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage('No workspace folder open.');
        return;
    }

    const workspaceRoot = workspaceFolders[0].uri;
    const instructionsPath = '.github/copilot-instructions.md';

    if (showConfirmation) {
        const preview = await initializer.previewChanges(workspaceRoot, instructionsPath);
        
        if (!preview.exists || preview.isDefault || preview.missingSection || preview.missingPractices.length > 0) {
            const confirm = await vscode.window.showQuickPick(['Yes, proceed', 'Cancel'], {
                placeHolder: 'Initialize/update copilot-instructions.md with CanonKeeper best practices?'
            });
            
            if (confirm !== 'Yes, proceed') {
                return;
            }
        } else {
            vscode.window.showInformationMessage('Your copilot-instructions.md already has all best practices!');
            return;
        }
    }

    try {
        const result = await initializer.initializeInstructions(workspaceRoot, instructionsPath);
        
        // Report result
        if (result.action === 'unchanged') {
            vscode.window.showInformationMessage(result.message);
        } else {
            const openFile = await vscode.window.showInformationMessage(
                `CanonKeeper: ${result.message}`,
                'Open file'
            );
            
            if (openFile === 'Open file') {
                const docUri = vscode.Uri.joinPath(workspaceRoot, instructionsPath);
                const doc = await vscode.workspace.openTextDocument(docUri);
                await vscode.window.showTextDocument(doc);
            }
        }
    } catch (error) {
        const msg = error instanceof Error ? error.message : 'Unknown error';
        vscode.window.showErrorMessage(`CanonKeeper initialization failed: ${msg}`);
    }
}

/**
 * Show preview of what would be changed
 */
async function showInitializationPreview(preview: {
    exists: boolean;
    isDefault: boolean;
    missingSection: boolean;
    missingPractices: string[];
}): Promise<void> {
    const items: string[] = [];
    
    if (!preview.exists) {
        items.push('• Create new file with best practice template');
    } else if (preview.isDefault) {
        items.push('• Replace default template with comprehensive best practices');
    } else {
        if (preview.missingSection) {
            items.push('• Add Session Learnings Log section (for auto-saving learnings)');
        }
        if (preview.missingPractices.length > 0) {
            items.push('• Add best practices:');
            for (const practice of preview.missingPractices) {
                items.push(`  - ${practice}`);
            }
        }
    }
    
    const choice = await vscode.window.showInformationMessage(
        `CanonKeeper will make these changes:\n\n${items.join('\n')}`,
        { modal: true },
        'Apply changes',
        'Cancel'
    );
    
    if (choice === 'Apply changes') {
        await runInitializationWithPrompt(false);
    }
}

export function deactivate() {
    console.log('[CanonKeeper] Extension deactivated');
}
