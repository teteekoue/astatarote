import React, { useState, useEffect } from 'react';
import { Play, Trash2, PlusCircle, Gamepad2, Layers, BookOpen, Clock, Zap, Cpu, Terminal as TermIcon } from 'lucide-react';
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
    <div className="flex-1 overflow-y-auto p-8 space-y-8 min-h-0">
      
      {/* Top Welcome Panel with Glassmorphism */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-gradient-to-br from-[#0F1423]/90 to-[#0A0D1A]/90 backdrop-blur-md border border-gray-800/80 p-8 rounded-2xl flex flex-col justify-between shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#10B981]/5 rounded-full blur-2xl group-hover:bg-[#10B981]/10 transition-all duration-300"></div>
          <div>
            <h2 className="text-3xl font-black text-white mb-2 leading-tight tracking-tight">
              Bienvenue, Agent <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#10B981] to-emerald-400 font-mono">{user.username}</span> !
            </h2>
            <p className="text-gray-400 text-sm leading-relaxed max-w-xl font-medium">
              Astatarote adapte dynamiquement les défis de sécurité et d'administration système selon tes performances. 
              Prépare-toi à déceler des failles, auditer des configurations et automatiser tes défenses.
            </p>
          </div>
          <div className="mt-8 flex">
            <button
              onClick={onCreateGameClick}
              className="px-5 py-3 bg-[#10B981] hover:bg-emerald-500 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] text-black font-extrabold font-mono rounded-xl flex items-center space-x-2 text-sm transition-all duration-300"
            >
              <PlusCircle className="h-4.5 w-4.5" />
              <span>Générer un Nouveau Jeu</span>
            </button>
          </div>
        </div>

        {/* Quick Stat Cards */}
        <div className="grid grid-cols-1 gap-4">
          <div className="bg-[#0A0D1A]/80 backdrop-blur-md border border-gray-800/60 p-5 rounded-2xl flex items-center space-x-4 shadow-xl hover:border-gray-750 transition-all duration-200">
            <div className="p-4 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-indigo-400">
              <Layers className="h-5.5 w-5.5" />
            </div>
            <div>
              <p className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Labos Actifs</p>
              <p className="text-2xl font-black font-mono text-white mt-0.5">
                {games.filter(g => g.status === 'active').length}
              </p>
            </div>
          </div>

          <div className="bg-[#0A0D1A]/80 backdrop-blur-md border border-gray-800/60 p-5 rounded-2xl flex items-center space-x-4 shadow-xl hover:border-gray-750 transition-all duration-200">
            <div className="p-4 bg-[#10B981]/10 rounded-xl border border-[#10B981]/20 text-[#10B981] shadow-[0_0_15px_rgba(16,185,129,0.05)]">
              <Zap className="h-5.5 w-5.5" />
            </div>
            <div>
              <p className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Total Points</p>
              <p className="text-2xl font-black font-mono text-[#10B981] mt-0.5">
                {user.stats.points || 0} pts
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Labs List Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-gray-800/80 pb-3">
          <h3 className="text-md font-bold font-mono tracking-wider text-gray-200 flex items-center space-x-2.5">
            <BookOpen className="h-5 w-5 text-[#10B981]" />
            <span>Mes Laboratoires Adaptatifs</span>
          </h3>
        </div>

        {loading ? (
          <div className="py-16 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#10B981]"></div>
          </div>
        ) : games.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-gray-800 rounded-2xl bg-gray-950/20">
            <Gamepad2 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 font-mono text-sm mb-5">Aucun laboratoire actif pour le moment.</p>
            <button
              onClick={onCreateGameClick}
              className="px-5 py-3 bg-gray-900 hover:bg-gray-850 text-[#10B981] border border-[#10B981]/20 hover:border-[#10B981]/40 font-semibold font-mono rounded-xl text-xs transition duration-200"
            >
              Créer mon premier jeu
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {games.map((game) => (
              <div 
                key={game.id} 
                className="bg-[#090D1A]/90 border border-gray-850 rounded-2xl flex flex-col justify-between hover:border-gray-700/60 shadow-xl transition-all duration-300 hover:shadow-2xl relative overflow-hidden group"
              >
                <div className="p-6 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex flex-wrap gap-1.5">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-black font-mono uppercase tracking-widest border ${
                        game.domain === 'linux' ? 'bg-blue-950/30 text-blue-400 border-blue-900/40' :
                        game.domain === 'security' ? 'bg-red-950/30 text-red-400 border-red-900/40' :
                        'bg-purple-950/30 text-purple-400 border-purple-900/40'
                      }`}>
                        {game.domain}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[9px] font-black font-mono bg-amber-950/30 text-amber-400 border border-amber-900/40 uppercase tracking-widest">
                        {game.level}
                      </span>
                    </div>
                    {deleteConfirmId === game.id ? (
                      <div className="flex items-center space-x-1.5">
                        <button 
                          onClick={() => handleDeleteGame(game.id)}
                          className="px-2 py-0.5 bg-red-600 text-white rounded text-[10px] font-mono font-bold hover:bg-red-700"
                        >
                          Oui
                        </button>
                        <button 
                          onClick={() => setDeleteConfirmId(null)}
                          className="px-2 py-0.5 bg-gray-800 text-gray-400 rounded text-[10px] font-mono font-bold"
                        >
                          Non
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirmId(game.id)}
                        className="text-gray-500 hover:text-red-400 transition p-1 rounded-lg hover:bg-gray-900"
                        title="Supprimer ce jeu"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>

                  <div>
                    <h4 className="text-md font-black text-white mb-2 font-mono tracking-wide">{game.name}</h4>
                    <p className="text-xs text-gray-400 leading-relaxed line-clamp-2 min-h-[2rem]">
                      {game.description}
                    </p>
                  </div>

                  {/* Progress panel */}
                  <div className="space-y-2 pt-2">
                    <div className="flex justify-between text-[10px] font-mono text-gray-500">
                      <span>Progression</span>
                      <span className="font-bold text-[#10B981]">{Math.round(game.progress)}%</span>
                    </div>
                    <div className="w-full bg-gray-950/60 border border-gray-850 rounded-full h-2 overflow-hidden p-[1px]">
                      <div 
                        className="bg-gradient-to-r from-[#10B981] to-emerald-400 h-full rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                        style={{ width: `${game.progress}%` }}
                      ></div>
                    </div>
                    <div className="text-[9px] text-gray-500 font-mono flex justify-between">
                      <span>NIVEAU {game.current_level_index + 1} / {game.total_levels}</span>
                      <span>STATUT: <span className={game.status === 'completed' ? 'text-emerald-500 font-bold' : 'text-gray-400'}>{game.status === 'completed' ? 'COMPLÉTÉ' : 'EN COURS'}</span></span>
                    </div>
                  </div>
                </div>

                <div className="px-6 pb-6 pt-0">
                  <button
                    onClick={() => onPlayGame(game.id)}
                    className="w-full py-2.5 bg-gray-950 hover:bg-[#10B981] text-[#10B981] hover:text-black border border-gray-800 hover:border-transparent font-bold font-mono rounded-xl text-xs flex items-center justify-center space-x-2 transition-all duration-300"
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
