
const API_URL = import.meta.env.VITE_API_URL;

export interface HealthResponse {
  status: string;
}

export interface DatabaseHealthResponse {
  status: string;
  database: string;
  result: number;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`);

  if (!response.ok) {
    throw new Error("Backend health check failed");
  }

  return response.json();
}

export async function getDatabaseHealth(): Promise<DatabaseHealthResponse> {
  const response = await fetch(`${API_URL}/api/db-health`);

  if (!response.ok) {
    throw new Error("Database health check failed");
  }

  return response.json();
}
