import json
import uuid
from typing import Any, Dict, List

from app.llm_client import LocalLLMClient
from app.memory import IncidentMemory
from app.models import Alert, TriageResult
from app.agents.planner_agent import PlannerAgent
from app.agents.intel_agent import IntelAgent
from app.agents.hunt_agent import HuntAgent


class CoordinatorAgent:
    def __init__(
        self,
        planner: PlannerAgent,
        intel_agent: IntelAgent,
        hunt_agent: HuntAgent,
        memory: IncidentMemory,
        llm: LocalLLMClient,
    ):
        self.planner = planner
        self.intel_agent = intel_agent
        self.hunt_agent = hunt_agent
        self.memory = memory
        self.llm = llm

    def triage(self, alert: Alert, log_text: str) -> TriageResult:
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        self.memory.create_incident(incident_id, alert.alert_id, alert.summary)

        plan = self.planner.build_plan(alert)
        for step in plan.steps:
            self.memory.add_step_event(incident_id, step.step_id, step.title, "planned", step.rationale)

        intel = self.intel_agent.run(alert)
        self.memory.add_step_event(incident_id, "S1", "Assess external source IP risk", "completed", json.dumps(intel["ip_reputation"]))
        self.memory.add_step_event(incident_id, "S3", "Retrieve relevant containment playbook", "completed", json.dumps(intel["kb_context"]))

        hunt = self.hunt_agent.run(log_text)
        self.memory.add_step_event(
            incident_id,
            "S2",
            "Check for lateral movement indicators",
            "completed",
            json.dumps(hunt["lateral_movement_analysis"]),
        )

        severity, confidence = self._score(intel, hunt)
        actions = self._recommend_actions(severity, intel, hunt)
        findings = {**intel, **hunt, "plan": [step.__dict__ for step in plan.steps]}

        llm_summary = self._generate_llm_summary(alert, findings, severity, confidence, actions)
        findings["llm_summary"] = llm_summary

        self.memory.update_incident_outcome(incident_id, severity, confidence, status="triaged")
        self.memory.add_step_event(incident_id, "S4", "Decide severity and first-response actions", "completed", llm_summary)

        return TriageResult(
            incident_id=incident_id,
            severity=severity,
            confidence=confidence,
            findings=findings,
            immediate_actions=actions,
        )

    def _score(self, intel: Dict[str, Any], hunt: Dict[str, Any]):
        ip_score = int(intel.get("ip_reputation", {}).get("score", 0))
        lateral_score = int(hunt.get("lateral_movement_analysis", {}).get("score", 0))
        blended = int((ip_score * 0.45) + (lateral_score * 0.55))

        severity = "critical" if blended >= 80 else "high" if blended >= 60 else "medium" if blended >= 35 else "low"
        confidence = round(min(0.99, 0.45 + (blended / 200)), 2)
        return severity, confidence

    def _recommend_actions(self, severity: str, intel: Dict[str, Any], hunt: Dict[str, Any]) -> List[str]:
        actions = [
            "Preserve volatile evidence (process list, active connections, auth sessions).",
            "Open incident ticket and notify SOC on-call.",
        ]
        if severity in {"critical", "high"}:
            actions.append("Isolate suspected host from network while maintaining forensic access.")
            actions.append("Temporarily disable or reset potentially compromised credentials.")
        if intel.get("ip_reputation", {}).get("risk") in {"high", "medium"}:
            actions.append("Block suspicious source IP at perimeter firewall/WAF for immediate containment.")
        if hunt.get("lateral_movement_analysis", {}).get("risk") in {"high", "medium"}:
            actions.append("Hunt adjacent hosts for same IoCs and remote-service creation events.")
        return actions

    def _generate_llm_summary(
        self,
        alert: Alert,
        findings: Dict[str, Any],
        severity: str,
        confidence: float,
        actions: List[str],
    ) -> str:
        prompt = [
            {
                "role": "system",
                "content": "You are a SOC tier-1 triage assistant. Provide concise, actionable incident summary in 5 bullet points.",
            },
            {
                "role": "user",
                "content": (
                    f"Alert: {alert.summary}\n"
                    f"User: {alert.user}\n"
                    f"Source IP: {alert.source_ip}\n"
                    f"Destination Host: {alert.destination_host}\n"
                    f"Preliminary severity: {severity}\n"
                    f"Confidence: {confidence}\n"
                    f"Findings: {json.dumps(findings)[:3000]}\n"
                    f"Actions: {actions}"
                ),
            },
        ]
        try:
            return self.llm.chat(prompt, temperature=0.1)
        except Exception as exc:
            return f"LLM summary unavailable: {exc}"
