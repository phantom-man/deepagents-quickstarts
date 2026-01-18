import * as vscode from 'vscode';

interface StatsData {
    totalExtractions: number;
    totalLearningsSaved: number;
    helpfulFeedback: number;
    unhelpfulFeedback: number;
    lastExtraction: number | null;
}

const STATS_KEY = 'canonKeeper.statistics';

export class Statistics {
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    getStats(): StatsData {
        return this.context.globalState.get<StatsData>(STATS_KEY, {
            totalExtractions: 0,
            totalLearningsSaved: 0,
            helpfulFeedback: 0,
            unhelpfulFeedback: 0,
            lastExtraction: null
        });
    }

    async incrementExtractionCount(): Promise<void> {
        const stats = this.getStats();
        stats.totalExtractions++;
        stats.lastExtraction = Date.now();
        await this.context.globalState.update(STATS_KEY, stats);
    }

    async incrementSavedCount(): Promise<void> {
        const stats = this.getStats();
        stats.totalLearningsSaved++;
        await this.context.globalState.update(STATS_KEY, stats);
    }

    async incrementFeedbackCount(type: 'helpful' | 'unhelpful'): Promise<void> {
        const stats = this.getStats();
        if (type === 'helpful') {
            stats.helpfulFeedback++;
        } else {
            stats.unhelpfulFeedback++;
        }
        await this.context.globalState.update(STATS_KEY, stats);
    }

    async reset(): Promise<void> {
        await this.context.globalState.update(STATS_KEY, {
            totalExtractions: 0,
            totalLearningsSaved: 0,
            helpfulFeedback: 0,
            unhelpfulFeedback: 0,
            lastExtraction: null
        });
    }
}
