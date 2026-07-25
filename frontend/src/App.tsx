import React, { useState, useEffect } from 'react';
import { Terminal, Settings as SettingsIcon, Award, PlusCircle, Gamepad2, User as UserIcon, LogOut, ShieldAlert } from 'lucide-react';
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

  // Fetch or initialize user profile on startup
  const fetchUser = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/users/me');
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        // Simple error logging
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

  // Sidebar or header navigation rendering
  return (
    <div className="min-h-screen flex flex-col bg-[#070A13]">
      {/* Header bar */}
      <header className="border-b border-gray-800 bg-[#0B0F19] px-6 py-4 flex items-center justify-between z-20">
        <div 
          className="flex items-center space-x-3 cursor-pointer select-none"
          onClick={() => { setActivePage('dashboard'); setSelectedGameId(null); }}
        >
          <div className="bg-[#10B981]/10 p-2 rounded-lg border border-[#10B981]/30">
            <ShieldAlert className="h-6 w-6 text-[#10B981] animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-[#10B981] to-emerald-400 font-mono">
              ASTATAROTE
            </h1>
            <p className="text-[10px] text-gray-500 font-mono tracking-widest uppercase">Ethical Adaptive Cyber-Lab</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1">
          <button
            onClick={() => { setActivePage('dashboard'); setSelectedGameId(null); }}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 font-mono text-sm transition-all duration-200 ${
              activePage === 'dashboard' || activePage === 'create-game' || activePage === 'game'
                ? 'bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/40'
            }`}
          >
            <Gamepad2 className="h-4 w-4" />
            <span>Mes Jeux</span>
          </button>
          <button
            onClick={() => { setActivePage('profile'); setSelectedGameId(null); }}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 font-mono text-sm transition-all duration-200 ${
              activePage === 'profile'
                ? 'bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/40'
            }`}
          >
            <Award className="h-4 w-4" />
            <span>Profil & Badges</span>
          </button>
          <button
            onClick={() => { setActivePage('settings'); setSelectedGameId(null); }}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 font-mono text-sm transition-all duration-200 ${
              activePage === 'settings'
                ? 'bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/40'
            }`}
          >
            <SettingsIcon className="h-4 w-4" />
            <span>Paramètres</span>
          </button>
        </nav>

        {/* User status */}
        <div className="flex items-center space-x-3">
          {user && (
            <div className="text-right hidden sm:block">
              <p className="text-xs text-gray-500 font-mono">Grade : <span className="text-amber-500 font-semibold">{user.stats.rank || "Novice"}</span></p>
              <p className="text-sm font-semibold text-[#10B981] font-mono">{user.stats.points || 0} pts</p>
            </div>
          )}
          <div 
            onClick={() => setActivePage('profile')}
            className="h-9 w-9 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center cursor-pointer hover:border-[#10B981] transition-all"
          >
            <UserIcon className="h-5 w-5 text-[#10B981]" />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-0 relative">
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#10B981]"></div>
            <p className="font-mono text-gray-400 text-sm">Initialisation d'Astatarote...</p>
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-4 p-6">
            <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-xl max-w-md text-center">
              <p className="font-mono text-red-400 font-bold mb-2">Une erreur est survenue</p>
              <p className="text-sm text-gray-300">{error}</p>
              <button 
                onClick={fetchUser}
                className="mt-4 px-4 py-2 bg-red-500 text-white font-mono text-sm rounded-lg hover:bg-red-600 transition"
              >
                Réessayer
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
                  fetchUser(); // Refresh stats/profile
                  setActivePage('game');
                }}
                onCancel={() => setActivePage('dashboard')}
              />
            )}
            {activePage === 'game' && selectedGameId && (
              <GameInterface 
                gameId={selectedGameId}
                user={user!}
                onBackToDashboard={() => {
                  fetchUser(); // Refresh stats/profile
                  setActivePage('dashboard');
                }}
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
