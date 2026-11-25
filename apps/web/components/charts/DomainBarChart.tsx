"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartCard } from "@/components/charts/ChartCard";
import type { DomainMetricDTO } from "@/lib/api-client";
import { formatVndCompact, formatVndFull } from "@/lib/formatters";

export function DomainBarChart({ data }: { data: DomainMetricDTO[] }) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const chartData = data.map((d) => ({
    ...d,
    prizeMillions: Math.round(d.allocated_prize_vnd / 1_000_000),
  }));

  return (
    <ChartCard
      title="Phân bổ Cuộc thi & Quỹ Giải thưởng theo Ngành"
      subtitle="Phân bổ theo nhóm ngành công nghệ; nhấp vào cột để xem danh sách cuộc thi"
      ariaLabel="Biểu đồ phân bổ cuộc thi và quỹ giải thưởng theo nhóm ngành"
      tableContent={
        <table className="w-full text-left text-xs">
          <caption className="visually-hidden">Số liệu phân bổ cuộc thi theo nhóm ngành</caption>
          <thead className="bg-[var(--color-surface-subtle)] text-[var(--color-text-primary)]">
            <tr>
              <th scope="col" className="px-3 py-2">Nhóm ngành</th>
              <th scope="col" className="px-3 py-2 text-right">Số cuộc thi</th>
              <th scope="col" className="px-3 py-2 text-right">Quỹ giải thưởng</th>
            </tr>
          </thead>
          <tbody>
            {data.map((d) => (
              <tr key={d.domain_slug} className="border-t border-[var(--color-border)]">
                <td className="px-3 py-2 font-medium">{d.domain_group}</td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{d.competition_count}</td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{formatVndCompact(d.allocated_prize_vnd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {mounted ? (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 20, left: 16, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis type="number" tick={{ fill: "var(--color-text-muted)", fontSize: 11 }} />
            <YAxis
              type="category"
              dataKey="domain_group"
              width={150}
              tick={{ fill: "var(--color-text-primary)", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-surface)",
                borderColor: "var(--color-border)",
                color: "var(--color-text-primary)",
                fontSize: "12px",
              }}
              formatter={(value, name) => {
                if (name === "prizeMillions") {
                  return [formatVndFull(Number(value) * 1_000_000), "Quỹ phân bổ"];
                }
                return [String(value), "Số cuộc thi"];
              }}
            />
            <Bar
              dataKey="prizeMillions"
              name="prizeMillions"
              fill="var(--color-chart-1)"
              radius={[0, 4, 4, 0]}
              cursor="pointer"
              onClick={(entry) => {
                const slug = (entry as unknown as DomainMetricDTO)?.domain_slug;
                if (slug) router.push(`/competitions?domain=${encodeURIComponent(slug)}`);
              }}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-full w-full animate-pulse rounded-lg bg-[var(--color-surface-subtle)]" />
      )}
    </ChartCard>
  );
}
