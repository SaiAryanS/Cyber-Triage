from app.agents.coordinator import CoordinatorAgent
from app.agents.hunt_agent import HuntAgent
from app.agents.intel_agent import IntelAgent
from app.agents.planner_agent import PlannerAgent
from app.config import settings
from app.llm_client import LocalLLMClient
from app.memory import IncidentMemory
from app.models import Alert
from app.rag import LocalSecurityRAG
from app.tools.ip_reputation import IPReputationTool
from app.tools.kb_search import KbSearchTool
from app.tools.log_analyzer import LogAnalyzerTool


def build_coordinator() -> CoordinatorAgent:
    rag = LocalSecurityRAG(kb_dir="data/security_kb")
    memory = IncidentMemory(settings.memory_db_path)
    llm = LocalLLMClient(settings.lm_studio_base_url, settings.lm_studio_model)

    planner = PlannerAgent()
    intel = IntelAgent(
        ip_tool=IPReputationTool(api_key=settings.abuseipdb_api_key, local_feed_path="data/threat_feeds.json"),
        kb_tool=KbSearchTool(rag),
    )
    hunt = HuntAgent(LogAnalyzerTool())

    return CoordinatorAgent(
        planner=planner,
        intel_agent=intel,
        hunt_agent=hunt,
        memory=memory,
        llm=llm,
    )


def triage_from_inputs(alert: Alert, logs: str):
    coordinator = build_coordinator()
    return coordinator.triage(alert, logs)
