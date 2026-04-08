"""
Regulatory Compliance Checker — Type Definitions

Action:  The agent submits a compliance finding (violation identified + suggested fix)
Observation: The agent sees a product feature description + applicable regulations + feedback
State: Episode metadata
"""

from typing import List, Optional, Dict, Any
from openenv.core.env_server import Action, Observation, State


class ComplianceAction(Action):
    """Agent submits a compliance finding.
    
    The agent identifies a specific violation and suggests a remediation.
    """
    violation_id: str           # Which regulation clause is violated (e.g., "GDPR-Art17")
    violation_description: str  # Free-text description of what's wrong
    severity: str               # "critical", "high", "medium", "low"
    suggested_fix: str          # What should be changed to comply


class ComplianceObservation(Observation):
    """What the agent sees after each action.
    
    Note: done (bool) and reward (Optional[float]) are inherited from Observation.
    """
    task_id: str                        # Which task is active
    feature_description: str            # The product feature to audit
    applicable_regulations: List[str]   # List of regulation excerpts
    findings_so_far: List[Dict[str, str]]   # Previously submitted findings
    remaining_violations: int           # How many violations are left to find
    feedback: str                       # Feedback on last action
    max_steps_remaining: int            # Steps left before episode ends


class ComplianceState(State):
    """Episode metadata.
    
    Note: episode_id (Optional[str]) and step_count (int) are inherited from State.
    """
    task_id: str = ""
    difficulty: str = ""
    total_violations: int = 0
    found_violations: int = 0
