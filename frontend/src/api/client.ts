
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
