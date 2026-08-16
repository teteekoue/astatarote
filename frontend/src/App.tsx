import React, { useState, useEffect } from "react";
import {
  Gamepad2,
  BarChart3,
  Award,
  Settings as SettingsIcon,
  Menu,
  X,
  LogOut,
  ShieldCheck,
} from "lucide-react";
import Dashboard from "./components/Dashboard/Dashboard";
import CreateGame from "./components/Dashboard/CreateGame";
import GameInterface from "./components/Game/GameInterface";
import Settings from "./components/Settings/Settings";
import Profile from "./components/Profile/Profile";
import StatsPage from "./components/Dashboard/StatsPage";
import { api } from "./lib/api";
import {
  getStoredUser,
  setStoredUser,
  setToken,
  clearSession,
  isAuthenticated,
  UserType,
} from "./lib/auth";

export type { UserType };

type Page = "dashboard" | "create-game" | "stats" | "profile" | "settings" | "game";

export default function App() {
  const [user, setUser] = useState<UserType | null>(getStoredUser());
  const [activePage, setActivePage] = useState<Page>("dashboard");
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const bootstrap = async () => {
    try {
      setLoading(true);
      setError(null);
      if (!isAuthenticated()) {
        // Private instance: no login page, auto-authenticate on landing.
        const data = await api.post<{
          access_token: string;
          user: UserType;
        }>("/api/auth/auto");
        setToken(data.access_token);
        setStoredUser(data.user);
        setUser(data.user);
      } else {
        const data = await api.get<UserType>("/api/users/me");
        setStoredUser(data);
        setUser(data);
      }
    } catch (err) {
      clearSession();
      setUser(null);
      setError(err instanceof Error ? err.message : "Erreur de connexion au serveur.");
    } finally {
      setLoading(false);
    }
  };

  const fetchUser = async () => {
    try {
      setLoading(true);
      const data = await api.get<UserType>("/api/users/me");
      setStoredUser(data);
      setUser(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && (err as { status?: number }).status === 401) {
        clearSession();
        setUser(null);
      } else {
        setError(err instanceof Error ? err.message : "Erreur de connexion au serveur.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const onUnauthorized = () => {
      clearSession();
      bootstrap();
    };
    window.addEventListener("astarote:unauthorized", onUnauthorized);
    return () => window.removeEventListener("astarote:unauthorized", onUnauthorized);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = () => {
    clearSession();
    setSelectedGameId(null);
    bootstrap();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-base">
        <div className="text-center space-y-4">
          <div className="inline-block h-10 w-10 border-2 border-asta-green border-t-transparent rounded-full animate-spin"></div>
          <p className="font-mono text-xs text-gray-500 uppercase tracking-widest">
            Initialisation du laboratoire...
          </p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-base">
        <div className="panel p-8 max-w-md text-center">
          <p className="font-mono text-red-400 font-bold mb-2">ERRUER DE DÉMARRAGE</p>
          <p className="text-sm text-gray-400 mb-4">{error || "Impossible de charger le compte admin."}</p>
          <button onClick={bootstrap} className="btn-primary w-full">
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  if (activePage === "game" && selectedGameId) {
    return (
      <div className="h-screen flex flex-col bg-ink-base overflow-hidden">
        <GameInterface
          gameId={selectedGameId}
          user={user}
          onBackToDashboard={() => {
            fetchUser();
            setActivePage("dashboard");
          }}
        />
      </div>
    );
  }

  const navItems = [
    { id: "dashboard" as Page, label: "Mes Laboratoires", icon: Gamepad2 },
    { id: "stats" as Page, label: "Statistiques", icon: BarChart3 },
    { id: "profile" as Page, label: "Profil & Badges", icon: Award },
    { id: "settings" as Page, label: "Paramètres", icon: SettingsIcon },
  ];

  return (
    <div className="min-h-screen flex bg-ink-base text-gray-100 overflow-hidden relative">
      <div className="absolute inset-0 bg-grid-cyber bg-grid-size opacity-50 pointer-events-none"></div>
      <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] bg-asta-green/6 rounded-full blur-3xl pointer-events-none"></div>

      {/* Mobile hamburger */}
      <div className="lg:hidden absolute top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2.5 bg-ink-panel/90 border border-ink-line rounded-xl text-gray-300 hover:text-white"
        >
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 w-64 bg-ink-panel/90 backdrop-blur-2xl border-r border-ink-line flex flex-col justify-between shrink-0 z-40 transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div>
          {/* Brand */}
          <div className="p-6 border-b border-ink-line/70 flex items-center gap-3">
            <div className="p-1.5 bg-asta-green/10 rounded-xl border border-asta-green/25">
              <ShieldCheck className="h-6 w-6 text-asta-green" />
            </div>
            <div>
              <h1 className="font-display text-sm font-extrabold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-asta-green to-emerald-300">
                ASTATAROTE
              </h1>
              <p className="text-[8px] text-gray-500 font-mono tracking-widest uppercase">Cyber Lab v2</p>
            </div>
          </div>

          {/* Nav */}
          <nav className="px-4 py-6 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id || (item.id === "dashboard" && activePage === "create-game");
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActivePage(item.id);
                    setSelectedGameId(null);
                    setSidebarOpen(false);
                  }}
                  className={`w-full px-4 py-3 rounded-xl flex items-center gap-4 font-mono text-xs tracking-wider transition-all duration-300 group relative ${
                    isActive
                      ? "bg-asta-green/10 text-asta-green border border-asta-green/25"
                      : "text-gray-400 hover:text-gray-200 hover:bg-ink-deep/40 border border-transparent"
                  }`}
                >
                  {isActive && (
                    <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-asta-green rounded-r-full shadow-glow-sm"></div>
                  )}
                  <Icon className={`h-4.5 w-4.5 ${isActive ? "text-asta-green" : "text-gray-500"}`} />
                  <span className="font-bold">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* User footer */}
        <div className="p-4 border-t border-ink-line/70 bg-ink-deep/30">
          <div className="flex items-center justify-between px-1 pb-3">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-asta-green/15 to-asta-violet/15 border border-ink-line flex items-center justify-center">
                <span className="font-mono text-sm font-bold text-asta-green uppercase">
                  {user.username.slice(0, 2)}
                </span>
              </div>
              <div>
                <p className="text-xs font-bold text-gray-200 font-mono truncate max-w-[110px]">{user.username}</p>
                <p className="text-[10px] text-asta-amber font-mono font-bold uppercase tracking-wider">
                  {user.stats.rank || "Novice"}
                </p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs font-black font-mono text-asta-green">{user.stats.points || 0} pts</span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full py-2 rounded-lg flex items-center justify-center gap-2 text-[10px] font-mono font-bold text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all"
          >
            <LogOut className="h-3.5 w-3.5" />
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Main area */}
      <main className="flex-1 flex flex-col min-h-0 relative z-10 overflow-hidden">
        {error ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6">
            <div className="panel p-8 max-w-md text-center">
              <p className="font-mono text-red-400 font-bold mb-2">ERREUR DE CHARGEMENT</p>
              <p className="text-sm text-gray-400 mb-4">{error}</p>
              <button onClick={fetchUser} className="btn-primary w-full">
                Tenter une Reconnexion
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            {activePage === "dashboard" && (
              <Dashboard
                user={user}
                onCreateGameClick={() => setActivePage("create-game")}
                onPlayGame={(gameId) => {
                  setSelectedGameId(gameId);
                  setActivePage("game");
                }}
              />
            )}
            {activePage === "create-game" && (
              <CreateGame
                user={user}
                onGameCreated={(gameId) => {
                  setSelectedGameId(gameId);
                  fetchUser();
                  setActivePage("game");
                }}
                onCancel={() => setActivePage("dashboard")}
              />
            )}
            {activePage === "stats" && <StatsPage user={user} />}
            {activePage === "profile" && <Profile user={user} onUserUpdate={setUser} />}
            {activePage === "settings" && <Settings user={user} onUserUpdate={setUser} />}
          </div>
        )}
      </main>
    </div>
  );
}
