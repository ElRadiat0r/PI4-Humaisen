const KEY = "projects";

export const DOMAINS = ["Engineering", "Finance", "Health", "Law", "Marketing", "Other"];

function readAll() {
  const saved = localStorage.getItem(KEY);
  return saved ? JSON.parse(saved) : [];
}

function writeAll(list) {
  localStorage.setItem(KEY, JSON.stringify(list));
}

export function createProject({ owner, title, description, domain, attachments, consentProcessing, consentReuse }) {
  const project = {
    id: String(Date.now()),
    owner,
    title,
    description,
    domain,
    attachments, 
    consentProcessing,
    consentReuse,
    status: "submitted",
    timeline: [{ date: new Date().toISOString(), event: "Dossier created" }],
  };
  writeAll([...readAll(), project]);
  return project;
}

export function listProjects(owner) {
  return readAll()
    .filter((p) => p.owner === owner)
    .reverse(); 
}

export function getProject(id) {
  return readAll().find((p) => p.id === id) || null;
}
export function listAllProjects() {
  return readAll().reverse();
}