"use client";

import { useEffect, useState } from "react";
import { withAuthHeaders } from "@/lib/auth";

const API_BASE = "/api";

interface Stats {
  documents: number;
  flashcards: number;
  quiz: number;
  fiches: number;
  flashcards_a_reviser: number;
}

interface Flashcard {
  id: number;
  question: string;
  prochaine_revision: string;
}

interface QuizData {
  id: number;
  titre: string;
}

interface Matiere {
  id: number;
  nom: string;
  nb_documents?: number;
}

interface AnimatedNumberProps {
  value: number;
  duration?: number;
}

// Animated counter component
const AnimatedNumber: React.FC<AnimatedNumberProps> = ({ value, duration = 1000 }) => {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const progress = Math.min((Date.now() - start) / duration, 1);
      setDisplay(Math.floor(progress * value));
    }, 16);

    return () => clearInterval(interval);
  }, [value, duration]);

  return <>{display}</>;
};

// Skeleton loader for stats card
const StatCardSkeleton = () => (
  <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/30 animate-pulse">
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="h-4 w-24 bg-slate-700 rounded" />
        <div className="mt-3 h-8 w-16 bg-slate-700 rounded" />
        <div className="mt-3 h-3 w-12 bg-slate-700 rounded" />
      </div>
      <div className="w-14 h-14 bg-slate-700 rounded-xl" />
    </div>
  </div>
);

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    documents: 0,
    flashcards: 0,
    quiz: 0,
    fiches: 0,
    flashcards_a_reviser: 0,
  });
  const [revisions, setRevisions] = useState<Flashcard[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState("");

  useEffect(() => {
    // Set current date in French
    const date = new Date();
    const formatter = new Intl.DateTimeFormat("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    setCurrentDate(formatter.format(date));
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch all data in parallel
        const [fcRes, qzRes, revRes, fichesRes, matiereRes] = await Promise.allSettled([
          fetch(`${API_BASE}/flashcards`, withAuthHeaders()),
          fetch(`${API_BASE}/quiz`, withAuthHeaders()),
          fetch(`${API_BASE}/flashcards/revision`, withAuthHeaders()),
          fetch(`${API_BASE}/fiches`, withAuthHeaders()),
          fetch(`${API_BASE}/matieres`, withAuthHeaders()),
        ]);

        let flashcardCount = 0;
        let quizCount = 0;
        let revisionsData: Flashcard[] = [];
        let fichesCount = 0;
        let documentsCount = 0;

        // Process flashcards
        if (fcRes.status === "fulfilled" && fcRes.value.ok) {
          const data = await fcRes.value.json();
          flashcardCount = Array.isArray(data) ? data.length : 0;
        }

        // Process quiz
        if (qzRes.status === "fulfilled" && qzRes.value.ok) {
          const data = await qzRes.value.json();
          quizCount = Array.isArray(data) ? data.length : 0;
        }

        // Process revisions
        if (revRes.status === "fulfilled" && revRes.value.ok) {
          const data = await revRes.value.json();
          revisionsData = Array.isArray(data) ? data.slice(0, 5) : [];
          setRevisions(revisionsData);
        }

        // Process fiches
        if (fichesRes.status === "fulfilled" && fichesRes.value.ok) {
          const data = await fichesRes.value.json();
          fichesCount = Array.isArray(data) ? data.length : 0;
        }

        // Process matieres and count documents
        if (matiereRes.status === "fulfilled" && matiereRes.value.ok) {
          const data = await matiereRes.value.json();
          if (Array.isArray(data)) {
            documentsCount = data.reduce((sum, m: Matiere) => sum + (m.nb_documents || 0), 0);
          }
        }

        setStats({
          documents: documentsCount,
          flashcards: flashcardCount,
          quiz: quizCount,
          fiches: fichesCount,
          flashcards_a_reviser: revisionsData.length,
        });
      } catch (error) {
        console.error("Erreur chargement dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const statCards = [
    {
      label: "Documents",
      value: stats.documents,
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      ),
      bgGlow: "bg-blue-500/10",
      textColor: "text-blue-400",
      borderColor: "border-blue-500/20",
    },
    {
      label: "Flashcards",
      value: stats.flashcards,
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
        </svg>
      ),
      bgGlow: "bg-violet-500/10",
      textColor: "text-violet-400",
      borderColor: "border-violet-500/20",
    },
    {
      label: "Fiches",
      value: stats.fiches,
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      ),
      bgGlow: "bg-emerald-500/10",
      textColor: "text-emerald-400",
      borderColor: "border-emerald-500/20",
    },
    {
      label: "Quiz",
      value: stats.quiz,
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
        </svg>
      ),
      bgGlow: "bg-amber-500/10",
      textColor: "text-amber-400",
      borderColor: "border-amber-500/20",
    },
    {
      label: "À réviser",
      value: stats.flashcards_a_reviser,
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
      bgGlow: "bg-rose-500/10",
      textColor: "text-rose-400",
      borderColor: "border-rose-500/20",
    },
    {
      label: "Score moyen",
      value: 0,
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25a.75.75 0 0 1 .75.75v6.75a.75.75 0 0 1-.75.75h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 12c-.414 0-.75.504-.75 1.125v6.75c0 .621.336 1.125.75 1.125h2.25a.75.75 0 0 0 .75-.75v-6.75a.75.75 0 0 0-.75-.75h-2.25ZM15.75 12c-.414 0-.75.504-.75 1.125v6.75c0 .621.336 1.125.75 1.125h2.25a.75.75 0 0 0 .75-.75v-6.75a.75.75 0 0 0-.75-.75h-2.25Z" />
        </svg>
      ),
      bgGlow: "bg-cyan-500/10",
      textColor: "text-cyan-400",
      borderColor: "border-cyan-500/20",
    },
  ];

  if (loading) {
    return (
      <div className="space-y-8">
        {/* Header skeleton */}
        <div className="space-y-3">
          <div className="h-10 w-64 bg-slate-700 rounded-lg animate-pulse" />
          <div className="h-4 w-96 bg-slate-700 rounded animate-pulse" />
        </div>

        {/* Stats skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>

        {/* Section skeleton */}
        <div className="h-64 bg-slate-800/50 border border-slate-700/30 rounded-2xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-800/50 via-slate-800/30 to-transparent border border-slate-700/30 p-8 backdrop-blur-sm">
        {/* Decorative gradient orbs */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-violet-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl" />

        <div className="relative z-10">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-violet-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent mb-2">
            Bienvenue sur IACA
          </h1>
          <p className="text-lg text-slate-300 mb-4">
            Préparez les concours administratifs avec l&apos;IA
          </p>
          <p className="text-sm text-slate-400 capitalize">
            {currentDate}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Votre progression</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {statCards.map((card) => (
            <div
              key={card.label}
              className={`group relative overflow-hidden rounded-2xl bg-slate-800/50 border ${card.borderColor} p-6 transition-all hover:bg-slate-800/80 hover:border-slate-600/50`}
            >
              {/* Decorative gradient background */}
              <div className={`absolute -right-8 -top-8 w-20 h-20 rounded-full ${card.bgGlow} blur-2xl opacity-40 group-hover:opacity-60 transition-opacity`} />

              <div className="relative flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-400">{card.label}</p>
                  <p className="mt-2 text-4xl font-bold text-white">
                    <AnimatedNumber value={card.value} duration={800} />
                  </p>
                  {card.value > 0 && (
                    <div className="mt-3 flex items-center gap-1">
                      <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 13.5V3m0 0H3m4.5 0l-4.5 4.5m9 0v13.5m0 0h4.5m-4.5 0l4.5 4.5" />
                      </svg>
                      <span className="text-xs font-medium text-emerald-400">Actif</span>
                    </div>
                  )}
                </div>
                <div className={`p-4 rounded-xl ${card.bgGlow}`}>
                  <span className={card.textColor}>{card.icon}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Révisions du jour */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Révisions du jour</h2>
          <a
            href="/flashcards"
            className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
          >
            Voir tout →
          </a>
        </div>

        <div className="rounded-2xl bg-slate-800/50 border border-slate-700/30 p-6">
          {revisions.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 mx-auto text-emerald-500/30 mb-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              <p className="text-lg font-semibold text-slate-300">Tout est à jour !</p>
              <p className="text-sm text-slate-500 mt-2">
                Vous n&apos;avez pas de flashcards à réviser aujourd&apos;hui
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {revisions.map((revision) => (
                <div
                  key={revision.id}
                  className="flex items-center gap-4 p-4 rounded-xl bg-slate-900/40 border border-slate-700/30 hover:border-slate-600/50 transition-all group"
                >
                  <div className="flex-shrink-0 w-1 h-12 rounded-full bg-gradient-to-b from-blue-400 to-violet-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 line-clamp-2">
                      {revision.question.length > 80
                        ? revision.question.substring(0, 80) + "..."
                        : revision.question}
                    </p>
                  </div>
                  <a
                    href="/flashcards"
                    className="flex-shrink-0 px-3 py-2 rounded-lg bg-blue-500/20 text-blue-400 text-sm font-medium hover:bg-blue-500/30 transition-colors"
                  >
                    Réviser
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Actions rapides</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href="/flashcards"
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-violet-600/20 to-violet-600/5 border border-violet-500/30 p-6 hover:border-violet-500/50 transition-all"
          >
            <div className="absolute -right-12 -top-12 w-24 h-24 bg-violet-500/20 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="p-3 rounded-xl bg-violet-500/20 w-fit mb-3">
                <svg className="w-6 h-6 text-violet-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Commencer une révision</h3>
              <p className="text-sm text-slate-400">
                {stats.flashcards} flashcards disponibles
              </p>
            </div>
          </a>

          <a
            href="/quiz"
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600/20 to-blue-600/5 border border-blue-500/30 p-6 hover:border-blue-500/50 transition-all"
          >
            <div className="absolute -right-12 -top-12 w-24 h-24 bg-blue-500/20 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="p-3 rounded-xl bg-blue-500/20 w-fit mb-3">
                <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Faire un quiz</h3>
              <p className="text-sm text-slate-400">
                {stats.quiz} quiz disponibles
              </p>
            </div>
          </a>

          <a
            href="/fiches"
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-600/20 to-emerald-600/5 border border-emerald-500/30 p-6 hover:border-emerald-500/50 transition-all"
          >
            <div className="absolute -right-12 -top-12 w-24 h-24 bg-emerald-500/20 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="p-3 rounded-xl bg-emerald-500/20 w-fit mb-3">
                <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Lire les fiches</h3>
              <p className="text-sm text-slate-400">
                {stats.fiches} fiches disponibles
              </p>
            </div>
          </a>

          <a
            href="/vocal"
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-rose-600/20 to-rose-600/5 border border-rose-500/30 p-6 hover:border-rose-500/50 transition-all"
          >
            <div className="absolute -right-12 -top-12 w-24 h-24 bg-rose-500/20 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="p-3 rounded-xl bg-rose-500/20 w-fit mb-3">
                <svg className="w-6 h-6 text-rose-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m0 0h3.75m-3.75 0H9M3 12a9 9 0 0 1 9-9m0 0v3.75m0 0h3.75M3 12a9 9 0 0 0 9 9" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Prof vocal</h3>
              <p className="text-sm text-slate-400">
                Réviser en parlant
              </p>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
