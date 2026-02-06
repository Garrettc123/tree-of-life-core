"""
TASK PLANNER
Decomposes complex goals into executable sub-tasks
"""
import json
from typing import List, Dict

class TaskPlanner:
    def __init__(self):
        self.task_templates = {
            'verify_contribution': [
                {'step': 1, 'action': 'fetch_metadata', 'branch': 'verification'},
                {'step': 2, 'action': 'check_duplicates', 'branch': 'verification'},
                {'step': 3, 'action': 'validate_format', 'branch': 'verification'},
                {'step': 4, 'action': 'mint_nft', 'branch': 'verification'},
                {'step': 5, 'action': 'distribute_reward', 'branch': 'governance'}
            ],
            'create_success_story': [
                {'step': 1, 'action': 'anonymize_data', 'branch': 'marketing'},
                {'step': 2, 'action': 'generate_graphic', 'branch': 'marketing'},
                {'step': 3, 'action': 'write_caption', 'branch': 'marketing'},
                {'step': 4, 'action': 'post_to_social', 'branch': 'marketing'}
            ],
            'portfolio_update': [
                {'step': 1, 'action': 'fetch_nft_value', 'branch': 'wealth'},
                {'step': 2, 'action': 'calculate_metrics', 'branch': 'wealth'},
                {'step': 3, 'action': 'update_dashboard', 'branch': 'wealth'}
            ]
        }
    
    def decompose(self, goal: str, context: Dict) -> List[Dict]:
        """Decompose a high-level goal into executable steps"""
        
        if goal in self.task_templates:
            return self.task_templates[goal]
        
        # For unknown goals, return a generic plan
        return [
            {'step': 1, 'action': 'analyze_goal', 'branch': 'orchestrator'},
            {'step': 2, 'action': 'route_to_branch', 'branch': 'orchestrator'}
        ]
    
    def create_execution_plan(self, goal: str, context: Dict) -> Dict:
        """Create a complete execution plan with dependencies"""
        steps = self.decompose(goal, context)
        
        return {
            'goal': goal,
            'context': context,
            'steps': steps,
            'total_steps': len(steps),
            'status': 'planned'
        }
