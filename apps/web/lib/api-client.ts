import type { components } from "@/types/api";

export type HealthResponse = components["schemas"]["HealthResponse"];
export type KpiOverviewDTO = components["schemas"]["KpiOverviewDTO"];
export type DomainMetricDTO = components["schemas"]["DomainMetricDTO"];
export type SeasonalityMetricDTO = components["schemas"]["SeasonalityMetricDTO"];
export type ModeTeamMetricDTO = components["schemas"]["ModeTeamMetricDTO"];
export type OrganizerMetricDTO = components["schemas"]["OrganizerMetricDTO"];
export type AnalyticsDashboardDTO = components["schemas"]["AnalyticsDashboardDTO"];
export type CompetitionSummaryDTO = components["schemas"]["CompetitionSummaryDTO"];
export type CompetitionDetailDTO = components["schemas"]["CompetitionDetailDTO"];
export type PaginatedCompetitionsDTO = components["schemas"]["PaginatedCompetitionsDTO"];
export type PrizeTierDTO = components["schemas"]["PrizeTierDTO"];
export type TimelineStageDTO = components["schemas"]["TimelineStageDTO"];
export type UserProfileDTO = components["schemas"]["UserProfileDTO"];
export type TokenResponse = components["schemas"]["TokenResponse"];
export type BookmarkDTO = components["schemas"]["BookmarkDTO"];
export type RagCitationDTO = components["schemas"]["RagCitationDTO"];
export type RagChatResponse = components["schemas"]["RagChatResponse"];
export type ChatSessionDTO = components["schemas"]["ChatSessionDTO"];
export type ChatMessageDTO = components["schemas"]["ChatMessageDTO"];
export type AdminUserDTO = components["schemas"]["AdminUserDTO"];
export type AdminUserUpdateRequest = components["schemas"]["AdminUserUpdateRequest"];
export type AdminUsersSummaryDTO = components["schemas"]["AdminUsersSummaryDTO"];
export type AdminTelemetryDTO = components["schemas"]["AdminTelemetryDTO"];
export type AdminCacheRefreshRequest = components["schemas"]["AdminCacheRefreshRequest"];
export type AdminCacheRefreshDTO = components["schemas"]["AdminCacheRefreshDTO"];

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  if (process.env.NEXT_PUBLIC_USE_REWRITE_PROXY === "true") {
    return "";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, headers, ...rest } = options;
  const reqHeaders = new Headers(headers);
  if (!reqHeaders.has("Content-Type") && rest.body) {
    reqHeaders.set("Content-Type", "application/json");
  }
  if (token) {
    reqHeaders.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    ...rest,
    headers: reqHeaders,
    credentials: "include",
    cache: rest.cache ?? "no-store",
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const errJson = (await res.json()) as { detail?: string };
      if (errJson?.detail) detail = errJson.detail;
    } catch {
      // Ignore non-JSON error body
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}
