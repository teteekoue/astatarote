import React, { useState, useEffect } from 'react';
import { Play, Trash2, PlusCircle, Gamepad2, Layers, BookOpen, Clock, Zap } from 'lucide-react';
import { UserType } from '../../App';

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

export default function Dashboard({ user, onCreateGameClick, onPlayGame }: DashboardProps) {
  const [games, setGames] = useState<GameType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const fetchGames = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/games');
      if (res.ok) {
        const data = await res.json();
        setGames(data);
      }
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
      const res = await fetch(`/api/games/${gameId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setGames(games.filter(g => g.id !== gameId));
        setDeleteConfirmId(null);
      }
    } catch (err) {
      console.error("Failed to delete game:", err);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-8">
      {/* Welcome & Stats Banner */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-2 bg-gradient-to-br from-[#111827] to-[#070A13] border border-gray-800 p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Bienvenue, Agent <span className="text-[#10B981] font-mono">{user.username}</span> !
            </h2>
            <p className="text-gray-400 text-sm leading-relaxed">
              Astatarote adapte dynamiquement les défis de sécurité et d'administration système selon tes performances. 
              Prépare-toi à déceler des failles, auditer des configurations et automatiser tes défenses.
            </p>
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            <button
              onClick={onCreateGameClick}
              className="px-4 py-2.5 bg-[#10B981] hover:bg-emerald-600 text-black font-semibold font-mono rounded-xl flex items-center space-x-2 text-sm transition-all"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Générer un Nouveau Jeu</span>
            </button>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-2xl flex items-center space-x-4">
          <div className="p-3.5 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-indigo-400">
            <Layers className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono uppercase">Labos Actifs</p>
            <p className="text-2xl font-bold font-mono text-white">
              {games.filter(g => g.status === 'active').length}
            </p>
          </div>
        </div>

        <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-2xl flex items-center space-x-4">
          <div className="p-3.5 bg-[#10B981]/10 rounded-xl border border-[#10B981]/20 text-[#10B981]">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono uppercase">Total Points</p>
            <p className="text-2xl font-bold font-mono text-[#10B981]">
              {user.stats.points || 0} pts
            </p>
          </div>
        </div>
      </div>

      {/* Main Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-gray-800 pb-3">
          <h3 className="text-lg font-bold font-mono tracking-wide text-gray-200 flex items-center space-x-2">
            <BookOpen className="h-5 w-5 text-[#10B981]" />
            <span>Mes Laboratoires Adaptatifs</span>
          </h3>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#10B981]"></div>
          </div>
        ) : games.length === 0 ? (
          <div className="text-center py-16 border-2 border-dashed border-gray-800 rounded-2xl">
            <Gamepad2 className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 font-mono text-sm mb-4">Aucun laboratoire actif pour le moment.</p>
            <button
              onClick={onCreateGameClick}
              className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-[#10B981] border border-[#10B981]/20 font-semibold font-mono rounded-xl text-xs transition"
            >
              Créer mon premier jeu
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {games.map((game) => (
              <div 
                key={game.id} 
                className="bg-[#111827] border border-gray-800 rounded-xl flex flex-col justify-between hover:border-gray-700 transition duration-200"
              >
                <div className="p-5 space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase tracking-wider ${
                        game.domain === 'linux' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                        game.domain === 'security' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                        'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                      }`}>
                        {game.domain}
                      </span>
                      <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wider">
                        {game.level}
                      </span>
                    </div>
                    {deleteConfirmId === game.id ? (
                      <div className="flex items-center space-x-1">
                        <button 
                          onClick={() => handleDeleteGame(game.id)}
                          className="px-1.5 py-0.5 bg-red-600 text-white rounded text-[10px] font-mono hover:bg-red-700"
                        >
                          Oui
                        </button>
                        <button 
                          onClick={() => setDeleteConfirmId(null)}
                          className="px-1.5 py-0.5 bg-gray-800 text-gray-400 rounded text-[10px] font-mono"
                        >
                          Non
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirmId(game.id)}
                        className="text-gray-500 hover:text-red-400 transition p-1"
                        title="Supprimer ce jeu"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>

                  <div>
                    <h4 className="text-md font-bold text-white mb-1 group-hover:text-[#10B981] font-mono">{game.name}</h4>
                    <p className="text-xs text-gray-400 line-clamp-2 min-h-[2rem]">
                      {game.description}
                    </p>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px] font-mono text-gray-500">
                      <span>Progression</span>
                      <span>{Math.round(game.progress)}%</span>
                    </div>
                    <div className="w-full bg-gray-950 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-[#10B981] h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${game.progress}%` }}
                      ></div>
                    </div>
                    <div className="text-[10px] text-gray-500 font-mono flex justify-between">
                      <span>Niveau {game.current_level_index + 1} / {game.total_levels}</span>
                      <span>Statut: {game.status === 'completed' ? 'Complété' : 'En cours'}</span>
                    </div>
                  </div>
                </div>

                <div className="px-5 pb-5 pt-0">
                  <button
                    onClick={() => onPlayGame(game.id)}
                    className="w-full py-2 bg-gray-800 hover:bg-gray-700 text-[#10B981] hover:text-emerald-400 border border-gray-700 hover:border-[#10B981]/30 font-semibold font-mono rounded-lg text-xs flex items-center justify-center space-x-2 transition"
                  >
                    <Play className="h-3.5 w-3.5" />
                    <span>{game.status === 'completed' ? 'Recommencer / Consulter' : 'Continuer le Lab'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
