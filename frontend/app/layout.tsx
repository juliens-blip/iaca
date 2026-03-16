import type { ReactNode } from "react";
import type { Metadata } from "next";
import { Cormorant_Garamond, Public_Sans } from "next/font/google";

import "./globals.css";
import Sidebar from "./sidebar";

const bodyFont = Public_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const headingFont = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "IACA | Cockpit de preparation",
  description: "Plateforme de preparation aux concours administratifs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className={`${bodyFont.variable} ${headingFont.variable} min-h-screen text-slate-100`}>
        <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.12),transparent_28%),radial-gradient(circle_at_85%_15%,rgba(234,88,12,0.12),transparent_22%),linear-gradient(180deg,#041018_0%,#071620_100%)]">
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.05)_1px,transparent_1px)] [background-size:56px_56px] opacity-[0.18]" />
          <div className="relative flex min-h-screen">
            <Sidebar />

            <div className="flex min-w-0 flex-1 flex-col">
              <main className="flex-1 overflow-y-auto">
                <div className="mx-auto w-full max-w-[1520px] px-4 pb-8 pt-24 sm:px-6 lg:px-10 lg:pt-8">
                  {children}
                </div>
              </main>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
