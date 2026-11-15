const KEY = "experts";

export const LEVELS = ["Confirmed", "Senior", "Expert"];
export const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

function readAll() {
  const saved = localStorage.getItem(KEY);
  return saved ? JSON.parse(saved) : {};
}

function writeAll(all) {
  localStorage.setItem(KEY, JSON.stringify(all));
}

export function getProfile(email) {
  const all = readAll();
  if (!all[email]) {
    all[email] = {
      email,
      fullName: "",
      level: LEVELS[0],
      skills: [],
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      verified: false,
      weekly: [], 
      unavailable: [], 
    };
    writeAll(all);
  }
  return all[email];
}

export function saveProfile(profile) {
  const all = readAll();
  const oldVerified = all[profile.email] ? all[profile.email].verified : false;
  all[profile.email] = { ...profile, verified: oldVerified };
  writeAll(all);
  return all[profile.email];
}

export function listProfiles() {
  return Object.values(readAll());
}

export function setVerified(email, value) {
  const all = readAll();
  if (all[email]) {
    all[email].verified = value;
    writeAll(all);
  }
}