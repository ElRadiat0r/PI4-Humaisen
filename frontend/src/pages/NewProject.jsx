import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser } from "../auth";
import { createProject, DOMAINS } from "../projects";

export default function NewProject() {
  const navigate = useNavigate();
  const user = getCurrentUser();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [domain, setDomain] = useState(DOMAINS[0]);
  const [attachments, setAttachments] = useState([]);
  const [consentProcessing, setConsentProcessing] = useState(false);
  const [consentReuse, setConsentReuse] = useState(false);

  function handleFiles(e) {
    setAttachments(Array.from(e.target.files).map((f) => f.name));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const project = createProject({
      owner: user.email,
      title,
      description,
      domain,
      attachments,
      consentProcessing,
      consentReuse,
    });
    navigate(`/client/projects/${project.id}`);
  }

  return (
    <div style={{ maxWidth: 560, margin: "24px auto", padding: "0 16px" }}>
      <h1>New Dossier Projet</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <input placeholder="Title" value={title}
          onChange={(e) => setTitle(e.target.value)} required />

        <textarea placeholder="Describe your problem" rows={6} value={description}
          onChange={(e) => setDescription(e.target.value)} required />

        <select value={domain} onChange={(e) => setDomain(e.target.value)}>
          {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>

        <div>
          <label>Attachments (optional): </label>
          <input type="file" multiple onChange={handleFiles} />
        </div>

        <label>
          <input type="checkbox" checked={consentProcessing}
            onChange={(e) => setConsentProcessing(e.target.checked)} required />
          {" "}I agree that my dossier is processed by the platform (required).
        </label>

        <label>
          <input type="checkbox" checked={consentReuse}
            onChange={(e) => setConsentReuse(e.target.checked)} />
          {" "}I agree that my case may be reused anonymously (optional).
        </label>

        <button type="submit">Create dossier</button>
      </form>
    </div>
  );
}