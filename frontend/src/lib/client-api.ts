export type ApiResult<T> = { ok: true; data: T } | { ok: false; status: number; error: string };

export async function clientApi<T>(path: string, options: RequestInit = {}): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`/api/backend${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    });
    const contentType = response.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json") ? await response.json() : null;
    if (!response.ok) {
      return { ok: false, status: response.status, error: data?.detail ?? `Request failed (${response.status}).` };
    }
    return { ok: true, data: data as T };
  } catch {
    return { ok: false, status: 0, error: "Unable to reach the application API." };
  }
}
