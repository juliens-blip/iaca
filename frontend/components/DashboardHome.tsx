"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import {
  ArrowUpRightIcon,
  CheckCircleIcon,
  ClockIcon,
  DashboardIcon,
  DocumentIcon,
  FlashcardIcon,
  MicrophoneIcon,
  MindMapIcon,
  QuizIcon,
  SubjectIcon,
} from "@/components/AppIcons";

export interface DashboardStats {
  documents: number;
  flashcards: number;
  fiches: number;
  matieres: number;
  quiz: number;
  revisions: number;
}

export interface DashboardRevision {
  id: number;
  prochaine_revision: string;
  question: string;
}

interface DashboardHomeProps {
  currentDate: string;
  error: string | null;
  revisions: DashboardRevision[];
  stats: DashboardStats;
}

interface MetricCardDefinition {
  accent: string;
  description: string;
  icon: ReactNode;
  label: string;
  value: number;
}

interface QuickActionDefinition {
  accent: string;
  description: string;
  href: string;
  icon: ReactNode;
  label: string;
  meta: string;
}

function AnimatedNumber({ duration = 850, value }: { duration?: number; value: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = window.setInterval(() => {
      const progress = Math.min((Date.now() - start) / duration, 1);
      setDisplay(Math.floor(progress * value));
    }, 16);

    return () => window.clearInterval(interval);
  }, [duration, value]);

  return <>{display}</>;
}

function formatRevisionDate(value: string) {
  if (!value) {
    return "A traiter aujourd'hui";
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return "A traiter aujourd'hui";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsedDate);
}

export function DashboardLoadingState() {
  return (
    <div className="space-y-8 lg:space-y-10">
      <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-slate-900/70 p-6 shadow-[0_30px_80px_rgba(2,12,27,0.35)] backdrop-blur-xl lg:p-8">
        <div className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
          <div className="space-y-4">
            <div className="h-3 w-28 rounded-full bg-white/10" />
            <div className="h-16 w-full max-w-2xl rounded-[1.5rem] bg-white/10" />
            <div className="h-5 w-full max-w-xl rounded-full bg-white/10" />
            <div className="h-5 w-40 rounded-full bg-white/10" />
            <div className="flex gap-3">
              <div className="h-12 w-40 rounded-full bg-white/10" />
              <div className="h-12 w-36 rounded-full bg-white/10" />
            </div>
          </div>
          <div className="rounded-[1.75rem] border border-white/10 bg-white/5 p-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="h-24 rounded-[1.25rem] bg-white/10" />
              <div className="h-24 rounded-[1.25rem] bg-white/10" />
            </div>
            <div className="mt-4 h-40 rounded-[1.5rem] bg-white/10" />
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="h-44 rounded-[1.75rem] border border-white/10 bg-slate-900/60" />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="h-[25rem] rounded-[2rem] border border-white/10 bg-slate-900/60" />
        <div className="h-[25rem] rounded-[2rem] border border-white/10 bg-slate-900/60" />
      </div>
    </div>
  );
}

export function DashboardHome({ currentDate, error, revisions, stats }: DashboardHomeProps) {
  const totalResources = stats.documents + stats.flashcards + stats.fiches + stats.quiz;
  const activeModes = [stats.flashcards, stats.quiz, stats.fiches, stats.revisions].filter((value) => value > 0).length;

  const priorityTitle = stats.revisions > 0
    ? "Consolider les cartes qui arrivent a echeance"
    : totalResources > 0
      ? "Continuer le rythme sans perdre le fil"
      : "Poser les bases de la preparation";

  const priorityDescription = stats.revisions > 0
    ? `${stats.revisions} revision${stats.revisions > 1 ? "s" : ""} prioritaire${stats.revisions > 1 ? "s" : ""} aujourd'hui.`
    : totalResources > 0
      ? "Le socle existe deja. L'objectif est maintenant de garder un cycle regulier."
      : "Ajoute d'abord des matieres et du contenu pour transformer le tableau en outil de travail.";

  const metricCards: MetricCardDefinition[] = [
    {
      label: "Documents",
      value: stats.documents,
      description: "Base documentaire chargee dans la plateforme.",
      accent: "from-teal-300/90 via-teal-400/30 to-transparent",
      icon: <DocumentIcon className="h-6 w-6" />,
    },
    {
      label: "Matieres",
      value: stats.matieres,
      description: "Disciplines actuellement organisees.",
      accent: "from-orange-300/90 via-orange-400/30 to-transparent",
      icon: <SubjectIcon className="h-6 w-6" />,
    },
    {
      label: "Flashcards",
      value: stats.flashcards,
      description: "Cartes mobilisables pour la memoire active.",
      accent: "from-cyan-300/90 via-cyan-400/30 to-transparent",
      icon: <FlashcardIcon className="h-6 w-6" />,
    },
    {
      label: "Fiches",
      value: stats.fiches,
      description: "Syntheses prêtes a etre relues rapidement.",
      accent: "from-amber-300/90 via-amber-400/30 to-transparent",
      icon: <DocumentIcon className="h-6 w-6" />,
    },
    {
      label: "Quiz",
      value: stats.quiz,
      description: "Series de verification pour tester le rappel.",
      accent: "from-sky-300/90 via-sky-400/30 to-transparent",
      icon: <QuizIcon className="h-6 w-6" />,
    },
    {
      label: "A reviser",
      value: stats.revisions,
      description: "Elements a traiter avant de passer a la suite.",
      accent: "from-rose-300/90 via-rose-400/30 to-transparent",
      icon: <ClockIcon className="h-6 w-6" />,
    },
  ];

  const quickActions: QuickActionDefinition[] = [
    {
      label: "Relancer la memoire",
      href: "/flashcards",
      description: "Passe en revue les cartes dues et garde un rappel actif.",
      meta: `${stats.flashcards} cartes prêtes`,
      accent: "from-teal-500/20 via-teal-400/5 to-transparent",
      icon: <FlashcardIcon className="h-6 w-6" />,
    },
    {
      label: "Tester sous pression",
      href: "/quiz",
      description: "Valide la rapidite de rappel avec une session courte.",
      meta: `${stats.quiz} quiz disponibles`,
      accent: "from-orange-500/20 via-orange-400/5 to-transparent",
      icon: <QuizIcon className="h-6 w-6" />,
    },
    {
      label: "Revenir au fond",
      href: "/fiches",
      description: "Relis les points durs et consolide les raisonnements.",
      meta: `${stats.fiches} fiches a parcourir`,
      accent: "from-sky-500/20 via-sky-400/5 to-transparent",
      icon: <DocumentIcon className="h-6 w-6" />,
    },
    {
      label: "Nettoyer la structure",
      href: "/matieres",
      description: "Reclasse les ressources avant le prochain sprint de revision.",
      meta: `${stats.matieres} matieres actives`,
      accent: "from-stone-200/10 via-stone-200/5 to-transparent",
      icon: <SubjectIcon className="h-6 w-6" />,
    },
    {
      label: "Parler les notions",
      href: "/vocal",
      description: "Passe en mode oral pour verifier la clarte du discours.",
      meta: "Mode oral guide",
      accent: "from-rose-500/20 via-rose-400/5 to-transparent",
      icon: <MicrophoneIcon className="h-6 w-6" />,
    },
    {
      label: "Relier les idees",
      href: "/mindmap",
      description: "Fais remonter les liens entre notions et exceptions.",
      meta: "Vision systemique",
      accent: "from-cyan-500/20 via-cyan-400/5 to-transparent",
      icon: <MindMapIcon className="h-6 w-6" />,
    },
  ];

  return (
    <div className="space-y-8 lg:space-y-10">
      <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-slate-900/70 p-6 shadow-[0_30px_80px_rgba(2,12,27,0.35)] backdrop-blur-xl lg:p-8">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.16),transparent_32%),radial-gradient(circle_at_85%_15%,rgba(234,88,12,0.14),transparent_24%),linear-gradient(135deg,rgba(255,255,255,0.03),transparent_45%)]" />
        <div className="relative grid gap-6 xl:grid-cols-[1.35fr_0.85fr] xl:gap-8">
          <div className="space-y-6">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-teal-200/80">
                Cockpit de revision
              </p>
              <div className="space-y-4">
                <h1 className="max-w-3xl font-heading text-5xl leading-none text-white sm:text-6xl">
                  Une interface plus nette pour piloter la preparation concours.
                </h1>
                <p className="max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                  IACA devient un poste de travail plus lisible: priorites du jour, volumes disponibles et points d&apos;entree rapides sur les modes de revision.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
              <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 capitalize">
                {currentDate || "Aujourd'hui"}
              </span>
              <span className="rounded-full border border-teal-400/20 bg-teal-400/10 px-4 py-2 text-teal-100">
                {stats.revisions > 0 ? `${stats.revisions} revision${stats.revisions > 1 ? "s" : ""} a traiter` : "Aucune revision urgente"}
              </span>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                href="/flashcards"
                className="inline-flex cursor-pointer items-center gap-2 rounded-full bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition-all duration-200 hover:bg-orange-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-200/80 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
              >
                Lancer la revision
                <ArrowUpRightIcon className="h-4 w-4" />
              </Link>
              <Link
                href="/quiz"
                className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-slate-100 transition-all duration-200 hover:border-teal-300/40 hover:bg-teal-300/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-200/80 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
              >
                Ouvrir un quiz
                <ArrowUpRightIcon className="h-4 w-4" />
              </Link>
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/45 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                  Ressources totales
                </p>
                <p className="mt-4 text-4xl font-semibold text-white">
                  <AnimatedNumber value={totalResources} />
                </p>
                <p className="mt-2 text-sm text-slate-400">Corpus pret a etre travaille.</p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                  Modes actifs
                </p>
                <p className="mt-4 text-4xl font-semibold text-white">
                  <AnimatedNumber value={activeModes} />
                </p>
                <p className="mt-2 text-sm text-slate-400">Flashcards, quiz, fiches et revisions.</p>
              </div>
            </div>

            <div className="mt-4 rounded-[1.5rem] border border-orange-300/15 bg-[linear-gradient(180deg,rgba(234,88,12,0.12),rgba(15,23,42,0.22))] p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-orange-100/80">
                    Priorite du jour
                  </p>
                  <h2 className="mt-3 max-w-md text-2xl font-semibold text-white">
                    {priorityTitle}
                  </h2>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/10 p-3 text-orange-50">
                  <DashboardIcon className="h-6 w-6" />
                </div>
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-200/90">
                {priorityDescription}
              </p>
            </div>
          </div>
        </div>
      </section>

      {error ? (
        <div
          role="alert"
          className="rounded-[1.5rem] border border-orange-300/20 bg-orange-300/10 px-5 py-4 text-sm text-orange-50"
        >
          {error}
        </div>
      ) : null}

      <section className="space-y-4">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Volumes
            </p>
            <h2 className="mt-2 font-heading text-3xl text-white">
              Vue d&apos;ensemble des briques de travail
            </h2>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-slate-400">
            Le tableau concentre les volumes utiles pour decider quoi relancer en premier, sans faire defiler plusieurs ecrans.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {metricCards.map((card) => (
            <article
              key={card.label}
              className="group relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-slate-900/70 p-5 shadow-[0_24px_60px_rgba(2,12,27,0.24)] transition-transform duration-300 hover:-translate-y-1"
            >
              <div className={`absolute inset-x-5 top-0 h-px bg-gradient-to-r ${card.accent}`} />
              <div className="relative flex h-full flex-col justify-between gap-8">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                      {card.label}
                    </p>
                    <p className="mt-4 text-4xl font-semibold text-white">
                      <AnimatedNumber value={card.value} />
                    </p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-100">
                    {card.icon}
                  </div>
                </div>
                <p className="text-sm leading-6 text-slate-400">{card.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-[2rem] border border-white/10 bg-slate-900/70 p-6 shadow-[0_24px_60px_rgba(2,12,27,0.24)]">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
                File prioritaire
              </p>
              <h2 className="mt-2 font-heading text-3xl text-white">
                Ce qui merite d&apos;etre traite maintenant
              </h2>
            </div>
            <Link
              href="/flashcards"
              className="inline-flex cursor-pointer items-center gap-2 self-start rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100 transition-colors duration-200 hover:border-teal-300/40 hover:bg-teal-300/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-200/80 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
            >
              Ouvrir les cartes
              <ArrowUpRightIcon className="h-4 w-4" />
            </Link>
          </div>

          {revisions.length === 0 ? (
            <div className="mt-8 rounded-[1.75rem] border border-emerald-300/15 bg-emerald-300/10 px-6 py-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-200/20 bg-emerald-200/10 text-emerald-100">
                <CheckCircleIcon className="h-7 w-7" />
              </div>
              <h3 className="mt-5 text-2xl font-semibold text-white">Aucune revision en retard.</h3>
              <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-300">
                Tu peux basculer sur un quiz, enrichir une matiere ou reprendre une fiche de synthese sans pression immediate.
              </p>
            </div>
          ) : (
            <div className="mt-8 space-y-3">
              {revisions.map((revision, index) => (
                <div
                  key={revision.id}
                  className="flex flex-col gap-4 rounded-[1.5rem] border border-white/10 bg-white/5 p-4 md:flex-row md:items-center md:justify-between"
                >
                  <div className="flex min-w-0 items-start gap-4">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-950/70 text-sm font-semibold text-slate-100">
                      {String(index + 1).padStart(2, "0")}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
                        {formatRevisionDate(revision.prochaine_revision)}
                      </p>
                      <p className="mt-2 line-clamp-2 text-base leading-7 text-slate-100">
                        {revision.question}
                      </p>
                    </div>
                  </div>
                  <Link
                    href="/flashcards"
                    className="inline-flex cursor-pointer items-center gap-2 self-start rounded-full bg-teal-400 px-4 py-2 text-sm font-semibold text-slate-950 transition-colors duration-200 hover:bg-teal-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-100/80 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 md:self-center"
                  >
                    Reviser
                    <ArrowUpRightIcon className="h-4 w-4" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-[2rem] border border-white/10 bg-slate-900/70 p-6 shadow-[0_24px_60px_rgba(2,12,27,0.24)]">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
            Cadence
          </p>
          <h2 className="mt-2 font-heading text-3xl text-white">
            Une journee de travail plus facile a lire
          </h2>

          <div className="mt-8 space-y-4">
            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                01. Consolider
              </p>
              <p className="mt-3 text-lg font-semibold text-white">
                {stats.revisions > 0 ? `${stats.revisions} carte${stats.revisions > 1 ? "s" : ""} prioritaire${stats.revisions > 1 ? "s" : ""}` : "Aucune revision urgente"}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Le meilleur levier pour garder le recall stable avant d&apos;ajouter du volume.
              </p>
            </div>

            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                02. Tester
              </p>
              <p className="mt-3 text-lg font-semibold text-white">
                {stats.quiz > 0 ? `${stats.quiz} quiz pour valider le rappel` : "Aucun quiz charge pour le moment"}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Enchaine un questionnaire court pour verifier ce qui tient sans support.
              </p>
            </div>

            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                03. Reformuler
              </p>
              <p className="mt-3 text-lg font-semibold text-white">
                {stats.fiches > 0 ? `${stats.fiches} fiche${stats.fiches > 1 ? "s" : ""} pour fixer les notions` : "Ajoute des fiches de synthese"}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Termine par une reformulation propre, a l&apos;ecrit ou a l&apos;oral, pour ancrer les nuances.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Entrees rapides
            </p>
            <h2 className="mt-2 font-heading text-3xl text-white">
              Choisir la bonne porte selon l&apos;effort voulu
            </h2>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-slate-400">
            Les actions sont pensees comme des sessions courtes: memoriser, tester, reformuler, reclasser ou faire emerger des liens.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {quickActions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="group relative cursor-pointer overflow-hidden rounded-[1.75rem] border border-white/10 bg-slate-900/70 p-5 shadow-[0_24px_60px_rgba(2,12,27,0.24)] transition-transform duration-300 hover:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-200/80 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${action.accent}`} />
              <div className="relative flex h-full flex-col justify-between gap-8">
                <div className="flex items-start justify-between gap-4">
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-100">
                    {action.icon}
                  </div>
                  <span className="rounded-full border border-white/10 bg-slate-950/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                    {action.meta}
                  </span>
                </div>

                <div>
                  <h3 className="text-2xl font-semibold text-white">{action.label}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-300">
                    {action.description}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
