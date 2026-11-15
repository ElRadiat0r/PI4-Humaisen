import { useState } from "react";
import { listProfiles, setVerified } from "../experts";
import { listAllProjects } from "../projects";

export default function AdminDashboard() {
  const [experts, setExperts] = useState(() => listProfiles());
  const projects = listAllProjects();

  function toggle(email, value) {
    setVerified(email, value);
    setExperts(listProfiles());
  }

  const cell = { border: "1px solid #ccc", padding: 8, textAlign: "left" };

  return (
    <div style={{ maxWidth: 900, margin: "24px auto", padding: "0 16px" }}>
      <h1>Admin</h1>

      <h2>HumAI experts</h2>
      {experts.length === 0 && <p>No expert profile yet.</p>}
      {experts.length > 0 && (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={cell}>Name</th>
              <th style={cell}>Email</th>
              <th style={cell}>Level</th>
              <th style={cell}>Skills</th>
              <th style={cell}>Status</th>
              <th style={cell}>Action</th>
            </tr>
          </thead>
          <tbody>
            {experts.map((x) => (
              <tr key={x.email}>
                <td style={cell}>{x.fullName || "(no name yet)"}</td>
                <td style={cell}>{x.email}</td>
                <td style={cell}>{x.level}</td>
                <td style={cell}>{x.skills.join(", ") || "-"}</td>
                <td style={cell}>{x.verified ? "Verified" : "Pending"}</td>
                <td style={cell}>
                  <button onClick={() => toggle(x.email, !x.verified)}>
                    {x.verified ? "Unverify" : "Verify"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2 style={{ marginTop: 32 }}>All dossiers</h2>
      {projects.length === 0 && <p>No dossier yet.</p>}
      {projects.length > 0 && (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={cell}>Title</th>
              <th style={cell}>Client</th>
              <th style={cell}>Domain</th>
              <th style={cell}>Status</th>
              <th style={cell}>Created</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id}>
                <td style={cell}>{p.title}</td>
                <td style={cell}>{p.owner}</td>
                <td style={cell}>{p.domain}</td>
                <td style={cell}>{p.status}</td>
                <td style={cell}>{new Date(p.timeline[0].date).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}