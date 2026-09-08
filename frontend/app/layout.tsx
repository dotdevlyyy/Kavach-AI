import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/shared/Sidebar";
import { Topbar } from "@/components/shared/Topbar";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Kavach AI | MRPL Workbench",
  description: "Air-gapped agentic AI workbench for industrial applications.",
};

import { ThemeProvider } from "@/components/theme-provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-background text-foreground flex h-screen overflow-hidden`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 bg-background">
            <Topbar />
            <main className="flex-1 overflow-auto bg-background flex flex-col min-h-0">
              {children}
            </main>
          </div>
          <Toaster theme="light" position="bottom-right" className="font-sans" />
        </ThemeProvider>
      </body>
    </html>
  );
}
