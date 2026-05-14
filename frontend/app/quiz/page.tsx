"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import QuizQuestion from "@/components/QuizQuestion";
import { withAuthHeaders } from "@/lib/auth";

const API_BASE = "/api";

const matiereColors = {
  "Droit public": { bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/30" },
  "Économie et finances publiques": { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  "Questions contemporaines": { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/30" },
  "Questions sociales": { bg: "bg-rose-500/20", text: "text-rose-400", border: "border-rose-500/30" },
  "Relations internationales": { bg: "bg-violet-500/20", text: "text-violet-400", border: "border-violet-500/30" },
};

interface Matiere {
  id: number;
  nom: string;
}

interface QuizQuestionData {
  id: number;
  quiz_id: number;
  question: string;
  choix: string[];
  reponse_correcte: number;
  explication?: string | null;
  difficulte?: number | null;
}

interface QuizData {
  id: number;
  titre: string;
  matiere_id: number | null;
  document_id: number | null;
  created_at: string;
  questions: QuizQuestionData[];
}

interface QuizAnswer {
  question_id: number;
  reponse: number;
}

interface QuizResultDetail {
  question_id: number;
  question: string;
  reponse_donnee: number;
  reponse_correcte: number;
  correct: boolean;
  explication?: string | null;
}

interface QuizResult {
  score: number;
  total: number;
  details: QuizResultDetail[];
}

export default function QuizPage() {
  const [matieres, setMatieres] = useState<Matiere[]>([]);
  const [selectedMatiere, setSelectedMatiere] = useState<number | null>(null);
  const [quizzes, setQuizzes] = useState<QuizData[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingQuizzes, setLoadingQuizzes] = useState(false);
  const [search, setSearch] = useState("");
  const [mode, setMode] = useState<"list" | "quiz" | "result">("list");
  const [activeQuiz, setActiveQuiz] = useState<QuizData | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<QuizAnswer[]>([]);
  const [currentAnswered, setCurrentAnswered] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set());

  const getMatiereName = useCallback(
    (matiereId: number | null) => {
      if (!matiereId) return "General";
      return matieres.find((m) => m.id === matiereId)?.nom || "General";
    },
    [matieres]
  );

  const getMatiereColor = useCallback(
    (matiereId: number | null) => {
      const name = getMatiereName(matiereId);
      return (matiereColors as Record<string, typeof matiereColors["Droit public"]>)[name] ||
        { bg: "bg-slate-500/20", text: "text-slate-400", border: "border-slate-500/30" };
    },
    [getMatiereName]
  );

  const fetchMatieres = useCallback(async () => {
    const res = await fetch(`${API_BASE}/matieres`);
    if (!res.ok) return [];
    return (await res.json()) as Matiere[];
  }, []);

  const fetchQuizzes = useCallback(async (matiereId: number | null) => {
    setLoadingQuizzes(true);
    try {
      const base = `${API_BASE}/quiz?limit=5000`;
      const url =
        matiereId === null
          ? base
          : `${base}&matiere_id=${matiereId}`;
      const res = await fetch(url);
      if (!res.ok) {
        setQuizzes([]);
        return;
      }
      const data = (await res.json()) as QuizData[];
      setQuizzes(data);
    } catch (error) {
      console.error("Erreur chargement quiz:", error);
      setQuizzes([]);
    } finally {
      setLoadingQuizzes(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const list = await fetchMatieres();
        setMatieres(list);

        const params = new URLSearchParams(window.location.search);
        const fromUrl = params.get("matiere_id");
        if (fromUrl) {
          setSelectedMatiere(parseInt(fromUrl, 10));
          return;
        }
        setSelectedMatiere(null);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [fetchMatieres]);

  useEffect(() => {
    if (mode !== "list") return;
    fetchQuizzes(selectedMatiere);
  }, [selectedMatiere, fetchQuizzes, mode]);

  const filteredQuizzes = useMemo(() => {
    const text = search.trim().toLowerCase();
    if (!text) return quizzes;
    return quizzes.filter((quiz) => {
      const inTitle = quiz.titre.toLowerCase().includes(text);
      const inQuestions = quiz.questions.some((q) =>
        q.question.toLowerCase().includes(text)
      );
      return inTitle || inQuestions;
    });
  }, [quizzes, search]);

  const quizCount = filteredQuizzes.length;
  const questionCount = filteredQuizzes.reduce(
    (sum, quiz) => sum + quiz.questions.length,
    0
  );

  const startQuiz = (quiz: QuizData) => {
    setActiveQuiz(quiz);
    setCurrentQuestionIndex(0);
    setAnswers([]);
    setCurrentAnswered(false);
    setResult(null);
    setMode("quiz");
  };

  const resetToList = () => {
    setActiveQuiz(null);
    setCurrentQuestionIndex(0);
    setAnswers([]);
    setCurrentAnswered(false);
    setResult(null);
    setMode("list");
  };

  const handleAnswer = (selectedIndex: number) => {
    if (!activeQuiz) return;
    const question = activeQuiz.questions[currentQuestionIndex];
    if (!question || currentAnswered) return;

    setAnswers((prev) => [
      ...prev,
      {
        question_id: question.id,
        reponse: selectedIndex,
      },
    ]);
    setCurrentAnswered(true);
  };

  const submitQuiz = async (finalAnswers: QuizAnswer[]) => {
    if (!activeQuiz) return;
    try {
      const res = await fetch(
        `${API_BASE}/quiz/${activeQuiz.id}/submit`,
        withAuthHeaders({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reponses: finalAnswers }),
        })
      );

      if (res.ok) {
        const payload = (await res.json()) as QuizResult;
        setResult(payload);
        setMode("result");
        return;
      }
    } catch (error) {
      console.error("Erreur soumission quiz:", error);
    }

    // Fallback local score if API submit fails
    if (!activeQuiz) return;
    const details: QuizResultDetail[] = activeQuiz.questions.map((q) => {
      const given = finalAnswers.find((a) => a.question_id === q.id)?.reponse ?? -1;
      return {
        question_id: q.id,
        question: q.question,
        reponse_donnee: given,
        reponse_correcte: q.reponse_correcte,
        correct: given === q.reponse_correcte,
        explication: q.explication,
      };
    });
    const score = details.filter((d) => d.correct).length;
    setResult({ score, total: details.length, details });
    setMode("result");
  };

  const goToNextQuestion = () => {
    if (!activeQuiz) return;
    if (!currentAnswered) return;

    const isLast = currentQuestionIndex >= activeQuiz.questions.length - 1;
    if (isLast) {
      void submitQuiz(answers);
      return;
    }
    setCurrentQuestionIndex((prev) => prev + 1);
    setCurrentAnswered(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Chargement des quiz...</p>
        </div>
      </div>
    );
  }

  if (mode === "result" && result && activeQuiz) {
    const percent = result.total > 0 ? Math.round((result.score / result.total) * 100) : 0;
    const matiereColor = getMatiereColor(activeQuiz.matiere_id);

    // Progress circle colors: green >70%, orange >40%, red <40%
    let circleColor = "text-rose-400";
    let circleBg = "bg-rose-500/20";
    if (percent >= 70) {
      circleColor = "text-emerald-400";
      circleBg = "bg-emerald-500/20";
    } else if (percent >= 40) {
      circleColor = "text-amber-400";
      circleBg = "bg-amber-500/20";
    }

    const radius = 45;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percent / 100) * circumference;

    return (
      <div className="space-y-6 max-w-3xl mx-auto">
        <div className={`card border-2 ${matiereColor.border} ${matiereColor.bg}`}>
          <p className={`text-sm ${matiereColor.text} mb-2`}>{getMatiereName(activeQuiz.matiere_id)}</p>
          <h1 className="text-2xl font-bold text-white mb-2 font-heading">Quiz termine</h1>
          <p className="text-slate-300 text-sm mb-6">{activeQuiz.titre}</p>

          {/* Progress circle */}
          <div className="flex flex-col items-center mb-6">
            <div className="relative w-32 h-32">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
                <circle
                  cx="60"
                  cy="60"
                  r={radius}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-slate-700"
                />
                <circle
                  cx="60"
                  cy="60"
                  r={radius}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset}
                  strokeLinecap="round"
                  className={`${circleColor} transition-all duration-1000`}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className={`text-3xl font-bold ${circleColor}`}>{percent}%</p>
                <p className="text-xs text-slate-400">réussite</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="card py-3 text-center border-blue-500/20 bg-blue-500/5">
              <p className="text-2xl font-bold text-blue-300">
                {result.score}/{result.total}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">score</p>
            </div>
            <div className="card py-3 text-center border-rose-500/20 bg-rose-500/5">
              <p className="text-2xl font-bold text-rose-300">{result.total - result.score}</p>
              <p className="text-xs text-slate-400 mt-0.5">à revoir</p>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={resetToList} className="btn-secondary flex-1">
              Retour à la liste
            </button>
            <button onClick={() => startQuiz(activeQuiz)} className="btn-primary flex-1">
              Refaire ce quiz
            </button>
          </div>
        </div>

        {/* Detailed answers */}
        <div className="card">
          <h2 className="text-white font-semibold mb-4">Détail des réponses</h2>
          <div className="space-y-2">
            {result.details.map((item, idx) => {
              const isCorrect = item.correct;
              const isExpanded = expandedQuestions.has(item.question_id);
              const toggleExpanded = () => {
                const newSet = new Set(expandedQuestions);
                if (newSet.has(item.question_id)) {
                  newSet.delete(item.question_id);
                } else {
                  newSet.add(item.question_id);
                }
                setExpandedQuestions(newSet);
              };

              return (
                <div
                  key={item.question_id}
                  className={`p-3 rounded-lg border ${
                    isCorrect
                      ? "border-emerald-500/30 bg-emerald-500/10"
                      : "border-rose-500/30 bg-rose-500/10"
                  }`}
                >
                  <button
                    onClick={toggleExpanded}
                    className="w-full text-left flex items-start gap-2 group"
                  >
                    <div className="mt-0.5">
                      {isCorrect ? (
                        <svg className="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4 text-rose-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 leading-tight">
                        <span className="font-medium">Q{idx + 1}.</span> {item.question}
                      </p>
                    </div>
                    <svg
                      className={`w-4 h-4 text-slate-500 flex-shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  </button>

                  {isExpanded && item.explication && (
                    <div className="mt-3 pt-3 border-t border-slate-700/50">
                      <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4">
                        <div className="flex items-start gap-3">
                          <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 shrink-0 mt-0.5">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                            </svg>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">Explication</p>
                            <p className="text-sm text-slate-200 leading-relaxed">{item.explication}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  if (mode === "quiz" && activeQuiz) {
    const total = activeQuiz.questions.length;
    const current = activeQuiz.questions[currentQuestionIndex];
    const progress = total > 0 ? Math.round(((currentQuestionIndex + 1) / total) * 100) : 0;
    const matiereColor = getMatiereColor(activeQuiz.matiere_id);

    if (!current) {
      return (
        <div className="card text-center">
          <p className="text-slate-300">Quiz vide.</p>
          <button onClick={resetToList} className="btn-secondary mt-4">
            Retour
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-4 max-w-2xl mx-auto">
        {/* Progress bar at top */}
        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-violet-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Header with quit, title, and matière */}
        <div className="flex items-center justify-between gap-2 px-1">
          <button onClick={resetToList} className="btn-ghost flex items-center gap-1.5 text-sm px-2 -ml-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
            Quitter
          </button>
          <div className="min-w-0 flex-1 text-center">
            <p className="text-sm font-medium text-slate-300 truncate">{activeQuiz.titre}</p>
          </div>
          <span className={`badge text-xs px-2.5 py-1 rounded-full ${matiereColor.bg} ${matiereColor.text}`}>
            {getMatiereName(activeQuiz.matiere_id)}
          </span>
        </div>

        {/* Question counter */}
        <div className="flex justify-between items-center px-1">
          <p className="text-xs text-slate-500 font-medium">
            Question {currentQuestionIndex + 1} sur {total}
          </p>
          <p className="text-xs text-slate-400">{progress}%</p>
        </div>

        {/* Question component */}
        <QuizQuestion
          key={current.id}
          question={current.question}
          choix={current.choix}
          reponse_correcte={current.reponse_correcte}
          explication={current.explication || ""}
          onAnswer={(selectedIndex) => handleAnswer(selectedIndex)}
        />

        {/* Navigation button */}
        <div className="flex justify-end pt-2">
          <button
            onClick={goToNextQuestion}
            disabled={!currentAnswered}
            className={`btn-primary ${!currentAnswered ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            {currentQuestionIndex >= total - 1 ? "Voir le résultat" : "Question suivante"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white font-heading">Quiz</h1>
          <p className="mt-1 text-slate-400">
            Lancez des sessions ciblees par matiere et validez vos acquis.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="card py-2 px-4 text-center">
            <p className="text-lg font-bold text-violet-300">{quizCount}</p>
            <p className="text-xs text-slate-400">quiz</p>
          </div>
          <div className="card py-2 px-4 text-center">
            <p className="text-lg font-bold text-blue-300">{questionCount}</p>
            <p className="text-xs text-slate-400">questions</p>
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <input
          className="input-field w-full"
          placeholder="Rechercher un quiz ou une question..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input-field w-full"
          value={selectedMatiere ?? ""}
          onChange={(e) => {
            const value = e.target.value;
            setSelectedMatiere(value ? parseInt(value, 10) : null);
          }}
        >
          <option value="">Toutes les matieres</option>
          {matieres.map((m) => (
            <option key={m.id} value={m.id}>
              {m.nom}
            </option>
          ))}
        </select>
      </div>

      {loadingQuizzes ? (
        <div className="card text-center">
          <p className="text-slate-400">Chargement des quiz...</p>
        </div>
      ) : filteredQuizzes.length === 0 ? (
        <div className="card text-center border-dashed border-slate-600/60">
          <h2 className="text-white font-semibold mb-1">Aucun quiz trouvé</h2>
          <p className="text-sm text-slate-400">
            Changez de matière ou réduisez votre recherche.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {(() => {
            // Group quizzes by matière using string keys
            const groupedByMatiere = filteredQuizzes.slice(0, 120).reduce(
              (acc, quiz) => {
                const key = quiz.matiere_id === null ? "null" : String(quiz.matiere_id);
                if (!acc[key]) {
                  acc[key] = [];
                }
                acc[key].push(quiz);
                return acc;
              },
              {} as Record<string, QuizData[]>
            );

            // Sort by matière order
            const sortedMatiereIds = Object.keys(groupedByMatiere)
              .map((id) => (id === "null" ? null : parseInt(id, 10)))
              .sort((a, b) => {
                if (a === null) return 1;
                if (b === null) return -1;
                return a - b;
              });

            return sortedMatiereIds.map((matiereId) => {
              const key = matiereId === null ? "null" : String(matiereId);
              const quizzesInMatiere = groupedByMatiere[key];
              const matiereColor = getMatiereColor(matiereId);
              const matiereName = getMatiereName(matiereId);

              return (
                <div key={key}>
                  <div className={`mb-4 pb-3 border-b-2 ${matiereColor.border}`}>
                    <h2 className={`text-lg font-semibold ${matiereColor.text}`}>
                      {matiereName}
                    </h2>
                    <p className="text-xs text-slate-500 mt-1">
                      {quizzesInMatiere.length} quiz disponible{quizzesInMatiere.length > 1 ? "s" : ""}
                    </p>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {quizzesInMatiere.map((quiz: QuizData) => (
                      <div
                        key={quiz.id}
                        className={`card-hover flex flex-col gap-4 border-2 ${matiereColor.border} ${matiereColor.bg} group`}
                      >
                        <div className="space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <h3 className="text-white font-semibold line-clamp-2">{quiz.titre}</h3>
                              <p className="text-xs text-slate-500 mt-1">
                                {new Date(quiz.created_at).toLocaleDateString("fr-FR")}
                              </p>
                            </div>
                            <span className={`badge text-xs px-2 py-1 rounded-full ${matiereColor.bg} ${matiereColor.text} flex-shrink-0 whitespace-nowrap`}>
                              {matiereName}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 pt-1">
                            <svg className="w-4 h-4 text-slate-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 1 1 0 000 2H6a6 6 0 016 6v3.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 111.414-1.414L12 14.586V11a4 4 0 00-4-4H6a1 1 0 000-2H4a2 2 0 00-2 2v11a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2h-2.586A1 1 0 0016 2h-3.586a1 1 0 00-.707.293L9.172 3.879A6 6 0 004 9v8a2 2 0 01-2-2V5z" clipRule="evenodd" />
                            </svg>
                            <span className="text-sm text-slate-300 font-medium">
                              {quiz.questions.length} question{quiz.questions.length > 1 ? "s" : ""}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => startQuiz(quiz)}
                          className="btn-primary w-full"
                        >
                          Commencer
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              );
            });
          })()}
        </div>
      )}
    </div>
  );
}
