"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigationGroups = [
  {
    label: "TABLEAU DE BORD",
    items: [
      {
        name: "Dashboard",
        href: "/",
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z" />
          </svg>
        ),
      },
    ],
  },
  {
    label: "APPRENTISSAGE",
    items: [
      {
        name: "Matieres",
        href: "/matieres",
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
          </svg>
        ),
      },
      {
        name: "Fiches",
        href: "/fiches",
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
          </svg>
        ),
      },
      {
        name: "Flashcards",
        href: "/flashcards",
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
          </svg>
        ),
      },
      {
        name: "Quiz",
        href: "/quiz",
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
          </svg>
        ),
      },
    ],
  },
  {
    label: "OUTILS",
    items: [
      {
        name: "Prof Vocal",
        href: "/vocal",
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
          </svg>
        ),
      },
      {
        name: "Mind Map",
        href: "/mindmap",
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
          </svg>
        ),
      },
    ],
  },
];

const JOURS_FR = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];

export default function Sidebar() {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>("");
  const [currentDay, setCurrentDay] = useState<string>("");
  const [progressData, setProgressData] = useState({ flashcards: 0, quiz: 0, fiches: 0 });
  const [revisionCount, setRevisionCount] = useState<number>(0);
  const [revisionLoading, setRevisionLoading] = useState<boolean>(true);

  useEffect(() => {
    // Update time every second
    const updateTime = () => {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      setCurrentTime(`${hours}:${minutes}`);
      setCurrentDay(JOURS_FR[now.getDay()]);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Fetch revision count and poll every 60s
    const fetchRevisions = async () => {
      try {
        const res = await fetch("/api/flashcards/revision");
        if (res.ok) {
          const data = await res.json();
          setRevisionCount(Array.isArray(data) ? data.length : 0);
        }
      } catch {
        // silent fail
      } finally {
        setRevisionLoading(false);
      }
    };

    fetchRevisions();
    const revInterval = setInterval(fetchRevisions, 60000);
    return () => clearInterval(revInterval);
  }, []);

  useEffect(() => {
    // Fetch progress data
    const fetchProgress = async () => {
      try {
        const [fcRes, qzRes, fichesRes] = await Promise.allSettled([
          fetch("/api/flashcards"),
          fetch("/api/quiz"),
          fetch("/api/fiches"),
        ]);

        let fc = 0, qz = 0, fi = 0;
        if (fcRes.status === "fulfilled" && fcRes.value.ok) {
          const data = await fcRes.value.json();
          fc = Array.isArray(data) ? data.length : 0;
        }
        if (qzRes.status === "fulfilled" && qzRes.value.ok) {
          const data = await qzRes.value.json();
          qz = Array.isArray(data) ? data.length : 0;
        }
        if (fichesRes.status === "fulfilled" && fichesRes.value.ok) {
          const data = await fichesRes.value.json();
          fi = Array.isArray(data) ? data.length : 0;
        }

        setProgressData({ flashcards: fc, quiz: qz, fiches: fi });
      } catch (error) {
        console.error("Erreur chargement progression:", error);
      }
    };

    fetchProgress();
  }, []);

  return (
    <>
      {/* Overlay mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-64 bg-slate-900/95 backdrop-blur-md border-r border-slate-800
          transform transition-transform duration-300 ease-in-out
          lg:relative lg:translate-x-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 shadow-lg shadow-blue-500/20 flex-shrink-0">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3zm0 2.18l7.46 4.07L12 13.29 4.54 9.25 12 5.18zM3 17v2c0 1.1 3.58 2 8 2h.09A5.47 5.47 0 0 1 9 17.5v-.16L3 17zm10 0v.5A3.5 3.5 0 0 0 16.5 21a3.5 3.5 0 0 0 3.5-3.5V17l-7 .01z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-violet-400 to-blue-400 bg-clip-text text-transparent">IACA</h1>
              <p className="text-xs text-slate-500 leading-tight">Concours Admin</p>
            </div>
          </div>

          {/* Navigation groupee */}
          <nav className="flex-1 px-3 py-4 overflow-y-auto">
            {navigationGroups.map((group, groupIndex) => (
              <div key={group.label} className={groupIndex > 0 ? "mt-6" : ""}>
                <p className="px-3 mb-2 text-[10px] font-semibold tracking-widest text-slate-500 uppercase">
                  {group.label}
                </p>
                {groupIndex > 0 && (
                  <div className="mx-3 mb-2 border-t border-slate-800/60" />
                )}
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        onClick={() => setSidebarOpen(false)}
                        className={`
                          flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                          ${
                            isActive
                              ? "bg-gradient-to-r from-violet-600/20 to-blue-600/20 text-white border border-violet-500/30 shadow-sm"
                              : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-colors"
                          }
                        `}
                      >
                        <span className={isActive ? "text-violet-400" : "text-slate-500"}>
                          {item.icon}
                        </span>
                        <span className="flex-1">{item.name}</span>
                        {item.name === "Flashcards" && (
                          revisionLoading ? (
                            <span className="w-5 h-5 rounded-full bg-slate-700 animate-pulse" />
                          ) : revisionCount > 0 ? (
                            <span className="flex items-center justify-center min-w-[20px] h-5 px-1 rounded-full bg-red-500 text-white text-xs font-bold">
                              {revisionCount > 99 ? "99+" : revisionCount}
                            </span>
                          ) : null
                        )}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>

          {/* Footer sidebar */}
          <div className="px-4 py-4 border-t border-slate-800 space-y-4">
            {/* Progression indicator */}
            <div className="space-y-2">
              <p className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase px-2">
                Progression
              </p>
              <div className="space-y-1.5">
                {/* Flashcards progress */}
                <div className="px-2 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
                      </svg>
                      Cards
                    </span>
                    <span className="text-xs text-violet-400 font-medium">{Math.min(Math.round((progressData.flashcards / 100) * 100), 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-700/40 rounded-full h-1 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-violet-600 rounded-full transition-all"
                      style={{ width: `${Math.min((progressData.flashcards / 100) * 100, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Quiz progress */}
                <div className="px-2 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
                      </svg>
                      Quiz
                    </span>
                    <span className="text-xs text-amber-400 font-medium">{Math.min(Math.round((progressData.quiz / 50) * 100), 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-700/40 rounded-full h-1 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-amber-600 rounded-full transition-all"
                      style={{ width: `${Math.min((progressData.quiz / 50) * 100, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Fiches progress */}
                <div className="px-2 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                      </svg>
                      Fiches
                    </span>
                    <span className="text-xs text-rose-400 font-medium">{Math.min(Math.round((progressData.fiches / 30) * 100), 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-700/40 rounded-full h-1 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-rose-500 to-rose-600 rounded-full transition-all"
                      style={{ width: `${Math.min((progressData.fiches / 30) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Separator */}
            <div className="border-t border-slate-800/60" />

            {/* Current time */}
            {currentTime && (
              <div className="border-t border-slate-700 pt-3 text-center">
                <p className="text-sm font-mono font-semibold text-slate-300">{currentTime}</p>
                <p className="text-xs text-slate-500 mt-0.5">{currentDay}</p>
              </div>
            )}

            {/* User profile */}
            <div className="flex items-center gap-3 px-2 pt-2 border-t border-slate-800/60">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-white">JL</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-300 truncate">Julien</p>
                <p className="text-xs text-slate-500">Préparation concours</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Header mobile */}
      <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>
        <span className="text-sm font-semibold text-gradient">IACA</span>
        <div className="w-10" />
      </header>
    </>
  );
}
