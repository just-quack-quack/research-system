#!/usr/bin/env python3
"""
Daily research workflow for binh's monthly publication goal
Called during heartbeats after paper ingestion
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add research-system to path
RESEARCH_DIR = Path.home() / '.openclaw' / 'workspace' / 'research-system'
sys.path.insert(0, str(RESEARCH_DIR))

from research_analyzer import ResearchAnalyzer
from experiment_runner import ExperimentRunner
from monthly_tracker import MonthlyGoalTracker

def run_daily_research_workflow():
    """Run complete daily research workflow"""

    print("📊 Running daily research analysis...")

    # 1. Analyze today's papers
    analyzer = ResearchAnalyzer()
    analysis = analyzer.analyze_today_papers()

    if 'error' in analysis:
        print(f"ℹ {analysis['error']}")
        return False

    print(f"✓ Analyzed {analysis['count']} papers")

    # 2. Suggest research directions
    suggestions = analyzer.suggest_research_directions(analysis)

    print(f"\n🎯 Research Directions Suggested:")
    for i, s in enumerate(suggestions, 1):
        print(f"\n{i}. {s['direction']}")
        print(f"   Gap: {s['gap']}")
        print(f"   Idea: {s['idea']}")
        print(f"   Novelty: {s['novelty']}")

    # 3. Save analysis
    analyzer.save_analysis(analysis)
    print(f"\n✓ Analysis saved to data/analysis_{analysis['date']}.json")

    # 4. Create monthly goal if needed
    tracker = MonthlyGoalTracker()
    month = datetime.now().strftime('%Y-%m')
    current_goal = tracker._load_goal(month)

    if not current_goal:
        goal = tracker.create_monthly_goal(month)
        print(f"\n✓ Monthly goal created for {month}")
        print(f"  Target: {goal['target']}")
        print(f"  Deadline: {goal['deadline']}")

    # 5. Add top suggestion to monthly goal
    if suggestions:
        top_idea = suggestions[0]
        tracker.add_idea(month, top_idea)
        print(f"\n✓ Top idea added to {month} goal")

    # 6. Create experiment for top idea
    runner = ExperimentRunner()
    exp_dir = runner.create_experiment(top_idea)
    print(f"\n✓ Experiment created: {exp_dir}")

    # 7. Track experiment in monthly goal
    exp_id = Path(exp_dir).name
    tracker.add_experiment(month, exp_id)
    print(f"✓ Experiment added to {month} goal")

    # 8. Show progress
    progress = tracker.get_progress(month)
    print(f"\n📈 Monthly Progress for {month}:")
    print(f"  Status: {progress['status']}")
    print(f"  Days remaining: {progress['days_remaining']}")
    print(f"  Ideas: {progress['ideas_count']}")
    print(f"  Experiments: {progress['experiments_count']}")
    print(f"  Drafts: {progress['drafts_count']}")

    # 9. Save workflow output for telegram
    output = {
        'date': analysis['date'],
        'papers_analyzed': analysis['count'],
        'top_topics': [t[0] for t in analysis['topics'][:3]],
        'top_methods': [m[0] for m in analysis['methods'][:3]],
        'suggestions': suggestions,
        'experiment_created': exp_dir,
        'monthly_progress': progress
    }

    output_file = Path.home() / '.openclaw' / 'workspace' / 'research-system' / 'daily_output.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    return True

if __name__ == '__main__':
    success = run_daily_research_workflow()
    sys.exit(0 if success else 1)
