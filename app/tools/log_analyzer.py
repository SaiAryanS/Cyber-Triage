import re
from collections import Counter
from typing import Any, Dict, List


class LogAnalyzerTool:
    LATERAL_PATTERNS = {
        "psexec": re.compile(r"psexec", re.IGNORECASE),
        "wmic_remote": re.compile(r"wmic\\s+/node|process call create", re.IGNORECASE),
        "smb_admin_share": re.compile(r"\\\\[^\\]+\\(admin\$|c\$)", re.IGNORECASE),
        "remote_service_creation": re.compile(r"service\s+created|7045", re.IGNORECASE),
        "multiple_failed_logons": re.compile(r"4625|failed logon|logon failure", re.IGNORECASE),
    }

    def analyze(self, log_text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in log_text.splitlines() if line.strip()]
        counts = Counter()
        evidence: Dict[str, List[str]] = {key: [] for key in self.LATERAL_PATTERNS}

        for line in lines:
            for key, pattern in self.LATERAL_PATTERNS.items():
                if pattern.search(line):
                    counts[key] += 1
                    if len(evidence[key]) < 5:
                        evidence[key].append(line)

        score = min(sum(counts.values()) * 10, 100)
        risk = "high" if score >= 70 else "medium" if score >= 35 else "low"
        return {
            "risk": risk,
            "score": score,
            "counts": dict(counts),
            "evidence": evidence,
            "total_lines": len(lines),
        }
