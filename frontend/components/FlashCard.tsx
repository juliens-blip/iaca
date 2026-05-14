"use client";

import { useState } from "react";

interface FlashCardProps {
  question: string;
  reponse: string;
  explication?: string;
  matiere?: string;
  onReview: (quality: number) => void;
}

// Couleurs par matiere - contraste de pertinence (charte section 2.1)
const matiereStyles: Record<string, { bg: string; text: string; border: string; gradient: string }> = {
  "Droit public": {
    bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30",
    gradient: "from-blue-600/15 to-blue-900/5",
  },
  "Economie et finances publiques": {
    bg: "bg-emerald-500/15", text: "text-emerald-400", border: "border-emerald-500/30",
    gradient: "from-emerald-600/15 to-emerald-900/5",
  },
  "\u00c9conomie et finances publiques": {
    bg: "bg-emerald-500/15", text: "text-emerald-400", border: "border-emerald-500/30",
    gradient: "from-emerald-600/15 to-emerald-900/5",
  },
  "Questions contemporaines": {
    bg: "bg-amber-500/15", text: "text-amber-400", border: "border-amber-500/30",
    gradient: "from-amber-600/15 to-amber-900/5",
  },
  "Questions sociales": {
    bg: "bg-rose-500/15", text: "text-rose-400", border: "border-rose-500/30",
    gradient: "from-rose-600/15 to-rose-900/5",
  },
  "Relations internationales": {
    bg: "bg-violet-500/15", text: "text-violet-400", border: "border-violet-500/30",
    gradient: "from-violet-600/15 to-violet-900/5",
  },
};

const defaultStyle = {
  bg: "bg-slate-500/15", text: "text-slate-400", border: "border-slate-500/30",
  gradient: "from-slate-600/15 to-slate-900/5",
};

const quickRatings = [
  {
    quality: 1, label: "Difficile",
    bg: "bg-rose-600 hover:bg-rose-500",
    border: "border-rose-500/40",
    icon: "M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  },
  {
    quality: 3, label: "Moyen",
    bg: "bg-amber-600 hover:bg-amber-500",
    border: "border-amber-500/40",
    icon: "M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  },
  {
    quality: 5, label: "Facile",
    bg: "bg-emerald-600 hover:bg-emerald-500",
    border: "border-emerald-500/40",
    icon: "M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  },
];

export default function FlashCard({
  question,
  reponse,
  explication,
  matiere,
  onReview,
}: FlashCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [showExplication, setShowExplication] = useState(false);

  const style = matiere ? (matiereStyles[matiere] || defaultStyle) : defaultStyle;

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const handleReview = (quality: number) => {
    setIsFlipped(false);
    setShowExplication(false);
    onReview(quality);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Badge matiere - couleur fonctionnelle (charte 2.1) */}
      {matiere && (
        <div className="mb-4 flex justify-center">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ${style.bg} ${style.text} ${style.border}`}>
            {matiere}
          </span>
        </div>
      )}

      {/* Card avec flip */}
      <div
        className="flip-card cursor-pointer min-h-[280px]"
        style={{ minHeight: "280px" }}
        onClick={handleFlip}
      >
        <div className={`flip-card-inner ${isFlipped ? "flipped" : ""}`}>
          {/* Face avant - Question : gradient matiere (charte 5.2) */}
          <div className="flip-card-front">
            <div className={`card h-full flex flex-col items-center justify-center text-center border ${style.border} bg-gradient-to-br ${style.gradient}`}>
              <div className="mb-4">
                <span className={`text-xs font-semibold ${style.text} uppercase tracking-wider`}>
                  Question
                </span>
              </div>
              <p className="text-xl font-semibold text-slate-100 leading-relaxed px-6 max-w-prose">
                {question}
              </p>
              {/* Indicateur subtil sans animation decorative (anti-pattern #5) */}
              <div className="mt-auto pt-6 flex items-center gap-2 text-slate-500">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 0 0-3.7-3.7 48.678 48.678 0 0 0-7.324 0 4.006 4.006 0 0 0-3.7 3.7c-.017.22-.032.441-.046.662M19.5 12l3-3m-3 3-3-3m-12 3c0 1.232.046 2.453.138 3.662a4.006 4.006 0 0 0 3.7 3.7 48.656 48.656 0 0 0 7.324 0 4.006 4.006 0 0 0 3.7-3.7c.017-.22.032-.441.046-.662M4.5 12l3 3m-3-3-3 3" />
                </svg>
                <span className="text-xs">Cliquer pour retourner</span>
              </div>
            </div>
          </div>

          {/* Face arriere - Reponse : fond neutre (charte 5.2) */}
          <div className="flip-card-back">
            <div className="card h-full flex flex-col items-center justify-center text-center border-slate-700/50 bg-slate-800/60">
              <div className="mb-4">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Reponse
                </span>
              </div>
              <p className="text-lg text-slate-200 leading-7 px-6 max-w-prose">
                {reponse}
              </p>

              {/* Explication dans encadre semantique (charte 5.1) */}
              {explication && (
                <div className="mt-5 w-full px-5">
                  {!showExplication ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowExplication(true);
                      }}
                      className="text-sm text-blue-400 hover:text-blue-300 transition-colors duration-200 flex items-center gap-1.5 mx-auto"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                      </svg>
                      Voir l&apos;explication
                    </button>
                  ) : (
                    <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-left">
                      <div className="flex items-start gap-3">
                        <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 shrink-0 mt-0.5">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">Explication</p>
                          <p className="text-sm text-slate-300 leading-relaxed">
                            {explication}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Boutons de notation avec icones (charte 7.3 - micro-feedback) */}
      {isFlipped && (
        <div className="mt-6 space-y-3">
          <p className="text-center text-sm text-slate-400 font-medium">
            Evaluez votre connaissance
          </p>
          <div className="flex justify-center gap-3">
            {quickRatings.map(({ quality, label, bg, border, icon }) => (
              <button
                key={quality}
                onClick={(e) => {
                  e.stopPropagation();
                  handleReview(quality);
                }}
                className={`
                  flex flex-col items-center gap-2 px-6 py-3 rounded-xl text-white font-semibold
                  transition-all duration-200 shadow-lg hover:shadow-xl active:scale-95
                  border ${border} ${bg}
                `}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                </svg>
                <span className="text-xs font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
