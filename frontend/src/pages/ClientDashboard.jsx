import { Link } from "react-router-dom";
import { getCurrentUser } from "../auth";
import { listProjects } from "../projects";

export default function ClientDashboard() {
  const user = getCurrentUser();
  const projects = listProjects(user.email);

  return (
    <div style={{ maxWidth: 720, margin: "24px auto", padding: "0 16px" }}>
      <h1>My Dossiers</h1>
      <Link to="/client/new"><button>+ New Dossier Projet</button></Link>

      {projects.length === 0 && <p>You have no dossier yet.</p>}

      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 12, marginTop: 16 }}>
        {projects.map((p) => (
          <li key={p.id} style={{ border: "1px solid #ccc", borderRadius: 8, padding: 12 }}>
            <h3 style={{ margin: 0 }}>
              <Link to={`/client/projects/${p.id}`}>{p.title}</Link>
            </h3>
            <p style={{ margin: "4px 0" }}>Domain: {p.domain} · Status: {p.status}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}