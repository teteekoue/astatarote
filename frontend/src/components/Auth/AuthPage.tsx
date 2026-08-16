import React, { useState } from "react";
import { ShieldCheck, Lock, User, Mail, ArrowRight, TerminalSquare, Sparkles, AlertTriangle } from "lucide-react";
import { api } from "../../lib/api";
import { setToken, setStoredUser, UserType } from "../../lib/auth";

interface AuthPageProps {
  onAuthenticated: (user: UserType) => void;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

export default function AuthPage({ onAuthenticated }: AuthPageProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "login") {
        const { access_token } = await api.post<LoginResponse>("/api/auth/login", {
          username,
          password,
        });
        setToken(access_token);
        const user = await api.get<UserType>("/api/users/me");
        setStoredUser(user);
        onAuthenticated(user);
      } else {
        await api.post<UserType>("/api/auth/register", {
          username,
          email,
          password,
        });
        const { access_token } = await api.post<LoginResponse>("/api/auth/login", {
          username,
          password,
        });
        setToken(access_token);
        const user = await api.get<UserType>("/api/users/me");
        setStoredUser(user);
        onAuthenticated(user);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de connexion.");
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const { access_token } = await api.post<LoginResponse>("/api/auth/login", {
        username: "admin",
        password: "admin123",
      });
      setToken(access_token);
      const user = await api.get<UserType>("/api/users/me");
      setStoredUser(user);
      onAuthenticated(user);
    } catch {
      setError("Compte de démonstration indisponible. Créez un compte.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-ink-base relative overflow-hidden flex">
      {/* Background décor */}
      <div className="absolute inset-0 bg-grid-cyber bg-grid-size opacity-60 pointer-events-none"></div>
      <div className="absolute top-[-10%] left-[-5%] w-[600px] h-[600px] bg-asta-green/8 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-[-15%] right-[-5%] w-[600px] h-[600px] bg-asta-violet/8 rounded-full blur-3xl pointer-events-none"></div>

      {/* Left branding panel */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-14 relative">
        <div className="relative z-10 space-y-10">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-xl bg-asta-green/15 border border-asta-green/40 flex items-center justify-center">
              <ShieldCheck className="h-6 w-6 text-asta-green" />
            </div>
            <div>
              <h1 className="font-display font-extrabold tracking-widest text-lg text-white">
                ASTATAROTE
              </h1>
              <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-gray-500">
                Ethical Cyber Lab
              </p>
            </div>
          </div>

          <div className="space-y-5">
            <h2 className="font-display text-4xl font-extrabold leading-tight text-white">
              Entraîne-toi sur un{" "}
              <span className="text-asta-green text-glow">vrai terminal Linux</span>,
              piloté par l'IA.
            </h2>
            <p className="text-gray-400 leading-relaxed max-w-md">
              Des scénarios de cybersécurité et d'administration système générés
              dynamiquement, une sandbox réelle à chaque défi, et un coéquipier IA
              pédagogique qui t'accompagne sans jamais te donner la solution brute.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            {[
              { icon: TerminalSquare, label: "Shell réel bash + pty" },
              { icon: Sparkles, label: "Scénarios IA adaptatifs" },
              { icon: ShieldCheck, label: "Gamification & grades" },
            ].map(({ icon: Icon, label }, i) => (
              <div
                key={i}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-ink-panel/70 border border-ink-line text-xs font-mono text-gray-300"
              >
                <Icon className="h-4 w-4 text-asta-green" />
                {label}
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 flex items-center gap-2 font-mono text-[10px] text-gray-600">
          <span className="h-2 w-2 rounded-full bg-asta-green animate-pulse-glow"></span>
          SANDBOX_READY · v2.0
        </div>
      </div>

      {/* Right auth form panel */}
      <div className="flex-1 flex items-center justify-center p-6 relative z-10">
        <div className="w-full max-w-md animate-fade-in">
          <div className="lg:hidden flex items-center gap-2.5 justify-center mb-8">
            <div className="h-9 w-9 rounded-lg bg-asta-green/15 border border-asta-green/40 flex items-center justify-center">
              <ShieldCheck className="h-5 w-5 text-asta-green" />
            </div>
            <span className="font-display font-extrabold tracking-widest text-white">ASTATAROTE</span>
          </div>

          <div className="panel p-8 shadow-card">
            {/* Mode switch */}
            <div className="flex bg-ink-deep/70 border border-ink-line rounded-xl p-1 mb-8">
              <button
                onClick={() => {
                  setMode("login");
                  setError(null);
                }}
                className={`flex-1 py-2.5 rounded-lg font-mono text-xs font-bold transition-all duration-200 ${
                  mode === "login"
                    ? "bg-asta-green/15 text-asta-green border border-asta-green/30"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                Connexion
              </button>
              <button
                onClick={() => {
                  setMode("register");
                  setError(null);
                }}
                className={`flex-1 py-2.5 rounded-lg font-mono text-xs font-bold transition-all duration-200 ${
                  mode === "register"
                    ? "bg-asta-green/15 text-asta-green border border-asta-green/30"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                Créer un compte
              </button>
            </div>

            <h3 className="font-display text-xl font-bold text-white mb-1.5">
              {mode === "login" ? "Accès au laboratoire" : "Débuter le parcours"}
            </h3>
            <p className="text-sm text-gray-500 mb-6">
              {mode === "login"
                ? "Renseigne tes identifiants pour accéder à tes laboratoires."
                : "Crée ton identité d'agent pour générer tes premiers défis adaptatifs."}
            </p>

            {error && (
              <div className="mb-5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/25 flex items-start gap-2.5 text-xs text-red-400">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Nom d'utilisateur</label>
                <div className="relative">
                  <User className="h-4 w-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="agent42"
                    className="input-field pl-10"
                  />
                </div>
              </div>

              {mode === "register" && (
                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-gray-400">Adresse email</label>
                  <div className="relative">
                    <Mail className="h-4 w-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="agent@astarote.io"
                      className="input-field pl-10"
                    />
                  </div>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Mot de passe</label>
                <div className="relative">
                  <Lock className="h-4 w-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={mode === "register" ? "6 caractères minimum" : "••••••••"}
                    className="input-field pl-10"
                  />
                </div>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full !py-3">
                {loading ? (
                  <span className="inline-block h-4 w-4 border-2 border-black border-t-transparent rounded-full animate-spin"></span>
                ) : (
                  <>
                    {mode === "login" ? "Se connecter" : "Créer mon compte"}
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-ink-line">
              <button
                onClick={quickLogin}
                disabled={loading}
                className="w-full text-center text-xs font-mono text-gray-500 hover:text-asta-green transition"
              >
                Connexion démo (admin / admin123)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
