import type { Metadata } from "next";
import { Cairo, Inter } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/contexts/language-context";
import { Sidebar } from "@/components/layout/sidebar";
import { AuthWrapper } from "@/components/auth-wrapper";

// Arabic-optimized font
const cairo = Cairo({
  variable: "--font-cairo",
  subsets: ["arabic", "latin"],
});

// English-optimized font
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "مساعد المطعم الذكي | Restaurant AI Assistant",
  description: "AI-powered customer feedback management system for restaurants",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html>
      <body
        className={`${cairo.variable} ${inter.variable} antialiased`}
      >
        <LanguageProvider>
          <AuthWrapper>
            <div className="flex h-screen bg-slate-50">
              <Sidebar />
              <main className="flex-1 overflow-auto">
                {children}
              </main>
            </div>
          </AuthWrapper>
        </LanguageProvider>
      </body>
    </html>
  );
}
