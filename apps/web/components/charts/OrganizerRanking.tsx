import type { OrganizerMetricDTO } from "@/lib/api-client";
import { formatVndCompact } from "@/lib/formatters";

export function OrganizerRanking({ data }: { data: OrganizerMetricDTO[] }) {
  return (
    <section
      role="region"
      aria-label="Hệ sinh thái Ban tổ chức và Nhà tài trợ"
      className="flex flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
    >
      <div className="mb-4">
        <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
          Hệ sinh thái Ban tổ chức &amp; Nhà tài trợ
        </h2>
        <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">
          Top 10 đơn vị tổ chức và đối tác đồng hành tích cực từ bridge_competition_organizer
        </p>
      </div>
      <div className="max-h-80 overflow-auto rounded-lg border border-[var(--color-border)]">
        <table className="w-full text-left text-xs">
          <caption className="visually-hidden">Xếp hạng đơn vị tổ chức và nhà tài trợ</caption>
          <thead className="bg-[var(--color-surface-subtle)] text-[var(--color-text-primary)]">
            <tr>
              <th scope="col" className="px-3 py-2">Đơn vị</th>
              <th scope="col" className="px-3 py-2">Loại</th>
              <th scope="col" className="px-3 py-2">Vai trò</th>
              <th scope="col" className="px-3 py-2 text-right">Cuộc thi</th>
              <th scope="col" className="px-3 py-2 text-right">Quỹ phân bổ</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 10).map((org, idx) => (
              <tr key={`${org.organizer_slug}-${org.role_type}-${idx}`} className="border-t border-[var(--color-border)]">
                <td className="px-3 py-2 font-medium text-[var(--color-text-primary)]">{org.organizer_name}</td>
                <td className="px-3 py-2 text-[var(--color-text-muted)]">{org.organizer_tier}</td>
                <td className="px-3 py-2">
                  <span className="rounded bg-[var(--color-surface-subtle)] px-1.5 py-0.5 font-mono text-[10px]">
                    {org.role_type === "organizer" ? "BTC" : "Tài trợ"}
                  </span>
                </td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{org.competition_count}</td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{formatVndCompact(org.allocated_prize_vnd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
