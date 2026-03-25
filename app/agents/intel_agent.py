from typing import Any, Dict

from app.models import Alert
from app.tools.ip_reputation import IPReputationTool
from app.tools.kb_search import KbSearchTool


class IntelAgent:
    def __init__(self, ip_tool: IPReputationTool, kb_tool: KbSearchTool):
        self.ip_tool = ip_tool
        self.kb_tool = kb_tool

    def run(self, alert: Alert) -> Dict[str, Any]:
        ip_result = self.ip_tool.lookup(alert.source_ip)
        kb_query = f"{alert.summary} {alert.user} {alert.destination_host} {alert.source_ip}"
        kb_result = self.kb_tool.query(kb_query, top_k=3)
        return {
            "ip_reputation": ip_result,
            "kb_context": kb_result,
        }
