import { useMemo, useState } from "react";
import { submitTriage } from "./api";

const SAMPLE_LOGS = `2026-03-24T22:11:03Z EventID=4625 Failed logon for user=jane.doe src=185.193.88.42
2026-03-24T22:11:11Z EventID=4625 Failed logon for user=jane.doe src=185.193.88.42
2026-03-24T22:12:44Z EventID=7045 Service created name=WinUpdSvc host=FIN-WS-014
2026-03-24T22:13:01Z Command=wmic /node:FIN-SRV-02 process call create "cmd /c whoami"
2026-03-24T22:13:14Z Network access to \\FIN-SRV-02\\ADMIN$ by user=jane.doe
2026-03-24T22:13:20Z ProcessStart psexec.exe target=FIN-SRV-02`;

const initialForm = {
  alert_id: "ALERT-2026-00110",
  source_ip: "185.193.88.42",
  destination_host: "FIN-WS-014",
  user: "jane.doe",
  summary: "Multiple failed authentications followed by remote service execution attempt",
  logs_text: SAMPLE_LOGS,
};

function severityClass(severity) {
  if (severity === "critical") return "sev-critical";
  if (severity === "high") return "sev-high";
  if (severity === "medium") return "sev-medium";
  return "sev-low";
}

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const topKbHits = useMemo(() => result?.findings?.kb_context?.hits || [], [result]);

  const onChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await submitTriage(form);
      setResult(data);
    } catch (submitError) {
      setError(submitError.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="header card">
        <h1>Cyber-Defense Triage Dashboard</h1>
        <p>Minimal SOC first-response dashboard powered by FastAPI + React.</p>
      </header>

      <main className="layout">
        <section className="card">
          <h2>Alert Input</h2>
          <form onSubmit={onSubmit} className="form-grid">
            <label>
              Alert ID
              <input value={form.alert_id} onChange={(event) => onChange("alert_id", event.target.value)} required />
            </label>
            <label>
              Source IP
              <input value={form.source_ip} onChange={(event) => onChange("source_ip", event.target.value)} required />
            </label>
            <label>
              Destination Host
              <input
                value={form.destination_host}
                onChange={(event) => onChange("destination_host", event.target.value)}
                required
              />
            </label>
            <label>
              User
              <input value={form.user} onChange={(event) => onChange("user", event.target.value)} required />
            </label>
            <label className="full">
              Summary
              <input value={form.summary} onChange={(event) => onChange("summary", event.target.value)} required />
            </label>
            <label className="full">
              Logs
              <textarea
                rows={10}
                value={form.logs_text}
                onChange={(event) => onChange("logs_text", event.target.value)}
                required
              />
            </label>
            <button disabled={loading} type="submit" className="btn-primary full">
              {loading ? "Running triage..." : "Run Triage"}
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="card">
          <h2>Triage Output</h2>
          {!result ? (
            <p className="muted">Submit an alert to view severity, confidence, findings, and actions.</p>
          ) : (
            <div className="result-stack">
              <div className="summary-row">
                <span className="chip">Incident: {result.incident_id}</span>
                <span className={`chip ${severityClass(result.severity)}`}>Severity: {result.severity}</span>
                <span className="chip">Confidence: {result.confidence}</span>
              </div>

              <div>
                <h3>Immediate Actions</h3>
                <ul>
                  {result.immediate_actions?.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3>IP Reputation</h3>
                <p>
                  Risk: <strong>{result.findings?.ip_reputation?.risk}</strong> | Score: {result.findings?.ip_reputation?.score}
                </p>
              </div>

              <div>
                <h3>Top KB Evidence</h3>
                {topKbHits.length === 0 ? (
                  <p className="muted">No KB hits found.</p>
                ) : (
                  topKbHits.map((hit, index) => (
                    <article key={`${hit.source}-${index}`} className="hit-card">
                      <div className="hit-meta">
                        <span>{hit.source}</span>
                        <span>{hit.section}</span>
                        <span>score {hit.score}</span>
                      </div>
                      <p>{hit.snippet}</p>
                    </article>
                  ))
                )}
              </div>

              <div>
                <h3>LLM Summary</h3>
                <pre>{result.findings?.llm_summary}</pre>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
