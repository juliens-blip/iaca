"use client";

import { useState } from "react";

interface QuizQuestionProps {
  question: string;
  choix: string[];
  reponse_correcte: number;
  explication?: string;
  onAnswer: (selectedIndex: number, isCorrect: boolean) => void;
}

export default function QuizQuestion({
  question,
  choix,
  reponse_correcte,
  explication,
  onAnswer,
}: QuizQuestionProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [hasAnswered, setHasAnswered] = useState(false);

  const handleSelect = (index: number) => {
    if (hasAnswered) return;
    setSelectedIndex(index);
  };

  const handleValidate = () => {
    if (selectedIndex === null || hasAnswered) return;
    setHasAnswered(true);
    const isCorrect = selectedIndex === reponse_correcte;
    onAnswer(selectedIndex, isCorrect);
  };

  const getChoiceStyle = (index: number) => {
    const base =
      "flex items-center gap-4 w-full p-4 rounded-xl border-2 transition-all duration-200 text-left";

    if (!hasAnswered) {
      if (selectedIndex === index) {
        return `${base} border-blue-500 bg-blue-500/10 text-blue-100 shadow-md shadow-blue-500/10`;
      }
      return `${base} border-slate-700 bg-slate-800/40 text-slate-300 hover:border-slate-500 hover:bg-slate-800/60 cursor-pointer`;
    }

    // Apres validation
    if (index === reponse_correcte) {
      return `${base} border-emerald-500 bg-emerald-500/10 text-emerald-100 shadow-md shadow-emerald-500/10`;
    }
    if (index === selectedIndex && index !== reponse_correcte) {
      return `${base} border-red-500 bg-red-500/10 text-red-100 shadow-md shadow-red-500/10`;
    }
    return `${base} border-slate-700/50 bg-slate-800/20 text-slate-500`;
  };

  const getRadioStyle = (index: number) => {
    const base =
      "w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all duration-200";

    if (!hasAnswered) {
      if (selectedIndex === index) {
        return `${base} border-blue-500 bg-blue-500`;
      }
      return `${base} border-slate-600`;
    }

    if (index === reponse_correcte) {
      return `${base} border-emerald-500 bg-emerald-500`;
    }
    if (index === selectedIndex && index !== reponse_correcte) {
      return `${base} border-red-500 bg-red-500`;
    }
    return `${base} border-slate-700`;
  };

  const letters = ["A", "B", "C", "D", "E", "F"];

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Question - hierarchie typographique (charte 3.1) */}
      <div className="card border-slate-600/50">
        <h3 className="text-lg font-semibold text-white leading-7">
          {question}
        </h3>
      </div>

      {/* Choix */}
      <div className="space-y-3">
        {choix.map((choice, index) => (
          <button
            key={index}
            onClick={() => handleSelect(index)}
            disabled={hasAnswered}
            className={getChoiceStyle(index)}
          >
            <div className={getRadioStyle(index)}>
              {((!hasAnswered && selectedIndex === index) ||
                (hasAnswered && index === reponse_correcte)) && (
                <svg
                  className="w-3.5 h-3.5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={3}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4.5 12.75l6 6 9-13.5"
                  />
                </svg>
              )}
              {hasAnswered &&
                index === selectedIndex &&
                index !== reponse_correcte && (
                  <svg
                    className="w-3.5 h-3.5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={3}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                )}
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-bold opacity-50">{letters[index]}.</span>
              <span className="text-sm font-medium">{choice}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Bouton valider */}
      {!hasAnswered && (
        <div className="flex justify-center">
          <button
            onClick={handleValidate}
            disabled={selectedIndex === null}
            className={`
              btn-primary px-8 py-3 text-base
              ${selectedIndex === null ? "opacity-40 cursor-not-allowed" : ""}
            `}
          >
            Valider la reponse
          </button>
        </div>
      )}

      {/* Resultat + Explication */}
      {hasAnswered && (
        <div className="space-y-3">
          {/* Message resultat */}
          <div
            className={`
              p-4 rounded-xl border flex items-center gap-3
              ${
                selectedIndex === reponse_correcte
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-red-500/10 border-red-500/30 text-red-300"
              }
            `}
          >
            {selectedIndex === reponse_correcte ? (
              <>
                <svg className="w-6 h-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">Bonne reponse !</span>
              </>
            ) : (
              <>
                <svg className="w-6 h-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">
                  Mauvaise reponse. La bonne reponse etait : {letters[reponse_correcte]}. {choix[reponse_correcte]}
                </span>
              </>
            )}
          </div>

          {/* Explication - encadre semantique (charte 5.1) */}
          {explication && (
            <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-5">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 shrink-0 mt-0.5">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">Explication</p>
                  <p className="text-sm text-slate-200 leading-relaxed">{explication}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
