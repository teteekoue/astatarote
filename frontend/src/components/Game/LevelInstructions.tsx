import React, { useState } from "react";
import {
  Target,
  Lightbulb,
  BookOpen,
  ChevronDown,
  ClipboardList,
  Lock,
} from "lucide-react";
import Markdown from "../Markdown";

export interface LevelType {
  id: number;
  game_id: number;
  level_index: number;
  title: string;
  description: string;
  objective: string;
  situation_probleme?: string | null;
  consigne?: string | null;
  support_technique?: string | null;
  hints: string[];
  difficulty: number;
  points: number;
  time_limit: number;
  status: string;
}

function DifficultyDots({ level }: { level: number }) {
  const dots = Math.min(5, Math.max(1, Math.round(level / 2)));
  return (
    <span className="flex items-center gap-1" title={`Difficulté ${level}/10`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={`h-1.5 w-1.5 rounded-full ${i < dots ? "bg-primary" : "bg-border"}`}
        />
      ))}
    </span>
  );
}

export default function LevelInstructions({ level }: { level: LevelType }) {
  const [openHints, setOpenHints] = useState(0);

  const steps: string[] = (level.consigne || "")
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map((s) => s.replace(/^-\s*/, ""));

  return (
    <div className="flex h-full flex-col gap-5 overflow-y-auto p-5">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-primary">
            Défi {level.level_index + 1}
          </span>
          <DifficultyDots level={level.difficulty} />
          <span className="chip">{level.points} pts</span>
          {level.status === "completed" && (
            <span className="chip border-accent/40 text-accent">terminé</span>
          )}
        </div>
        <h2 className="mt-2 text-lg font-bold leading-snug">{level.title}</h2>
      </div>

      {/* Situation */}
      {level.situation_probleme && (
        <section className="card bg-surface-2/40 p-4">
          <div className="mb-2 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wide text-muted">
            <BookOpen className="h-3.5 w-3.5 text-primary" />
            Contexte
          </div>
          <Markdown text={level.situation_probleme} />
        </section>
      )}

      {/* Mission */}
      <section>
        <div className="mb-2.5 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wide text-muted">
          <Target className="h-3.5 w-3.5 text-primary" />
          Votre mission
        </div>
        <ol className="space-y-2.5">
          {steps.map((step, i) => (
            <li
              key={i}
              className="flex items-start gap-3 rounded-xl border border-border bg-surface px-3.5 py-3"
            >
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-primary/15 font-mono text-[11px] font-bold text-primary">
                {i + 1}
              </span>
              <Markdown text={step} />
            </li>
          ))}
        </ol>
      </section>

      {/* Objective */}
      <section className="rounded-xl border border-primary/25 bg-primary/8 p-4">
        <div className="flex items-start gap-2.5">
          <Target className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <div>
            <span className="text-[12px] font-semibold uppercase tracking-wide text-primary">
              Objectif
            </span>
            <p className="mt-1 text-sm leading-relaxed text-fg/90">{level.objective}</p>
          </div>
        </div>
      </section>

      {/* Hints */}
      {level.hints.length > 0 && (
        <section>
          <div className="mb-2 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wide text-muted">
            <Lightbulb className="h-3.5 w-3.5 text-warning" />
            Indices progressifs
          </div>
          <div className="space-y-2">
            {level.hints.map((hint, i) => {
              const unlocked = i < openHints;
              return (
                <div key={i}>
                  {unlocked ? (
                    <div className="rounded-xl border border-warning/25 bg-warning/8 px-3.5 py-3 text-sm leading-relaxed text-fg/90">
                      <span className="font-mono text-[11px] font-bold uppercase text-warning">
                        Indice {i + 1}
                      </span>
                      <p className="mt-1">{hint}</p>
                    </div>
                  ) : (
                    i === openHints && (
                      <button
                        onClick={() => setOpenHints(i + 1)}
                        className="btn-secondary w-full justify-between text-[13px]"
                      >
                        <span className="flex items-center gap-2">
                          <Lock className="h-3.5 w-3.5 text-warning" />
                          Révéler l'indice {i + 1} / {level.hints.length}
                        </span>
                        <ChevronDown className="h-4 w-4" />
                      </button>
                    )
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Tech sheet */}
      {level.support_technique && (
        <section>
          <details className="group rounded-xl border border-border bg-surface">
            <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-[13px] font-semibold text-fg transition-colors hover:text-primary">
              <span className="flex items-center gap-2">
                <ClipboardList className="h-4 w-4 text-primary" />
                Fiche technique — aide-mémoire
              </span>
              <ChevronDown className="h-4 w-4 transition-transform duration-200 group-open:rotate-180" />
            </summary>
            <div className="border-t border-border px-4 py-3">
              <Markdown text={level.support_technique} />
            </div>
          </details>
        </section>
      )}
    </div>
  );
}
