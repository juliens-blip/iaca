"use client";

import { useEffect, useMemo, useState } from "react";
import MindMap, {
  convertGeminiMindMapToGraph,
  type GeminiMindMapData,
  type MindMapData,
} from "@/components/MindMap";

const API_BASE = "/api";

interface DocumentItem {
  id: number;
  titre: string;
  matiere_id: number | null;
}

export default function MindMapPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string>("");
  const [geminiMap, setGeminiMap] = useState<GeminiMindMapData | null>(null);

  useEffect(() => {
    const loadDocuments = async () => {
      setLoadingDocs(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/documents`);
        if (!res.ok) {
          throw new Error(`Chargement documents impossible (${res.status})`);
        }
        const data = (await res.json()) as DocumentItem[];
        setDocuments(data);
        if (data.length > 0) {
          setSelectedDocId(data[0].id);
        }
      } catch (e) {
        setError(`Erreur chargement documents: ${e}`);
      } finally {
        setLoadingDocs(false);
      }
    };

    loadDocuments();
  }, []);

  const graphData: MindMapData | null = useMemo(() => {
    if (!geminiMap) return null;
    return convertGeminiMindMapToGraph(geminiMap);
  }, [geminiMap]);

  const generate = async () => {
    if (!selectedDocId) return;
    setGenerating(true);
    setError("");
    setGeminiMap(null);

    try {
      const res = await fetch(`${API_BASE}/recommandations/mindmap/${selectedDocId}`);
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`Generation mind map echouee (${res.status}): ${detail}`);
      }
      const data = (await res.json()) as GeminiMindMapData;
      if (!data?.centre || !Array.isArray(data?.branches)) {
        throw new Error("Reponse Gemini invalide");
      }
      setGeminiMap(data);
    } catch (e) {
      setError(`${e}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Mind Map (Gemini)</h1>
        <p className="mt-1 text-slate-400">
          Selectionnez un document puis generez une carte mentale.
        </p>
      </div>

      <div className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end">
          <div>
            <label className="block text-sm text-slate-300 mb-1.5">Document source</label>
            <select
              className="input-field w-full"
              disabled={loadingDocs || documents.length === 0}
              value={selectedDocId ?? ""}
              onChange={(e) => setSelectedDocId(Number(e.target.value))}
            >
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  #{doc.id} - {doc.titre}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={generate}
            disabled={generating || !selectedDocId || loadingDocs}
            className="btn-primary"
          >
            {generating ? "Generation..." : "Generer la mind map"}
          </button>
        </div>

        {loadingDocs && <p className="text-sm text-slate-400">Chargement des documents...</p>}
        {!loadingDocs && documents.length === 0 && (
          <p className="text-sm text-amber-300">Aucun document disponible.</p>
        )}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </div>
        )}
      </div>

      {graphData && geminiMap && (
        <MindMap
          title={`${geminiMap.centre} (${geminiMap.branches.length} branches)`}
          data={graphData}
          height={620}
        />
      )}
    </div>
  );
}
