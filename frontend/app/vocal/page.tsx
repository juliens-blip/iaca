"use client";

import { useState, useEffect } from "react";
import VocalChat from "../../components/VocalChat";

interface ServiceStatus {
  ollama: boolean;
  piper: boolean;
  whisper: boolean;
  model?: string;
}

function ErrorState({ status }: { status: ServiceStatus }) {
  return (
    <div className="h-[calc(100vh-4rem)] flex items-center justify-center">
      <div className="text-center max-w-md mx-auto px-6">
        {/* Avatar error */}
        <div className="mx-auto w-24 h-24 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center ring-4 ring-red-500/20 mb-6">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="9" r="4" stroke="#94a3b8" strokeWidth="1.5" />
            <path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M7 3h10l-2 3H9L7 3z" fill="#94a3b8" opacity="0.4" />
          </svg>
        </div>

        <h2 className="text-xl font-bold text-white mb-2">Prof Vocal indisponible</h2>
        <p className="text-slate-400 text-sm mb-6">
          {!status.ollama
            ? "Le service Ollama n'est pas démarré. Le professeur vocal a besoin de l'IA pour fonctionner."
            : "Un service requis est indisponible."}
        </p>

        {!status.ollama && (
          <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 text-left">
            <p className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">Pour démarrer :</p>
            <code className="text-sm text-violet-300 bg-slate-900/60 px-3 py-1.5 rounded-lg inline-block">
              ollama serve
            </code>
          </div>
        )}

        <div className="mt-6 flex items-center justify-center gap-3 text-xs text-slate-600">
          {["ollama", "whisper", "piper"].map((svc) => {
            const active = status[svc as keyof ServiceStatus];
            return (
              <span key={svc} className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${active ? "bg-emerald-500" : "bg-red-500"}`} />
                <span className={active ? "text-slate-500" : "text-red-400/80"}>{svc}</span>
              </span>
            );
          })}
        </div>

        <button
          onClick={() => window.location.reload()}
          className="mt-6 px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-xl border border-slate-700/60 transition-colors"
        >
          Réessayer
        </button>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="h-[calc(100vh-4rem)] flex items-center justify-center">
      <div className="text-center">
        <div className="mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-violet-500/20 to-blue-500/20 flex items-center justify-center ring-4 ring-violet-500/10 animate-pulse mb-4">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="9" r="4" stroke="#a78bfa" strokeWidth="1.5" />
            <path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" stroke="#a78bfa" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M7 3h10l-2 3H9L7 3z" fill="#a78bfa" opacity="0.4" />
          </svg>
        </div>
        <p className="text-slate-500 text-sm">Connexion au professeur...</p>
      </div>
    </div>
  );
}

export default function VocalPage() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [statusChecked, setStatusChecked] = useState(false);

  useEffect(() => {
    fetch("/api/vocal/status")
      .then((r) => r.json())
      .then((data) => {
        setStatus(data);
        setStatusChecked(true);
      })
      .catch(() => {
        setStatus(null);
        setStatusChecked(true);
      });
  }, []);

  // Loading while checking services
  if (!statusChecked) {
    return <LoadingState />;
  }

  // Ollama down -> show error
  if (status && !status.ollama) {
    return <ErrorState status={status} />;
  }

  // Network error fetching status -> try anyway (VocalChat has its own reconnect)
  // Ollama up -> immersive vocal mode
  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      <VocalChat />
    </div>
  );
}
