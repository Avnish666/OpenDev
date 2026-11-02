
const API_URL = import.meta.env.VITE_API_URL;

export interface AuthUser {
  id: number;
  github_id: number;
  username: string;
  avatar_url: string | null;
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    credentials: "include",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Authentication check failed: ${response.status}`);
  }

  return response.json();
}

export function loginWithGitHub() {
  window.location.assign(`${API_URL}/api/auth/github/login`);
}

export async function logoutUser(): Promise<void> {
  const response = await fetch(`${API_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Logout failed: ${response.status}`);
  }
}

export interface Budget { category: string; allocated_cents: number }
export interface Project { id: number; title: string; description: string; github_repo_url: string; funding_goal_cents: number; currency: string; status: string; owner_id: number }
export interface ProjectDetail extends Project { budget: Budget[]; maintainers: AuthUser[]; can_manage: boolean }
export interface Reward { id: number; name: string; description: string; price_cents: number; currency: string; benefits: { title: string; description: string }[]; quantity_limit: number | null; active: boolean }
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { method, credentials: 'include', headers: body === undefined ? {} : { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}). Check form values and try again.`);
  return data as T;
}
