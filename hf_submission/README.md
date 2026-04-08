# Regulatory Compliance Checker — OpenEnv Environment

An RL environment that simulates regulatory compliance auditing. An AI agent reviews product feature descriptions and must identify violations of **GDPR**, **HIPAA**, and **SOC2** regulations, classify their severity, and suggest remediations.

## Why This Matters

Regulatory compliance is one of the most expensive and error-prone tasks in software development. Companies spend millions on legal counsel and compliance teams to ensure their products don't violate data protection laws. This environment trains and evaluates AI agents on their ability to:

- Read product specifications and identify regulatory risks
- Cite the correct regulation clause being violated
- Assess violation severity accurately
- Suggest actionable remediations

## Environment Description

### Action Space

The agent submits a compliance finding at each step:

| Field | Type | Description |
|-------|------|-------------|
| `violation_id` | `str` | Regulation clause violated (e.g., "GDPR-Art17", "HIPAA-Security") |
| `violation_description` | `str` | What's wrong and why it violates the regulation |
| `severity` | `str` | "critical", "high", "medium", or "low" |
| `suggested_fix` | `str` | Concrete, actionable remediation |

### Observation Space

After each action, the agent sees:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | Current task (easy/medium/hard) |
| `feature_description` | `str` | The product feature being audited |
| `applicable_regulations` | `List[str]` | Full text of relevant regulation excerpts |
| `findings_so_far` | `List[Dict]` | Previously accepted findings |
| `remaining_violations` | `int` | How many violations are left to find |
| `feedback` | `str` | Feedback on the last submitted finding |
| `max_steps_remaining` | `int` | Steps remaining in the episode |

### Reward Function

Rewards are **not sparse** — the agent gets partial credit:

| Component | Weight | Description |
|-----------|--------|-------------|
| Violation match | 0.4 | Finding matches a real violation (keyword-based) |
| Correct regulation | 0.2 | Agent cites the correct regulation clause |
| Correct severity | 0.2 | Agent classifies severity accurately |
| Quality fix | 0.1 | Suggested fix is substantive (>20 chars) |
| Strong match | 0.1 | High-confidence keyword match (≥60%) |

**Episode score** = 0.7 × (violations found / total violations) + 0.3 × (average step quality)

Score range: **0.0 – 1.0**

## Tasks

### Task 1: Easy — Single Regulation (GDPR)
- **Scenarios**: User analytics dashboard, Newsletter signup
- **Violations**: 3 per scenario (obvious: no consent, excessive data, no deletion)
- **Max steps**: 8
- **Regulations**: GDPR only

### Task 2: Medium — Multiple Regulations (GDPR + HIPAA)
- **Scenarios**: Telehealth patient portal, Employee wellness platform
- **Violations**: 5 per scenario (subtler: inadequate anonymization, purpose limitation, bundled consent)
- **Max steps**: 12
- **Regulations**: GDPR + HIPAA

### Task 3: Hard — Full Stack (GDPR + HIPAA + SOC2)
- **Scenarios**: AI insurance claims processor, Smart building access system
- **Violations**: 7 per scenario (ambiguous: shared credentials, fail-open design, training data PII, no explainability)
- **Max steps**: 15
- **Regulations**: GDPR + HIPAA + SOC2

## Setup & Usage

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally
```bash
# Start the server
uvicorn compliance_checker.server.app:app --host 0.0.0.0 --port 8000

# In another terminal, run inference
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-token"
python -m compliance_checker.inference
```

### Docker
```bash
docker build -t compliance-checker .
docker run -p 8000:8000 compliance-checker
```

### Deploy to HF Spaces
```bash
openenv push --repo-id your-username/compliance-checker
```

## Baseline Scores

| Task | Score | Model |
|------|-------|-------|
| Easy | ~0.75 | Qwen2.5-72B-Instruct |
| Medium | ~0.55 | Qwen2.5-72B-Instruct |
| Hard | ~0.35 | Qwen2.5-72B-Instruct |

*Scores are approximate and vary by run.*

## Architecture

```
compliance_checker/
├── models.py              ← Action, Observation, State (Pydantic)
├── client.py              ← WebSocket client (EnvClient subclass)
├── server/
│   ├── environment.py     ← Compliance audit logic + scenarios
│   ├── app.py             ← FastAPI server (1 line)
│   └── __init__.py
├── inference.py           ← LLM agent using OpenAI client
├── openenv.yaml           ← Manifest
├── Dockerfile             ← Container
├── requirements.txt       ← Dependencies
└── README.md              ← This file
```

## Team

**Team Daedalus**
- T Preetham Reddy (Lead)
- Somaraju Sai Ashrith Venkata Ram Krish Naga
- Jyothiraditya SSVKSS
