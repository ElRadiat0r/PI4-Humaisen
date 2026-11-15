const USERS_KEY = "users";
const CURRENT_KEY = "currentUser";

export const homeForRole = { client: "/client", humai: "/humai", admin: "/admin" };

function readUsers() {
  const saved = localStorage.getItem(USERS_KEY);
  if (saved) return JSON.parse(saved);
  const defaults = [{ email: "admin@test.com", password: "admin123", role: "admin" }];
  localStorage.setItem(USERS_KEY, JSON.stringify(defaults));
  return defaults;
}

export function register(email, password, role) {
  const users = readUsers();
  if (users.some((u) => u.email === email)) {
    return { ok: false, error: "This email is already registered." };
  }
  users.push({ email, password, role });
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
  return { ok: true };
}

export function login(email, password) {
  const user = readUsers().find((u) => u.email === email && u.password === password);
  if (!user) return { ok: false, error: "Wrong email or password." };
  const current = { email: user.email, role: user.role };
  localStorage.setItem(CURRENT_KEY, JSON.stringify(current));
  return { ok: true, user: current };
}

export function logout() {
  localStorage.removeItem(CURRENT_KEY);
}

export function getCurrentUser() {
  const saved = localStorage.getItem(CURRENT_KEY);
  return saved ? JSON.parse(saved) : null;
}