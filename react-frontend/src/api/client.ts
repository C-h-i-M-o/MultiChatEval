export interface HealthStatus {
  status: "ok";
}

export type UserRole = "user" | "admin";
export type UserStatus = "active" | "disabled";

export interface UserProfile {
  id: number;
  username: string;
  role: UserRole;
  status: UserStatus;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response): Promise<string> {
  const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
  return payload?.detail || `请求失败：${response.status}`;
}

export async function getHealthStatus(): Promise<HealthStatus> {
  return fetchJson<HealthStatus>("/api/health");
}

export async function getCurrentUser(): Promise<UserProfile> {
  return fetchJson<UserProfile>("/api/auth/me");
}
