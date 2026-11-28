import type { Metadata } from "next";
import { CopilotWorkspace, type CompetitionScopeOption } from "@/components/copilot/CopilotWorkspace";
import { apiFetch, type PaginatedCompetitionsDTO } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Trợ lý Thể lệ",
};

function buildCompetitionScopes(items: PaginatedCompetitionsDTO["items"]): CompetitionScopeOption[] {
  const seen = new Set<string>();
  const options: CompetitionScopeOption[] = [];
  for (const item of items) {
    try {
      const host = new URL(item.canonical_url).hostname;
      if (host && !seen.has(host)) {
        seen.add(host);
        options.push({ value: host, label: item.name });
      }
    } catch {
      // Skip malformed URL
    }
  }
  return options.sort((a, b) => a.label.localeCompare(b.label, "vi"));
}

export default async function CopilotPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const initialDomain = typeof sp.domain === "string" ? sp.domain.trim() : "";
  const initialQuestion = typeof sp.q === "string" ? sp.q.trim() : "";

  let scopes: CompetitionScopeOption[] = [];
  try {
    const res = await apiFetch<PaginatedCompetitionsDTO>("/api/v1/competitions?page_size=100");
    scopes = buildCompetitionScopes(res.items);
  } catch {
    scopes = [];
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
          Trợ lý Hỏi đáp Thể lệ Cuộc thi
        </h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Tra cứu điều kiện dự thi, hạn nộp, giải thưởng và thể lệ chính thức kèm đường dẫn nguồn để kiểm chứng
        </p>
      </div>
      <CopilotWorkspace
        competitionScopes={scopes}
        initialDomain={initialDomain}
        initialQuestion={initialQuestion}
      />
    </div>
  );
}
