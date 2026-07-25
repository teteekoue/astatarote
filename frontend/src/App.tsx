import React, { useState, useEffect } from 'react';
import { Terminal, Settings as SettingsIcon, Award, PlusCircle, Gamepad2, User as UserIcon, LogOut, ShieldAlert, Cpu } from 'lucide-react';
import Dashboard from './components/Dashboard/Dashboard';
import CreateGame from './components/Dashboard/CreateGame';
import GameInterface from './components/Game/GameInterface';
import Settings from './components/Settings/Settings';
import Profile from './components/Profile/Profile';

export interface UserPreferencesType {
  provider_ia: string;
  api_key: string;
  theme: string;
  font_size: number;
  terminal_type: string;
}

export interface UserType {
  id: number;
  username: string;
  email: string;
  preferences: UserPreferencesType;
  stats: {
    total_time: number;
    levels_completed: number;
    points: number;
    rank: string;
    badges: string[];
  };
}

export default function App() {
  const [activePage, setActivePage] = useState<string>('dashboard');
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [user, setUser] = useState<UserType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUser = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/users/me');
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        setError("Impossible de charger le profil utilisateur.");
      }
    } catch (err) {
      console.error(err);
      setError("Erreur de connexion au serveur backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const handlePreferencesUpdated = (updatedUser: UserType) => {
    setUser(updatedUser);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#030712] relative overflow-hidden">
        {/* Futuristic glowing bg circles */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#10B981]/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#8B5CF6]/5 rounded-full blur-3xl"></div>
        
        <div className="z-10 flex flex-col items-center space-y-4">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#10B981]"></div>
            <ShieldAlert className="h-6 w-6 text-[#10B981] absolute inset-0 m-auto animate-pulse" />
          </div>
          <h2 className="text-lg font-bold font-mono tracking-widest text-[#10B981]">ASTATAROTE SYSTEMS</h2>
          <p className="font-mono text-xs text-gray-500 uppercase tracking-widest">Initialisation du Noyau Adaptatif...</p>
        </div>
      </div>
    );
  }

  // If in game interface, hide sidebar for maximum focus on terminal (SaaS IDE layout)
  if (activePage === 'game' && selectedGameId) {
    return (
      <div className="min-h-screen flex flex-col bg-[#030712]">
        <GameInterface 
          gameId={selectedGameId}
          user={user!}
          onBackToDashboard={() => {
            fetchUser();
            setActivePage('dashboard');
          }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#030712] text-gray-100 overflow-hidden relative font-sans">
      {/* Dynamic atmospheric ambient lights */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-b from-[#10B981]/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-t from-purple-500/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>

      {/* Modern Vertical Left Sidebar (VS Code / SaaS Style) */}
      <aside className="w-64 bg-[#090D1A]/85 backdrop-blur-xl border-r border-gray-850 flex flex-col justify-between shrink-0 z-20">
        
        {/* Brand Header */}
        <div className="p-6 border-b border-gray-850/60 flex items-center space-x-3">
          <div className="bg-[#10B981]/15 p-2 rounded-xl border border-[#10B981]/30 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <ShieldAlert className="h-5 w-5 text-[#10B981]" />
          </div>
          <div>
            <h1 className="text-md font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-[#10B981] to-emerald-400 font-mono">
              ASTATAROTE
            </h1>
            <p className="text-[9px] text-gray-500 font-mono tracking-widest uppercase">LABS DE CYBERSECURITÉ</p>
          </div>
        </div>

        {/* Sidebar Nav Items */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          <button
            onClick={() => { setActivePage('dashboard'); setSelectedGameId(null); }}
            className={`w-full px-4 py-3 rounded-xl flex items-center space-x-3.5 font-mono text-sm transition-all duration-200 group ${
              activePage === 'dashboard' || activePage === 'create-game'
                ? 'bg-gradient-to-r from-[#10B981]/15 to-emerald-500/5 text-[#10B981] border border-[#10B981]/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/40 border border-transparent'
            }`}
          >
            <Gamepad2 className="h-4.5 w-4.5 group-hover:scale-105 transition-transform" />
            <span className="font-semibold">Mes Laboratoires</span>
          </button>

          <button
            onClick={() => { setActivePage('profile'); setSelectedGameId(null); }}
            className={`w-full px-4 py-3 rounded-xl flex items-center space-x-3.5 font-mono text-sm transition-all duration-200 group ${
              activePage === 'profile'
                ? 'bg-gradient-to-r from-[#10B981]/15 to-emerald-500/5 text-[#10B981] border border-[#10B981]/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/40 border border-transparent'
            }`}
          >
            <Award className="h-4.5 w-4.5 group-hover:scale-105 transition-transform" />
            <span className="font-semibold">Profil & Badges</span>
          </button>

          <button
            onClick={() => { setActivePage('settings'); setSelectedGameId(null); }}
            className={`w-full px-4 py-3 rounded-xl flex items-center space-x-3.5 font-mono text-sm transition-all duration-200 group ${
              activePage === 'settings'
                ? 'bg-gradient-to-r from-[#10B981]/15 to-emerald-500/5 text-[#10B981] border border-[#10B981]/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/40 border border-transparent'
            }`}
          >
            <SettingsIcon className="h-4.5 w-4.5 group-hover:scale-105 transition-transform" />
            <span className="font-semibold">Paramètres</span>
          </button>
        </nav>

        {/* Profile Footer Panel */}
        {user && (
          <div className="p-4 border-t border-gray-850/60 bg-gray-950/30 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#10B981]/10 to-indigo-500/10 border border-gray-850 flex items-center justify-center">
                <UserIcon className="h-4 w-4 text-[#10B981]" />
              </div>
              <div className="text-left">
                <p className="text-xs font-bold text-gray-200 font-mono truncate max-w-[110px]">{user.username}</p>
                <p className="text-[10px] text-amber-500 font-mono tracking-wider">{user.stats.rank}</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs font-black font-mono text-[#10B981]">{user.stats.points} pt</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main Page Area */}
      <main className="flex-1 flex flex-col min-h-0 relative">
        {error ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6">
            <div className="bg-red-950/10 border border-red-500/30 p-6 rounded-2xl max-w-md text-center backdrop-blur-md shadow-2xl">
              <p className="font-mono text-red-400 font-bold mb-2">ERREUR DE CHARGEMENT</p>
              <p className="text-sm text-gray-400 mb-4">{error}</p>
              <button 
                onClick={fetchUser}
                className="w-full py-2 bg-red-500 hover:bg-red-600 text-white font-mono text-sm rounded-xl transition shadow-lg"
              >
                Tenter une Reconnexion
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            {activePage === 'dashboard' && (
              <Dashboard 
                user={user!}
                onCreateGameClick={() => setActivePage('create-game')}
                onPlayGame={(gameId) => {
                  setSelectedGameId(gameId);
                  setActivePage('game');
                }}
              />
            )}
            {activePage === 'create-game' && (
              <CreateGame 
                user={user!}
                onGameCreated={(gameId) => {
                  setSelectedGameId(gameId);
                  fetchUser();
                  setActivePage('game');
                }}
                onCancel={() => setActivePage('dashboard')}
              />
            )}
            {activePage === 'settings' && (
              <Settings 
                user={user!} 
                onPreferencesUpdated={handlePreferencesUpdated} 
              />
            )}
            {activePage === 'profile' && (
              <Profile user={user!} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
