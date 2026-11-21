import type { Metadata } from "next";
import { CopilotWorkspace } from "@/components/copilot/CopilotWorkspace";

export const metadata: Metadata = {
  title: "RAG Regulation Copilot",
};

export default function CopilotPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
          RAG Regulation Copilot
        </h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Tra cứu điều khoản thể lệ từ kho vector Qdrant (425 đoạn trích / 17 nguồn) kèm nguồn kiểm chứng
        </p>
      </div>
      <CopilotWorkspace />
    </div>
  );
}
