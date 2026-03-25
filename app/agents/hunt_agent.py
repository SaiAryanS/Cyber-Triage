from typing import Any, Dict

from app.tools.log_analyzer import LogAnalyzerTool


class HuntAgent:
    def __init__(self, log_tool: LogAnalyzerTool):
        self.log_tool = log_tool

    def run(self, log_text: str) -> Dict[str, Any]:
        return {
            "lateral_movement_analysis": self.log_tool.analyze(log_text),
        }
