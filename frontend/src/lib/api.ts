import { DashboardData } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function fetchDashboard(userId = "1"): Promise<DashboardData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard`, {
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as DashboardData;
  } catch {
    return null;
  }
}
