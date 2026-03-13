# Research System

Automated research analysis and experiment tracking for binh's monthly publication goal.

## Goal

Publish **one novel paper or article every month** on robotics research.

## System Components

### 1. Research Analyzer (`research_analyzer.py`)

Analyzes daily arXiv robotics papers to:
- Extract trending topics and methods
- Identify research gaps
- Suggest novel research directions

**Outputs:**
- `data/analysis_YYYY-MM-DD.json` - Daily analysis
- Research suggestions ranked by novelty

### 2. Experiment Runner (`experiment_runner.py`)

Creates and tracks experiments to test research ideas:
- Auto-generates experiment directories
- Provides templates for implementation
- Tracks status (pending → running → complete)

**Structure:**
```
experiments/
└── YYYYMMDD_HHMMSS/
    ├── README.md (problem, idea, plan, results)
    └── implementation.py (code for experiment)
```

### 3. Monthly Tracker (`monthly_tracker.py`)

Tracks progress toward monthly publication goal:
- Creates monthly goals
- Logs ideas, experiments, drafts
- Tracks deadlines and completion status

**Commands:**
```bash
python monthly_tracker.py create [month]      # Create monthly goal
python monthly_tracker.py progress [month]      # Show progress
python monthly_tracker.py add-idea <month> <json>  # Add idea
python monthly_tracker.py mark-published <month> <json>  # Mark complete
```

### 4. Daily Workflow (`daily_workflow.py`)

Automated workflow that runs during heartbeats:

1. **Analyze** today's arXiv papers
2. **Suggest** research directions
3. **Create** monthly goal if needed
4. **Add** top idea to monthly goal
5. **Create** experiment for top idea
6. **Track** experiment in monthly goal
7. **Report** progress

## Daily Workflow

Every day (after paper ingestion):

```bash
cd ~/.openclaw/workspace/research-system
uv run python daily_workflow.py
```

This:
- Analyzes papers and suggests directions
- Creates experiment for top suggestion
- Tracks everything in monthly goal
- Generates summary for telegram

## Heartbeat Integration

Add to `HEARTBEAT.md`:

```bash
# After paper ingestion
cd ~/.openclaw/workspace/research-system
uv run python daily_workflow.py
```

## Project Structure

```
research-system/
├── data/                          # All data storage
│   ├── analysis_YYYY-MM-DD.json   # Daily analyses
│   ├── experiments.json            # Experiment log
│   ├── monthly_goals.json         # Monthly goals
│   └── publications.json         # Published papers
├── experiments/                    # Experiment directories
│   └── YYYYMMDD_HHMMSS/
│       ├── README.md
│       └── implementation.py
├── research_analyzer.py           # Paper analysis
├── experiment_runner.py           # Experiment management
├── monthly_tracker.py            # Goal tracking
└── daily_workflow.py            # Main workflow
```

## Monthly Workflow

### Start of Month
1. Create monthly goal: `uv run python monthly_tracker.py create`
2. Review daily research suggestions
3. Select most promising direction
4. Start implementation

### During Month
1. Run experiments and collect results
2. Draft paper sections
3. Update monthly goal: `uv run python monthly_tracker.py progress`
4. Iterate based on results

### End of Month
1. Finalize paper
2. Submit to arXiv
3. Mark complete: `uv run python monthly_tracker.py mark-published <month> <json>`
4. Start next month's goal

## Example Daily Output

```
📊 Running daily research analysis...
✓ Analyzed 15 papers

🎯 Research Directions Suggested:

1. Adaptive sim-to-real for contact-rich tasks
   Gap: Sim-to-real fails on high-frequency contact manipulation
   Idea: Learn contact dynamics online and adapt policy in real-time
   Novelty: high

✓ Analysis saved
✓ Monthly goal created for 2026-03
✓ Top idea added to 2026-03 goal
✓ Experiment created: /home/dietpi/.openclaw/workspace/research-system/experiments/20260314_014722
✓ Experiment added to 2026-03 goal

📈 Monthly Progress for 2026-03:
  Status: in_progress
  Days remaining: 17
  Ideas: 1
  Experiments: 1
  Drafts: 0
```

## Tracking Progress

All progress is tracked in JSON files under `data/`:
- **monthly_goals.json** - Monthly goals and status
- **experiments.json** - All experiments and results
- **publications.json** - Published papers log
- **analysis_*.json** - Daily paper analyses

---

Created by: quack quack
Purpose: Help binh publish 1 paper/month
