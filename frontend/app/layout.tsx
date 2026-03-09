import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "./sidebar";

export const metadata: Metadata = {
  title: "IACA - Concours Administratifs",
  description: "Plateforme de preparation aux concours administratifs",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="min-h-screen">
        <div className="flex h-screen overflow-hidden">
          <Sidebar />

          {/* Contenu principal */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Page content */}
            <main className="flex-1 overflow-y-auto">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
              </div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
