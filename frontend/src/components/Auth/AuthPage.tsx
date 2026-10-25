import React, { useState } from "react";
import {
  ShieldCheck,
  LogIn,
  UserPlus,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import { api } from "../../lib/api";
import { setToken, setStoredUser, UserType } from "../../lib/auth";

interface AuthPageProps {
  onSuccess: (user: UserType) => void;
  onBack: () => void;
}

export default function AuthPage({ onSuccess, onBack }: AuthPageProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await api.post<UserType>("/api/auth/register", {
          username: username.trim(),
          email: email.trim(),
          password,
        });
      }
      const data = await api.post<{ access_token: string }>("/api/auth/login", {
        username: username.trim(),
        password,
      });
      setToken(data.access_token);
      const user = await api.get<UserType>("/api/users/me");
      setStoredUser(user);
      onSuccess(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-bg px-4 py-10">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(500px circle at 50% 0%, rgba(99,102,241,0.14), transparent 65%)",
        }}
      />
      <div className="relative w-full max-w-md animate-fade-up">
        <button onClick={onBack} className="btn-ghost mb-6 -ml-2">
          <ArrowLeft className="h-4 w-4" />
          Retour
        </button>

        <div className="card p-8">
          <div className="mb-8 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10">
              <ShieldCheck className="h-6 w-6 text-primary" />
            </div>
            <h1 className="mt-4 text-xl font-extrabold tracking-tight">
              {mode === "login" ? "Content de vous revoir" : "Créer un compte"}
            </h1>
            <p className="mt-1.5 text-sm text-muted">
              {mode === "login"
                ? "Reprenez votre progression là où vous l'avez laissée."
                : "30 secondes pour accéder à votre laboratoire Linux."}
            </p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="username" className="label">
                Nom d'utilisateur
              </label>
              <input
                id="username"
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ex. ada_lovelace"
                autoComplete="username"
                required
                minLength={2}
              />
            </div>

            {mode === "register" && (
              <div>
                <label htmlFor="email" className="label">
                  Adresse e-mail
                </label>
                <input
                  id="email"
                  type="email"
                  className="input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="vous@exemple.com"
                  autoComplete="email"
                  required
                />
              </div>
            )}

            <div>
              <label htmlFor="password" className="label">
                Mot de passe
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  className="input pr-11"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "register" ? "6 caractères minimum" : "••••••••"}
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  required
                  minLength={mode === "register" ? 6 : 1}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer text-muted transition-colors hover:text-fg"
                  aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div
                role="alert"
                className="flex items-start gap-2.5 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-[13px] text-danger"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-3">
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : mode === "login" ? (
                <>
                  <LogIn className="h-4 w-4" /> Se connecter
                </>
              ) : (
                <>
                  <UserPlus className="h-4 w-4" /> Créer mon compte
                </>
              )}
            </button>
          </form>

          <div className="mt-6 border-t border-border pt-5 text-center text-sm text-muted">
            {mode === "login" ? (
              <>
                Pas encore de compte ?{" "}
                <button
                  onClick={() => {
                    setMode("register");
                    setError(null);
                  }}
                  className="cursor-pointer font-semibold text-primary transition-colors hover:text-primary-hover"
                >
                  Créez-en un gratuitement
                </button>
              </>
            ) : (
              <>
                Déjà inscrit ?{" "}
                <button
                  onClick={() => {
                    setMode("login");
                    setError(null);
                  }}
                  className="cursor-pointer font-semibold text-primary transition-colors hover:text-primary-hover"
                >
                  Connectez-vous
                </button>
              </>
            )}
          </div>
        </div>

        <p className="mt-6 text-center text-[12px] text-muted">
          En créant un compte, vous rejoignez une plateforme d'apprentissage éthique :
          tout se déroule dans un environnement simulé isolé.
        </p>
      </div>
    </div>
  );
}
