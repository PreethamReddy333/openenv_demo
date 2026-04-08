"""
Regulatory Compliance Checker Environment

Simulates a compliance audit where an AI agent must identify regulatory violations
in product feature descriptions and suggest remediations.

Supports 3 tasks:
  - easy:   Single regulation (GDPR), obvious violations, 2-3 violations to find
  - medium: Multiple regulations (GDPR + HIPAA), subtle violations, 4-5 to find
  - hard:   Multiple regulations (GDPR + HIPAA + SOC2), ambiguous violations, 6-7 to find
"""

import random
import uuid
from typing import Dict, List, Any, Optional

from openenv.core.env_server import Environment
from compliance_checker.models import ComplianceAction, ComplianceObservation, ComplianceState


# ─────────────────────────────────────────────────────────────────────────────
# COMPLIANCE SCENARIOS DATABASE
# ─────────────────────────────────────────────────────────────────────────────

REGULATION_EXCERPTS = {
    "GDPR-Art5": (
        "GDPR Article 5 — Principles: Personal data shall be processed lawfully, fairly and "
        "transparently. Data shall be collected for specified, explicit and legitimate purposes "
        "and not further processed in a manner incompatible with those purposes. Data shall be "
        "adequate, relevant and limited to what is necessary (data minimization)."
    ),
    "GDPR-Art6": (
        "GDPR Article 6 — Lawfulness of Processing: Processing is lawful only if the data subject "
        "has given consent, or processing is necessary for the performance of a contract, compliance "
        "with a legal obligation, protection of vital interests, public task, or legitimate interests."
    ),
    "GDPR-Art7": (
        "GDPR Article 7 — Conditions for Consent: The controller shall be able to demonstrate that the "
        "data subject has consented. The request for consent shall be clearly distinguishable, in clear "
        "and plain language. The data subject shall have the right to withdraw consent at any time."
    ),
    "GDPR-Art13": (
        "GDPR Article 13 — Information to be Provided: Where personal data are collected, the controller "
        "shall provide: identity and contact details, purposes and legal basis, recipients or categories "
        "of recipients, data retention period, right to lodge a complaint."
    ),
    "GDPR-Art17": (
        "GDPR Article 17 — Right to Erasure ('Right to be Forgotten'): The data subject shall have the "
        "right to obtain erasure of personal data without undue delay where the data is no longer "
        "necessary, consent is withdrawn, or data has been unlawfully processed."
    ),
    "GDPR-Art25": (
        "GDPR Article 25 — Data Protection by Design and by Default: The controller shall implement "
        "appropriate technical and organisational measures for ensuring that, by default, only personal "
        "data which are necessary for each specific purpose are processed."
    ),
    "GDPR-Art32": (
        "GDPR Article 32 — Security of Processing: The controller and processor shall implement "
        "appropriate technical and organisational measures including pseudonymisation and encryption, "
        "ability to ensure confidentiality, integrity, and availability of processing systems."
    ),
    "HIPAA-Privacy": (
        "HIPAA Privacy Rule: Covered entities must not use or disclose protected health information (PHI) "
        "except as permitted. Minimum necessary standard applies — only the minimum PHI needed should be "
        "used. Patients have the right to access their records and request amendments."
    ),
    "HIPAA-Security": (
        "HIPAA Security Rule: Covered entities must implement administrative, physical, and technical "
        "safeguards to ensure confidentiality, integrity, and availability of electronic PHI (ePHI). "
        "This includes access controls, audit controls, integrity controls, and transmission security."
    ),
    "HIPAA-Breach": (
        "HIPAA Breach Notification Rule: Covered entities must notify affected individuals within 60 days "
        "of discovering a breach of unsecured PHI. If the breach affects 500+ individuals, HHS and media "
        "must also be notified."
    ),
    "SOC2-CC6": (
        "SOC2 CC6 — Logical and Physical Access Controls: The entity implements logical access security "
        "measures to protect against unauthorized access. This includes credential management, "
        "multi-factor authentication, role-based access, and regular access reviews."
    ),
    "SOC2-CC7": (
        "SOC2 CC7 — System Operations: The entity monitors system components and detects anomalies. "
        "Incidents are identified, reported, and acted upon. The entity has a defined incident response "
        "plan with escalation procedures."
    ),
    "SOC2-CC8": (
        "SOC2 CC8 — Change Management: Changes to infrastructure, data, software, and procedures are "
        "authorized, designed, developed, configured, documented, tested, approved, and implemented "
        "to meet the entity's objectives."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# TASK SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS = {
    # ═══════════════════════════════════════════════════════════════════
    # EASY TASKS — Single regulation, obvious violations
    # ═══════════════════════════════════════════════════════════════════
    "easy_1": {
        "difficulty": "easy",
        "feature_description": (
            "Feature: User Analytics Dashboard\n\n"
            "Our new analytics dashboard collects user browsing history, location data, device "
            "fingerprints, and keystroke patterns to build detailed behavioral profiles. Data is "
            "collected automatically when users visit the site — no consent banner or opt-out "
            "mechanism is provided. User profiles are stored indefinitely and shared with third-party "
            "advertising networks. There is no way for users to view, export, or delete their data. "
            "All data is stored in plaintext in a cloud database."
        ),
        "applicable_regulation_ids": ["GDPR-Art5", "GDPR-Art7", "GDPR-Art17", "GDPR-Art32"],
        "violations": [
            {
                "id": "GDPR-Art7",
                "description": "No consent mechanism — data is collected without user consent or a consent banner",
                "severity": "critical",
                "keywords": ["consent", "opt-in", "opt-out", "banner", "permission"],
            },
            {
                "id": "GDPR-Art5",
                "description": "Excessive data collection violates data minimization — keystroke patterns and device fingerprints go beyond what's necessary",
                "severity": "high",
                "keywords": ["minimization", "excessive", "unnecessary", "proportional", "keystroke", "fingerprint"],
            },
            {
                "id": "GDPR-Art17",
                "description": "No mechanism for users to delete their data — violates right to erasure",
                "severity": "critical",
                "keywords": ["erasure", "delete", "removal", "forget", "right to be forgotten"],
            },
        ],
    },
    "easy_2": {
        "difficulty": "easy",
        "feature_description": (
            "Feature: Newsletter Signup\n\n"
            "Our website has a newsletter signup form that pre-checks the 'Subscribe to marketing emails' "
            "checkbox by default. The form collects name, email, phone number, home address, date of birth, "
            "and employer name. Once subscribed, there is no unsubscribe link in the emails. The privacy "
            "policy is a 50-page legal document linked in the footer with 6pt font."
        ),
        "applicable_regulation_ids": ["GDPR-Art5", "GDPR-Art7", "GDPR-Art13"],
        "violations": [
            {
                "id": "GDPR-Art7",
                "description": "Pre-checked consent box is not valid consent under GDPR — consent must be freely given via affirmative action",
                "severity": "critical",
                "keywords": ["pre-checked", "pre-ticked", "default", "opt-out", "affirmative", "active consent"],
            },
            {
                "id": "GDPR-Art5",
                "description": "Collecting phone, home address, DOB, and employer for a newsletter violates data minimization",
                "severity": "high",
                "keywords": ["minimization", "excessive", "unnecessary", "phone", "address", "date of birth"],
            },
            {
                "id": "GDPR-Art7",
                "description": "No unsubscribe mechanism — users cannot withdraw consent",
                "severity": "critical",
                "keywords": ["unsubscribe", "withdraw", "opt-out", "revoke", "withdraw consent"],
            },
        ],
    },

    # ═══════════════════════════════════════════════════════════════════
    # MEDIUM TASKS — Multiple regulations, subtler violations
    # ═══════════════════════════════════════════════════════════════════
    "medium_1": {
        "difficulty": "medium",
        "feature_description": (
            "Feature: Patient Portal for Telehealth App\n\n"
            "Our telehealth app allows patients to video-call doctors and share medical records. "
            "Patient records including diagnoses, prescriptions, and lab results are stored in the app. "
            "The app shares anonymized usage statistics with a third-party analytics provider, but the "
            "anonymization process only removes the patient's name (keeping age, ZIP code, diagnosis, and "
            "visit dates). Doctors can access any patient's records without role-based restrictions. "
            "The app sends appointment reminders via unencrypted SMS that include the doctor's name and "
            "reason for visit. Data backups are performed weekly but are stored on a developer's personal "
            "laptop. There is no audit log for who accesses patient records. The consent form is available "
            "only in English."
        ),
        "applicable_regulation_ids": [
            "HIPAA-Privacy", "HIPAA-Security", "HIPAA-Breach",
            "GDPR-Art5", "GDPR-Art7", "GDPR-Art25", "GDPR-Art32"
        ],
        "violations": [
            {
                "id": "HIPAA-Privacy",
                "description": "Inadequate anonymization — keeping age, ZIP, diagnosis, and dates can allow re-identification (violates de-identification standard)",
                "severity": "critical",
                "keywords": ["anonymization", "de-identification", "re-identification", "quasi-identifier", "zip", "age"],
            },
            {
                "id": "HIPAA-Security",
                "description": "No role-based access control — doctors can access any patient's records without restrictions",
                "severity": "critical",
                "keywords": ["access control", "role-based", "rbac", "authorization", "restriction", "any patient"],
            },
            {
                "id": "HIPAA-Security",
                "description": "Unencrypted SMS containing PHI (doctor name + reason for visit) violates transmission security requirements",
                "severity": "high",
                "keywords": ["unencrypted", "sms", "transmission", "encrypt", "plaintext", "phi"],
            },
            {
                "id": "HIPAA-Security",
                "description": "Backups stored on developer's personal laptop — violates physical and technical safeguard requirements",
                "severity": "critical",
                "keywords": ["backup", "personal laptop", "physical safeguard", "secure storage", "developer"],
            },
            {
                "id": "HIPAA-Security",
                "description": "No audit log for record access — violates audit control requirements",
                "severity": "high",
                "keywords": ["audit", "log", "access log", "tracking", "monitoring", "who accessed"],
            },
        ],
    },
    "medium_2": {
        "difficulty": "medium",
        "feature_description": (
            "Feature: Employee Wellness Platform\n\n"
            "Our company wellness platform tracks employee health metrics including heart rate, "
            "sleep patterns, stress levels, and mental health questionnaire responses. HR managers "
            "have full access to individual employee health data to 'identify at-risk employees.' "
            "The platform integrates with the company's performance review system, and managers can "
            "see health data alongside performance scores. Data is retained for 10 years after an "
            "employee leaves. The platform uses a third-party cloud provider in a country without "
            "an adequacy decision. Employees must agree to data collection as part of their employment "
            "contract with no separate opt-out. The privacy notice mentions 'data may be shared with "
            "partners' without specifying who these partners are."
        ),
        "applicable_regulation_ids": [
            "GDPR-Art5", "GDPR-Art6", "GDPR-Art7", "GDPR-Art13", "GDPR-Art25",
            "HIPAA-Privacy"
        ],
        "violations": [
            {
                "id": "GDPR-Art7",
                "description": "Consent bundled with employment contract is not freely given — employees cannot refuse without risking their job",
                "severity": "critical",
                "keywords": ["freely given", "employment", "bundled", "contract", "coerced", "power imbalance", "opt-out"],
            },
            {
                "id": "GDPR-Art5",
                "description": "Linking health data to performance reviews violates purpose limitation — health data collected for wellness used for employment decisions",
                "severity": "critical",
                "keywords": ["purpose limitation", "performance review", "incompatible purpose", "employment decision", "health data"],
            },
            {
                "id": "GDPR-Art5",
                "description": "10-year retention after employment ends violates storage limitation — excessive retention period",
                "severity": "high",
                "keywords": ["retention", "storage limitation", "10 year", "excessive", "after employment", "how long"],
            },
            {
                "id": "GDPR-Art13",
                "description": "Vague 'partners' disclosure without specifics violates transparency — must name recipients or categories",
                "severity": "medium",
                "keywords": ["transparency", "partners", "vague", "specific", "recipients", "categories", "who"],
            },
            {
                "id": "GDPR-Art25",
                "description": "HR managers having full access to individual health data violates data protection by default — should use aggregated/anonymized data",
                "severity": "high",
                "keywords": ["data protection by default", "full access", "individual", "aggregate", "anonymize", "minimization"],
            },
        ],
    },

    # ═══════════════════════════════════════════════════════════════════
    # HARD TASKS — Multiple regulations, ambiguous, many violations
    # ═══════════════════════════════════════════════════════════════════
    "hard_1": {
        "difficulty": "hard",
        "feature_description": (
            "Feature: AI-Powered Medical Insurance Claims Processor\n\n"
            "Our system uses an LLM to automatically review and approve/deny medical insurance claims. "
            "The system ingests full medical records including doctor's notes, lab results, imaging reports, "
            "and prescription history. The AI model was trained on historical claims data from 5 years of "
            "records, and the training data was not scrubbed of personal identifiers. The model outputs "
            "a binary approve/deny decision with a confidence score but no explanation of the reasoning. "
            "Denied claims go into a queue reviewed by a single clerk who processes 500 claims per day. "
            "The system uses a shared API key across all service instances. Access to the claims database "
            "is granted via a single admin account shared by the engineering team. The system has no "
            "mechanism to handle data subject access requests. Error logs containing patient data are "
            "shipped to a third-party log aggregation service. The system's uptime SLA is 95% but there "
            "is no documented disaster recovery plan. Model retraining happens ad-hoc with no change "
            "management process. The consent form says 'by submitting a claim, you agree to automated "
            "processing' buried on page 14 of the terms of service."
        ),
        "applicable_regulation_ids": [
            "HIPAA-Privacy", "HIPAA-Security", "HIPAA-Breach",
            "GDPR-Art5", "GDPR-Art6", "GDPR-Art7", "GDPR-Art13",
            "GDPR-Art17", "GDPR-Art25", "GDPR-Art32",
            "SOC2-CC6", "SOC2-CC7", "SOC2-CC8"
        ],
        "violations": [
            {
                "id": "HIPAA-Privacy",
                "description": "Training data contains personal identifiers — PHI used for model training without de-identification violates minimum necessary standard",
                "severity": "critical",
                "keywords": ["training data", "identifiers", "de-identification", "phi", "minimum necessary", "scrub"],
            },
            {
                "id": "GDPR-Art13",
                "description": "No explanation for AI decisions — automated processing of claims without meaningful information about the logic involved",
                "severity": "critical",
                "keywords": ["explanation", "explainability", "reasoning", "automated decision", "logic", "transparent", "black box"],
            },
            {
                "id": "SOC2-CC6",
                "description": "Shared API key and shared admin account violate credential management and individual accountability requirements",
                "severity": "critical",
                "keywords": ["shared", "api key", "admin account", "credential", "individual", "accountability", "shared password"],
            },
            {
                "id": "HIPAA-Security",
                "description": "Error logs containing patient data sent to third-party without proper safeguards — PHI exposure via logging",
                "severity": "high",
                "keywords": ["error log", "log", "third-party", "patient data", "phi", "logging", "leak"],
            },
            {
                "id": "GDPR-Art17",
                "description": "No mechanism to handle data subject access requests — cannot fulfill erasure or access rights",
                "severity": "high",
                "keywords": ["access request", "data subject", "erasure", "dsar", "right to access", "mechanism"],
            },
            {
                "id": "SOC2-CC7",
                "description": "No documented disaster recovery plan despite processing critical healthcare claims — inadequate system operations controls",
                "severity": "high",
                "keywords": ["disaster recovery", "drp", "business continuity", "incident response", "downtime"],
            },
            {
                "id": "SOC2-CC8",
                "description": "Ad-hoc model retraining with no change management process — model changes can affect claim decisions without review or approval",
                "severity": "high",
                "keywords": ["change management", "ad-hoc", "retraining", "approval", "review process", "documented"],
            },
        ],
    },
    "hard_2": {
        "difficulty": "hard",
        "feature_description": (
            "Feature: Smart Building Access & Monitoring System\n\n"
            "Our system manages building access for a hospital campus. It uses facial recognition at "
            "all entrances, tracking employee and patient movements throughout the facility. The facial "
            "recognition data is stored alongside employee HR records and patient medical records in a "
            "single database. Visitors are scanned upon entry without advance notice. The system generates "
            "a 'contact tracing' report showing who was near whom, which is accessible by department heads. "
            "Facial recognition templates are backed up to a cloud provider using the vendor's default "
            "encryption settings (not reviewed by security team). Access badges can be cloned by any "
            "security desk staff without logging. The system retains movement data for 5 years for "
            "'security purposes' without documented retention justification. Employees were informed "
            "about badge access but not about facial recognition tracking. The system has a single "
            "point of failure — if the main server goes down, all doors lock open as a 'safety' measure, "
            "granting unrestricted access to all areas including pharmacy and records rooms. There is no "
            "regular penetration testing or security audit schedule."
        ),
        "applicable_regulation_ids": [
            "HIPAA-Privacy", "HIPAA-Security", "HIPAA-Breach",
            "GDPR-Art5", "GDPR-Art6", "GDPR-Art7", "GDPR-Art13",
            "GDPR-Art25", "GDPR-Art32",
            "SOC2-CC6", "SOC2-CC7"
        ],
        "violations": [
            {
                "id": "GDPR-Art7",
                "description": "Facial recognition deployed without informed consent — employees not told about biometric tracking, visitors scanned without notice",
                "severity": "critical",
                "keywords": ["consent", "facial recognition", "biometric", "informed", "notice", "visitors", "without"],
            },
            {
                "id": "HIPAA-Privacy",
                "description": "Patient medical records co-mingled with facial recognition data and HR records in single database — violates minimum necessary and data segregation",
                "severity": "critical",
                "keywords": ["co-mingled", "single database", "segregation", "minimum necessary", "combined", "mixed", "together"],
            },
            {
                "id": "HIPAA-Privacy",
                "description": "Contact tracing reports accessible by department heads reveal patient and employee proximity data — unauthorized PHI disclosure",
                "severity": "high",
                "keywords": ["contact tracing", "department head", "proximity", "disclosure", "unauthorized", "who was near"],
            },
            {
                "id": "SOC2-CC6",
                "description": "Badge cloning without logging violates access control and audit requirements — no accountability for credential duplication",
                "severity": "high",
                "keywords": ["badge", "clone", "logging", "audit", "accountability", "without logging", "access control"],
            },
            {
                "id": "GDPR-Art32",
                "description": "Vendor default encryption not reviewed by security team — failure to implement appropriate technical measures for biometric data",
                "severity": "high",
                "keywords": ["encryption", "default", "vendor", "security review", "appropriate", "biometric"],
            },
            {
                "id": "SOC2-CC7",
                "description": "Doors lock open on server failure, granting unrestricted access to pharmacy and records — catastrophic fail-open design",
                "severity": "critical",
                "keywords": ["fail-open", "lock open", "unrestricted", "pharmacy", "records", "single point of failure", "server down"],
            },
            {
                "id": "GDPR-Art5",
                "description": "5-year movement data retention without documented justification violates storage limitation principle",
                "severity": "medium",
                "keywords": ["retention", "5 year", "storage limitation", "justification", "movement data", "excessive"],
            },
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# TASK DEFINITIONS (which scenarios belong to which task)
# ─────────────────────────────────────────────────────────────────────────────

TASKS = {
    "easy": {
        "description": "Identify obvious GDPR violations in a simple product feature",
        "scenario_ids": ["easy_1", "easy_2"],
        "max_steps": 8,
    },
    "medium": {
        "description": "Identify violations across GDPR and HIPAA in a healthcare/enterprise product",
        "scenario_ids": ["medium_1", "medium_2"],
        "max_steps": 12,
    },
    "hard": {
        "description": "Identify violations across GDPR, HIPAA, and SOC2 in a complex AI/IoT system",
        "scenario_ids": ["hard_1", "hard_2"],
        "max_steps": 15,
    },
}


class ComplianceEnvironment(Environment):
    """Regulatory Compliance Checker Environment.
    
    The agent receives a product feature description and must identify
    regulatory violations, classify their severity, and suggest remediations.
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = ComplianceState()
        self._scenario: Dict = {}
        self._found_violation_ids: List[str] = []
        self._step_rewards: List[float] = []
        self._max_steps: int = 10
        self._task_id: str = "easy"

    def reset(self, seed=None, episode_id=None, **kwargs) -> ComplianceObservation:
        """Start a new compliance audit episode."""
        self._task_id = kwargs.get("task_id", "easy")
        if self._task_id not in TASKS:
            self._task_id = "easy"

        task = TASKS[self._task_id]
        self._max_steps = task["max_steps"]

        # Pick a random scenario from the task
        scenario_id = random.choice(task["scenario_ids"])
        if seed is not None:
            random.seed(seed)
            scenario_id = task["scenario_ids"][seed % len(task["scenario_ids"])]

        self._scenario = SCENARIOS[scenario_id]
        self._found_violation_ids = []
        self._step_rewards = []

        self._state = ComplianceState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            task_id=self._task_id,
            difficulty=self._scenario["difficulty"],
            total_violations=len(self._scenario["violations"]),
            found_violations=0,
        )

        # Build the regulation text the agent sees
        reg_texts = []
        for reg_id in self._scenario["applicable_regulation_ids"]:
            if reg_id in REGULATION_EXCERPTS:
                reg_texts.append(REGULATION_EXCERPTS[reg_id])

        return ComplianceObservation(
            done=False,
            reward=None,
            task_id=self._task_id,
            feature_description=self._scenario["feature_description"],
            applicable_regulations=reg_texts,
            findings_so_far=[],
            remaining_violations=len(self._scenario["violations"]),
            feedback="Audit started. Review the feature description and identify regulatory violations.",
            max_steps_remaining=self._max_steps,
        )

    def step(self, action: ComplianceAction, timeout_s=None, **kwargs) -> ComplianceObservation:
        """Process an agent's compliance finding submission."""
        self._state.step_count += 1
        steps_remaining = self._max_steps - self._state.step_count

        # Score this finding against known violations
        reward, feedback, matched = self._grade_finding(action)
        self._step_rewards.append(reward)

        if matched and matched not in self._found_violation_ids:
            self._found_violation_ids.append(matched)
            self._state.found_violations = len(self._found_violation_ids)

        remaining = len(self._scenario["violations"]) - len(self._found_violation_ids)
        done = remaining <= 0 or steps_remaining <= 0

        # Build findings history for observation
        findings_list = []
        for vid in self._found_violation_ids:
            for v in self._scenario["violations"]:
                if v["id"] == vid or self._violation_key(v) in self._found_violation_ids:
                    findings_list.append({
                        "violation_id": v["id"],
                        "description": v["description"],
                        "severity": v["severity"],
                    })
                    break

        # Calculate episode reward
        if done:
            episode_score = len(self._found_violation_ids) / len(self._scenario["violations"])
            # Bonus for severity accuracy (average of step rewards)
            if self._step_rewards:
                avg_quality = sum(self._step_rewards) / len(self._step_rewards)
                final_reward = 0.7 * episode_score + 0.3 * avg_quality
            else:
                final_reward = episode_score
            final_reward = min(max(final_reward, 0.0), 1.0)
        else:
            final_reward = reward

        reg_texts = []
        for reg_id in self._scenario["applicable_regulation_ids"]:
            if reg_id in REGULATION_EXCERPTS:
                reg_texts.append(REGULATION_EXCERPTS[reg_id])

        return ComplianceObservation(
            done=done,
            reward=round(final_reward, 4),
            task_id=self._task_id,
            feature_description=self._scenario["feature_description"],
            applicable_regulations=reg_texts,
            findings_so_far=findings_list,
            remaining_violations=remaining,
            feedback=feedback,
            max_steps_remaining=max(0, steps_remaining),
        )

    @property
    def state(self) -> ComplianceState:
        return self._state

    # ─────────────────────────────────────────────────────────────────
    # GRADING LOGIC
    # ─────────────────────────────────────────────────────────────────

    def _violation_key(self, violation: Dict) -> str:
        """Create unique key for a violation."""
        return f"{violation['id']}:{violation['description'][:30]}"

    def _grade_finding(self, action: ComplianceAction) -> tuple:
        """Grade a single finding against known violations.
        
        Returns: (reward, feedback_message, matched_violation_key_or_None)
        """
        best_match = None
        best_score = 0.0
        best_violation = None

        for violation in self._scenario["violations"]:
            vkey = self._violation_key(violation)

            # Skip already found
            if vkey in self._found_violation_ids:
                continue

            score = self._match_score(action, violation)
            if score > best_score:
                best_score = score
                best_match = vkey
                best_violation = violation

        if best_score >= 0.4:
            # Matched a violation
            severity_correct = (
                action.severity.lower().strip() == best_violation["severity"].lower().strip()
            )
            regulation_correct = (
                best_violation["id"].lower() in action.violation_id.lower()
                or action.violation_id.lower() in best_violation["id"].lower()
            )

            # Build reward
            reward = 0.4  # base for finding a real violation
            if regulation_correct:
                reward += 0.2
            if severity_correct:
                reward += 0.2
            if len(action.suggested_fix.strip()) > 20:
                reward += 0.1
            if best_score >= 0.6:
                reward += 0.1

            reward = min(reward, 1.0)

            feedback_parts = [f"✓ Valid finding identified."]
            if regulation_correct:
                feedback_parts.append("Correct regulation cited.")
            else:
                feedback_parts.append(f"Regulation citation could be more specific (expected {best_violation['id']}).")
            if severity_correct:
                feedback_parts.append("Severity assessment is accurate.")
            else:
                feedback_parts.append(f"Severity should be '{best_violation['severity']}', not '{action.severity}'.")

            return reward, " ".join(feedback_parts), best_match
        else:
            # No match — false positive or too vague
            feedback = (
                "✗ Finding not matched to a known violation. "
                "Be more specific about which regulation clause is violated and what part of the feature causes it."
            )
            return 0.0, feedback, None

    def _match_score(self, action: ComplianceAction, violation: Dict) -> float:
        """Score how well an action matches a known violation.
        
        Uses keyword matching against the violation's keyword list
        and the action's description text.
        """
        action_text = (
            f"{action.violation_description} {action.suggested_fix} {action.violation_id}"
        ).lower()

        keywords = violation.get("keywords", [])
        if not keywords:
            return 0.0

        matched_keywords = sum(1 for kw in keywords if kw.lower() in action_text)
        keyword_score = matched_keywords / len(keywords)

        # Also check if the regulation ID matches
        reg_match = 1.0 if violation["id"].lower() in action.violation_id.lower() else 0.0

        # Weighted combination
        return 0.7 * keyword_score + 0.3 * reg_match
