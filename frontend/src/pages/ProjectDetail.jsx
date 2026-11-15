import { Link, useParams } from "react-router-dom";
import { getCurrentUser } from "../auth";
import { getProject } from "../projects";

export default function ProjectDetail() {
  const { id } = useParams();
  const user = getCurrentUser();
  const project = getProject(id);

  if (!project || project.owner !== user.email) {
    return (
      <div style={{ maxWidth: 720, margin: "24px auto" }}>
        <p>Dossier not found.</p>
        <Link to="/client">Back to my dossiers</Link>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 720, margin: "24px auto", padding: "0 16px" }}>
      <Link to="/client">← Back</Link>
      <h1>{project.title}</h1>
      <p><strong>Domain:</strong> {project.domain}</p>
      <p><strong>Status:</strong> {project.status}</p>

      <h3>Problem description</h3>
      <p style={{ whiteSpace: "pre-wrap" }}>{project.description}</p>

      <h3>Attachments</h3>
      {project.attachments.length === 0
        ? <p>None</p>
        : <ul>{project.attachments.map((a) => <li key={a}>{a}</li>)}</ul>}

      <h3>Consent</h3>
      <p>Processing: {project.consentProcessing ? "Yes" : "No"}</p>
      <p>Anonymous reuse: {project.consentReuse ? "Yes" : "No"}</p>

      <h3>Timeline</h3>
      <ul>
        {project.timeline.map((t, i) => (
          <li key={i}>{new Date(t.date).toLocaleString()} — {t.event}</li>
        ))}
      </ul>
    </div>
  );
}