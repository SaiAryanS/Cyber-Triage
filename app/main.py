import argparse
import json

from app.models import Alert
from app.runtime import triage_from_inputs


def load_alert(path: str) -> Alert:
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return Alert(
        alert_id=payload["alert_id"],
        source_ip=payload["source_ip"],
        destination_host=payload["destination_host"],
        user=payload["user"],
        summary=payload["summary"],
        raw=payload,
    )


def load_logs(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def run(alert_path: str, logs_path: str) -> None:
    alert = load_alert(alert_path)
    logs = load_logs(logs_path)

    result = triage_from_inputs(alert, logs)
    print(json.dumps(result.__dict__, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Cyber-Defense Triage First Responder")
    parser.add_argument("--alert", required=True, help="Path to alert JSON file")
    parser.add_argument("--logs", required=True, help="Path to system/security logs")
    args = parser.parse_args()
    run(args.alert, args.logs)


if __name__ == "__main__":
    main()
