"use client";

import { useEffect, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { ChartCard } from "@/components/charts/ChartCard";
import type { ModeTeamMetricDTO } from "@/lib/api-client";

const MODE_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-5)",
];

export function ModeDonutChart({ data }: { data: ModeTeamMetricDTO[] }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const byMode = Object.values(
    data.reduce<Record<string, { mode: string; count: number }>>((acc, row) => {
      if (!acc[row.mode_canonical]) {
        acc[row.mode_canonical] = { mode: row.mode_canonical, count: 0 };
      }
      acc[row.mode_canonical].count += row.competition_count;
      return acc;
    }, {}),
  );

  return (
    <ChartCard
      title="Hình thức Tổ chức & Quy mô Đội"
      subtitle="Phân bố Online / Offline / Hybrid kết hợp hồ sơ số lượng thành viên"
      ariaLabel="Biểu đồ tròn phân bố hình thức tổ chức cuộc thi"
      tableContent={
        <table className="w-full text-left text-xs">
          <caption className="visually-hidden">Ma trận hình thức tổ chức và quy mô đội thi</caption>
          <thead className="bg-[var(--color-surface-subtle)] text-[var(--color-text-primary)]">
            <tr>
              <th scope="col" className="px-3 py-2">Hình thức</th>
              <th scope="col" className="px-3 py-2">Quy mô đội</th>
              <th scope="col" className="px-3 py-2 text-right">Số cuộc thi</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={`${row.mode_canonical}-${row.team_profile}-${idx}`} className="border-t border-[var(--color-border)]">
                <td className="px-3 py-2 font-medium">{row.mode_canonical}</td>
                <td className="px-3 py-2">{row.team_profile}</td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{row.competition_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {mounted ? (
        <div className="flex h-full flex-col items-center justify-center sm:flex-row">
          <div className="h-64 w-full sm:w-3/5">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={byMode}
                  dataKey="count"
                  nameKey="mode"
                  innerRadius={52}
                  outerRadius={88}
                  paddingAngle={3}
                >
                  {byMode.map((entry, idx) => (
                    <Cell key={entry.mode} fill={MODE_COLORS[idx % MODE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-surface)",
                    borderColor: "var(--color-border)",
                    color: "var(--color-text-primary)",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="w-full space-y-2 text-xs sm:w-2/5">
            {byMode.map((entry, idx) => (
              <li key={entry.mode} className="flex items-center justify-between gap-2 rounded-md border border-[var(--color-border)] px-2.5 py-1.5">
                <span className="inline-flex items-center gap-2 font-medium text-[var(--color-text-primary)]">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: MODE_COLORS[idx % MODE_COLORS.length] }}
                    aria-hidden="true"
                  />
                  {entry.mode}
                </span>
                <span className="font-mono font-semibold tabular-nums">{entry.count}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="h-full w-full animate-pulse rounded-lg bg-[var(--color-surface-subtle)]" />
      )}
    </ChartCard>
  );
}
