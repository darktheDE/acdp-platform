import type { Metadata } from "next";
import { Be_Vietnam_Pro, JetBrains_Mono, Plus_Jakarta_Sans } from "next/font/google";
import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { AuthProvider } from "@/lib/auth-context";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin", "vietnamese"],
  variable: "--font-jakarta",
  display: "swap",
});

const beVietnam = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-be-vietnam",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin", "vietnamese"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "ACDP | Nền tảng Khám phá Cuộc thi Học thuật HCM-UTE",
    template: "%s | ACDP HCM-UTE",
  },
  description:
    "Khám phá cuộc thi học thuật, phân tích dữ liệu Gold Star Schema và tra cứu thể lệ qua RAG Copilot dành cho sinh viên FIT-HCM-UTE.",
  icons: {
    icon: "/favicon.svg",
  },
};

const THEME_INIT_SCRIPT = `
try {
  var s = localStorage.getItem("color-scheme");
  var m = document.querySelector('meta[name="color-scheme"]');
  if (m && (s === "light" || s === "dark")) m.setAttribute("content", s);
  var isDark = s ? s === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.classList.toggle("dark", isDark);
} catch (e) {}
`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="vi"
      suppressHydrationWarning
      className={`${jakarta.variable} ${beVietnam.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        <meta name="color-scheme" content="light dark" />
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="antialiased">
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
