import { api, clearTokens, saveTokens } from "../api";

export async function registerAccount(email, password, role) {
  return api("auth/register/", {
    method: "POST",
    body: JSON.stringify({ email, password, role }),
  }, false);
}

export async function loginAndStoreTokens(email, password) {
  const result = await api("auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }, false);
  saveTokens(result.tokens);
  localStorage.setItem("currentUser", JSON.stringify(result.user));
  return result.user;
}

export async function logoutFromApi() {
  const refresh = localStorage.getItem("humaisenRefresh");
  try {
    if (refresh) {
      await api("auth/logout/", { method: "POST", body: JSON.stringify({ refresh }) }, false);
    }
  } finally {
    clearTokens();
    localStorage.removeItem("currentUser");
  }
}
