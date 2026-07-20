import { env } from "./env";

export type ApiEnvelope<T> = { data: T; meta: Record<string, unknown> | null };

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) { super(message); }
}

async function request<T>(path: string, init: RequestInit, retry: boolean): Promise<T> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { Accept: "application/json", "Content-Type": "application/json", ...init.headers },
  });
  const cannotRefresh = ["/auth/login", "/auth/register", "/auth/refresh"].includes(path);
  if (response.status === 401 && retry && !cannotRefresh) {
    const refreshed = await fetch(`${env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
      method: "POST", credentials: "include", headers: { Accept: "application/json" },
    });
    if (refreshed.ok) return request(path, init, false);
  }
  if (response.status === 204) return undefined as T;
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { error?: { message?: string } } | null;
    throw new ApiError(response.status, body?.error?.message ?? "The service request failed");
  }
  return ((await response.json()) as ApiEnvelope<T>).data;
}

export function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  return request<T>(path, init, true);
}
