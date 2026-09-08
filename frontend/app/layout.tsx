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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-background text-foreground flex h-screen overflow-hidden`}>
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 bg-white">
          <Topbar />
          <main className="flex-1 overflow-auto bg-white">
            {children}
          </main>
        </div>
        <Toaster theme="light" position="bottom-right" className="font-sans" />
      </body>
    </html>
  );
}
