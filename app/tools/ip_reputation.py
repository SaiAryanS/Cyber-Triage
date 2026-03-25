import json
import os
from typing import Any, Dict

import requests


class IPReputationTool:
    def __init__(self, api_key: str, local_feed_path: str = "data/threat_feeds.json"):
        self.api_key = api_key
        self.local_feed_path = local_feed_path

    def lookup(self, ip: str) -> Dict[str, Any]:
        if self.api_key:
            try:
                return self._lookup_abuseipdb(ip)
            except Exception as exc:
                return {
                    "source": "abuseipdb",
                    "error": str(exc),
                    "risk": "unknown",
                    "score": 0,
                }
        return self._lookup_local(ip)

    def _lookup_abuseipdb(self, ip: str) -> Dict[str, Any]:
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {"Key": self.api_key, "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": 90}
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json().get("data", {})
        score = int(data.get("abuseConfidenceScore", 0))
        risk = "high" if score >= 75 else "medium" if score >= 35 else "low"
        return {
            "source": "abuseipdb",
            "ip": ip,
            "score": score,
            "risk": risk,
            "country": data.get("countryCode"),
            "usage_type": data.get("usageType"),
            "isp": data.get("isp"),
        }

    def _lookup_local(self, ip: str) -> Dict[str, Any]:
        if not os.path.exists(self.local_feed_path):
            return {"source": "local_feed", "ip": ip, "score": 0, "risk": "unknown", "match": None}
        with open(self.local_feed_path, "r", encoding="utf-8") as file:
            feed = json.load(file)
        hit = next((entry for entry in feed.get("malicious_ips", []) if entry.get("ip") == ip), None)
        if not hit:
            return {"source": "local_feed", "ip": ip, "score": 5, "risk": "low", "match": None}
        return {
            "source": "local_feed",
            "ip": ip,
            "score": hit.get("score", 90),
            "risk": hit.get("risk", "high"),
            "match": hit,
        }
