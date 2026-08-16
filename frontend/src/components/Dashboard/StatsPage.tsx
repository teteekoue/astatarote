import React from "react";
import {
  BarChart3,
  Zap,
  CheckCircle2,
  Trophy,
  Shield,
  TrendingUp,
  Award,
  Terminal,
} from "lucide-react";
import { UserType } from "../../App";

interface StatsPageProps {
  user: UserType;
}

const RANK_TIERS = [
  { min: 500, label: "Maître" },
  { min: 350, label: "Expert" },
  { min: 200, label: "Administrateur" },
  { min: 100, label: "Apprenti" },
  { min: 0, label: "Novice" },
];

export default function StatsPage({ user }: StatsPageProps) {
  const points = user.stats.points || 0;
  const levelsDone = user.stats.levels_completed || 0;
  const badges = user.stats.badges?.length || 0;

  const currentTierIndex = RANK_TIERS.findIndex((t) => points >= t.min);
  const nextTier = RANK_TIERS[currentTierIndex - 1];
  const progressToNext =
    nextTier && nextTier.min > points ? Math.min(100, Math.round((points / nextTier.min) * 100)) : 100;

  const statsList = [
    { label: "Points cumulés", value: `${points}`, icon: Zap, color: "text-asta-amber bg-asta-amber/10 border-asta-amber/20" },
    { label: "Défis résolus", value: `${levelsDone}`, icon: CheckCircle2, color: "text-asta-green bg-asta-green/10 border-asta-green/20" },
    { label: "Badges obtenus", value: `${badges}`, icon: Award, color: "text-asta-violet bg-asta-violet/10 border-asta-violet/20" },
    { label: "Grade actuel", value: `${user.stats.rank || "Novice"}`, icon: Trophy, color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 select-none">
      <div className="flex items-center gap-3 border-b border-ink-line/70 pb-4">
        <div className="p-2.5 bg-asta-green/10 rounded-xl border border-asta-green/20">
          <BarChart3 className="h-5 w-5 text-asta-green" />
        </div>
        <div>
          <h2 className="text-xl font-display font-bold text-white tracking-wide">Centre de télémétrie</h2>
          <p className="text-xs text-gray-400">Ta progression réelle à travers les laboratoires Astatarote.</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsList.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="panel panel-hover p-6 flex items-center gap-4 shadow-card animate-fade-in" style={{ animationDelay: `${idx * 60}ms` }}>
              <div className={`p-3.5 rounded-xl border ${stat.color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest font-bold">{stat.label}</p>
                <p className="text-xl font-black font-mono text-white mt-1">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rank progression */}
        <div className="lg:col-span-2 panel p-6 space-y-5 shadow-card">
          <h4 className="section-title">
            <TrendingUp className="h-4 w-4 text-asta-green" />
            Progression du grade
          </h4>

          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono font-bold">
                <span className="text-gray-300">Grade actuel : {user.stats.rank || "Novice"}</span>
                <span className="text-asta-green">
                  {nextTier ? `${points} / ${nextTier.min} pts` : "Grade maximal atteint"}
                </span>
              </div>
              <div className="w-full bg-ink-deep border border-ink-line p-[1px] rounded-full h-2.5 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-asta-green to-emerald-400 shadow-glow-sm transition-all duration-500"
                  style={{ width: `${progressToNext}%` }}
                ></div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {RANK_TIERS.map((t, i) => {
                const reached = points >= t.min;
                return (
                  <div
                    key={i}
                    className={`p-2.5 rounded-lg border text-center ${
                      reached
                        ? "bg-asta-green/10 border-asta-green/30"
                        : "bg-ink-deep/50 border-ink-line opacity-50"
                    }`}
                  >
                    <p className={`text-[10px] font-mono font-black uppercase tracking-wide ${reached ? "text-asta-green" : "text-gray-500"}`}>
                      {t.label}
                    </p>
                    <p className="text-[8px] font-mono text-gray-500 mt-0.5">{t.min} pts</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Rank summary */}
        <div className="panel p-6 space-y-4 shadow-card flex flex-col justify-between">
          <h4 className="section-title">
            <Shield className="h-4 w-4 text-asta-green" />
            Résumé de l'agent
          </h4>
          <div className="space-y-3">
            {[
              { label: "Défis complétés", value: `${levelsDone}` },
              { label: "Points de carrière", value: `${points}` },
              { label: "Badges de spécialisation", value: `${badges}` },
            ].map((row, i) => (
              <div key={i} className="flex justify-between items-center text-xs font-mono p-3 rounded-lg bg-ink-deep/50 border border-ink-line/60">
                <span className="text-gray-400">{row.label}</span>
                <span className="text-white font-bold">{row.value}</span>
              </div>
            ))}
          </div>
          <div className="pt-2 text-center">
            <span className="text-[11px] font-mono font-bold bg-asta-green/10 border border-asta-green/25 text-asta-green px-4 py-2 rounded-xl block">
              <Terminal className="h-3 w-3 inline mr-1" />
              SANDBOX RÉELLE À CHAQUE DÉFI
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
