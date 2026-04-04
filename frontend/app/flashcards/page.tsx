"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import FlashCard from "@/components/FlashCard";
import { withAuthHeaders } from "@/lib/auth";

const API_BASE = "/api";
const FETCH_LIMIT = 5000;

interface FlashcardData {
  id: number;
  question: string;
  reponse: string;
  explication?: string;
  matiere_id?: number;
  matiere_nom?: string;
  next_review?: string;
  ease_factor?: number;
  interval?: number;
  repetitions?: number;
}

interface Matiere {
  id: number;
  nom: string;
}

// Mapping couleurs des matières
const matiereColors: Record<string, { bg: string; text: string; border: string }> = {
  "Droit public": { bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/30" },
  "Économie et finances publiques": { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  "Questions contemporaines": { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/30" },
  "Questions sociales": { bg: "bg-rose-500/20", text: "text-rose-400", border: "border-rose-500/30" },
  "Relations internationales": { bg: "bg-violet-500/20", text: "text-violet-400", border: "border-violet-500/30" },
};

export default function FlashcardsPage() {
  const [flashcards, setFlashcards] = useState<FlashcardData[]>([]);
  const [matieres, setMatieres] = useState<Matiere[]>([]);
  const [selectedMatiere, setSelectedMatiere] = useState<number | null>(null);
  const [contentMode, setContentMode] = useState<"revision" | "all">("all");
  const [invertedSides, setInvertedSides] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<"list" | "review">("list");
  const [reviewedCount, setReviewedCount] = useState(0);
  const [sessionResults, setSessionResults] = useState<{ quality: number }[]>([]);
  const [revisionFilter, setRevisionFilter] = useState<"all" | "review" | "mastered">("all");
  const [flippedCards, setFlippedCards] = useState<Set<number>>(new Set());

  const toggleFlip = (id: number) => {
    setFlippedCards((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const fetchFlashcards = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(FETCH_LIMIT));
      if (selectedMatiere) {
        params.set("matiere_id", String(selectedMatiere));
      }
      const endpoint = contentMode === "revision" ? "flashcards/revision" : "flashcards";
      const url = `${API_BASE}/${endpoint}?${params.toString()}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const raw = Array.isArray(data) ? data : [];
        // Map backend field names to frontend expectations
        const mapped = raw.map((fc: any) => ({
          ...fc,
          ease_factor: fc.facteur_facilite ?? fc.ease_factor ?? 2.5,
          next_review: fc.prochaine_revision ?? fc.next_review,
          interval: fc.intervalle_jours ?? fc.interval,
        }));
        setFlashcards(mapped);
        setCurrentIndex(0);
      }
    } catch (error) {
      console.error("Erreur chargement flashcards:", error);
    } finally {
      setLoading(false);
    }
  }, [selectedMatiere, contentMode]);

  const fetchMatieres = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/matieres`);
      if (res.ok) {
        setMatieres(await res.json());
      }
    } catch (error) {
      console.error("Erreur chargement matieres:", error);
    }
  }, []);

  useEffect(() => {
    fetchMatieres();
  }, [fetchMatieres]);

  useEffect(() => {
    fetchFlashcards();
  }, [fetchFlashcards]);

  const handleReview = async (quality: number) => {
    const card = flashcards[currentIndex];
    if (!card) return;

    // Envoi de la notation au backend (SM-2)
    try {
      await fetch(`${API_BASE}/flashcards/${card.id}/review`, withAuthHeaders({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ qualite: quality }),
      }));
    } catch (error) {
      console.error("Erreur envoi review:", error);
    }

    setSessionResults((prev) => [...prev, { quality }]);
    setReviewedCount((prev) => prev + 1);

    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      // Session terminee
      setMode("list");
    }
  };

  const skipToNextCard = () => {
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      return;
    }
    setMode("list");
  };

  const startReview = () => {
    setCurrentIndex(0);
    setReviewedCount(0);
    setSessionResults([]);
    setMode("review");
  };

  const totalCards = flashcards.length;
  const progress = totalCards > 0 ? Math.round((currentIndex / totalCards) * 100) : 0;
  const avgQuality =
    sessionResults.length > 0
      ? (sessionResults.reduce((s, r) => s + r.quality, 0) / sessionResults.length).toFixed(1)
      : "0";
  const matiereBreakdown = useMemo(() => {
    const counts = new Map<string, number>();
    for (const card of flashcards) {
      const matiereName =
        card.matiere_nom ||
        matieres.find((m) => m.id === card.matiere_id)?.nom ||
        "Sans matiere";
      counts.set(matiereName, (counts.get(matiereName) || 0) + 1);
    }
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  }, [flashcards, matieres]);

  // Utilitaires pour les stats et filtres
  const getColorForMatiere = (matiereName?: string): { bg: string; text: string; border: string } => {
    if (!matiereName) return { bg: "bg-slate-500/20", text: "text-slate-400", border: "border-slate-500/30" };
    return matiereColors[matiereName] || { bg: "bg-slate-500/20", text: "text-slate-400", border: "border-slate-500/30" };
  };

  const getDifficultyStars = (easeFactor?: number) => {
    const factor = easeFactor || 2.5;
    const stars = Math.round((factor - 1.3) / 0.43); // Map 1.3-2.5 -> 1-5 stars
    return Math.max(1, Math.min(5, stars));
  };

  const getReviewIndicator = (nextReview?: string): { color: string; label: string } => {
    if (!nextReview) return { color: "text-slate-500", label: "Nouvelle" };
    const daysUntil = Math.floor((new Date(nextReview).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
    if (daysUntil < 0) return { color: "text-red-400", label: `Urgent (${daysUntil} j)` };
    if (daysUntil < 7) return { color: "text-amber-400", label: `Bientôt (${daysUntil} j)` };
    return { color: "text-emerald-400", label: "OK" };
  };

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const filteredFlashcards = useMemo(() => {
    return flashcards.filter((card) => {
      if (revisionFilter === "review") {
        if (!card.next_review) return true;
        const reviewDate = new Date(card.next_review);
        reviewDate.setHours(0, 0, 0, 0);
        return reviewDate <= today;
      }
      if (revisionFilter === "mastered") {
        return (card.ease_factor || 2.5) > 3.0;
      }
      return true;
    });
  }, [flashcards, revisionFilter]);

  const dueToday = useMemo(() => {
    return flashcards.filter((card) => {
      if (!card.next_review) return false;
      const reviewDate = new Date(card.next_review);
      reviewDate.setHours(0, 0, 0, 0);
      return reviewDate <= today;
    }).length;
  }, [flashcards]);

  const masteryRate = useMemo(() => {
    if (flashcards.length === 0) return 0;
    const mastered = flashcards.filter((c) => (c.ease_factor || 2.5) > 3.0).length;
    return Math.round((mastered / flashcards.length) * 100);
  }, [flashcards]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Chargement des flashcards...</p>
        </div>
      </div>
    );
  }

  // Mode revision
  if (mode === "review") {
    const currentCard = flashcards[currentIndex];
    const prompt = invertedSides ? currentCard?.reponse : currentCard?.question;
    const answer = invertedSides ? currentCard?.question : currentCard?.reponse;

    // Session terminee
    if (!currentCard || reviewedCount >= totalCards) {
      return (
        <div className="space-y-8">
          <div className="text-center py-12">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg className="w-10 h-10 text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Session terminee !</h2>
            <p className="text-slate-400 mb-6">
              Vous avez revise {reviewedCount} carte{reviewedCount > 1 ? "s" : ""}
            </p>

            {/* Stats session — 3 cols */}
            <div className="grid grid-cols-3 gap-3 max-w-sm mx-auto mb-8">
              <div className="card text-center py-3 px-2">
                <p className="text-2xl font-bold text-white">{reviewedCount}</p>
                <p className="text-xs text-slate-400">révisées</p>
              </div>
              <div className="card text-center py-3 px-2">
                <p className="text-2xl font-bold text-emerald-400">{sessionResults.filter(r => r.quality >= 4).length}</p>
                <p className="text-xs text-slate-400">maîtrisées</p>
              </div>
              <div className="card text-center py-3 px-2">
                <p className="text-2xl font-bold text-amber-400">{avgQuality}</p>
                <p className="text-xs text-slate-400">qualité /5</p>
              </div>
            </div>

            <div className="flex justify-center gap-3">
              <button onClick={() => setMode("list")} className="btn-secondary">
                Retour
              </button>
              <button
                onClick={() => {
                  fetchFlashcards();
                  startReview();
                }}
                className="btn-primary"
              >
                Nouvelle session
              </button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-4 max-w-2xl mx-auto">
        {/* Header révision */}
        <div className="flex items-center justify-between gap-2">
          <button onClick={() => setMode("list")} className="btn-ghost flex items-center gap-1.5 text-sm px-3">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
            Quitter
          </button>
          <div className="flex-1 text-center">
            {currentCard.matiere_nom && (
              <span className="badge-violet text-xs">{currentCard.matiere_nom}</span>
            )}
          </div>
          <div className="text-sm font-semibold tabular-nums px-3 py-1 rounded-lg bg-slate-800 text-slate-300 shrink-0">
            {currentIndex + 1}/{totalCards}
          </div>
        </div>

        {/* Barre de progression */}
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-violet-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Flashcard */}
        <div className="py-6">
          <FlashCard
            question={prompt || ""}
            reponse={answer || ""}
            explication={currentCard.explication}
            matiere={currentCard.matiere_nom}
            onReview={handleReview}
          />
        </div>
        <div className="flex justify-center">
          <button onClick={skipToNextCard} className="btn-ghost text-sm">
            Passer a la suivante
          </button>
        </div>
      </div>
    );
  }

  const goodCards = sessionResults.filter(r => r.quality >= 4).length;
  const hardCards = sessionResults.filter(r => r.quality <= 2).length;

  // Mode liste
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">Flashcards</h1>
          <p className="mt-1 text-slate-400">Révisez avec la répétition espacée (algorithme SM-2)</p>
        </div>
        {totalCards > 0 && (
          <button onClick={startReview} className="btn-primary flex items-center gap-2 shrink-0">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
            </svg>
            Réviser maintenant ({totalCards})
          </button>
        )}
      </div>

      {/* Bandeau stats session précédente */}
      {sessionResults.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <div className="card py-3 text-center border-violet-500/20 bg-violet-500/5">
            <p className="text-2xl font-bold text-violet-300">{sessionResults.length}</p>
            <p className="text-xs text-slate-400 mt-0.5">cartes révisées</p>
          </div>
          <div className="card py-3 text-center border-emerald-500/20 bg-emerald-500/5">
            <p className="text-2xl font-bold text-emerald-300">{goodCards}</p>
            <p className="text-xs text-slate-400 mt-0.5">bien maîtrisées</p>
          </div>
          <div className="card py-3 text-center border-red-500/20 bg-red-500/5">
            <p className="text-2xl font-bold text-red-300">{hardCards}</p>
            <p className="text-xs text-slate-400 mt-0.5">à retravailler</p>
          </div>
        </div>
      )}

      {/* Barre de stats en haut */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="card py-4 px-4 bg-blue-500/5 border-blue-500/20">
          <p className="text-2xl font-bold text-blue-400">{totalCards}</p>
          <p className="text-xs text-slate-400 mt-1">Total flashcards</p>
        </div>
        <div className={`card py-4 px-4 border ${dueToday > 0 ? "bg-red-500/5 border-red-500/20" : "bg-slate-700/50 border-slate-600/50"}`}>
          <p className={`text-2xl font-bold ${dueToday > 0 ? "text-red-400" : "text-slate-400"}`}>{dueToday}</p>
          <p className="text-xs text-slate-400 mt-1">À réviser aujourd'hui</p>
        </div>
        <div className="card py-4 px-4 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-2xl font-bold text-emerald-400">{masteryRate}%</p>
          <p className="text-xs text-slate-400 mt-1">Taux de maîtrise</p>
        </div>
      </div>

      {/* Filtres par état de révision */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setRevisionFilter("all")}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${revisionFilter === "all"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/40"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
            }
          `}
        >
          Toutes
        </button>
        <button
          onClick={() => setRevisionFilter("review")}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${revisionFilter === "review"
              ? "bg-red-600/20 text-red-400 border border-red-500/40"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
            }
          `}
        >
          À réviser ({dueToday})
        </button>
        <button
          onClick={() => setRevisionFilter("mastered")}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${revisionFilter === "mastered"
              ? "bg-emerald-600/20 text-emerald-400 border border-emerald-500/40"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
            }
          `}
        >
          Maîtrisées
        </button>
      </div>

      {/* Ancien filtre mode contenu */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setContentMode("all")}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${contentMode === "all"
              ? "bg-violet-600/20 text-violet-300 border border-violet-500/40"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
            }
          `}
        >
          Toutes les cartes
        </button>
        <button
          onClick={() => setContentMode("revision")}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${contentMode === "revision"
              ? "bg-violet-600/20 text-violet-300 border border-violet-500/40"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
            }
          `}
        >
          Cartes a reviser
        </button>
        <button
          onClick={() => setInvertedSides((prev) => !prev)}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 bg-slate-800 text-slate-300 border border-slate-700 hover:border-slate-600"
        >
          Inverser Q/R: {invertedSides ? "ON" : "OFF"}
        </button>
      </div>
      {matiereBreakdown.length > 0 && (
        <p className="text-xs text-slate-500">
          Repartition chargee: {matiereBreakdown.map(([name, count]) => `${name} (${count})`).join(" · ")}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedMatiere(null)}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${!selectedMatiere
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
            }
          `}
        >
          Toutes
        </button>
        {matieres.map((matiere) => (
          <button
            key={matiere.id}
            onClick={() => setSelectedMatiere(matiere.id)}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              ${selectedMatiere === matiere.id
                ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
              }
            `}
          >
            {matiere.nom}
          </button>
        ))}
      </div>

      {/* Stats session precedente */}
      {sessionResults.length > 0 && (
        <div className="card bg-gradient-to-r from-violet-500/5 to-blue-500/5 border-violet-500/20">
          <div className="flex items-center gap-3 mb-2">
            <svg className="w-5 h-5 text-violet-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
            <h3 className="font-semibold text-violet-300">Derniere session</h3>
          </div>
          <p className="text-sm text-slate-400">
            {sessionResults.length} cartes revisees - Qualite moyenne : {avgQuality}/5
          </p>
        </div>
      )}

      {/* Liste ou etat vide */}
      {filteredFlashcards.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
          </svg>
          <h3 className="text-lg font-semibold text-slate-300 mb-2">
            {revisionFilter === "review"
              ? "Aucune flashcard à réviser"
              : revisionFilter === "mastered"
              ? "Aucune flashcard maîtrisée"
              : contentMode === "revision"
              ? "Aucune flashcard a reviser"
              : "Aucune flashcard disponible"}
          </h3>
          <p className="text-slate-500 max-w-md mx-auto">
            {revisionFilter !== "all"
              ? "Essayez un autre filtre pour trouver des flashcards."
              : contentMode === "revision"
              ? "Passez en mode 'Toutes les cartes' pour travailler au-dela des revisions urgentes."
              : "Importez des documents dans vos matieres pour generer automatiquement des flashcards."}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {(() => {
            const groups = new Map<string, FlashcardData[]>();
            for (const card of filteredFlashcards) {
              const key = card.matiere_nom || matieres.find(m => m.id === card.matiere_id)?.nom || "Sans matière";
              if (!groups.has(key)) groups.set(key, []);
              groups.get(key)!.push(card);
            }
            return Array.from(groups.entries()).map(([matiereName, cards]) => (
              <div key={matiereName} className="space-y-3">
                <div className="flex items-center gap-3">
                  <h2 className="text-lg font-semibold text-white">{matiereName}</h2>
                  <span className="badge-blue">{cards.length} carte{cards.length > 1 ? "s" : ""}</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {cards.map((card) => {
                    const colors = getColorForMatiere(matiereName);
                    const stars = getDifficultyStars(card.ease_factor);
                    const indicator = getReviewIndicator(card.next_review);
                    const isFlipped = flippedCards.has(card.id);
                    return (
                      <div
                        key={card.id}
                        onClick={() => toggleFlip(card.id)}
                        className="cursor-pointer select-none h-[180px]"
                      >
                        {!isFlipped ? (
                          /* Face avant — question */
                          <div className="h-full rounded-xl border border-slate-700/80 bg-slate-800/70 p-4 flex flex-col transition-all duration-200 hover:border-blue-500/40 hover:shadow-lg hover:shadow-blue-500/5">
                            <div className="flex items-start justify-between gap-2 mb-2">
                              <div className={`inline-block px-2 py-0.5 rounded-md text-xs font-semibold border ${colors.bg} ${colors.text} ${colors.border}`}>
                                {matiereName}
                              </div>
                              <div className="flex items-center gap-0.5 shrink-0">
                                {Array.from({ length: 5 }).map((_, i) => (
                                  <svg key={i} className={`w-3 h-3 ${i < stars ? "text-amber-400 fill-current" : "text-slate-700"}`} viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" />
                                  </svg>
                                ))}
                              </div>
                            </div>
                            <p className="text-sm font-medium text-slate-200 line-clamp-3 flex-1">{card.question}</p>
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-[10px] text-slate-600 flex items-center gap-1">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" stroke="currentColor" strokeWidth="1.5"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7s-8.268-2.943-9.542-7Z" stroke="currentColor" strokeWidth="1.5"/></svg>
                                Cliquer pour la réponse
                              </span>
                              <span className={`text-xs font-medium ${indicator.color}`}>{indicator.label}</span>
                            </div>
                          </div>
                        ) : (
                          /* Face arrière — réponse */
                          <div className="h-full rounded-xl border border-violet-500/30 bg-violet-900/20 p-4 flex flex-col transition-all duration-200">
                            <div className="text-[10px] font-semibold uppercase tracking-widest text-violet-400 mb-2">Réponse</div>
                            <p className="text-sm text-violet-100 flex-1 overflow-y-auto leading-relaxed">{card.reponse}</p>
                            {card.explication && (
                              <p className="text-xs text-slate-400 mt-2 border-t border-violet-500/20 pt-2 line-clamp-2">{card.explication}</p>
                            )}
                            <span className="text-[10px] text-violet-500 mt-2">↩ Cliquer pour revenir</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ));
          })()}
        </div>
      )}
    </div>
  );
}
