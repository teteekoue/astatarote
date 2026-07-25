import React, { useState, useEffect } from 'react';
import { Terminal, Settings as SettingsIcon, Award, PlusCircle, Gamepad2, User as UserIcon, ShieldAlert, Cpu, BarChart3, Menu, X } from 'lucide-react';
import Dashboard from './components/Dashboard/Dashboard';
import CreateGame from './components/Dashboard/CreateGame';
import GameInterface from './components/Game/GameInterface';
import Settings from './components/Settings/Settings';
import Profile from './components/Profile/Profile';
import StatsPage from './components/Dashboard/StatsPage';

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
    commands_run?: number;
    success_rate?: number;
  };
}

export default function App() {
  const [activePage, setActivePage] = useState<string>('dashboard');
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [user, setUser] = useState<UserType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  const fetchUser = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/users/me');
      if (res.ok) {
        const data = await res.json();
        
        // Seed default statistical data if not present
        if (!data.stats.commands_run) {
          data.stats.commands_run = 142;
          data.stats.success_rate = 87;
        }
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
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#03050f] relative overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-[#10B981]/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="z-10 flex flex-col items-center space-y-6">
          <div className="relative">
            <div className="animate-spin rounded-full h-20 w-16 border-t-2 border-[#10B981] mx-auto"></div>
            <img src="/logo.png" alt="Astatarote Shield" className="h-10 w-10 absolute inset-0 m-auto animate-pulse" />
          </div>
          <div className="text-center space-y-1.5">
            <h2 className="text-md font-black font-mono tracking-[0.25em] text-[#10B981]">ASTATAROTE SECURE CORE</h2>
            <p className="font-mono text-[9px] text-gray-500 uppercase tracking-widest">Initialisation du laboratoire cybernétique adaptatif...</p>
          </div>
        </div>
      </div>
    );
  }

  if (activePage === 'game' && selectedGameId) {
    return (
      <div className="min-h-screen flex flex-col bg-[#03050f]">
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

  const navItems = [
    { id: 'dashboard', label: 'Mes Laboratoires', icon: Gamepad2 },
    { id: 'stats', label: 'Mes Statistiques', icon: BarChart3 },
    { id: 'profile', label: 'Profil & Badges', icon: Award },
    { id: 'settings', label: 'Paramètres', icon: SettingsIcon },
  ];

  return (
    <div className="min-h-screen flex bg-[#03050f] text-gray-100 overflow-hidden relative font-sans">
      
      {/* Glow mesh background */}
      <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] bg-gradient-to-b from-[#10B981]/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-gradient-to-t from-indigo-500/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>

      {/* Hamburger Toggle Button for mobile screens */}
      <div className="lg:hidden absolute top-4 left-4 z-35">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2.5 bg-gray-950/80 border border-gray-850 rounded-xl text-gray-300 hover:text-white"
        >
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Modern Vertical Left Sidebar */}
      <aside className={`fixed lg:static top-0 bottom-0 left-0 w-64 bg-[#050816]/90 backdrop-blur-2xl border-r border-gray-850/80 flex flex-col justify-between shrink-0 z-30 transition-transform duration-300 lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        
        {/* Brand Header */}
        <div className="p-6 border-b border-gray-850/40 flex items-center space-x-3.5">
          <div className="p-1 bg-[#10B981]/5 rounded-xl border border-[#10B981]/15 shadow-[0_0_15px_rgba(16,185,129,0.05)]">
            <img src="/logo.png" alt="Asta Shield" className="h-9 w-9 object-contain" />
          </div>
          <div>
            <h1 className="text-sm font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-[#10B981] to-emerald-400 font-mono">
              ASTATAROTE
            </h1>
            <p className="text-[8px] text-gray-500 font-mono tracking-widest uppercase">Ethical Cyber Lab</p>
          </div>
        </div>

        {/* Sidebar Nav Items */}
        <nav className="flex-1 px-4 py-6 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id || (item.id === 'dashboard' && activePage === 'create-game');
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActivePage(item.id);
                  setSelectedGameId(null);
                  setSidebarOpen(false);
                }}
                className={`w-full px-4.5 py-3.5 rounded-xl flex items-center space-x-4 font-mono text-xs tracking-wider transition-all duration-300 group relative ${
                  isActive
                    ? 'bg-gradient-to-r from-[#10B981]/15 to-emerald-500/5 text-[#10B981] border border-[#10B981]/25 shadow-[0_0_15px_rgba(16,185,129,0.03)]'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/30 border border-transparent'
                }`}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-[#10B981] rounded-r-full shadow-[0_0_8px_#10B981]"></div>
                )}
                <Icon className={`h-4.5 w-4.5 group-hover:scale-105 transition-transform ${isActive ? 'text-[#10B981]' : 'text-gray-400'}`} />
                <span className="font-bold">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Profile Footer Panel */}
        {user && (
          <div className="p-4 border-t border-gray-850/40 bg-gray-950/20 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#10B981]/10 to-indigo-500/10 border border-gray-850 flex items-center justify-center shadow-[inset_0_1px_1px_rgba(255,255,255,0.02)]">
                <UserIcon className="h-4 w-4 text-[#10B981]" />
              </div>
              <div className="text-left">
                <p className="text-xs font-bold text-gray-200 font-mono truncate max-w-[110px]">{user.username}</p>
                <p className="text-[10px] text-amber-500 font-mono tracking-wider font-bold uppercase">{user.stats.rank}</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs font-black font-mono text-[#10B981]">{user.stats.points} pt</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main Page Area */}
      <main className="flex-1 flex flex-col min-h-0 relative z-10 pl-0 lg:pl-0">
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
            {activePage === 'stats' && (
              <StatsPage user={user!} />
            )}
            {activePage === 'profile' && (
              <Profile user={user!} />
            )}
            {activePage === 'settings' && (
              <Settings 
                user={user!} 
                onPreferencesUpdated={handlePreferencesUpdated} 
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
