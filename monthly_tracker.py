"""Monthly publication goal tracker"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'research-system' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

class MonthlyGoalTracker:
    """Track progress toward monthly publication goal"""

    def __init__(self):
        self.goals_file = DATA_DIR / 'monthly_goals.json'
        self.publications_file = DATA_DIR / 'publications.json'

    def create_monthly_goal(self, month: str = None) -> dict:
        """Create a new monthly publication goal"""
        if month is None:
            month = datetime.now().strftime('%Y-%m')

        goal = {
            'month': month,
            'target': 'one novel paper or article',
            'status': 'in_progress',
            'created': datetime.now().isoformat(),
            'deadline': self._get_month_deadline(month),
            'ideas': [],
            'experiments': [],
            'drafts': [],
            'final_paper': None
        }

        self._save_goal(goal)
        return goal

    def _get_month_deadline(self, month: str) -> str:
        """Get the last day of the month"""
        year, month_num = month.split('-')
        month_num = int(month_num)

        # Days in each month
        days_in_month = {
            1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }

        return f"{year}-{month_num}-{days_in_month[month_num]}"

    def add_idea(self, month: str, idea: dict) -> None:
        """Add a research idea to monthly goal"""
        goal = self._load_goal(month)
        if goal:
            idea['added'] = datetime.now().isoformat()
            goal['ideas'].append(idea)
            self._save_goal(goal)

    def add_experiment(self, month: str, exp_id: str) -> None:
        """Add an experiment to monthly goal"""
        goal = self._load_goal(month)
        if goal:
            goal['experiments'].append({
                'id': exp_id,
                'added': datetime.now().isoformat(),
                'status': 'running'
            })
            self._save_goal(goal)

    def update_draft(self, month: str, draft_path: str, status: str) -> None:
        """Add or update draft status"""
        goal = self._load_goal(month)
        if goal:
            # Check if draft exists
            draft = next((d for d in goal['drafts'] if d['path'] == draft_path), None)

            if draft:
                draft['status'] = status
                draft['updated'] = datetime.now().isoformat()
            else:
                goal['drafts'].append({
                    'path': draft_path,
                    'status': status,
                    'created': datetime.now().isoformat()
                })

            self._save_goal(goal)

    def mark_published(self, month: str, paper_info: dict) -> None:
        """Mark monthly goal as completed with publication"""
        goal = self._load_goal(month)
        if goal:
            goal['status'] = 'completed'
            goal['final_paper'] = {
                'title': paper_info.get('title', ''),
                'arxiv_id': paper_info.get('arxiv_id', ''),
                'url': paper_info.get('url', ''),
                'published': datetime.now().isoformat()
            }
            self._save_goal(goal)

            # Also add to publications log
            self._log_publication(paper_info)

    def get_progress(self, month: str = None) -> dict:
        """Get progress report for current or specified month"""
        if month is None:
            month = datetime.now().strftime('%Y-%m')

        goal = self._load_goal(month)
        if not goal:
            return {'error': f'No goal found for {month}'}

        # Calculate progress
        progress = {
            'month': month,
            'target': goal['target'],
            'status': goal['status'],
            'deadline': goal['deadline'],
            'days_remaining': self._days_remaining(goal['deadline']),
            'ideas_count': len(goal['ideas']),
            'experiments_count': len(goal['experiments']),
            'drafts_count': len(goal['drafts']),
            'complete': goal['status'] == 'completed'
        }

        return progress

    def _load_goal(self, month: str) -> dict:
        """Load goal for specified month"""
        if self.goals_file.exists():
            with open(self.goals_file) as f:
                goals = json.load(f)
                for goal in goals:
                    if goal['month'] == month:
                        return goal
        return None

    def _save_goal(self, goal: dict) -> None:
        """Save goal to file"""
        goals = []

        if self.goals_file.exists():
            with open(self.goals_file) as f:
                goals = json.load(f)

        # Update or add goal
        updated = False
        for i, g in enumerate(goals):
            if g['month'] == goal['month']:
                goals[i] = goal
                updated = True
                break

        if not updated:
            goals.append(goal)

        with open(self.goals_file, 'w') as f:
            json.dump(goals, f, indent=2)

    def _log_publication(self, paper_info: dict) -> None:
        """Log publication to central file"""
        publications = []

        if self.publications_file.exists():
            with open(self.publications_file) as f:
                publications = json.load(f)

        publication = {
            'title': paper_info.get('title', ''),
            'arxiv_id': paper_info.get('arxiv_id', ''),
            'url': paper_info.get('url', ''),
            'published': datetime.now().isoformat(),
            'month': datetime.now().strftime('%Y-%m')
        }

        publications.append(publication)

        with open(self.publications_file, 'w') as f:
            json.dump(publications, f, indent=2)

    def _days_remaining(self, deadline: str) -> int:
        """Calculate days remaining until deadline"""
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        now = datetime.now()
        delta = deadline_date - now
        return max(0, delta.days)

if __name__ == '__main__':
    import sys

    tracker = MonthlyGoalTracker()

    if len(sys.argv) < 2:
        print("Usage: monthly_tracker.py <command> [args]")
        print("Commands:")
        print("  create [month] - Create monthly goal")
        print("  progress [month] - Show progress report")
        print("  add-idea <month> '<idea_json>' - Add research idea")
        print("  mark-published <month> '<paper_json>' - Mark as published")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'create':
        month = sys.argv[2] if len(sys.argv) > 2 else None
        goal = tracker.create_monthly_goal(month)
        print(f"✓ Monthly goal created for {goal['month']}")
        print(f"  Deadline: {goal['deadline']}")

    elif command == 'progress':
        month = sys.argv[2] if len(sys.argv) > 2 else None
        progress = tracker.get_progress(month)
        print(json.dumps(progress, indent=2))

    elif command == 'add-idea':
        if len(sys.argv) < 4:
            print("Error: month and idea JSON required")
            sys.exit(1)

        month = sys.argv[2]
        idea = json.loads(sys.argv[3])
        tracker.add_idea(month, idea)
        print(f"✓ Idea added to {month}")

    elif command == 'mark-published':
        if len(sys.argv) < 4:
            print("Error: month and paper JSON required")
            sys.exit(1)

        month = sys.argv[2]
        paper = json.loads(sys.argv[3])
        tracker.mark_published(month, paper)
        print(f"✓ {month} marked as published!")
