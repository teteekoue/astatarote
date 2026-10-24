import React, { useState, useEffect, useCallback } from "react";
import {
  LayoutDashboard,
  Compass,
  BarChart3,
  Award,
  Settings as SettingsIcon,
  Menu,
  X,
  LogOut,
  ShieldCheck,
  Gamepad2,
} from "lucide-react";
import Landing from "./components/Landing";
import AuthPage from "./components/Auth/AuthPage";
import Dashboard from "./components/Dashboard/Dashboard";
import Catalog from "./components/Dashboard/Catalog";
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

type Page = "dashboard" | "catalog" | "stats" | "profile" | "settings" | "game";

export default function App() {
  const [user, setUser] = useState<UserType | null>(getStoredUser());
  const [view, setView] = useState<"landing" | "auth" | "app">(
    isAuthenticated() ? "app" : "landing"
  );
  const [activePage, setActivePage] = useState<Page>("dashboard");
  const [selectedGame, setSelectedGame] = useState<{ id: number; name: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(isAuthenticated());
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /* ------------------------- Session bootstrap ------------------------- */
  const bootstrap = useCallback(async () => {
    if (!isAuthenticated()) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const data = await api.get<UserType>("/api/users/me");
      setStoredUser(data);
      setUser(data);
      setView("app");
    } catch {
      clearSession();
      setUser(null);
      setView("landing");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const onUnauthorized = () => {
      clearSession();
      setUser(null);
      setSelectedGame(null);
      setActivePage("dashboard");
      setView("landing");
    };
    window.addEventListener("astarote:unauthorized", onUnauthorized);
    return () => window.removeEventListener("astarote:unauthorized", onUnauthorized);
  }, []);

  const handleLogout = () => {
    clearSession();
    setUser(null);
    setSelectedGame(null);
    setActivePage("dashboard");
    setView("landing");
  };

  const enterApp = () => {
    if (isAuthenticated()) {
      setView("app");
      bootstrap();
    } else {
      setView("auth");
    }
  };

  const playGame = (gameId: number, gameName: string) => {
    setSelectedGame({ id: gameId, name: gameName });
    setActivePage("game");
  };

  /* ------------------------------ Screens ------------------------------ */

  if (loading && view === "app") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="mt-4 font-mono text-[11px] uppercase tracking-widest text-muted">
            Chargement de votre espace…
          </p>
        </div>
      </div>
    );
  }

  if (view === "landing") {
    return <Landing onEnter={enterApp} />;
  }

  if (view === "auth") {
    return (
      <AuthPage
        onBack={() => setView("landing")}
        onSuccess={(u) => {
          setUser(u);
          setView("app");
          setActivePage("dashboard");
        }}
      />
    );
  }

  if (!user) {
    return <Landing onEnter={enterApp} />;
  }

  if (activePage === "game" && selectedGame) {
    return (
      <div className="h-screen overflow-hidden bg-bg">
        <GameInterface
          gameId={selectedGame.id}
          gameName={selectedGame.name}
          user={user}
          onBackToDashboard={() => {
            bootstrap();
            setActivePage("dashboard");
          }}
        />
      </div>
    );
  }

  const navItems = [
    { id: "dashboard" as Page, label: "Mes parcours", icon: LayoutDashboard },
    { id: "catalog" as Page, label: "Catalogue", icon: Compass },
    { id: "stats" as Page, label: "Progression", icon: BarChart3 },
    { id: "profile" as Page, label: "Profil", icon: Award },
    { id: "settings" as Page, label: "Paramètres", icon: SettingsIcon },
  ];

  return (
    <div className="flex min-h-screen bg-bg text-fg">
      {/* Mobile hamburger */}
      <div className="fixed left-4 top-4 z-50 lg:hidden">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="rounded-xl border border-border bg-surface/95 p-2.5 text-muted backdrop-blur transition-colors hover:text-fg"
          aria-label="Menu"
        >
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col justify-between border-r border-border bg-surface/95 backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div>
          {/* Brand */}
          <div className="flex items-center gap-3 border-b border-border/70 p-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-primary/30 bg-primary/10">
              <ShieldCheck className="h-5 w-5 text-primary" />
            </div>
            <div className="leading-tight">
              <p className="text-[14px] font-extrabold tracking-tight">Astatarote</p>
              <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted">
                Cyber Lab · SaaS
              </p>
            </div>
          </div>

          {/* Nav */}
          <nav className="space-y-1 p-3" aria-label="Navigation principale">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActivePage(item.id);
                    setSelectedGame(null);
                    setSidebarOpen(false);
                  }}
                  className={`group relative flex w-full cursor-pointer items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-primary/12 text-primary"
                      : "text-muted hover:bg-surface-2 hover:text-fg"
                  }`}
                >
                  {isActive && (
                    <span className="absolute left-0 top-1/4 bottom-1/4 w-1 rounded-r-full bg-primary" />
                  )}
                  <Icon className={`h-[18px] w-[18px] ${isActive ? "text-primary" : ""}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User footer */}
        <div className="border-t border-border/70 p-4">
          <div className="mb-3 flex items-center gap-3 px-1">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-border bg-gradient-to-br from-primary/20 to-accent/10">
              <span className="font-mono text-[12px] font-bold text-primary">
                {user.username.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold">{user.username}</p>
              <p className="font-mono text-[10px] uppercase tracking-wider text-accent">
                {user.stats?.rank || "Novice"} · {user.stats?.points || 0} pts
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg py-2 text-[12px] font-semibold text-muted transition-all duration-200 hover:bg-danger/10 hover:text-danger"
          >
            <LogOut className="h-3.5 w-3.5" />
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <main className="min-h-screen flex-1 overflow-x-hidden">
        {activePage === "dashboard" && (
          <Dashboard user={user} onPlayGame={playGame} onBrowseCatalog={() => setActivePage("catalog")} />
        )}
        {activePage === "catalog" && <Catalog onPlayGame={playGame} />}
        {activePage === "stats" && <StatsPage user={user} />}
        {activePage === "profile" && (
          <Profile
            user={user}
            onUserUpdate={(u) => {
              setUser(u);
              setStoredUser(u);
            }}
          />
        )}
        {activePage === "settings" && (
          <Settings
            user={user}
            onUserUpdate={(u) => {
              setUser(u);
              setStoredUser(u);
            }}
          />
        )}
      </main>
    </div>
  );
}
