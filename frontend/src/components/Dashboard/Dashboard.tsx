import React, { useEffect, useState } from "react";
import {
  Play,
  RotateCcw,
  Trophy,
  Zap,
  BarChart3,
  Award,
  ChevronRight,
  Compass,
  CheckCircle2,
  Clock,
  Target,
} from "lucide-react";
import { api, GameSummary } from "../../lib/api";
import { UserType } from "../../App";

interface DashboardProps {
  user: UserType;
  onPlayGame: (gameId: number, gameName: string) => void;
  onBrowseCatalog: () => void;
}

const RANK_COLORS: Record<string, string> = {
  Novice: "text-muted",
  Apprenti: "text-accent",
  Administrateur: "text-primary",
  Expert: "text-warning",
  Maître: "text-warning",
};

export default function Dashboard({ user, onPlayGame, onBrowseCatalog }: DashboardProps) {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  const load = () => {
    api
      .get<GameSummary[]>("/api/games")
      .then((data) => {
        setGames(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(load, []);

  const removeGame = async (gameId: number) => {
    try {
      await api.delete(`/api/games/${gameId}`);
      setConfirmDelete(null);
      load();
    } catch (err) {
      console.error(err);
    }
  };

  const stats = user.stats || { points: 0, rank: "Novice", levels_completed: 0, badges: [] };
  const activeGames = games.filter((g) => g.status === "active");
  const completedGames = games.filter((g) => g.status === "completed");

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 p-4 py-8 sm:px-6 lg:py-10">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="section-title">Tableau de bord</p>
          <h1 className="mt-1.5 text-2xl font-extrabold tracking-tight sm:text-3xl">
            Bon retour, {user.username} 👋
          </h1>
          <p className="mt-1 text-sm text-muted">
            {activeGames.length > 0
              ? "Vos parcours en cours vous attendent."
              : "Lancez votre premier parcours pour entrer dans le laboratoire."}
          </p>
        </div>
        <button onClick={onBrowseCatalog} className="btn-secondary">
          <Compass className="h-4 w-4" />
          Explorer le catalogue
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 text-muted">
            <Zap className="h-4 w-4 text-primary" />
            <span className="text-[12px] font-semibold uppercase tracking-wide">Points</span>
          </div>
          <p className="mt-2 font-mono text-3xl font-bold">{stats.points || 0}</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-2 text-muted">
            <Award className="h-4 w-4 text-primary" />
            <span className="text-[12px] font-semibold uppercase tracking-wide">Grade</span>
          </div>
          <p className={`mt-2 text-2xl font-extrabold ${RANK_COLORS[stats.rank] ?? "text-fg"}`}>
            {stats.rank || "Novice"}
          </p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-2 text-muted">
            <Target className="h-4 w-4 text-primary" />
            <span className="text-[12px] font-semibold uppercase tracking-wide">Défis réussis</span>
          </div>
          <p className="mt-2 font-mono text-3xl font-bold">{stats.levels_completed || 0}</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-2 text-muted">
            <Trophy className="h-4 w-4 text-primary" />
            <span className="text-[12px] font-semibold uppercase tracking-wide">Badges</span>
          </div>
          <p className="mt-2 font-mono text-3xl font-bold">{(stats.badges || []).length}</p>
        </div>
      </div>

      {/* Active courses */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold">Mes parcours</h2>
          {games.length > 0 && (
            <span className="text-[13px] text-muted">
              {completedGames.length} terminé{completedGames.length > 1 ? "s" : ""} sur {games.length}
            </span>
          )}
        </div>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {[0, 1].map((i) => (
              <div key={i} className="card h-40 animate-pulse" />
            ))}
          </div>
        ) : activeGames.length === 0 && completedGames.length === 0 ? (
          <div className="card flex flex-col items-center p-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-border bg-surface-2">
              <Compass className="h-6 w-6 text-primary" />
            </div>
            <p className="mt-4 font-semibold">Aucun parcours pour l'instant</p>
            <p className="mt-1 max-w-sm text-sm text-muted">
              Choisissez un parcours figé dans le catalogue et lancez votre première mission
              dans le terminal simulé.
            </p>
            <button onClick={onBrowseCatalog} className="btn-primary mt-6">
              Découvrir le catalogue
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {[...activeGames, ...completedGames].map((game) => {
              const done = game.status === "completed";
              return (
                <div key={game.id} className="card group p-5 transition-all duration-300 hover:border-primary/40">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="chip">{game.domain}</span>
                        <span className="chip">{game.level}</span>
                        {done && (
                          <span className="chip border-accent/40 text-accent">
                            <CheckCircle2 className="h-3 w-3" /> terminé
                          </span>
                        )}
                      </div>
                      <h3 className="mt-2.5 truncate font-bold">{game.name}</h3>
                      <p className="mt-1 line-clamp-2 text-[13px] leading-relaxed text-muted">
                        {game.description}
                      </p>
                    </div>
                    <button
                      onClick={() => setConfirmDelete(game.id)}
                      className="btn-ghost !p-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100 focus-visible:opacity-100"
                      title="Supprimer ce parcours"
                      aria-label="Supprimer ce parcours"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </button>
                  </div>

                  {confirmDelete === game.id ? (
                    <div className="mt-4 flex items-center justify-between rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5">
                      <span className="text-[13px] text-danger">
                        Supprimer ce parcours et sa progression ?
                      </span>
                      <div className="flex gap-2">
                        <button onClick={() => setConfirmDelete(null)} className="btn-ghost !py-1.5 !text-[12px]">
                          Annuler
                        </button>
                        <button onClick={() => removeGame(game.id)} className="btn-danger !py-1.5 !px-3 !text-[12px]">
                          Supprimer
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-[12px] text-muted">
                          <span>
                            Défi {Math.min(game.current_level_index + 1, game.total_levels)} /{" "}
                            {game.total_levels}
                          </span>
                          <span className="font-mono">{Math.round(game.progress)}%</span>
                        </div>
                        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-border/60">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              done
                                ? "bg-accent"
                                : "bg-gradient-to-r from-primary to-accent"
                            }`}
                            style={{ width: `${game.progress}%` }}
                          />
                        </div>
                      </div>
                      <button
                        onClick={() => onPlayGame(game.id, game.name)}
                        className="btn-primary mt-4 w-full"
                      >
                        <Play className="h-4 w-4" />
                        {done ? "Rejouer" : game.progress > 0 ? "Continuer" : "Commencer"}
                      </button>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
