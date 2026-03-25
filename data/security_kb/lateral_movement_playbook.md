# Lateral Movement Triage Playbook

## Detection clues

- Windows Event ID 7045 (service creation)
- Use of PsExec, WMIC remote execution, or suspicious SMB ADMIN$ access
- Multiple failed logins followed by successful privileged actions

## Immediate containment

1. Isolate impacted endpoints while preserving forensic collection capability.
2. Disable or reset potentially compromised credentials.
3. Block identified malicious source IPs and related indicators.
4. Hunt for same IoCs across adjacent hosts and domain controllers.

## Escalation

- Escalate to IR lead if service creation + remote execution is observed on 2+ hosts.
