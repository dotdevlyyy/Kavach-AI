import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/shared/Sidebar";
import { Topbar } from "@/components/shared/Topbar";
import { Toaster } from "sonner";

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
      <body className="bg-background text-foreground flex min-h-[100dvh] overflow-hidden">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 bg-background">
            <Topbar />
            <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:bg-background focus:px-4 focus:py-2 focus:text-foreground">Skip to main content</a>
            <main id="main-content" tabIndex={-1} className="flex-1 overflow-auto bg-background flex flex-col min-h-0">
              {children}
            </main>
          </div>
          <Toaster theme="light" position="bottom-right" className="font-sans" />
        </ThemeProvider>
      </body>
    </html>
  );
}
