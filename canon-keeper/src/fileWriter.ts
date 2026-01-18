import * as vscode from 'vscode';
import { ExtractedLearning } from './extractor';

export class FileWriter {
    async writeLearning(learning: ExtractedLearning): Promise<void> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            throw new Error('No workspace folder open');
        }

        const workspaceRoot = workspaceFolders[0].uri;
        const targetUri = vscode.Uri.joinPath(workspaceRoot, learning.targetFile);

        // Check if file exists
        let existingContent = '';
        try {
            const fileContent = await vscode.workspace.fs.readFile(targetUri);
            existingContent = new TextDecoder().decode(fileContent);
        } catch {
            // File doesn't exist, will create it
            existingContent = await this.getTemplateContent(learning.targetFile);
        }

        // Format the learning entry
        const entry = this.formatLearningEntry(learning);

        // Find the right place to insert
        const updatedContent = this.insertLearning(existingContent, entry, learning);

        // Write back to file
        const encoder = new TextEncoder();
        await vscode.workspace.fs.writeFile(targetUri, encoder.encode(updatedContent));

        console.log(`[CanonKeeper] Wrote learning to ${learning.targetFile}`);
    }

    async getInstructionsPath(): Promise<vscode.Uri | null> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            return null;
        }

        const config = vscode.workspace.getConfiguration('canonKeeper');
        const instructionsPath = config.get('copilotInstructionsPath', '.github/copilot-instructions.md');
        
        const workspaceRoot = workspaceFolders[0].uri;
        const targetUri = vscode.Uri.joinPath(workspaceRoot, instructionsPath);

        try {
            await vscode.workspace.fs.stat(targetUri);
            return targetUri;
        } catch {
            return null;
        }
    }

    private formatLearningEntry(learning: ExtractedLearning): string {
        const date = new Date(learning.timestamp).toISOString().split('T')[0];
        const categoryFormatted = learning.category
            .split('-')
            .map(w => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ');

        return `| ${date} | ${categoryFormatted} | ${learning.title} | ${learning.content} |`;
    }

    private insertLearning(
        existingContent: string,
        entry: string,
        learning: ExtractedLearning
    ): string {
        // Look for Session Learnings Log table
        const tableHeaderPattern = /\|\s*Date\s*\|\s*Topic\s*\|\s*Decision\s*\|\s*Rationale\s*\|/i;
        const tableMatch = existingContent.match(tableHeaderPattern);

        if (tableMatch && tableMatch.index !== undefined) {
            // Find the separator line after header
            const afterHeader = existingContent.substring(tableMatch.index);
            const separatorMatch = afterHeader.match(/\|[-\s|]+\|\n/);
            
            if (separatorMatch && separatorMatch.index !== undefined) {
                const insertPosition = tableMatch.index + separatorMatch.index + separatorMatch[0].length;
                
                // Insert after the separator line
                return (
                    existingContent.substring(0, insertPosition) +
                    entry + '\n' +
                    existingContent.substring(insertPosition)
                );
            }
        }

        // Fallback: Look for "### 7. Session Learnings Log" section
        const sectionPattern = /###\s*7\.\s*Session Learnings Log/i;
        const sectionMatch = existingContent.match(sectionPattern);

        if (sectionMatch && sectionMatch.index !== undefined) {
            // Find the end of the table or section
            const afterSection = existingContent.substring(sectionMatch.index);
            const nextSectionMatch = afterSection.match(/\n###\s+\d+\./);
            
            let insertPosition: number;
            if (nextSectionMatch && nextSectionMatch.index !== undefined) {
                // Insert before the next section
                insertPosition = sectionMatch.index + nextSectionMatch.index;
            } else {
                // Insert at end of file
                insertPosition = existingContent.length;
            }

            // Add table if not present
            if (!tableMatch) {
                const table = `
| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
${entry}
`;
                return (
                    existingContent.substring(0, insertPosition) +
                    table +
                    existingContent.substring(insertPosition)
                );
            }
        }

        // Last resort: Append to end with a new section
        const newSection = `

## CanonKeeper Learnings

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
${entry}
`;
        return existingContent + newSection;
    }

    private async getTemplateContent(targetFile: string): Promise<string> {
        if (targetFile.includes('copilot-instructions')) {
            return `# Project Instructions (Copilot Memory)

## Overview
This file contains project-specific instructions and learnings for GitHub Copilot.

## Session Learnings Log

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
`;
        }

        if (targetFile.includes('CANON')) {
            const agentName = targetFile.match(/(\w+)_CANON\.md/)?.[1] || 'Agent';
            return `# ${agentName} Canon

## Overview
This file contains knowledge specific to the ${agentName} agent.

## Learnings

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
`;
        }

        return `# Knowledge Base

## Learnings

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
`;
    }
}
