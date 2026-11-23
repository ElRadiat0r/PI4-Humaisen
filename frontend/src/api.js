const API_ROOT = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
const ACCESS_KEY = "humaisenAccess";
const REFRESH_KEY = "humaisenRefresh";

export const getAccessToken = () => localStorage.getItem(ACCESS_KEY);
export const saveTokens = ({ access, refresh }) => {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
};
export const clearTokens = () => {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

function errorMessage(data, fallback) {
  if (typeof data === "string") return data;
  if (data?.detail) return data.detail;
  if (data?.error) return data.error;
  if (data && typeof data === "object") {
    return Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`).join(" · ");
  }
  return fallback;
}

async function send(path, options, accessToken) {
  const headers = new Headers(options.headers || {});
  const isForm = options.body instanceof FormData;
  if (options.body && !isForm && typeof options.body !== "string") {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${API_ROOT}/${path.replace(/^\//, "")}`, { ...options, headers });
  const raw = await response.text();
  const data = raw ? (() => { try { return JSON.parse(raw); } catch { return raw; } })() : null;
  return { response, data };
}

export async function api(path, options = {}, retry = true) {
  const { response, data } = await send(path, options, getAccessToken());
  if (response.status === 401 && retry && localStorage.getItem(REFRESH_KEY)) {
    const refreshed = await send("auth/token/refresh/", {
      method: "POST",
      body: JSON.stringify({ refresh: localStorage.getItem(REFRESH_KEY) }),
    });
    if (refreshed.response.ok && refreshed.data?.access) {
      localStorage.setItem(ACCESS_KEY, refreshed.data.access);
      if (refreshed.data.refresh) localStorage.setItem(REFRESH_KEY, refreshed.data.refresh);
      return api(path, options, false);
    }
    clearTokens();
  }
  if (!response.ok) throw new Error(errorMessage(data, `Request failed (${response.status})`));
  return data;
}

export const apiList = (data) => Array.isArray(data) ? data : (data?.results || []);
