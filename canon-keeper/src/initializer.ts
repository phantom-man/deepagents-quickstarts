import * as vscode from 'vscode';
import {
    BEST_PRACTICE_TEMPLATE,
    REQUIRED_SECTIONS,
    CORE_BEST_PRACTICES,
    isDefaultTemplate,
    hasLearningsSection,
    getMissingPractices
} from './templates';

export interface InitializationResult {
    action: 'created' | 'replaced' | 'merged' | 'unchanged';
    sectionsAdded: string[];
    practicesAdded: string[];
    message: string;
}

export class InstructionsInitializer {
    
    /**
     * Initialize or update the copilot-instructions.md file.
     * 
     * Logic:
     * 1. If file doesn't exist -> Create with best practice template
     * 2. If file is default/empty -> Replace with best practice template
     * 3. If file is customized -> Merge missing sections and practices
     */
    async initializeInstructions(
        workspaceRoot: vscode.Uri,
        instructionsPath: string
    ): Promise<InitializationResult> {
        const targetUri = vscode.Uri.joinPath(workspaceRoot, instructionsPath);
        
        // Check if file exists
        let existingContent: string | null = null;
        try {
            const fileContent = await vscode.workspace.fs.readFile(targetUri);
            existingContent = new TextDecoder().decode(fileContent);
        } catch {
            // File doesn't exist
        }
        
        // Case 1: File doesn't exist
        if (existingContent === null) {
            await this.ensureDirectoryExists(targetUri);
            await this.writeFile(targetUri, BEST_PRACTICE_TEMPLATE);
            return {
                action: 'created',
                sectionsAdded: ['Full template'],
                practicesAdded: CORE_BEST_PRACTICES.map(p => p.title),
                message: 'Created new copilot-instructions.md with best practice template'
            };
        }
        
        // Case 2: File is default/empty template
        if (isDefaultTemplate(existingContent)) {
            await this.writeFile(targetUri, BEST_PRACTICE_TEMPLATE);
            return {
                action: 'replaced',
                sectionsAdded: ['Full template'],
                practicesAdded: CORE_BEST_PRACTICES.map(p => p.title),
                message: 'Replaced default template with best practice structure'
            };
        }
        
        // Case 3: File has custom content - merge intelligently
        return this.mergeWithExisting(targetUri, existingContent);
    }
    
    /**
     * Merge missing sections and practices into existing content
     */
    private async mergeWithExisting(
        targetUri: vscode.Uri,
        existingContent: string
    ): Promise<InitializationResult> {
        let updatedContent = existingContent;
        const sectionsAdded: string[] = [];
        const practicesAdded: string[] = [];
        
        // 1. Ensure Session Learnings Log section exists
        if (!hasLearningsSection(existingContent)) {
            updatedContent = this.addLearningsSection(updatedContent);
            sectionsAdded.push('Session Learnings Log');
        }
        
        // 2. Add missing best practices (only if they don't conflict)
        const missingPractices = getMissingPractices(existingContent);
        
        for (const practice of missingPractices) {
            // Check if adding this would conflict
            if (!this.wouldConflict(updatedContent, practice)) {
                updatedContent = this.addBestPractice(updatedContent, practice);
                practicesAdded.push(practice.title);
            }
        }
        
        // 3. Add CanonKeeper footer if not present
        if (!updatedContent.includes('CanonKeeper')) {
            updatedContent = this.addCanonKeeperFooter(updatedContent);
        }
        
        // Only write if changes were made
        if (sectionsAdded.length > 0 || practicesAdded.length > 0) {
            await this.writeFile(targetUri, updatedContent);
            return {
                action: 'merged',
                sectionsAdded,
                practicesAdded,
                message: `Added ${sectionsAdded.length} section(s) and ${practicesAdded.length} best practice(s)`
            };
        }
        
        return {
            action: 'unchanged',
            sectionsAdded: [],
            practicesAdded: [],
            message: 'File already has required structure and best practices'
        };
    }
    
    /**
     * Add the Session Learnings Log section to content
     */
    private addLearningsSection(content: string): string {
        // Find a good insertion point - prefer end of file or before references
        const referenceMatch = content.match(/##\s*\d*\.?\s*(Reference|Appendix|Notes)/i);
        
        if (referenceMatch && referenceMatch.index !== undefined) {
            // Insert before reference section
            return (
                content.substring(0, referenceMatch.index) +
                '\n' + REQUIRED_SECTIONS.learningsLog.content + '\n---\n\n' +
                content.substring(referenceMatch.index)
            );
        }
        
        // Append to end
        return content.trimEnd() + '\n\n---\n\n' + REQUIRED_SECTIONS.learningsLog.content;
    }
    
    /**
     * Add a best practice to the content
     */
    private addBestPractice(content: string, practice: typeof CORE_BEST_PRACTICES[0]): string {
        // Find the appropriate section to add to
        const sectionPatterns: Record<string, RegExp> = {
            'Error Handling': /##\s*\d*\.?\s*(Error|Exception|Fail)/i,
            'Operational Protocols': /##\s*\d*\.?\s*(Operational|Protocol|Workflow|Process)/i,
            'Research & Documentation': /##\s*\d*\.?\s*(Research|Documentation|Reference)/i,
        };
        
        const pattern = sectionPatterns[practice.section];
        
        if (pattern) {
            const match = content.match(pattern);
            if (match && match.index !== undefined) {
                // Find the end of this section (next ## or end)
                const afterSection = content.substring(match.index);
                const nextSectionMatch = afterSection.match(/\n##\s+/);
                
                let insertIndex: number;
                if (nextSectionMatch && nextSectionMatch.index !== undefined) {
                    insertIndex = match.index + nextSectionMatch.index;
                } else {
                    // Add at end of file
                    insertIndex = content.length;
                }
                
                return (
                    content.substring(0, insertIndex) +
                    '\n\n' + practice.content + '\n' +
                    content.substring(insertIndex)
                );
            }
        }
        
        // No matching section found - add before Session Learnings Log
        const learningsMatch = content.match(REQUIRED_SECTIONS.learningsLog.pattern);
        if (learningsMatch && learningsMatch.index !== undefined) {
            return (
                content.substring(0, learningsMatch.index) +
                '## Best Practices (Added by CanonKeeper)\n\n' +
                practice.content + '\n\n---\n\n' +
                content.substring(learningsMatch.index)
            );
        }
        
        // Last resort - append to end
        return content.trimEnd() + '\n\n---\n\n## Best Practices\n\n' + practice.content + '\n';
    }
    
    /**
     * Check if adding a practice would conflict with existing content
     */
    private wouldConflict(content: string, practice: typeof CORE_BEST_PRACTICES[0]): boolean {
        const lowerContent = content.toLowerCase();
        
        // Check for explicit contradictions
        const conflictPatterns: Record<string, string[]> = {
            'Fail Fast Methodology': [
                'use fallbacks',
                'graceful degradation',
                'silent fail',
                'suppress error'
            ],
            'Deprecation Policy': [
                'use legacy',
                'backward compatible',
                'support old'
            ]
        };
        
        const patterns = conflictPatterns[practice.title];
        if (patterns) {
            for (const pattern of patterns) {
                if (lowerContent.includes(pattern)) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    /**
     * Add CanonKeeper management footer
     */
    private addCanonKeeperFooter(content: string): string {
        const footer = `
---

*This file is managed by CanonKeeper. Learnings are automatically extracted from Copilot conversations and added to the Session Learnings Log.*
`;
        return content.trimEnd() + footer;
    }
    
    /**
     * Ensure the directory exists for a file path
     */
    private async ensureDirectoryExists(fileUri: vscode.Uri): Promise<void> {
        const dirUri = vscode.Uri.joinPath(fileUri, '..');
        try {
            await vscode.workspace.fs.createDirectory(dirUri);
        } catch {
            // Directory already exists
        }
    }
    
    /**
     * Write content to file
     */
    private async writeFile(uri: vscode.Uri, content: string): Promise<void> {
        const encoder = new TextEncoder();
        await vscode.workspace.fs.writeFile(uri, encoder.encode(content));
    }
    
    /**
     * Preview what would be changed without actually writing
     */
    async previewChanges(
        workspaceRoot: vscode.Uri,
        instructionsPath: string
    ): Promise<{
        exists: boolean;
        isDefault: boolean;
        missingSection: boolean;
        missingPractices: string[];
    }> {
        const targetUri = vscode.Uri.joinPath(workspaceRoot, instructionsPath);
        
        let existingContent: string | null = null;
        try {
            const fileContent = await vscode.workspace.fs.readFile(targetUri);
            existingContent = new TextDecoder().decode(fileContent);
        } catch {
            // File doesn't exist
        }
        
        if (existingContent === null) {
            return {
                exists: false,
                isDefault: false,
                missingSection: true,
                missingPractices: CORE_BEST_PRACTICES.map(p => p.title)
            };
        }
        
        return {
            exists: true,
            isDefault: isDefaultTemplate(existingContent),
            missingSection: !hasLearningsSection(existingContent),
            missingPractices: getMissingPractices(existingContent).map(p => p.title)
        };
    }
}
