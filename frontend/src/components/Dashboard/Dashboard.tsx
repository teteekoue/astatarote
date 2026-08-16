import React, { useState, useEffect } from "react";
import {
  Play,
  Trash2,
  PlusCircle,
  Gamepad2,
  Layers,
  BookOpen,
  Zap,
  ShieldCheck,
  Trophy,
  Wifi,
  Lock,
} from "lucide-react";
import { api } from "../../lib/api";
import { UserType } from "../../App";

interface GameType {
  id: number;
  name: string;
  description: string;
  domain: string;
  level: string;
  status: string;
  current_level_index: number;
  total_levels: number;
  progress: number;
  created_at: string;
  updated_at: string;
}

interface DashboardProps {
  user: UserType;
  onCreateGameClick: () => void;
  onPlayGame: (gameId: number) => void;
}

const DOMAIN_META: Record<string, { color: string; icon: typeof ShieldCheck; label: string }> = {
  linux: { color: "bg-blue-500/10 text-blue-400 border-blue-500/25", icon: ShieldCheck, label: "Linux" },
  security: { color: "bg-red-500/10 text-red-400 border-red-500/25", icon: Lock, label: "Cybersécurité" },
  network: { color: "bg-asta-violet/10 text-asta-violet border-asta-violet/25", icon: Wifi, label: "Réseau" },
};

export default function Dashboard({ user, onCreateGameClick, onPlayGame }: DashboardProps) {
  const [games, setGames] = useState<GameType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const fetchGames = async () => {
    try {
      setLoading(true);
      const data = await api.get<GameType[]>("/api/games");
      setGames(data);
    } catch (err) {
      console.error("Failed to fetch games:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
  }, []);

  const handleDeleteGame = async (gameId: number) => {
    try {
      await api.delete(`/api/games/${gameId}`);
      setGames((g) => g.filter((x) => x.id !== gameId));
      setDeleteConfirmId(null);
    } catch (err) {
      console.error("Failed to delete game:", err);
    }
  };

  const activeCount = games.filter((g) => g.status === "active").length;
  const completedCount = games.filter((g) => g.status === "completed").length;
  const totalPoints = user.stats.points || 0;
  const badges = user.stats.badges?.length || 0;

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 min-h-0">
      {/* Welcome hero */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 panel panel-hover p-8 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-40 h-40 bg-asta-green/8 rounded-full blur-3xl group-hover:bg-asta-green/12 transition-all duration-500"></div>
          <div className="relative z-10">
            <span className="chip bg-asta-green/10 text-asta-green border-asta-green/25 mb-4">
              <span className="h-1.5 w-1.5 rounded-full bg-asta-green animate-pulse-glow mr-1"></span>
              SYSTÈME ADAPTATIF ACTIF
            </span>
            <h2 className="text-3xl font-display font-extrabold text-white mb-2 leading-tight tracking-tight">
              Bienvenue,{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-asta-green to-emerald-300 font-mono">
                {user.username}
              </span>
            </h2>
            <p className="text-gray-400 text-sm leading-relaxed max-w-xl">
              Astatarote construit chaque défi sur mesure : un vrai shell Linux, des fichiers réels à auditer,
              et un coéquipier IA pour t'épauler sans te mâcher le travail.
            </p>
          </div>
          <div className="mt-8 relative z-10 flex">
            <button onClick={onCreateGameClick} className="btn-primary">
              <PlusCircle className="h-4 w-4" />
              Générer un nouveau laboratoire
            </button>
          </div>
        </div>

        {/* Stat stack */}
        <div className="grid grid-cols-2 gap-4">
          <div className="panel panel-hover p-5 flex items-center gap-4">
            <div className="p-3.5 bg-asta-violet/10 rounded-xl border border-asta-violet/20 text-asta-violet">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest">Labos actifs</p>
              <p className="text-2xl font-black font-mono text-white mt-0.5">{activeCount}</p>
            </div>
          </div>
          <div className="panel panel-hover p-5 flex items-center gap-4">
            <div className="p-3.5 bg-asta-green/10 rounded-xl border border-asta-green/20 text-asta-green">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest">Points</p>
              <p className="text-2xl font-black font-mono text-asta-green mt-0.5">{totalPoints}</p>
            </div>
          </div>
          <div className="panel panel-hover p-5 flex items-center gap-4">
            <div className="p-3.5 bg-blue-500/10 rounded-xl border border-blue-500/20 text-blue-400">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest">Labos terminés</p>
              <p className="text-2xl font-black font-mono text-white mt-0.5">{completedCount}</p>
            </div>
          </div>
          <div className="panel panel-hover p-5 flex items-center gap-4">
            <div className="p-3.5 bg-asta-amber/10 rounded-xl border border-asta-amber/20 text-asta-amber">
              <Trophy className="h-5 w-5" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest">Badges</p>
              <p className="text-2xl font-black font-mono text-asta-amber mt-0.5">{badges}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Labs list */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-ink-line/70 pb-3">
          <h3 className="section-title">
            <BookOpen className="h-5 w-5 text-asta-green" />
            Mes laboratoires adaptatifs
          </h3>
        </div>

        {loading ? (
          <div className="py-16 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-asta-green"></div>
          </div>
        ) : games.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-ink-line rounded-2xl bg-ink-deep/20">
            <Gamepad2 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 font-mono text-sm mb-5">Aucun laboratoire actif pour le moment.</p>
            <button onClick={onCreateGameClick} className="btn-ghost">
              Créer mon premier laboratoire
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {games.map((game) => {
              const meta = DOMAIN_META[game.domain] ?? DOMAIN_META.linux;
              const Icon = meta.icon;
              return (
                <div
                  key={game.id}
                  className="panel flex flex-col justify-between hover:border-gray-600/60 hover:shadow-glow transition-all duration-300 relative overflow-hidden group"
                >
                  <div className="p-6 space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex flex-wrap gap-1.5">
                        <span className={`chip gap-1 ${meta.color}`}>
                          <Icon className="h-3 w-3" />
                          {meta.label}
                        </span>
                        <span className="chip bg-asta-amber/10 text-asta-amber border-asta-amber/25">
                          {game.level}
                        </span>
                      </div>
                      {deleteConfirmId === game.id ? (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handleDeleteGame(game.id)}
                            className="px-2 py-0.5 bg-red-600 text-white rounded text-[10px] font-mono font-bold hover:bg-red-700"
                          >
                            Oui
                          </button>
                          <button
                            onClick={() => setDeleteConfirmId(null)}
                            className="px-2 py-0.5 bg-ink-deep text-gray-400 rounded text-[10px] font-mono font-bold"
                          >
                            Non
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirmId(game.id)}
                          className="text-gray-600 hover:text-red-400 transition p-1 rounded-lg hover:bg-red-500/10"
                          title="Supprimer ce laboratoire"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>

                    <div>
                      <h4 className="text-md font-display font-bold text-white mb-2 font-mono tracking-wide">
                        {game.name}
                      </h4>
                      <p className="text-xs text-gray-400 leading-relaxed line-clamp-2 min-h-[2rem]">
                        {game.description}
                      </p>
                    </div>

                    <div className="space-y-2 pt-2">
                      <div className="flex justify-between text-[10px] font-mono text-gray-500">
                        <span>Progression</span>
                        <span className="font-bold text-asta-green">{Math.round(game.progress)}%</span>
                      </div>
                      <div className="w-full bg-ink-deep border border-ink-line rounded-full h-2 overflow-hidden p-[1px]">
                        <div
                          className="bg-gradient-to-r from-asta-green to-emerald-400 h-full rounded-full transition-all duration-300 shadow-glow-sm"
                          style={{ width: `${game.progress}%` }}
                        ></div>
                      </div>
                      <div className="text-[9px] text-gray-500 font-mono flex justify-between">
                        <span>
                          DÉFI {Math.min(game.current_level_index + 1, game.total_levels)} / {game.total_levels}
                        </span>
                        <span className={game.status === "completed" ? "text-emerald-500 font-bold" : "text-gray-400"}>
                          {game.status === "completed" ? "TERMINÉ" : "EN COURS"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="px-6 pb-6 pt-0">
                    <button
                      onClick={() => onPlayGame(game.id)}
                      className="w-full py-2.5 bg-ink-deep hover:bg-asta-green text-asta-green hover:text-black border border-ink-line hover:border-transparent font-bold font-mono rounded-xl text-xs flex items-center justify-center gap-2 transition-all duration-300"
                    >
                      <Play className="h-3.5 w-3.5" />
                      {game.status === "completed" ? "Consulter / Recommencer" : "Continuer le laboratoire"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
