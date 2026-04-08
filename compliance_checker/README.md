# 🛡️ Regulatory Compliance Checker — OpenEnv Environment

**An RL environment that teaches AI agents to audit software products for GDPR, HIPAA, and SOC2 violations.**

> Every startup scrambles for regulatory compliance. Lawyers cost $500/hr. This environment trains agents to do it at machine speed.

## What Makes This Different

Most environments just say "right" or "wrong." Ours **teaches the agent through progressive hints**, creating a learning curriculum within each episode:

```
Failure 1: "There are 5 violations remaining... a critical-severity issue."
Failure 2: "Consider the HIPAA regulations... relates to anonymization."
Failure 3: "Look at HIPAA-Privacy... related to: anonymization, de-identification, re-identification."
Failure 4: "HIPAA-Privacy is violated. Issue: Inadequate anonymization — keeping age, ZIP..."
```

This approach creates meaningful reward signal for RLHF/GRPO training — agents don't just memorize answers, they learn to reason about regulations.

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🎓 **Progressive Hints** | Failed attempts trigger increasingly specific hints — a learning curriculum within each episode |
| 💊 **Remediation Quality Scoring** | Checks if the suggested fix actually addresses the violation type (e.g., encryption fix for encryption violation) |
| 🔄 **Duplicate Detection** | Repeated submissions are penalized (-0.1), preventing exploitation |
| 📊 **Composite Reward** | 60% coverage + 25% quality + 15% efficiency — not binary, truly continuous |
| 📏 **13 Real Regulation Excerpts** | GDPR Articles 5/6/7/13/17/25/32, HIPAA Privacy/Security/Breach, SOC2 CC6/7/8 |
| 🎯 **6 Realistic Scenarios** | From newsletter signups to AI insurance processors to smart building systems |

---

## Environment Description

### The Task
The agent receives a **product feature description** (e.g., "Our telehealth app allows patients to video-call doctors...") and the **full text of applicable regulations**. It must:

1. **Identify** specific regulatory violations in the feature
2. **Classify** severity (critical/high/medium/low)
3. **Cite** the correct regulation article (e.g., GDPR-Art17, HIPAA-Security)
4. **Suggest** a concrete, actionable remediation

### Action Space

```python
class ComplianceAction(Action):
    violation_id: str           # "GDPR-Art17", "HIPAA-Security", "SOC2-CC6"
    violation_description: str  # What's wrong and why
    severity: str               # "critical" | "high" | "medium" | "low"
    suggested_fix: str          # Concrete remediation
```

### Observation Space

```python
class ComplianceObservation(Observation):
    task_id: str                        # "easy" | "medium" | "hard"
    feature_description: str            # Product feature to audit
    applicable_regulations: List[str]   # Full regulation text
    findings_so_far: List[Dict]         # Previously accepted findings
    remaining_violations: int           # How many left to find
    feedback: str                       # Progressive hints or success feedback
    max_steps_remaining: int            # Steps left
```

### Reward Function (Composite, Not Binary)

**Step-level rewards** (0.0–1.0):

| Component | Points | Condition |
|-----------|--------|-----------|
| Base match | 0.40 | Violation matches a known issue |
| Correct regulation | 0.20 | Agent cites the right article |
| Correct severity | 0.15 | Severity classification matches |
| Strong keyword match | 0.10 | ≥60% keyword coverage |
| Remediation quality | 0.00–0.15 | Fix uses violation-specific terminology |

**Episode-level score:**
```
score = 0.60 × coverage + 0.25 × quality + 0.15 × efficiency
```
- `coverage` = violations found / total violations
- `quality` = average step reward
- `efficiency` = violations found / steps taken

**Special rewards:**
- Miss (wrong finding): 0.05 (not 0.0 — continuous signal)
- Duplicate submission: -0.1 (penalizes bad behavior)

---

## Tasks (3 Difficulty Levels)

### Task 1: Easy — GDPR Basics
- **Scenarios**: User analytics dashboard, newsletter signup form
- **Violations**: 3 per scenario (obvious: no consent, excessive data, no deletion)
- **Max steps**: 8
- **Regulations**: GDPR only
- **Baseline score**: ~0.97

### Task 2: Medium — Healthcare Compliance
- **Scenarios**: Telehealth patient portal, employee wellness platform
- **Violations**: 5 per scenario (subtle: inadequate anonymization, purpose limitation, bundled consent)
- **Max steps**: 12
- **Regulations**: GDPR + HIPAA
- **Baseline score**: ~0.85

### Task 3: Hard — Enterprise AI Audit
- **Scenarios**: AI insurance claims processor, smart building access system
- **Violations**: 7 per scenario (ambiguous: shared credentials, fail-open design, training data PII, no AI explainability)
- **Max steps**: 15
- **Regulations**: GDPR + HIPAA + SOC2
- **Baseline score**: ~0.81

---

## Progressive Hints — The Learning Curriculum

When an agent submits wrong findings, the environment provides increasingly specific hints:

| Failure # | Hint Level | Example |
|-----------|-----------|---------|
| 1 | General | "5 violations remaining... a critical-severity issue" |
| 2 | Regulation family | "Consider HIPAA... relates to anonymization" |
| 3 | Specific article | "Look at HIPAA-Privacy... anonymization, de-identification, re-identification" |
| 4+ | Near-answer | "HIPAA-Privacy is violated. Issue: Inadequate anonymization..." |

This creates a **curriculum within each episode** — agents learn by attempting, failing, receiving guidance, and improving. This is ideal for RLHF and GRPO training.

---

## Setup & Usage

### Install
```bash
pip install -r requirements.txt
```

### Run Server
```bash
uvicorn compliance_checker.server.app:app --host 0.0.0.0 --port 7860
```

### Run Inference
```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-token"
python inference.py
```

### Docker
```bash
docker build -t compliance-checker .
docker run -p 7860:7860 compliance-checker
```

---

## Architecture

```
hf_submission/
├── inference.py                     ← LLM agent with [START]/[STEP]/[END] logging
├── compliance_checker/              ← Python package
│   ├── __init__.py
│   ├── models.py                    ← Typed Pydantic models
│   ├── client.py                    ← WebSocket client
│   └── server/
│       ├── __init__.py
│       ├── app.py                   ← FastAPI server + main()
│       └── environment.py           ← 800+ lines: scenarios, grading, hints
├── server/                          ← Root-level entry (openenv validate)
│   ├── app.py
│   └── environment.py
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── openenv.yaml                     ← Task definitions + reward spec
└── README.md
```

## Team Daedalus

- **T Preetham Reddy** (Lead)
- **Somaraju Sai Ashrith Venkata Ram Krish Naga**
- **Jyothiraditya SSVKSS**
