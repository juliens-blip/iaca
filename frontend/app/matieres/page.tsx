"use client";

import { useEffect, useState } from "react";
import { withAuthHeaders } from "@/lib/auth";

const API_BASE = "/api";

interface Matiere {
  id: number;
  nom: string;
  description?: string;
  couleur?: string;
  nb_documents: number;
  nb_flashcards: number;
  nb_fiches: number;
}

const matiereColorMap = {
  "Droit public": "blue",
  "Économie et finances publiques": "emerald",
  "Questions contemporaines": "amber",
  "Questions sociales": "rose",
  "Relations internationales": "violet",
};

const matiereIconMap: Record<string, React.ReactNode> = {
  "Droit public": (
    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
    </svg>
  ),
  "Économie et finances publiques": (
    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 9.128 9.466 9.128 8.466 9.659m5.532 3.182c1.172.879 3.071.879 4.242 0 1.172-.879 1.172-2.303 0-3.182m0 0c-1.172-.879-3.07-.879-4.242 0M9 20.25c-4.418 0-8.003 2.991-8.003 6.697 0 .734.458 1.338 1.119 1.338H15.884c.66 0 1.119-.604 1.119-1.338 0-3.706-3.585-6.697-8.003-6.697Z" />
    </svg>
  ),
  "Questions contemporaines": (
    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8.25v4.5m0 4.5v.008m0 0h.008m-.008 0h-.008M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  ),
  "Questions sociales": (
    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.75H6m0-12h12m-12 6h12M6 5.25h12a2.25 2.25 0 0 1 2.25 2.25v10.5A2.25 2.25 0 0 1 18 20.25H6a2.25 2.25 0 0 1-2.25-2.25V7.5A2.25 2.25 0 0 1 6 5.25Z" />
    </svg>
  ),
  "Relations internationales": (
    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.798-.696 6.783-1.899M12 21c-2.485 0-4.798-.696-6.783-1.899M3.171 12a9 9 0 0 1 16.658 0M12 12a9 9 0 0 0 8.716 6.747M12 12c2.485 0 4.798.696 6.783 1.899m0 0A8.973 8.973 0 0 0 21 12M12 12c-2.485 0-4.798.696-6.783 1.899m0 0A8.973 8.973 0 0 1 3 12" />
    </svg>
  ),
};

const defaultMatieres: Matiere[] = [
  { id: 0, nom: "Droit public", description: "Droit constitutionnel, administratif, collectivités", couleur: "blue", nb_documents: 0, nb_flashcards: 0, nb_fiches: 0 },
  { id: 0, nom: "Économie et finances publiques", description: "Budget, comptabilité publique, fiscalité", couleur: "emerald", nb_documents: 0, nb_flashcards: 0, nb_fiches: 0 },
  { id: 0, nom: "Questions contemporaines", description: "Questions d'actualité, enjeux contemporains", couleur: "amber", nb_documents: 0, nb_flashcards: 0, nb_fiches: 0 },
  { id: 0, nom: "Questions sociales", description: "Protection sociale, politiques sociales", couleur: "rose", nb_documents: 0, nb_flashcards: 0, nb_fiches: 0 },
  { id: 0, nom: "Relations internationales", description: "Droit international, relations géopolitiques", couleur: "violet", nb_documents: 0, nb_flashcards: 0, nb_fiches: 0 },
];

const colorMap: Record<string, { bg: string; border: string; text: string; glow: string; icon: string }> = {
  blue: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/30 hover:border-blue-500/50",
    text: "text-blue-400",
    glow: "hover:shadow-blue-500/10",
    icon: "bg-blue-500/20",
  },
  emerald: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30 hover:border-emerald-500/50",
    text: "text-emerald-400",
    glow: "hover:shadow-emerald-500/10",
    icon: "bg-emerald-500/20",
  },
  amber: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30 hover:border-amber-500/50",
    text: "text-amber-400",
    glow: "hover:shadow-amber-500/10",
    icon: "bg-amber-500/20",
  },
  violet: {
    bg: "bg-violet-500/10",
    border: "border-violet-500/30 hover:border-violet-500/50",
    text: "text-violet-400",
    glow: "hover:shadow-violet-500/10",
    icon: "bg-violet-500/20",
  },
  rose: {
    bg: "bg-rose-500/10",
    border: "border-rose-500/30 hover:border-rose-500/50",
    text: "text-rose-400",
    glow: "hover:shadow-rose-500/10",
    icon: "bg-rose-500/20",
  },
  cyan: {
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30 hover:border-cyan-500/50",
    text: "text-cyan-400",
    glow: "hover:shadow-cyan-500/10",
    icon: "bg-cyan-500/20",
  },
};

export default function MatieresPage() {
  const [matieres, setMatieres] = useState<Matiere[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newMatiere, setNewMatiere] = useState({ nom: "", description: "" });

  useEffect(() => {
    const fetchMatieres = async () => {
      try {
        const res = await fetch(`${API_BASE}/matieres`);
        if (res.ok) {
          const data = await res.json();
          // Enrich with fiches count
          const fichesRes = await fetch(`${API_BASE}/fiches`);
          const fiches = fichesRes.ok ? await fichesRes.json() : [];
          const enriched = (data.length > 0 ? data : defaultMatieres).map((m: Matiere) => ({
            ...m,
            nb_fiches: fiches.filter((f: { matiere_id: number | null }) => f.matiere_id === m.id).length,
          }));
          setMatieres(enriched);
        } else {
          setMatieres(defaultMatieres);
        }
      } catch {
        setMatieres(defaultMatieres);
      } finally {
        setLoading(false);
      }
    };

    fetchMatieres();
  }, []);

  const handleAddMatiere = async () => {
    if (!newMatiere.nom.trim()) return;

    try {
      const res = await fetch(`${API_BASE}/matieres`, withAuthHeaders({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newMatiere),
      }));
      if (res.ok) {
        const created = await res.json();
        setMatieres([...matieres, created]);
      }
    } catch (error) {
      console.error("Erreur ajout matiere:", error);
    }

    setNewMatiere({ nom: "", description: "" });
    setShowAddModal(false);
  };

  const colors = Object.keys(colorMap);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Chargement des matieres...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient font-heading">Matieres</h1>
          <p className="mt-1 text-slate-400">
            {matieres.length} matière{matieres.length !== 1 ? 's' : ''} • Explorez les ressources du concours
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Ajouter
        </button>
      </div>

      {/* Grid matieres */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {matieres.map((matiere, index) => {
          const colorKey = matiere.couleur || colors[index % colors.length];
          const style = colorMap[colorKey] || colorMap.blue;
          const totalResources = matiere.nb_documents + matiere.nb_flashcards + matiere.nb_fiches;
          const docsPercent = totalResources > 0 ? Math.round((matiere.nb_documents / totalResources) * 100) : 0;

          return (
            <div
              key={matiere.id || index}
              className={`
                relative overflow-hidden rounded-xl border p-6
                bg-slate-800/40 backdrop-blur-sm
                transition-all duration-300 hover:shadow-xl hover:-translate-y-0.5 cursor-pointer group
                ${style.border} ${style.glow}
              `}
            >
              {/* Decorative gradient */}
              <div className={`absolute top-0 right-0 w-32 h-32 rounded-full ${style.bg} blur-2xl -translate-y-8 translate-x-8 opacity-40 group-hover:opacity-60 transition-opacity`} />

              <div className="relative space-y-4">
                {/* Icon - Top center */}
                <div className="flex justify-center">
                  <div className={`w-16 h-16 rounded-2xl ${style.icon} flex items-center justify-center`}>
                    <div className={`${style.text}`}>
                      {matiereIconMap[matiere.nom] || (
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                        </svg>
                      )}
                    </div>
                  </div>
                </div>

                {/* Titre + description */}
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-white">{matiere.nom}</h3>
                  {matiere.description && (
                    <p className="text-sm text-slate-400 mt-1 line-clamp-2">
                      {matiere.description}
                    </p>
                  )}
                </div>

                {/* Compteurs avec barres de progression */}
                <div className="space-y-3 border-t border-slate-700/40 pt-4">
                  {/* Documents */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                        </svg>
                        <span className="text-xs font-medium text-slate-400">Documents</span>
                      </div>
                      <span className="text-xs font-semibold text-slate-200">{matiere.nb_documents}</span>
                    </div>
                    <div className="w-full bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all`}
                        style={{ width: `${Math.min(docsPercent, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Flashcards */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
                        </svg>
                        <span className="text-xs font-medium text-slate-400">Flashcards</span>
                      </div>
                      <span className="text-xs font-semibold text-slate-200">{matiere.nb_flashcards}</span>
                    </div>
                    <div className="w-full bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r from-violet-500 to-violet-600 rounded-full transition-all`}
                        style={{ width: `${Math.min(totalResources > 0 ? Math.round((matiere.nb_flashcards / totalResources) * 100) : 0, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Fiches */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                        </svg>
                        <span className="text-xs font-medium text-slate-400">Fiches</span>
                      </div>
                      <span className="text-xs font-semibold text-slate-200">{matiere.nb_fiches}</span>
                    </div>
                    <div className="w-full bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r from-rose-500 to-rose-600 rounded-full transition-all`}
                        style={{ width: `${Math.min(totalResources > 0 ? Math.round((matiere.nb_fiches / totalResources) * 100) : 0, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Quick links */}
                {matiere.id > 0 && (
                  <div className="grid grid-cols-3 gap-2 border-t border-slate-700/40 pt-4">
                    <a
                      href={`/flashcards?matiere_id=${matiere.id}`}
                      className="flex flex-col items-center gap-1 p-2 rounded-lg bg-slate-900/30 hover:bg-violet-600/20 transition-colors group/link"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
                      </svg>
                      <span className="text-xs text-slate-400 group-hover/link:text-violet-400 transition-colors">Flashcards</span>
                    </a>
                    <a
                      href={`/quiz?matiere_id=${matiere.id}`}
                      className="flex flex-col items-center gap-1 p-2 rounded-lg bg-slate-900/30 hover:bg-amber-600/20 transition-colors group/link"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
                      </svg>
                      <span className="text-xs text-slate-400 group-hover/link:text-amber-400 transition-colors">Quiz</span>
                    </a>
                    <a
                      href={`/fiches?matiere_id=${matiere.id}`}
                      className="flex flex-col items-center gap-1 p-2 rounded-lg bg-slate-900/30 hover:bg-rose-600/20 transition-colors group/link"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg className="w-4 h-4 text-rose-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                      </svg>
                      <span className="text-xs text-slate-400 group-hover/link:text-rose-400 transition-colors">Fiches</span>
                    </a>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal ajout matiere */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="card w-full max-w-md mx-4 border-slate-600/50">
            <h2 className="text-xl font-semibold text-white mb-4">
              Ajouter une matiere
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Nom de la matiere
                </label>
                <input
                  type="text"
                  value={newMatiere.nom}
                  onChange={(e) => setNewMatiere({ ...newMatiere, nom: e.target.value })}
                  className="input-field w-full"
                  placeholder="Ex: Droit constitutionnel"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Description
                </label>
                <textarea
                  value={newMatiere.description}
                  onChange={(e) => setNewMatiere({ ...newMatiere, description: e.target.value })}
                  className="input-field w-full h-24 resize-none"
                  placeholder="Description de la matiere..."
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setNewMatiere({ nom: "", description: "" });
                }}
                className="btn-ghost"
              >
                Annuler
              </button>
              <button
                onClick={handleAddMatiere}
                className="btn-primary"
                disabled={!newMatiere.nom.trim()}
              >
                Ajouter
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
