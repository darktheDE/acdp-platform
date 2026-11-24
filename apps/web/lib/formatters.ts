export function formatVndFull(amount: number | null | undefined): string {
  if (!amount || amount <= 0) return "0 VNĐ";
  return `${new Intl.NumberFormat("vi-VN").format(amount)} VNĐ`;
}

export function formatVndCompact(amount: number | null | undefined): string {
  if (!amount || amount <= 0) return "Theo thể lệ BTC";
  if (amount >= 1_000_000_000) {
    const val = amount / 1_000_000_000;
    return `${val.toFixed(val % 1 === 0 ? 0 : 2)} tỷ VNĐ`;
  }
  if (amount >= 1_000_000) {
    const val = amount / 1_000_000;
    return `${val.toFixed(val % 1 === 0 ? 0 : 1)} triệu VNĐ`;
  }
  return `${new Intl.NumberFormat("vi-VN").format(amount)} VNĐ`;
}

export function formatCompetitionPrizeLabel(
  totalPrizeVnd: number,
  hasScholarship?: boolean,
): string {
  if (totalPrizeVnd > 0) {
    return formatVndCompact(totalPrizeVnd);
  }
  return hasScholarship ? "Học bổng / Tài trợ" : "Theo thể lệ BTC";
}

export function formatStatusLabel(status: string | null | undefined): {
  label: string;
  tone: "open" | "upcoming" | "closed" | "unknown";
} {
  const s = (status || "").toLowerCase();
  if (s === "open") return { label: "Đang mở", tone: "open" };
  if (s === "upcoming") return { label: "Sắp diễn ra", tone: "upcoming" };
  if (s === "closed") return { label: "Đã đóng", tone: "closed" };
  return { label: "Chưa rõ", tone: "unknown" };
}
