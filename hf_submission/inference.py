"""
Inference Script — Regulatory Compliance Checker
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    LOCAL_IMAGE_NAME The name of the local image to use for the environment if using from_docker_image()

- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables

STDOUT FORMAT
- The script must emit exactly three line types to stdout, in this order:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import asyncio
import json
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from compliance_checker.models import ComplianceAction
from compliance_checker.client import ComplianceCheckerEnv

IMAGE_NAME = os.getenv("IMAGE_NAME")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
BENCHMARK = "compliance_checker"
TEMPERATURE = 0.3
MAX_TOKENS = 800

TASKS = ["easy", "medium", "hard"]

SYSTEM_PROMPT = textwrap.dedent("""
You are an expert regulatory compliance auditor specializing in GDPR, HIPAA, and SOC2.

You are auditing a product feature description for regulatory violations. For each violation you find, you must provide:

1. violation_id: The specific regulation clause violated (e.g., "GDPR-Art17", "HIPAA-Security", "SOC2-CC6")
2. violation_description: A clear description of what's wrong and why it violates the regulation
3. severity: One of "critical", "high", "medium", or "low"
4. suggested_fix: A concrete, actionable remediation

IMPORTANT: Respond with ONLY a valid JSON object in this exact format:
{
    "violation_id": "REGULATION-CLAUSE",
    "violation_description": "Description of the violation...",
    "severity": "critical|high|medium|low",
    "suggested_fix": "How to fix this..."
}

Focus on the most impactful violations first. Be specific — cite the exact part of the feature description that causes the violation. Do NOT repeat violations you have already submitted.
""").strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Truncate action for logging
    action_short = action.replace("\n", " ")[:200]
    print(
        f"[STEP] step={step} action={action_short} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


def build_user_prompt(observation) -> str:
    """Build a user prompt from the observation."""
    findings_text = ""
    if observation.findings_so_far:
        findings_text = "\n\nViolations already identified (DO NOT repeat these):\n"
        for i, f in enumerate(observation.findings_so_far, 1):
            findings_text += f"  {i}. [{f['violation_id']}] {f['description']} (severity: {f['severity']})\n"

    regulations_text = "\n\n".join(observation.applicable_regulations)

    return textwrap.dedent(f"""
PRODUCT FEATURE TO AUDIT:
{observation.feature_description}

APPLICABLE REGULATIONS:
{regulations_text}
{findings_text}
REMAINING VIOLATIONS TO FIND: {observation.remaining_violations}
STEPS REMAINING: {observation.max_steps_remaining}

Identify the next violation. Respond with ONLY a JSON object.
""").strip()


def parse_llm_response(text: str) -> dict:
    """Parse LLM response into a compliance finding dict."""
    # Try to extract JSON from the response
    text = text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()

    try:
        data = json.loads(text)
        return {
            "violation_id": str(data.get("violation_id", "UNKNOWN")),
            "violation_description": str(data.get("violation_description", "")),
            "severity": str(data.get("severity", "medium")),
            "suggested_fix": str(data.get("suggested_fix", "")),
        }
    except json.JSONDecodeError:
        # Fallback — try to find JSON in the text
        import re
        json_match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "violation_id": str(data.get("violation_id", "UNKNOWN")),
                    "violation_description": str(data.get("violation_description", text[:200])),
                    "severity": str(data.get("severity", "medium")),
                    "suggested_fix": str(data.get("suggested_fix", "")),
                }
            except json.JSONDecodeError:
                pass

        # Last resort fallback
        return {
            "violation_id": "UNKNOWN",
            "violation_description": text[:300],
            "severity": "medium",
            "suggested_fix": "Review and remediate the identified issue.",
        }


def get_model_response(client: OpenAI, observation) -> dict:
    """Get a compliance finding from the LLM."""
    user_prompt = build_user_prompt(observation)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return parse_llm_response(text)
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return {
            "violation_id": "UNKNOWN",
            "violation_description": "Failed to get response from model",
            "severity": "medium",
            "suggested_fix": "N/A",
        }


async def run_task(client: OpenAI, task_id: str) -> tuple:
    """Run one task and return (success, steps, score, rewards)."""
    if IMAGE_NAME:
        env = await ComplianceCheckerEnv.from_docker_image(IMAGE_NAME)
    else:
        # Fallback to local testing — import and run directly
        from compliance_checker.server.environment import ComplianceEnvironment
        env_impl = ComplianceEnvironment()
        # Simulate the env interface directly for local testing
        class LocalEnvWrapper:
            def __init__(self, env_impl, task_id):
                self.env = env_impl
                self.task_id = task_id
            async def reset(self):
                obs = self.env.reset(task_id=self.task_id)
                return type('Result', (), {'observation': obs, 'done': obs.done, 'reward': obs.reward})()
            async def step(self, action):
                obs = self.env.step(action)
                return type('Result', (), {'observation': obs, 'done': obs.done, 'reward': obs.reward})()
            async def close(self):
                pass
        env = LocalEnvWrapper(env_impl, task_id)
    
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    task_config = {"easy": 8, "medium": 12, "hard": 15}
    max_steps = task_config.get(task_id, 10)

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        if IMAGE_NAME:
            result = await env.reset(task_id=task_id)
        else:
            result = await env.reset()
        observation = result.observation

        for step in range(1, max_steps + 1):
            if result.done:
                break

            # Get LLM response
            finding = get_model_response(client, observation)

            # Create action
            action = ComplianceAction(
                violation_id=finding["violation_id"],
                violation_description=finding["violation_description"],
                severity=finding["severity"],
                suggested_fix=finding["suggested_fix"],
            )

            # Step the environment
            result = await env.step(action)
            observation = result.observation

            reward = result.reward or 0.0
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step

            action_str = f"violation={finding['violation_id']}|severity={finding['severity']}"
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            if done:
                break

        # Final score: last reward is the episode score
        if rewards:
            score = rewards[-1]  # The final step reward is the episode-level score
        score = min(max(score, 0.0), 1.0)
        success = score >= 0.3

    except Exception as e:
        print(f"[DEBUG] Task {task_id} error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return success, steps_taken, score, rewards


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    for task_id in TASKS:
        await run_task(client, task_id)


if __name__ == "__main__":
    asyncio.run(main())
