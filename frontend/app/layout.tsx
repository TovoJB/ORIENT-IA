import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

// Logo SVG sous forme de String Data-URI avec les couleurs vertes
const logoSvgDataUri = `data:image/svg+xml;utf8,<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="robotGradient" x1="8" y1="8" x2="40" y2="40" gradientUnits="userSpaceOnUse"><stop stop-color="%236EE7B7"/><stop offset="0.5" stop-color="%2334D399"/><stop offset="1" stop-color="%23059669"/></linearGradient></defs><circle cx="24" cy="24" r="20" fill="url(%23robotGradient)" opacity="0.15"/><rect x="10" y="13" width="28" height="23" rx="8" fill="%2318181B" stroke="url(%23robotGradient)" stroke-width="2"/><path d="M24 13V9" stroke="url(%23robotGradient)" stroke-width="2" stroke-linecap="round"/><circle cx="24" cy="7" r="2.5" fill="url(%23robotGradient)"/><circle cx="18" cy="23" r="3" fill="url(%23robotGradient)"/><circle cx="30" cy="23" r="3" fill="url(%23robotGradient)"/><path d="M18 30C21 33 27 33 30 30" stroke="url(%23robotGradient)" stroke-width="2" stroke-linecap="round"/><rect x="7" y="20" width="4" height="9" rx="2" fill="url(%23robotGradient)"/><rect x="37" y="20" width="4" height="9" rx="2" fill="url(%23robotGradient)"/></svg>`;

export const metadata: Metadata = {
  title: "ORIENT'IA",
  description: "AI assistant with LLM chat and ML prediction",
  icons: {
    icon: logoSvgDataUri,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}