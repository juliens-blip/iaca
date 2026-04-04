"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { withAuthHeaders } from "@/lib/auth";

const API_BASE = "/api";

interface FicheSection {
  id: number;
  titre: string;
  contenu: string;
  ordre: number;
}

interface FicheListItem {
  id: number;
  titre: string;
  resume: string;
  matiere_id: number | null;
  document_id: number | null;
  chapitre: string;
  tags: string;
  nb_sections: number;
  created_at: string;
}

interface FicheDetail {
  id: number;
  titre: string;
  resume: string;
  matiere_id: number | null;
  document_id: number | null;
  chapitre: string;
  tags: string;
  sections: FicheSection[];
  created_at: string;
}

interface Matiere {
  id: number;
  nom: string;
}

interface Document {
  id: number;
  titre: string;
  matiere_id: number | null;
}

const matiereColors: Record<string, { bg: string; text: string; border: string; gradient: string; icon: string }> = {
  "Droit public": {
    bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/30",
    gradient: "from-blue-600/20 to-blue-900/10",
    icon: "M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21",
  },
  "Economie et finances publiques": {
    bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30",
    gradient: "from-emerald-600/20 to-emerald-900/10",
    icon: "M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z",
  },
  "\u00c9conomie et finances publiques": {
    bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30",
    gradient: "from-emerald-600/20 to-emerald-900/10",
    icon: "M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z",
  },
  "Questions contemporaines": {
    bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/30",
    gradient: "from-amber-600/20 to-amber-900/10",
    icon: "M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418",
  },
  "Questions sociales": {
    bg: "bg-rose-500/20", text: "text-rose-400", border: "border-rose-500/30",
    gradient: "from-rose-600/20 to-rose-900/10",
    icon: "M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z",
  },
  "Relations internationales": {
    bg: "bg-violet-500/20", text: "text-violet-400", border: "border-violet-500/30",
    gradient: "from-violet-600/20 to-violet-900/10",
    icon: "M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 0 1 6-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 0 1-3.827-5.802",
  },
};

const defaultColor = {
  bg: "bg-slate-500/20", text: "text-slate-400", border: "border-slate-500/30",
  gradient: "from-slate-600/20 to-slate-900/10",
  icon: "M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z",
};

function getMatiereStyle(matiereName: string) {
  return matiereColors[matiereName] || defaultColor;
}

/** Render fiche section content with better formatting than plain whitespace-pre-line */
function FormattedContent({ text }: { text: string }) {
  const paragraphs = text.split(/\n{2,}/);
  return (
    <div className="space-y-3">
      {paragraphs.map((para, i) => {
        const trimmed = para.trim();
        if (!trimmed) return null;
        // Detect bullet lists
        const lines = trimmed.split("\n");
        const isList = lines.every(l => /^[\s]*[-\u2022\u2013*]\s/.test(l) || !l.trim());
        if (isList) {
          return (
            <ul key={i} className="space-y-1.5 ml-1">
              {lines.filter(l => l.trim()).map((line, j) => (
                <li key={j} className="flex gap-2 text-slate-300 text-sm leading-relaxed">
                  <span className="text-blue-400/60 mt-1 shrink-0">
                    <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor"><circle cx="6" cy="6" r="3" /></svg>
                  </span>
                  <span>{line.replace(/^[\s]*[-\u2022\u2013*]\s*/, "")}</span>
                </li>
              ))}
            </ul>
          );
        }
        // Detect numbered items
        const isNumbered = lines.every(l => /^[\s]*\d+[.)]\s/.test(l) || !l.trim());
        if (isNumbered) {
          return (
            <ol key={i} className="space-y-1.5 ml-1">
              {lines.filter(l => l.trim()).map((line, j) => {
                const match = line.match(/^[\s]*(\d+)[.)]\s*(.*)/);
                return (
                  <li key={j} className="flex gap-2.5 text-slate-300 text-sm leading-relaxed">
                    <span className="text-blue-400/70 font-semibold tabular-nums shrink-0 w-5 text-right">{match ? match[1] : j + 1}.</span>
                    <span>{match ? match[2] : line}</span>
                  </li>
                );
              })}
            </ol>
          );
        }
        // Default paragraph
        return (
          <p key={i} className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
            {trimmed}
          </p>
        );
      })}
    </div>
  );
}

export default function FichesPage() {
  const [fiches, setFiches] = useState<FicheListItem[]>([]);
  const [matieres, setMatieres] = useState<Matiere[]>([]);
  const [selectedMatiere, setSelectedMatiere] = useState<number | null>(null);
  const [selectedFiche, setSelectedFiche] = useState<FicheDetail | null>(null);
  const [openSections, setOpenSections] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenModal, setShowGenModal] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [nextContent, setNextContent] = useState<{ flashcards: { id: number; question: string }[]; quizzes: { id: number; titre: string }[] } | null>(null);
  const [search, setSearch] = useState("");
  const sectionRefs = useRef<Record<number, HTMLDivElement | null>>({});

  // Read matiere_id from URL search params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const mid = params.get("matiere_id");
    if (mid) setSelectedMatiere(parseInt(mid));
  }, []);

  const fetchFiches = useCallback(async () => {
    try {
      const base = `${API_BASE}/fiches?limit=5000`;
      const url = selectedMatiere
        ? `${base}&matiere_id=${selectedMatiere}`
        : base;
      const res = await fetch(url);
      if (res.ok) setFiches(await res.json());
    } catch (e) {
      console.error("Erreur chargement fiches:", e);
    }
  }, [selectedMatiere]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [matRes] = await Promise.allSettled([
          fetch(`${API_BASE}/matieres`),
        ]);
        if (matRes.status === "fulfilled" && matRes.value.ok) {
          setMatieres(await matRes.value.json());
        }
        await fetchFiches();
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [fetchFiches]);

  const openFiche = async (ficheId: number) => {
    try {
      const res = await fetch(`${API_BASE}/fiches/${ficheId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedFiche(data);
        setOpenSections(new Set());
        // Load next content (flashcards/quiz)
        const nextRes = await fetch(`${API_BASE}/fiches/${ficheId}/next`);
        if (nextRes.ok) setNextContent(await nextRes.json());
      }
    } catch (e) {
      console.error("Erreur chargement fiche:", e);
    }
  };

  const toggleSection = (sectionId: number) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) next.delete(sectionId);
      else next.add(sectionId);
      return next;
    });
  };

  const toggleAllSections = () => {
    if (!selectedFiche) return;
    const allIds = selectedFiche.sections.map(s => s.id);
    const allOpen = allIds.every(id => openSections.has(id));
    if (allOpen) {
      setOpenSections(new Set());
    } else {
      setOpenSections(new Set(allIds));
    }
  };

  const scrollToSection = (sectionId: number) => {
    // Open section first
    setOpenSections(prev => {
      const next = new Set(prev);
      next.add(sectionId);
      return next;
    });
    // Scroll after a tick
    setTimeout(() => {
      const el = sectionRefs.current[sectionId];
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  };

  const openGenModal = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`);
      if (res.ok) {
        const docs = await res.json();
        setDocuments(docs);
        setSelectedDocId(docs.length > 0 ? docs[0].id : null);
      }
    } catch (e) {
      console.error(e);
    }
    setShowGenModal(true);
  };

  const generateFiche = async () => {
    if (!selectedDocId) return;
    setGenerating(true);
    try {
      const res = await fetch(
        `${API_BASE}/recommandations/generer-fiche/${selectedDocId}`,
        withAuthHeaders({ method: "POST" })
      );
      if (res.ok) {
        const data = await res.json();
        setShowGenModal(false);
        await fetchFiches();
        // Auto-open the generated fiche
        if (data.fiche_id) openFiche(data.fiche_id);
      } else {
        const err = await res.text();
        alert(`Erreur generation: ${err}`);
      }
    } catch (e) {
      alert(`Erreur: ${e}`);
    } finally {
      setGenerating(false);
    }
  };

  const getMatiereName = (matiereId: number | null) => {
    if (!matiereId) return "";
    return matieres.find((m) => m.id === matiereId)?.nom || "";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-blue-500/20 rounded-full" />
            <div className="w-12 h-12 border-4 border-transparent border-t-blue-500 rounded-full animate-spin absolute inset-0" />
          </div>
          <p className="text-slate-400 text-sm">Chargement des fiches...</p>
        </div>
      </div>
    );
  }

  // Detail view
  if (selectedFiche) {
    const matiereName = getMatiereName(selectedFiche.matiere_id);
    const style = getMatiereStyle(matiereName);
    const sortedSections = [...selectedFiche.sections].sort((a, b) => a.ordre - b.ordre);
    const allOpen = sortedSections.length > 0 && sortedSections.every(s => openSections.has(s.id));

    return (
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Back button */}
        <button
          onClick={() => { setSelectedFiche(null); setNextContent(null); }}
          aria-label="Retour aux fiches"
          className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white px-3 py-2 rounded-lg hover:bg-slate-800/60 transition-all duration-200 -ml-3"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Retour aux fiches
        </button>

        {/* Header with gradient */}
        <div className={`rounded-2xl border ${style.border} bg-gradient-to-br ${style.gradient} p-6 relative overflow-hidden`}>
          <div className="absolute top-0 right-0 w-40 h-40 opacity-5">
            <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" strokeWidth={0.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d={style.icon} />
            </svg>
          </div>
          <div className="relative">
            {matiereName && (
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${style.bg} ${style.text} border ${style.border} mb-3`}>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d={style.icon} />
                </svg>
                {matiereName}
              </span>
            )}
            <h1 className="text-2xl font-bold text-white leading-tight">{selectedFiche.titre}</h1>
            {selectedFiche.chapitre && (
              <p className="text-sm text-slate-400 mt-2 flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                </svg>
                {selectedFiche.chapitre}
              </p>
            )}
          </div>
        </div>

        {/* Resume */}
        {selectedFiche.resume && (
          <div className="card border-slate-700/50 bg-slate-800/40">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 shrink-0 mt-0.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Resume</p>
                <p className="text-slate-300 text-sm leading-relaxed">{selectedFiche.resume}</p>
              </div>
            </div>
          </div>
        )}

        {/* Sommaire cliquable + toggle all */}
        {sortedSections.length > 1 && (
          <div className="card border-slate-700/50 bg-slate-800/30">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                </svg>
                Sommaire ({sortedSections.length} sections)
              </h2>
              <button
                onClick={toggleAllSections}
                className="text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-700/50 transition-all duration-200 flex items-center gap-1.5"
              >
                <svg className={`w-3.5 h-3.5 transition-transform duration-200 ${allOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                </svg>
                {allOpen ? "Tout replier" : "Tout deplier"}
              </button>
            </div>
            <nav className="grid grid-cols-1 gap-1">
              {sortedSections.map((section, idx) => (
                <button
                  key={section.id}
                  onClick={() => scrollToSection(section.id)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-left hover:bg-slate-700/40 transition-all duration-150 group"
                >
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${style.bg} ${style.text} border ${style.border}`}>
                    {idx + 1}
                  </span>
                  <span className="text-sm text-slate-400 group-hover:text-white transition-colors truncate">
                    {section.titre}
                  </span>
                  <svg className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 ml-auto shrink-0 transition-colors" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                  </svg>
                </button>
              ))}
            </nav>
          </div>
        )}

        {/* Sections en accordeon */}
        <div className="space-y-3">
          {sortedSections.map((section, idx) => {
            const isOpen = openSections.has(section.id);
            return (
              <div
                key={section.id}
                ref={(el) => { sectionRefs.current[section.id] = el; }}
                className={`rounded-xl border transition-all duration-200 ${
                  isOpen
                    ? `${style.border} bg-slate-800/60`
                    : "border-slate-700/40 bg-slate-800/30 hover:border-slate-600/50"
                }`}
              >
                <button
                  onClick={() => toggleSection(section.id)}
                  className="w-full flex items-center gap-3 text-left p-4"
                >
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-colors duration-200 ${
                    isOpen
                      ? `${style.bg} ${style.text} border ${style.border}`
                      : "bg-slate-700/50 text-slate-400 border border-slate-600/30"
                  }`}>
                    {idx + 1}
                  </span>
                  <h3 className={`font-medium flex-1 transition-colors duration-200 ${isOpen ? "text-white" : "text-slate-300"}`}>
                    {section.titre}
                  </h3>
                  <svg
                    className={`w-5 h-5 text-slate-400 transition-transform duration-300 shrink-0 ${isOpen ? "rotate-180" : ""}`}
                    fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                  </svg>
                </button>
                <div
                  className={`overflow-hidden transition-all duration-300 ${
                    isOpen ? "max-h-[5000px] opacity-100" : "max-h-0 opacity-0"
                  }`}
                >
                  <div className="px-4 pb-4 pt-1 ml-10 border-t border-slate-700/30">
                    <FormattedContent text={section.contenu} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Liens vers flashcards / quiz */}
        {nextContent && (nextContent.flashcards.length > 0 || nextContent.quizzes.length > 0) && (
          <div className="card border-violet-500/20 bg-gradient-to-r from-violet-900/10 to-slate-800/40">
            <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
              Continuer a reviser
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {nextContent.flashcards.length > 0 && (
                <a
                  href="/flashcards"
                  className="flex items-center gap-3 p-4 rounded-xl bg-violet-600/10 border border-violet-500/20 hover:bg-violet-600/20 hover:border-violet-500/40 transition-all duration-200"
                >
                  <div className="p-2 rounded-lg bg-violet-500/20 text-violet-400">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-violet-300">Flashcards sur ce sujet</p>
                    <p className="text-xs text-slate-500">{nextContent.flashcards.length} disponibles</p>
                  </div>
                </a>
              )}
              {nextContent.quizzes.length > 0 && (
                <a
                  href="/quiz"
                  className="flex items-center gap-3 p-4 rounded-xl bg-amber-600/10 border border-amber-500/20 hover:bg-amber-600/20 hover:border-amber-500/40 transition-all duration-200"
                >
                  <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-amber-300">Quiz sur ce sujet</p>
                    <p className="text-xs text-slate-500">{nextContent.quizzes.length} disponibles</p>
                  </div>
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  const filteredFiches = fiches.filter(f =>
    !search.trim() || f.titre.toLowerCase().includes(search.toLowerCase()) || (f.resume || "").toLowerCase().includes(search.toLowerCase())
  );

  // Group fiches by matiere
  const groupedFiches: { matiereName: string; matiereId: number | null; fiches: FicheListItem[] }[] = [];
  const grouped = new Map<number | null, FicheListItem[]>();
  for (const f of filteredFiches) {
    const key = f.matiere_id;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(f);
  }
  // Sort groups: named matieres first (alphabetically), then null
  const sortedKeys = Array.from(grouped.keys()).sort((a, b) => {
    if (a === null) return 1;
    if (b === null) return -1;
    return getMatiereName(a).localeCompare(getMatiereName(b));
  });
  for (const key of sortedKeys) {
    groupedFiches.push({
      matiereName: key !== null ? getMatiereName(key) : "Autres",
      matiereId: key,
      fiches: grouped.get(key)!,
    });
  }

  // List view
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <svg className="w-7 h-7 text-blue-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
            </div>
            Fiches de revision
          </h1>
          <p className="mt-2 text-slate-400">
            {fiches.length > 0 ? `${fiches.length} fiche${fiches.length > 1 ? "s" : ""} disponible${fiches.length > 1 ? "s" : ""}` : "Fiches structurees pour reviser efficacement"}
          </p>
        </div>
        <button onClick={openGenModal} className="btn-primary flex items-center gap-2 shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
          </svg>
          Generer une fiche IA
        </button>
      </div>

      {/* Filtres + recherche */}
      {fiches.length > 0 && (
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input
              type="text"
              placeholder="Rechercher une fiche..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input-field w-full pl-9 py-2.5"
            />
          </div>
          {matieres.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedMatiere(null)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  selectedMatiere === null
                    ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm shadow-blue-500/10"
                    : "text-slate-400 hover:text-slate-200 bg-slate-800/40 border border-slate-700/30 hover:border-slate-600/40"
                }`}
              >
                Toutes
              </button>
              {matieres.map((m) => {
                const mStyle = getMatiereStyle(m.nom);
                const isActive = selectedMatiere === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMatiere(m.id)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-1.5 ${
                      isActive
                        ? `${mStyle.bg} ${mStyle.text} border ${mStyle.border}`
                        : "text-slate-400 hover:text-slate-200 bg-slate-800/40 border border-slate-700/30 hover:border-slate-600/40"
                    }`}
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d={mStyle.icon} />
                    </svg>
                    {m.nom}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Fiches */}
      {fiches.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-blue-500/10 to-violet-500/10 border border-blue-500/20 flex items-center justify-center">
            <svg className="w-10 h-10 text-blue-500/40" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
          <p className="text-slate-300 text-lg font-medium mb-2">Aucune fiche de revision</p>
          <p className="text-slate-500 text-sm mb-6">Generez votre premiere fiche a partir d&apos;un document</p>
          <button onClick={openGenModal} className="btn-primary">Generer une fiche IA</button>
        </div>
      ) : filteredFiches.length === 0 ? (
        <div className="text-center py-12">
          <svg className="w-12 h-12 mx-auto mb-3 text-slate-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <p className="text-slate-400">Aucune fiche ne correspond a votre recherche.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {groupedFiches.map((group) => {
            const style = getMatiereStyle(group.matiereName);
            return (
              <div key={group.matiereName}>
                {/* Group header */}
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-2 rounded-lg ${style.bg} border ${style.border}`}>
                    <svg className={`w-4.5 h-4.5 ${style.text}`} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: 18, height: 18 }}>
                      <path strokeLinecap="round" strokeLinejoin="round" d={style.icon} />
                    </svg>
                  </div>
                  <div>
                    <h2 className={`text-lg font-semibold ${style.text}`}>{group.matiereName}</h2>
                    <p className="text-xs text-slate-500">{group.fiches.length} fiche{group.fiches.length > 1 ? "s" : ""}</p>
                  </div>
                  <div className={`flex-1 h-px ${style.border} border-t ml-2`} />
                </div>

                {/* Cards grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {group.fiches.map((fiche) => (
                    <div
                      key={fiche.id}
                      onClick={() => openFiche(fiche.id)}
                      className={`group cursor-pointer rounded-xl border border-slate-700/40 bg-slate-800/30 p-4
                        hover:border-opacity-100 hover:${style.border} hover:bg-slate-800/60
                        transition-all duration-200 flex flex-col`}
                    >
                      <div className="flex items-start justify-between mb-2 gap-2">
                        <h3 className={`font-semibold text-sm text-slate-200 group-hover:${style.text} transition-colors line-clamp-2 flex-1`}>
                          {fiche.titre}
                        </h3>
                        <svg className={`w-4 h-4 text-slate-600 group-hover:${style.text} flex-shrink-0 mt-0.5 transition-all duration-200 group-hover:translate-x-0.5`} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                        </svg>
                      </div>
                      {fiche.resume && (
                        <p className="text-xs text-slate-500 mb-3 line-clamp-2 flex-1 leading-relaxed">{fiche.resume}</p>
                      )}
                      <div className="flex items-center gap-2 pt-3 border-t border-slate-700/30 mt-auto">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${style.bg} ${style.text} border ${style.border}`}>
                          <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d={style.icon} />
                          </svg>
                          {group.matiereName}
                        </span>
                        <span className="text-[10px] text-slate-500 ml-auto flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                          </svg>
                          {fiche.nb_sections} section{fiche.nb_sections !== 1 ? "s" : ""}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal generation IA */}
      {showGenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => !generating && setShowGenModal(false)}>
          <div
            className="card w-full max-w-lg mx-4 border-slate-600/50 shadow-2xl shadow-black/50 animate-in"
            onClick={(e) => e.stopPropagation()}
            style={{ animation: "modalIn 0.2s ease-out" }}
          >
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 border border-blue-500/20">
                <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Generer une fiche IA</h2>
                <p className="text-xs text-slate-400">Selectionnez un document source</p>
              </div>
            </div>
            <div className="mb-5">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Document source
              </label>
              <select
                value={selectedDocId || ""}
                onChange={(e) => setSelectedDocId(parseInt(e.target.value))}
                className="input-field w-full"
              >
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.titre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-700/40">
              <button
                onClick={() => setShowGenModal(false)}
                className="btn-ghost"
                disabled={generating}
              >
                Annuler
              </button>
              <button
                onClick={generateFiche}
                className="btn-primary flex items-center gap-2"
                disabled={generating || !selectedDocId}
              >
                {generating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Generation en cours...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                    </svg>
                    Generer
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inline keyframe for modal animation */}
      <style jsx>{`
        @keyframes modalIn {
          from { opacity: 0; transform: scale(0.95) translateY(10px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
    </div>
  );
}
