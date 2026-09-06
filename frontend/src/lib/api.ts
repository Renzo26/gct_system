const BASE_URL = (import.meta.env?.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const res = await fetch(`${BASE_URL}/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (res.status === 401) {
    clearAuth();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Sessão expirada");
  }

  // Sessão válida, mas sem cliente ativo: manda escolher em vez de deslogar.
  if (res.status === 403) {
    const body = await res.clone().json().catch(() => ({}) as { detail?: string });
    if (body?.detail === "Nenhum cliente selecionado") {
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_workshop");
        window.location.href = "/selecionar-cliente";
      }
      throw new ApiError(403, body.detail);
    }
  }

  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new ApiError(res.status, data.detail ?? `Erro ${res.status}`);
  }

  return data as T;
}

function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("auth_user");
  localStorage.removeItem("auth_workshop");
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
};
