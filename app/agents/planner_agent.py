from app.models import Alert, Plan, PlanStep


class PlannerAgent:
    def build_plan(self, alert: Alert) -> Plan:
        steps = [
            PlanStep(
                step_id="S1",
                title="Assess external source IP risk",
                rationale="Determine if source IP is known-malicious or suspicious.",
            ),
            PlanStep(
                step_id="S2",
                title="Check for lateral movement indicators",
                rationale="Detect spread behavior across hosts, services, or credentials.",
            ),
            PlanStep(
                step_id="S3",
                title="Retrieve relevant containment playbook",
                rationale="Map findings to known response steps in internal KB.",
            ),
            PlanStep(
                step_id="S4",
                title="Decide severity and first-response actions",
                rationale="Produce actionable triage with confidence and next actions.",
            ),
        ]

        if "credential" in alert.summary.lower() or "auth" in alert.summary.lower():
            steps.insert(
                2,
                PlanStep(
                    step_id="S2B",
                    title="Prioritize credential abuse checks",
                    rationale="Alert content indicates potential account compromise.",
                ),
            )

        return Plan(incident_type="cyber_defense_triage", steps=steps)
