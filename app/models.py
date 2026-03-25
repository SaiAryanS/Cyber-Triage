from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Alert:
    alert_id: str
    source_ip: str
    destination_host: str
    user: str
    summary: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanStep:
    step_id: str
    title: str
    rationale: str


@dataclass
class Plan:
    incident_type: str
    steps: List[PlanStep]


@dataclass
class TriageResult:
    incident_id: str
    severity: str
    confidence: float
    findings: Dict[str, Any]
    immediate_actions: List[str]
