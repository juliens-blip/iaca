"use client";

import { useEffect, useState } from "react";

import {
  DashboardHome,
  DashboardLoadingState,
  type DashboardRevision,
  type DashboardStats,
} from "@/components/DashboardHome";
import { withAuthHeaders } from "@/lib/auth";

const API_BASE = "/api";

const EMPTY_STATS: DashboardStats = {
  documents: 0,
  flashcards: 0,
  fiches: 0,
  matieres: 0,
  quiz: 0,
  revisions: 0,
};

interface MatiereResponse {
  id: number;
  nb_documents?: number;
}

function isSuccessfulResponse(
  result: PromiseSettledResult<Response>,
): result is PromiseFulfilledResult<Response> {
  return result.status === "fulfilled" && result.value.ok;
}

export default function DashboardPage() {
  const [currentDate, setCurrentDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [revisions, setRevisions] = useState<DashboardRevision[]>([]);
  const [stats, setStats] = useState<DashboardStats>(EMPTY_STATS);

  useEffect(() => {
    const formatter = new Intl.DateTimeFormat("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });

    setCurrentDate(formatter.format(new Date()));
  }, []);

  useEffect(() => {
    let ignore = false;

    const fetchDashboardData = async () => {
      setLoading(true);

      try {
        const results = await Promise.allSettled([
          fetch(`${API_BASE}/flashcards`, withAuthHeaders()),
          fetch(`${API_BASE}/quiz`, withAuthHeaders()),
          fetch(`${API_BASE}/flashcards/revision`, withAuthHeaders()),
          fetch(`${API_BASE}/fiches`, withAuthHeaders()),
          fetch(`${API_BASE}/matieres`, withAuthHeaders()),
        ]);

        if (ignore) {
          return;
        }

        const [flashcardsResult, quizResult, revisionsResult, fichesResult, matieresResult] = results;

        let failedRequests = 0;
        let documents = 0;
        let flashcards = 0;
        let fiches = 0;
        let matieres = 0;
        let quiz = 0;
        let revisionItems: DashboardRevision[] = [];

        if (isSuccessfulResponse(flashcardsResult)) {
          const data = await flashcardsResult.value.json();
          flashcards = Array.isArray(data) ? data.length : 0;
        } else {
          failedRequests += 1;
        }

        if (isSuccessfulResponse(quizResult)) {
          const data = await quizResult.value.json();
          quiz = Array.isArray(data) ? data.length : 0;
        } else {
          failedRequests += 1;
        }

        if (isSuccessfulResponse(revisionsResult)) {
          const data = await revisionsResult.value.json();
          revisionItems = Array.isArray(data) ? data.slice(0, 5) : [];
        } else {
          failedRequests += 1;
        }

        if (isSuccessfulResponse(fichesResult)) {
          const data = await fichesResult.value.json();
          fiches = Array.isArray(data) ? data.length : 0;
        } else {
          failedRequests += 1;
        }

        if (isSuccessfulResponse(matieresResult)) {
          const data = await matieresResult.value.json();
          if (Array.isArray(data)) {
            const matieresData = data as MatiereResponse[];
            matieres = matieresData.length;
            documents = matieresData.reduce((sum, matiere) => sum + (matiere.nb_documents ?? 0), 0);
          }
        } else {
          failedRequests += 1;
        }

        setRevisions(revisionItems);
        setStats({
          documents,
          flashcards,
          fiches,
          matieres,
          quiz,
          revisions: revisionItems.length,
        });

        if (failedRequests === results.length) {
          setError("Impossible de charger le cockpit de revision pour le moment.");
        } else if (failedRequests > 0) {
          setError("Certaines statistiques sont temporairement indisponibles.");
        } else {
          setError(null);
        }
      } catch (fetchError) {
        console.error("Erreur chargement dashboard:", fetchError);

        if (!ignore) {
          setError("Impossible de charger le cockpit de revision pour le moment.");
          setRevisions([]);
          setStats(EMPTY_STATS);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetchDashboardData();

    return () => {
      ignore = true;
    };
  }, []);

  if (loading) {
    return <DashboardLoadingState />;
  }

  return (
    <DashboardHome
      currentDate={currentDate}
      error={error}
      revisions={revisions}
      stats={stats}
    />
  );
}
