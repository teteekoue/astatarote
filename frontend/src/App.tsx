import React, { useState, useEffect, useCallback } from "react";
import {
  LayoutDashboard,
  Compass,
  BarChart3,
  Menu,
  X,
  ShieldCheck,
  FlaskConical,
  AlertTriangle,
} from "lucide-react";
import Dashboard from "./components/Dashboard/Dashboard";
import Catalog from "./components/Dashboard/Catalog";
import GameInterface from "./components/Game/GameInterface";
import StatsPage from "./components/Dashboard/StatsPage";
import { api, ApiError } from "./lib/api";
import {
  getStoredUser,
  setStoredUser,
  setToken,
  clearSession,
  isAuthenticated,
  UserType,
} from "./lib/auth";

export type { UserType };

type Page = "dashboard" | "catalog" | "stats" | "game";

/**
 * PHASE DE TEST — ACCÈS OUVERT
 * ----------------------------
 * Pas d'écran de connexion ni de gestion de compte : au chargement, la app
 * obtient automatiquement une session sur le compte démo partagé
 * (admin / admin) via POST /api/auth/auto.
 *
 * Pour réactiver le flux SaaS complet plus tard : remettre les vues
 * "landing" / "auth" (components/Landing.tsx et Auth/AuthPage.tsx sont
 * conservés), la nav Profil/Paramètres et l'inscription/connexion.
 */
export default function App() {
  const [user, setUser] = useState<UserType | null>(getStoredUser());
  const [activePage, setActivePage] = useState<Page>("dashboard");
  const [selectedGame, setSelectedGame] = useState<{ id: number; name: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /* ------------------------- Session bootstrap ------------------------- */
  const bootstrap = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (isAuthenticated()) {
        try {
          const data = await api.get<UserType>("/api/users/me");
          setStoredUser(data);
          setUser(data);
          return;
        } catch (err) {
          if (!(err instanceof ApiError && err.status === 401)) throw err;
          clearSession(); // token expiré → nouvelle session auto
        }
      }
      // Accès ouvert : session sur le compte démo partagé (admin/admin)
      const data = await api.post<{ access_token: string; user: UserType }>(
        "/api/auth/auto"
      );
      setToken(data.access_token);
      setStoredUser(data.user);
      setUser(data.user);
    } catch (err) {
      clearSession();
      setUser(null);
      setError(
        err instanceof Error
          ? err.message
          : "Impossible de démarrer une session sur le serveur."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const onUnauthorized = () => {
      // Session expirée en cours de route → renouvellement silencieux.
      bootstrap();
    };
    window.addEventListener("astarote:unauthorized", onUnauthorized);
    return () => window.removeEventListener("astarote:unauthorized", onUnauthorized);
  }, [bootstrap]);

  const playGame = (gameId: number, gameName: string) => {
    setSelectedGame({ id: gameId, name: gameName });
    setActivePage("game");
  };

  /* ------------------------------ Screens ------------------------------ */

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="mt-4 font-mono text-[11px] uppercase tracking-widest text-muted">
            Démarrage du laboratoire…
          </p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg px-4">
        <div className="card max-w-md p-8 text-center">
          <AlertTriangle className="mx-auto h-8 w-8 text-warning" />
          <p className="mt-3 font-mono text-[12px] font-bold uppercase tracking-widest text-warning">
            Serveur injoignable
          </p>
          <p className="mt-2 text-sm leading-relaxed text-muted">{error}</p>
          <button onClick={bootstrap} className="btn-primary mt-6 w-full">
            Réessayer
          </button>
        </div>
      </div>
    );
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
                    <span className="absolute bottom-1/4 left-0 top-1/4 w-1 rounded-r-full bg-primary" />
                  )}
                  <Icon className={`h-[18px] w-[18px] ${isActive ? "text-primary" : ""}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer — session info (open-access test mode) */}
        <div className="border-t border-border/70 p-4">
          <div className="flex items-center gap-3 px-1">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-border bg-gradient-to-br from-primary/20 to-accent/10">
              <span className="font-mono text-[12px] font-bold text-primary">AD</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold">{user.username}</p>
              <p className="font-mono text-[10px] uppercase tracking-wider text-accent">
                {user.stats?.rank || "Novice"} · {user.stats?.points || 0} pts
              </p>
            </div>
          </div>
          <div className="mt-3 flex items-center justify-center gap-1.5 rounded-lg border border-warning/25 bg-warning/8 px-2 py-1.5">
            <FlaskConical className="h-3 w-3 text-warning" />
            <span className="font-mono text-[9.5px] font-semibold uppercase tracking-wider text-warning">
              Mode test · accès ouvert
            </span>
          </div>
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
          <Dashboard
            user={user}
            onPlayGame={playGame}
            onBrowseCatalog={() => setActivePage("catalog")}
          />
        )}
        {activePage === "catalog" && <Catalog onPlayGame={playGame} />}
        {activePage === "stats" && <StatsPage user={user} />}
      </main>
    </div>
  );
}
