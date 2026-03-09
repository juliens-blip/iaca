"use client";

import { useState } from "react";

interface FlashCardProps {
  question: string;
  reponse: string;
  explication?: string;
  matiere?: string;
  onReview: (quality: number) => void;
}

const quickRatings = [
  { quality: 1, label: "Difficile", color: "bg-red-600 hover:bg-red-500 border-red-500/40 shadow-red-900/20", icon: "M" },
  { quality: 3, label: "Moyen", color: "bg-amber-600 hover:bg-amber-500 border-amber-500/40 shadow-amber-900/20", icon: "M" },
  { quality: 5, label: "Facile", color: "bg-emerald-600 hover:bg-emerald-500 border-emerald-500/40 shadow-emerald-900/20", icon: "M" },
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
      {/* Badge matiere */}
      {matiere && (
        <div className="mb-4 flex justify-center">
          <span className="badge-blue">{matiere}</span>
        </div>
      )}

      {/* Card avec flip */}
      <div
        className="flip-card cursor-pointer min-h-[280px]"
        style={{ minHeight: "280px" }}
        onClick={handleFlip}
      >
        <div className={`flip-card-inner ${isFlipped ? "flipped" : ""}`}>
          {/* Face avant - Question */}
          <div className="flip-card-front">
            <div className="card h-full flex flex-col items-center justify-center text-center border-blue-500/20 glow-blue">
              <div className="mb-4">
                <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                  Question
                </span>
              </div>
              <p className="text-xl font-medium text-slate-100 leading-relaxed px-4">
                {question}
              </p>
              <div className="mt-auto pt-6 flex flex-col items-center gap-1 text-slate-500">
                <span className="text-xs">Cliquez pour reveler</span>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  className="animate-bounce"
                >
                  <path
                    d="M12 5v14M5 12l7 7 7-7"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Face arriere - Reponse */}
          <div className="flip-card-back">
            <div className="card h-full flex flex-col items-center justify-center text-center border-violet-500/20 glow-violet">
              <div className="mb-4">
                <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">
                  Reponse
                </span>
              </div>
              <p className="text-xl font-medium text-slate-100 leading-relaxed px-4">
                {reponse}
              </p>

              {/* Explication */}
              {explication && (
                <div className="mt-4 w-full px-4">
                  {!showExplication ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowExplication(true);
                      }}
                      className="text-sm text-violet-400 hover:text-violet-300 underline underline-offset-2 transition-colors"
                    >
                      Voir l&apos;explication
                    </button>
                  ) : (
                    <div className="mt-2 p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
                      <p className="text-sm text-slate-300 leading-relaxed">
                        {explication}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Boutons de notation - visibles apres flip */}
      {isFlipped && (
        <div className="mt-6 space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <p className="text-center text-sm text-slate-400 font-medium">
            Evaluez votre connaissance
          </p>
          <div className="flex justify-center gap-3">
            {quickRatings.map(({ quality, label, color }) => (
              <button
                key={quality}
                onClick={(e) => {
                  e.stopPropagation();
                  handleReview(quality);
                }}
                className={`
                  flex flex-col items-center gap-1.5 px-6 py-3 rounded-xl text-white font-semibold
                  transition-all duration-200 shadow-lg hover:shadow-xl active:scale-95
                  border ${color}
                `}
              >
                <span className="text-lg">{quality}</span>
                <span className="text-xs opacity-90 font-normal">{label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
