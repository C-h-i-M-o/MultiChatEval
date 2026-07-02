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

export interface AuthCredentials {
  username: string;
  password: string;
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

async function postJson<T>(url: string, payload?: unknown): Promise<T> {
  const headers: HeadersInit = {
    Accept: "application/json"
  };
  const init: RequestInit = {
    method: "POST",
    credentials: "include",
    headers
  };

  if (payload !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(payload);
  }

  const response = await fetch(url, init);

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response): Promise<string> {
  const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  return formatErrorDetail(payload?.detail) || `请求失败：${response.status}`;
}

function formatErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail.map(formatValidationIssue).filter((message) => message.length > 0);
    return messages.length > 0 ? messages.join("；") : null;
  }

  if (detail && typeof detail === "object" && "msg" in detail) {
    return formatValidationIssue(detail);
  }

  return null;
}

function formatValidationIssue(issue: unknown): string {
  if (!issue || typeof issue !== "object") {
    return "";
  }

  const record = issue as { loc?: unknown; msg?: unknown };
  const field = Array.isArray(record.loc) ? record.loc.at(-1) : null;
  const message = typeof record.msg === "string" ? record.msg : "";

  if (field === "username" && message.includes("at least 3")) {
    return "用户名长度不能少于 3 位";
  }
  if (field === "password" && message.includes("at least 8")) {
    return "密码长度不能少于 8 位";
  }

  return message;
}

export async function getHealthStatus(): Promise<HealthStatus> {
  return fetchJson<HealthStatus>("/api/health");
}

export async function getCurrentUser(): Promise<UserProfile> {
  return fetchJson<UserProfile>("/api/auth/me");
}

export async function loginUser(credentials: AuthCredentials): Promise<UserProfile> {
  return postJson<UserProfile>("/api/auth/login", credentials);
}

export async function registerUser(credentials: AuthCredentials): Promise<UserProfile> {
  return postJson<UserProfile>("/api/auth/register", credentials);
}

export async function logoutUser(): Promise<void> {
  await postJson<void>("/api/auth/logout");
}
