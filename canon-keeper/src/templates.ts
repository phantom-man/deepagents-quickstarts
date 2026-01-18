/**
 * Templates and initialization logic for copilot-instructions.md files.
 * 
 * CanonKeeper uses these templates to:
 * 1. Detect if a user has the default VS Code template
 * 2. Initialize with best-practice structure
 * 3. Merge learnings without conflicting with user directives
 */

// The default VS Code copilot-instructions.md content (or near-empty states)
export const DEFAULT_VSCODE_PATTERNS = [
    '# Copilot Instructions',
    'Add your custom instructions here',
    'This file is automatically loaded',
    '<!-- Add instructions here -->',
    '# Instructions for GitHub Copilot',
];

/**
 * Best-practice copilot-instructions template.
 * Environment-agnostic, no project-specific details.
 * Organized for CanonKeeper to write to Section 7 (Session Learnings Log).
 */
export const BEST_PRACTICE_TEMPLATE = `# Project Instructions (Copilot Memory)

This file contains project-specific instructions and learnings for GitHub Copilot.
It is automatically loaded at the start of every chat session.

---

## 1. Copilot Identity & Role

- **Copilot (You)**: The Lead Engineer/Orchestrator. You write the code.
- **Role**: Help maintain a robust, modular, and error-resilient codebase.

---

## 2. Operational Protocols

### A. Prompt Processing
- **Read First**: You MUST read every new prompt from beginning to end before taking action.
- **Clarify Ambiguity**: If a request is unclear, ask clarifying questions before implementing.

### B. Code Quality Standards
> **The Jewel Standard:** Strive to write code that is highly rated and error-free. After writing code, clean, lint, and refine it until it is a sparkling jewel of coding. Mediocrity is a bug.

- **Validation**: After any code creation or significant modification, run validation tools (linters, type checkers).
- **Compliance**: All identified issues must be fixed immediately. The goal is zero critical errors.

### C. File Safety Protocol
When overwriting existing files with complex changes:
1. Write content to a new temporary file first.
2. Verify the contents of the new file are correct.
3. Delete the old file only after verification.
4. Rename the temporary file to the original filename.

### D. Data Query Protocol
When querying large datasets or logs:
- Pipe output to a file and read it.
- DO NOT echo massive text to the terminal to avoid scroll-lock freezing.

### E. Deprecation Policy
- Forbidden to use deprecated code.
- Always use the "latest and greatest" libraries and patterns.
- Research current best practices before implementing.

---

## 3. Error Handling Philosophy

### Fail Fast Methodology (CRITICAL)
- Do NOT use fallbacks to hide errors.
- If a configured resource is unavailable, the application MUST fail immediately so the root cause is visible.
- NO SILENT FAILURES.

### Error Protocol
1. If a critical operation fails, **STOP**.
2. Do NOT guess solutions.
3. **Consult the User** immediately if simple fixes fail.
4. **Research**: Read API/SDK documentation. Do NOT rely solely on internal training.

---

## 4. Architecture Principles

### A. Modularity
- Components should be separate classes/files.
- Each module should have a single responsibility.

### B. Statelessness
- Do not assume memory persists across restarts unless explicitly saved to disk.
- Use explicit persistence mechanisms for important state.

### C. Configuration
- Environment variables and API Keys must be loaded safely via \`.env\` files.
- Never hardcode secrets or sensitive configuration.

---

## 5. Research & Documentation

### Model Knowledge Directive
When connecting to an API or model:
- **MUST** read all available documentation first.
- Look for specific parameters and ensure they are set correctly.
- **Forbidden**: Do not guess parameters based on generic assumptions.

### Dynamic Knowledge Acquisition
- Actively search for latest patterns and best practices.
- Documentation may be outdated - verify against current API behavior.

---

## 6. Persistent Memory & Learning

### How This File Works
- **Recall**: This file auto-loads on every chat session.
- **Learn**: When a durable decision is made, add it to Section 7 (Session Learnings Log).
- **Continuity**: This file IS the memory system.

### What to Record
- Technical decisions and rationale
- Bug fixes with root cause analysis
- Architecture patterns discovered
- Configuration discoveries
- Code patterns and best practices

---

## 7. Session Learnings Log

This section tracks decisions and learnings that evolve over time.
CanonKeeper automatically writes new entries here.

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|

---

## 8. Project-Specific Configuration

*Add your project-specific technology stack, tools, and conventions below.*

### Technology Stack
<!-- Define your project's tech stack here -->

### Known Issues
<!-- Document known issues and their workarounds here -->

### Reference Files
<!-- List important documentation files here -->

---

*This file is managed by CanonKeeper. Learnings are automatically extracted from Copilot conversations and added to Section 7.*
`;

/**
 * Sections that CanonKeeper needs to write to.
 * These will be added if missing from an existing file.
 */
export const REQUIRED_SECTIONS = {
    learningsLog: {
        header: '## 7. Session Learnings Log',
        pattern: /##\s*\d*\.?\s*Session Learnings Log/i,
        content: `## 7. Session Learnings Log

This section tracks decisions and learnings that evolve over time.
CanonKeeper automatically writes new entries here.

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
`
    },
    projectConfig: {
        header: '## 8. Project-Specific Configuration',
        pattern: /##\s*\d*\.?\s*Project-Specific Configuration/i,
        content: `## 8. Project-Specific Configuration

*Add your project-specific technology stack, tools, and conventions below.*

### Technology Stack
<!-- Define your project's tech stack here -->

### Known Issues
<!-- Document known issues and their workarounds here -->
`
    }
};

/**
 * Core best practices that should be in every instructions file.
 * These are environment-agnostic and don't conflict with project specifics.
 */
export const CORE_BEST_PRACTICES = [
    {
        title: 'Fail Fast Methodology',
        section: 'Error Handling',
        content: `### Fail Fast Methodology
- Do NOT use fallbacks to hide errors.
- If a configured resource is unavailable, fail immediately so the root cause is visible.
- NO SILENT FAILURES.`
    },
    {
        title: 'Code Quality Standards',
        section: 'Operational Protocols',
        content: `### Code Quality Standards
> **The Jewel Standard:** Strive to write code that is highly rated and error-free. After writing code, clean, lint, and refine it. Mediocrity is a bug.

- Run validation tools (linters, type checkers) after any code modification.
- Fix all identified issues immediately.`
    },
    {
        title: 'File Safety Protocol',
        section: 'Operational Protocols',
        content: `### File Safety Protocol
When overwriting files with complex changes:
1. Write content to a temporary file first.
2. Verify the new file contents are correct.
3. Delete the old file only after verification.
4. Rename the temporary file to the original filename.`
    },
    {
        title: 'Prompt Processing',
        section: 'Operational Protocols',
        content: `### Prompt Processing
- **Read First**: Read every new prompt from beginning to end before taking action.
- **Clarify Ambiguity**: If a request is unclear, ask clarifying questions before implementing.`
    },
    {
        title: 'Research Directive',
        section: 'Research & Documentation',
        content: `### Research Directive
When connecting to an API or model:
- Read all available documentation first.
- Look for specific parameters and set them correctly.
- Do not guess parameters based on generic assumptions.`
    },
    {
        title: 'Deprecation Policy',
        section: 'Operational Protocols',
        content: `### Deprecation Policy
- Forbidden to use deprecated code.
- Always use the latest libraries and patterns.
- Research current best practices before implementing.`
    }
];

/**
 * Check if content appears to be the default VS Code template
 */
export function isDefaultTemplate(content: string): boolean {
    const trimmed = content.trim().toLowerCase();
    
    // Empty or very short
    if (trimmed.length < 100) {
        return true;
    }
    
    // Contains default patterns
    for (const pattern of DEFAULT_VSCODE_PATTERNS) {
        if (trimmed.includes(pattern.toLowerCase())) {
            return true;
        }
    }
    
    // Only has a single heading with minimal content
    const lines = content.split('\n').filter(l => l.trim().length > 0);
    if (lines.length <= 5) {
        return true;
    }
    
    return false;
}

/**
 * Check if content has the Session Learnings Log section
 */
export function hasLearningsSection(content: string): boolean {
    return REQUIRED_SECTIONS.learningsLog.pattern.test(content);
}

/**
 * Check if a specific best practice is already present
 */
export function hasBestPractice(content: string, practice: typeof CORE_BEST_PRACTICES[0]): boolean {
    // Check for the title or key phrases
    const lowerContent = content.toLowerCase();
    const lowerTitle = practice.title.toLowerCase();
    
    // Direct title match
    if (lowerContent.includes(lowerTitle)) {
        return true;
    }
    
    // Check for key phrases from the content
    const keyPhrases = extractKeyPhrases(practice.content);
    const matchCount = keyPhrases.filter(phrase => 
        lowerContent.includes(phrase.toLowerCase())
    ).length;
    
    // If more than half of key phrases are present, consider it covered
    return matchCount > keyPhrases.length / 2;
}

function extractKeyPhrases(content: string): string[] {
    // Extract quoted or bold phrases
    const phrases: string[] = [];
    
    const boldMatches = content.match(/\*\*([^*]+)\*\*/g);
    if (boldMatches) {
        phrases.push(...boldMatches.map(m => m.replace(/\*\*/g, '')));
    }
    
    const backtickMatches = content.match(/`([^`]+)`/g);
    if (backtickMatches) {
        phrases.push(...backtickMatches.map(m => m.replace(/`/g, '')));
    }
    
    return phrases;
}

/**
 * Get the best practices that are missing from the content
 */
export function getMissingPractices(content: string): typeof CORE_BEST_PRACTICES {
    return CORE_BEST_PRACTICES.filter(practice => !hasBestPractice(content, practice));
}
