import React from "react";
import { Zap, Target, Award, ShieldCheck, TrendingUp } from "lucide-react";
import { UserType } from "../../App";

const RANK_STEPS = [
  { label: "Novice", threshold: 0 },
  { label: "Apprenti", threshold: 100 },
  { label: "Administrateur", threshold: 200 },
  { label: "Expert", threshold: 350 },
  { label: "Maître", threshold: 500 },
];

const BADGE_META: Record<string, { label: string; description: string }> = {
  "Linux Ninja": { label: "Linux Ninja", description: "Premier parcours Linux terminé avec succès" },
  "Network Sentinel": { label: "Network Sentinel", description: "Maîtrise des défis réseau" },
  Defender: { label: "Defender", description: "Expertise en cybersécurité défensive" },
  "White Hat": { label: "White Hat", description: "Éthique et excellence offensives" },
};

export default function StatsPage({ user }: { user: UserType }) {
  const stats = user.stats || { points: 0, rank: "Novice", levels_completed: 0, badges: [] };
  const points = stats.points || 0;
  const badges = stats.badges || [];

  const currentStep = [...RANK_STEPS].reverse().find((r) => points >= r.threshold) ?? RANK_STEPS[0];
  const nextStep = RANK_STEPS[RANK_STEPS.indexOf(currentStep) + 1];
  const rankProgress = nextStep
    ? Math.round(((points - currentStep.threshold) / (nextStep.threshold - currentStep.threshold)) * 100)
    : 100;

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 p-4 py-8 sm:px-6 lg:py-10">
      <div>
        <p className="section-title">Statistiques</p>
        <h1 className="mt-1.5 text-2xl font-extrabold tracking-tight sm:text-3xl">
          Votre progression
        </h1>
      </div>

      {/* Points + rank */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="card p-6">
          <div className="flex items-center gap-2 text-muted">
            <Zap className="h-4 w-4 text-primary" />
            <span className="text-[12px] font-semibold uppercase tracking-wide">Points totaux</span>
          </div>
          <p className="mt-2 font-mono text-4xl font-bold">{points}</p>
        </div>
        <div className="card p-6">
          <div className="flex items-center gap-2 text-muted">
            <Target className="h-4 w-4 text-primary" />
            <span className="text-[12px] font-semibold uppercase tracking-wide">Défis validés</span>
          </div>
          <p className="mt-2 font-mono text-4xl font-bold">{stats.levels_completed || 0}</p>
        </div>
        <div className="card p-6">
          <div className="flex items-center gap-2 text-muted">
            <Award className="h-4 w-4 text-primary" />
            <span className="text-[12px] font-semibold uppercase tracking-wide">Grade actuel</span>
          </div>
          <p className="mt-2 text-2xl font-extrabold text-primary">{stats.rank || "Novice"}</p>
        </div>
      </div>

      {/* Rank ladder */}
      <section className="card p-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <h2 className="font-bold">Échelle des grades</h2>
        </div>
        <div className="mt-5 space-y-1">
          {RANK_STEPS.map((step) => {
            const reached = points >= step.threshold;
            const isCurrent = currentStep.label === step.label;
            return (
              <div
                key={step.label}
                className={`flex items-center justify-between rounded-xl border px-4 py-3 transition-colors ${
                  isCurrent
                    ? "border-primary/50 bg-primary/10"
                    : reached
                      ? "border-accent/30 bg-accent/5"
                      : "border-border bg-surface-2/30"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${
                      reached ? "bg-accent" : "bg-border"
                    }`}
                  />
                  <span className={`text-sm font-semibold ${reached ? "text-fg" : "text-muted"}`}>
                    {step.label}
                  </span>
                  {isCurrent && (
                    <span className="chip border-primary/40 text-primary">grade actuel</span>
                  )}
                </div>
                <span className="font-mono text-[12px] text-muted">{step.threshold} pts</span>
              </div>
            );
          })}
        </div>
        {nextStep && (
          <p className="mt-4 text-center text-[13px] text-muted">
            Encore <strong className="text-fg">{nextStep.threshold - points} points</strong> pour
            atteindre le grade <strong className="text-fg">{nextStep.label}</strong>
            <span className="mt-2 block">
              <span className="mt-2 block h-1.5 w-full overflow-hidden rounded-full bg-border/60">
                <span
                  className="block h-full rounded-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
                  style={{ width: `${rankProgress}%` }}
                />
              </span>
            </span>
          </p>
        )}
      </section>

      {/* Badges */}
      <section className="card p-6">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-primary" />
          <h2 className="font-bold">Badges de spécialisation</h2>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(BADGE_META).map(([key, meta]) => {
            const owned = badges.includes(key);
            return (
              <div
                key={key}
                className={`rounded-2xl border p-4 text-center transition-all duration-300 ${
                  owned
                    ? "border-accent/40 bg-accent/10"
                    : "border-border bg-surface-2/30 opacity-60"
                }`}
              >
                <div
                  className={`mx-auto flex h-10 w-10 items-center justify-center rounded-xl ${
                    owned ? "bg-accent/20" : "bg-surface"
                  }`}
                >
                  <Award className={`h-5 w-5 ${owned ? "text-accent" : "text-muted"}`} />
                </div>
                <p className={`mt-3 text-sm font-bold ${owned ? "text-accent" : "text-muted"}`}>
                  {meta.label}
                </p>
                <p className="mt-1 text-[12px] leading-relaxed text-muted">
                  {owned ? "Débloqué" : meta.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
