"""Research analysis for binh's monthly publication goal"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'research-system' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

class ResearchAnalyzer:
    """Analyze arXiv papers and suggest research directions"""

    def __init__(self):
        self.trends_file = DATA_DIR / 'research_trends.json'
        self.ideas_file = DATA_DIR / 'research_ideas.json'
        self.experiments_file = DATA_DIR / 'experiments.json'
        self.monthly_goals_file = DATA_DIR / 'monthly_goals.json'

    def analyze_today_papers(self) -> dict:
        """Analyze today's ingested papers"""
        today = datetime.now().strftime('%Y-%m-%d')
        papers_file = Path.home() / '.openclaw' / 'workspace' / 'papers' / f'today_papers_{today}.json'

        if not papers_file.exists():
            return {'error': 'No papers for today'}

        with open(papers_file) as f:
            data = json.load(f)

        papers = data.get('papers', [])
        analysis = {
            'date': today,
            'count': len(papers),
            'topics': self.extract_topics(papers),
            'methods': self.extract_methods(papers),
            'keywords': self.extract_keywords(papers),
            'papers': papers[:5]  # Top 5 for reference
        }

        return analysis

    def extract_topics(self, papers) -> list:
        """Extract research topics from paper titles"""
        topics = []

        topic_keywords = {
            'humanoid': ['humanoid', 'locomanipulation', 'dexterous', 'manipulation'],
            'learning': ['learning', 'policy', 'imitation', 'reinforcement', 'RL'],
            'vision': ['vision', 'perception', 'visual', 'scene', 'VLM'],
            'simulation': ['simulation', 'sim-to-real', 'digital twin'],
            'control': ['control', 'MPC', 'dynamics', 'optimal'],
            'navigation': ['navigation', 'localization', 'SLAM', 'mapping'],
            'grasping': ['grasp', 'hand', 'finger', 'tendon'],
            'flying': ['flight', 'drone', 'aerial', 'UAV'],
            'underwater': ['underwater', 'AUV', 'docking'],
        }

        for paper in papers:
            title = paper.get('title', '').lower()
            for topic, keywords in topic_keywords.items():
                if any(kw in title for kw in keywords):
                    topics.append(topic)

        return Counter(topics).most_common(5)

    def extract_methods(self, papers) -> list:
        """Extract research methods from paper titles/summaries"""
        methods = []

        method_keywords = {
            'foundation model': ['foundation', 'VLM', 'pre-train'],
            'transformer': ['transformer', 'attention'],
            'diffusion': ['diffusion'],
            'policy gradient': ['policy gradient', 'PPO'],
            'behavior cloning': ['behavior cloning', 'BC'],
            'model-predictive control': ['MPC', 'model predictive'],
            'teleoperation': ['teleoperation', 'teleop'],
            'imitation learning': ['imitation', 'demo', 'demonstration'],
        }

        for paper in papers:
            title = paper.get('title', '').lower()
            summary = paper.get('summary', '').lower()
            text = f"{title} {summary}"

            for method, keywords in method_keywords.items():
                if any(kw in text for kw in keywords):
                    methods.append(method)

        return Counter(methods).most_common(5)

    def extract_keywords(self, papers) -> list:
        """Extract key terms from papers"""
        all_text = []
        for paper in papers:
            title = paper.get('title', '')
            summary = paper.get('summary', '')
            all_text.append(f"{title} {summary}")

        combined = ' '.join(all_text)

        # Common technical terms in robotics
        keywords = ['robot', 'control', 'policy', 'learning', 'vision',
                  'manipulation', 'grasp', 'humanoid', 'simulation',
                  'SLAM', 'localization', 'navigation', 'detection',
                  'tracking', 'planning', 'optimal', 'real-time']

        found = []
        for kw in keywords:
            if kw.lower() in combined.lower():
                count = combined.lower().count(kw.lower())
                found.append((kw, count))

        return sorted(found, key=lambda x: x[1], reverse=True)[:10]

    def suggest_research_directions(self, analysis: dict) -> list:
        """Suggest novel research directions based on analysis"""
        suggestions = []

        # Get current trends
        trending_topics = [t[0] for t in analysis.get('topics', [])]
        trending_methods = [m[0] for m in analysis.get('methods', [])]

        # Generate suggestions
        if 'humanoid' in trending_topics and 'foundation model' in trending_methods:
            suggestions.append({
                'direction': 'Multi-modal foundation models for humanoid control',
                'gap': 'Most humanoid foundation models focus on vision, fewer on audio/tactile integration',
                'idea': 'Combine VLM with tactile and audio sensing for richer understanding',
                'novelty': 'medium'
            })

        if 'learning' in trending_topics and 'simulation' in trending_topics:
            suggestions.append({
                'direction': 'Adaptive sim-to-real for contact-rich tasks',
                'gap': 'Sim-to-real fails on high-frequency contact manipulation',
                'idea': 'Learn contact dynamics online and adapt policy in real-time',
                'novelty': 'high'
            })

        if 'vision' in trending_topics and 'navigation' in trending_topics:
            suggestions.append({
                'direction': 'Neuro-symbolic navigation with learned primitives',
                'gap': 'End-to-end learning struggles with long-horizon planning',
                'idea': 'Combine learned primitive policies with symbolic reasoning',
                'novelty': 'medium'
            })

        # Default suggestions
        if not suggestions:
            suggestions.append({
                'direction': 'Data-efficient learning from limited demonstrations',
                'gap': 'Most methods need hundreds of demonstrations',
                'idea': 'Meta-learn across tasks to enable few-shot adaptation',
                'novelty': 'medium'
            })

        return suggestions

    def save_analysis(self, analysis: dict) -> None:
        """Save today's analysis"""
        date = analysis.get('date')
        analysis_file = DATA_DIR / f'analysis_{date}.json'
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)

    def load_previous_analyses(self) -> list:
        """Load previous analyses for trend tracking"""
        analyses = []
        for file in sorted(DATA_DIR.glob('analysis_*.json')):
            with open(file) as f:
                analyses.append(json.load(f))
        return analyses[-7:]  # Last 7 days

if __name__ == '__main__':
    analyzer = ResearchAnalyzer()
    analysis = analyzer.analyze_today_papers()
    print(json.dumps(analysis, indent=2))

    suggestions = analyzer.suggest_research_directions(analysis)
    analyzer.save_analysis(analysis)

    print("\n📊 Research Suggestions:")
    for i, s in enumerate(suggestions, 1):
        print(f"\n{i}. {s['direction']}")
        print(f"   Gap: {s['gap']}")
        print(f"   Idea: {s['idea']}")
        print(f"   Novelty: {s['novelty']}")
