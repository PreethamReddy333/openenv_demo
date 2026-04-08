"""Client for the Compliance Checker environment."""

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from compliance_checker.models import ComplianceAction, ComplianceObservation, ComplianceState


class ComplianceCheckerEnv(EnvClient[ComplianceAction, ComplianceObservation, ComplianceState]):
    """WebSocket client for the Regulatory Compliance Checker environment."""

    def _step_payload(self, action: ComplianceAction) -> dict:
        return {
            "violation_id": action.violation_id,
            "violation_description": action.violation_description,
            "severity": action.severity,
            "suggested_fix": action.suggested_fix,
        }

    def _parse_result(self, payload: dict) -> StepResult:
        obs_data = payload.get("observation", {})
        return StepResult(
            observation=ComplianceObservation(
                done=payload.get("done", False),
                reward=payload.get("reward"),
                task_id=obs_data.get("task_id", ""),
                feature_description=obs_data.get("feature_description", ""),
                applicable_regulations=obs_data.get("applicable_regulations", []),
                findings_so_far=obs_data.get("findings_so_far", []),
                remaining_violations=obs_data.get("remaining_violations", 0),
                feedback=obs_data.get("feedback", ""),
                max_steps_remaining=obs_data.get("max_steps_remaining", 0),
            ),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> ComplianceState:
        return ComplianceState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", ""),
            difficulty=payload.get("difficulty", ""),
            total_violations=payload.get("total_violations", 0),
            found_violations=payload.get("found_violations", 0),
        )
