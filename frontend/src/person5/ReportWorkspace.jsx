import { useEffect, useState } from "react";
import { api, apiList } from "../api";

function currentRole() {
  try {
    return JSON.parse(localStorage.getItem("currentUser") || "{}").role?.toLowerCase();
  } catch {
    return "";
  }
}

export default function ReportWorkspace({ projectId }) {
  const [reports, setReports] = useState([]);
  const [content, setContent] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const humai = currentRole() === "humai";
  const draft = reports.find((report) => report.status === "DRAFT");

  useEffect(() => {
    let active = true;
    api(`reports/?project=${encodeURIComponent(projectId)}`).then((data) => {
      if (!active) return;
      setReports(apiList(data));
      setError("");
    }).catch((err) => {
      if (active) setError(err.message);
    });
    return () => { active = false; };
  }, [projectId]);

  useEffect(() => {
    setContent(draft?.content || null);
  }, [draft]);

  async function generateDraft() {
    try {
      const report = await api("reports/", { method: "POST", body: JSON.stringify({ project: projectId }) });
      setReports((items) => [report, ...items]);
      setContent(report.content);
      setMessage("Draft generated. Review it before validation.");
    } catch (err) {
      setError(err.message);
    }
  }

  function edit(key, value) {
    setContent((current) => ({ ...current, [key]: value }));
  }

  async function saveDraft() {
    try {
      const saved = await api(`reports/${draft.id}/`, { method: "PATCH", body: JSON.stringify({ content }) });
      setReports((items) => items.map((item) => item.id === saved.id ? saved : item));
      setMessage("Draft saved.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function validateDraft() {
    try {
      const saved = await api(`reports/${draft.id}/`, { method: "PATCH", body: JSON.stringify({ content }) });
      const validated = await api(`reports/${saved.id}/validate/`, { method: "POST", body: JSON.stringify({}) });
      setReports((items) => items.map((item) => item.id === validated.id ? validated : item));
      setContent(null);
      setMessage("Validated restitution is now visible to the project owner.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section aria-labelledby="report-workspace-title">
      <h2 id="report-workspace-title">Restitution</h2>
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      {humai && (!draft || draft.status === "VALIDATED") && <button onClick={generateDraft}>Generate a draft version</button>}
      {draft && humai && content && <div>
        <p>Version {draft.version} · {draft.provider} · human review required</p>
        {Object.entries(content).map(([key, value]) => <label key={key} style={{ display: "grid", gap: 4, margin: "12px 0" }}>
          <strong>{key}</strong>
          <textarea rows={Array.isArray(value) ? 4 : 2}
            value={Array.isArray(value) ? value.join("\n") : String(value)}
            onChange={(event) => edit(key, Array.isArray(value) ? event.target.value.split("\n") : event.target.value)} />
        </label>)}
        <button onClick={saveDraft}>Save draft</button>{" "}
        <button onClick={validateDraft}>Validate and deliver</button>
      </div>}
      {reports.filter((report) => report.status === "VALIDATED").map((report) => <article key={report.id}>
        <h3>Version {report.version}</h3>
        <h4>{report.content.overview}</h4>
        {Object.entries(report.content).filter(([key]) => key !== "overview").map(([key, value]) => <div key={key}>
          <strong>{key}</strong>
          <p style={{ whiteSpace: "pre-wrap" }}>{Array.isArray(value) ? value.join("\n") : String(value)}</p>
        </div>)}
      </article>)}
      {reports.length === 0 && !humai && !error && <p>No validated restitution is available yet.</p>}
    </section>
  );
}
