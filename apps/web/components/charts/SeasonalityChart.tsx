"use client";

import { useEffect, useState } from "react";
import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartCard } from "@/components/charts/ChartCard";
import type { SeasonalityMetricDTO } from "@/lib/api-client";
import { formatVndCompact } from "@/lib/formatters";

export function SeasonalityChart({ data }: { data: SeasonalityMetricDTO[] }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const chartData = data.map((s) => ({
    ...s,
    label: s.year && s.month ? `${String(s.month).padStart(2, "0")}/${String(s.year).slice(-2)} (${s.academic_term})` : "Chưa rõ",
    prizeMillions: Math.round(s.total_prize_vnd / 1_000_000),
  }));

  return (
    <ChartCard
      title="Mùa vụ Cuộc thi theo Học kỳ HCM-UTE"
      subtitle="Phân bổ theo tháng và chu kỳ HK1 (T9–T12), HK2 (T1–T5), Hè (T6–T8)"
      ariaLabel="Biểu đồ mùa vụ cuộc thi theo tháng và học kỳ HCM-UTE"
      tableContent={
        <table className="w-full text-left text-xs">
          <caption className="visually-hidden">Số liệu mùa vụ cuộc thi theo tháng và học kỳ</caption>
          <thead className="bg-[var(--color-surface-subtle)] text-[var(--color-text-primary)]">
            <tr>
              <th scope="col" className="px-3 py-2">Thời gian</th>
              <th scope="col" className="px-3 py-2">Học kỳ</th>
              <th scope="col" className="px-3 py-2 text-right">Cuộc thi</th>
              <th scope="col" className="px-3 py-2 text-right">Tổng giải</th>
            </tr>
          </thead>
          <tbody>
            {data.map((s, idx) => (
              <tr key={`${s.year}-${s.month}-${idx}`} className="border-t border-[var(--color-border)]">
                <td className="px-3 py-2 font-mono">{s.year && s.month ? `${s.month}/${s.year}` : "Chưa rõ"}</td>
                <td className="px-3 py-2">{s.academic_term} ({s.academic_year})</td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{s.competition_count}</td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{formatVndCompact(s.total_prize_vnd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {mounted ? (
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="label" tick={{ fill: "var(--color-text-muted)", fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
            <YAxis yAxisId="left" allowDecimals={false} tick={{ fill: "var(--color-text-muted)", fontSize: 11 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fill: "var(--color-text-muted)", fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-surface)",
                borderColor: "var(--color-border)",
                color: "var(--color-text-primary)",
                fontSize: "12px",
              }}
            />
            <Bar yAxisId="left" dataKey="competition_count" name="Số cuộc thi" fill="var(--color-chart-1)" radius={[4, 4, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="prizeMillions" name="Giải thưởng (triệu VNĐ)" stroke="var(--color-chart-2)" strokeWidth={2} dot={{ r: 3 }} />
          </ComposedChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-full w-full animate-pulse rounded-lg bg-[var(--color-surface-subtle)]" />
      )}
    </ChartCard>
  );
}
