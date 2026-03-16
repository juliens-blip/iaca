"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import {
  ClockIcon,
  DashboardIcon,
  DocumentIcon,
  FlashcardIcon,
  MicrophoneIcon,
  MindMapIcon,
  QuizIcon,
  SubjectIcon,
} from "@/components/AppIcons";
import { withAuthHeaders } from "@/lib/auth";

interface NavigationItem {
  href: string;
  icon: ReactNode;
  name: string;
}

interface NavigationGroup {
  items: NavigationItem[];
  label: string;
}

const navigationGroups: NavigationGroup[] = [
  {
    label: "Tableau de bord",
    items: [
      {
        name: "Vue generale",
        href: "/",
        icon: <DashboardIcon className="h-5 w-5" />,
      },
    ],
  },
  {
    label: "Apprentissage",
    items: [
      {
        name: "Matieres",
        href: "/matieres",
        icon: <SubjectIcon className="h-5 w-5" />,
      },
      {
        name: "Fiches",
        href: "/fiches",
        icon: <DocumentIcon className="h-5 w-5" />,
      },
      {
        name: "Flashcards",
        href: "/flashcards",
        icon: <FlashcardIcon className="h-5 w-5" />,
      },
      {
        name: "Quiz",
        href: "/quiz",
        icon: <QuizIcon className="h-5 w-5" />,
      },
    ],
  },
  {
    label: "Outils",
    items: [
      {
        name: "Coach vocal",
        href: "/vocal",
        icon: <MicrophoneIcon className="h-5 w-5" />,
      },
      {
        name: "Mind map",
        href: "/mindmap",
        icon: <MindMapIcon className="h-5 w-5" />,
      },
    ],
  },
];

const DAYS_FR = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];

export default function Sidebar() {
  const pathname = usePathname();
  const [currentDay, setCurrentDay] = useState("");
  const [currentTime, setCurrentTime] = useState("");
  const [progressData, setProgressData] = useState({ flashcards: 0, fiches: 0, quiz: 0 });
  const [revisionCount, setRevisionCount] = useState(0);
  const [revisionLoading, setRevisionLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");

      setCurrentDay(DAYS_FR[now.getDay()]);
      setCurrentTime(`${hours}:${minutes}`);
    };

    updateClock();
    const interval = window.setInterval(updateClock, 30000);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  useEffect(() => {
    const fetchRevisions = async () => {
      try {
        const response = await fetch("/api/flashcards/revision", withAuthHeaders());
        if (response.ok) {
          const data = await response.json();
          setRevisionCount(Array.isArray(data) ? data.length : 0);
        }
      } finally {
        setRevisionLoading(false);
      }
    };

    fetchRevisions();
    const interval = window.setInterval(fetchRevisions, 60000);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const [flashcardsResult, quizResult, fichesResult] = await Promise.allSettled([
          fetch("/api/flashcards", withAuthHeaders()),
          fetch("/api/quiz", withAuthHeaders()),
          fetch("/api/fiches", withAuthHeaders()),
        ]);

        let flashcards = 0;
        let fiches = 0;
        let quiz = 0;

        if (flashcardsResult.status === "fulfilled" && flashcardsResult.value.ok) {
          const data = await flashcardsResult.value.json();
          flashcards = Array.isArray(data) ? data.length : 0;
        }

        if (quizResult.status === "fulfilled" && quizResult.value.ok) {
          const data = await quizResult.value.json();
          quiz = Array.isArray(data) ? data.length : 0;
        }

        if (fichesResult.status === "fulfilled" && fichesResult.value.ok) {
          const data = await fichesResult.value.json();
          fiches = Array.isArray(data) ? data.length : 0;
        }

        setProgressData({ flashcards, fiches, quiz });
      } catch {
        setProgressData({ flashcards: 0, fiches: 0, quiz: 0 });
      }
    };

    fetchProgress();
  }, []);

  const maxProgress = Math.max(progressData.flashcards, progressData.quiz, progressData.fiches, 1);
  const progressItems = [
    {
      label: "Flashcards",
      value: progressData.flashcards,
      accentClass: "from-teal-300 to-teal-500",
      textClass: "text-teal-100",
    },
    {
      label: "Quiz",
      value: progressData.quiz,
      accentClass: "from-orange-300 to-orange-500",
      textClass: "text-orange-100",
    },
    {
      label: "Fiches",
      value: progressData.fiches,
      accentClass: "from-sky-300 to-sky-500",
      textClass: "text-sky-100",
    },
  ];

  const rhythmLabel = revisionCount > 0 ? "Focus memoire" : "Rythme stable";
  const rhythmDescription = revisionCount > 0
    ? `${revisionCount} carte${revisionCount > 1 ? "s" : ""} a repasser en priorite.`
    : "Aucune revision urgente, tu peux ouvrir un nouveau sprint.";

  return (
    <>
      {sidebarOpen ? (
        <button
          type="button"
          aria-label="Fermer la navigation"
          className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-[19rem] border-r border-white/10 bg-[#07131b]/92 shadow-[0_30px_70px_rgba(2,12,27,0.45)] backdrop-blur-2xl transition-transform duration-300 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          <div className="border-b border-white/10 p-4">
            <div className="rounded-[1.75rem] border border-white/10 bg-white/5 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.28em] text-teal-200/80">
                    IACA
                  </p>
                  <h1 className="mt-3 font-heading text-4xl text-white">Bureau de revision</h1>
                  <p className="mt-3 text-sm leading-6 text-slate-300">
                    Une barre laterale plus utile pour passer du pilotage a l&apos;action.
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/10 p-3 text-white">
                  <DashboardIcon className="h-6 w-6" />
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                    Jour
                  </p>
                  <p className="mt-2 text-sm font-semibold text-white">{currentDay || "Aujourd'hui"}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                    Heure
                  </p>
                  <p className="mt-2 text-sm font-semibold text-white">{currentTime || "--:--"}</p>
                </div>
              </div>
            </div>
          </div>

          <nav className="flex-1 overflow-y-auto px-3 py-4">
            {navigationGroups.map((group, index) => (
              <section key={group.label} className={index > 0 ? "mt-6" : ""}>
                <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">
                  {group.label}
                </p>
                <div className="mt-3 space-y-1.5">
                  {group.items.map((item) => {
                    const isActive = pathname === item.href;
                    const isFlashcards = item.href === "/flashcards";

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        aria-current={isActive ? "page" : undefined}
                        className={`flex cursor-pointer items-center gap-3 rounded-2xl border px-3 py-3 text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? "border-teal-300/25 bg-teal-300/12 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
                            : "border-transparent text-slate-400 hover:border-white/10 hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <span className={isActive ? "text-teal-100" : "text-slate-500"}>{item.icon}</span>
                        <span className="flex-1">{item.name}</span>
                        {isFlashcards ? (
                          revisionLoading ? (
                            <span className="h-5 w-10 rounded-full bg-white/10" />
                          ) : revisionCount > 0 ? (
                            <span className="rounded-full bg-orange-500 px-2 py-0.5 text-[11px] font-semibold text-white">
                              {revisionCount > 99 ? "99+" : revisionCount}
                            </span>
                          ) : null
                        ) : null}
                      </Link>
                    );
                  })}
                </div>
              </section>
            ))}
          </nav>

          <div className="border-t border-white/10 p-4">
            <div className="space-y-4">
              <section className="rounded-[1.75rem] border border-white/10 bg-white/5 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                      Ressources actives
                    </p>
                    <p className="mt-2 text-sm text-slate-300">
                      Lecture immediate des volumes accessibles.
                    </p>
                  </div>
                  <ClockIcon className="h-5 w-5 text-slate-400" />
                </div>

                <div className="mt-4 space-y-3">
                  {progressItems.map((item) => (
                    <div key={item.label} className="space-y-1.5">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-300">{item.label}</span>
                        <span className={`font-semibold ${item.textClass}`}>{item.value}</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-950/60">
                        <div
                          className={`h-full rounded-full bg-gradient-to-r ${item.accentClass}`}
                          style={{ width: `${(item.value / maxProgress) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-[1.75rem] border border-orange-300/15 bg-[linear-gradient(180deg,rgba(234,88,12,0.12),rgba(15,23,42,0.2))] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-orange-100/80">
                  Cadence du jour
                </p>
                <h2 className="mt-3 text-xl font-semibold text-white">{rhythmLabel}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-200/90">{rhythmDescription}</p>

                <div className="mt-4 flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                      Status
                    </p>
                    <p className="mt-1 text-sm font-semibold text-white">
                      {revisionCount > 0 ? "Memoire a consolider" : "Session ouverte"}
                    </p>
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-200">
                    {currentTime || "IACA"}
                  </span>
                </div>
              </section>
            </div>
          </div>
        </div>
      </aside>

      <header className="fixed inset-x-0 top-0 z-40 flex items-center justify-between border-b border-white/10 bg-[#07131b]/85 px-4 py-3 backdrop-blur-2xl lg:hidden">
        <button
          type="button"
          aria-label={sidebarOpen ? "Fermer la navigation" : "Ouvrir la navigation"}
          className="rounded-2xl border border-white/10 bg-white/5 p-2 text-slate-200 transition-colors duration-200 hover:bg-white/10"
          onClick={() => setSidebarOpen((open) => !open)}
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.6} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>

        <div className="text-center">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-teal-200/80">
            IACA
          </p>
          <p className="font-heading text-xl text-white">Cockpit</p>
        </div>

        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-slate-200">
          {currentTime || "--:--"}
        </span>
      </header>
    </>
  );
}
