import React, { useState } from "react";
import { User, Save, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { api } from "../../lib/api";
import { UserType } from "../../App";

interface ProfileProps {
  user: UserType;
  onUserUpdate: (user: UserType) => void;
}

export default function Profile({ user, onUserUpdate }: ProfileProps) {
  const [username, setUsername] = useState(user.username);
  const [email, setEmail] = useState(user.email);
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      const updated = await api.put<UserType>("/api/users/me", {
        username: username.trim(),
        email: email.trim(),
      });
      onUserUpdate(updated);
      setStatus({ ok: true, text: "Profil mis à jour." });
    } catch (err) {
      setStatus({ ok: false, text: err instanceof Error ? err.message : "Erreur." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-2xl space-y-6 p-4 py-8 sm:px-6 lg:py-10">
      <div>
        <p className="section-title">Profil</p>
        <h1 className="mt-1.5 text-2xl font-extrabold tracking-tight sm:text-3xl">
          Informations personnelles
        </h1>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10">
            <span className="font-mono text-lg font-bold text-primary">
              {user.username.slice(0, 2).toUpperCase()}
            </span>
          </div>
          <div>
            <p className="font-bold">{user.username}</p>
            <p className="text-[13px] text-muted">
              {user.stats?.rank || "Novice"} · {user.stats?.points || 0} pts · membre depuis{" "}
              {new Date(user.created_at).toLocaleDateString("fr-FR")}
            </p>
          </div>
        </div>

        <form onSubmit={save} className="mt-6 space-y-4">
          <div>
            <label htmlFor="p-username" className="label">
              Nom d'utilisateur
            </label>
            <input
              id="p-username"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={2}
              maxLength={50}
            />
          </div>
          <div>
            <label htmlFor="p-email" className="label">
              Adresse e-mail
            </label>
            <input
              id="p-email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {status && (
            <div
              role="status"
              className={`flex items-center gap-2 rounded-xl border px-4 py-2.5 text-[13px] ${
                status.ok
                  ? "border-accent/30 bg-accent/10 text-accent"
                  : "border-danger/30 bg-danger/10 text-danger"
              }`}
            >
              {status.ok ? (
                <CheckCircle2 className="h-4 w-4 shrink-0" />
              ) : (
                <AlertCircle className="h-4 w-4 shrink-0" />
              )}
              {status.text}
            </div>
          )}

          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Enregistrer
          </button>
        </form>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-primary" />
          <h2 className="font-bold">Badges obtenus</h2>
        </div>
        {(user.stats?.badges || []).length === 0 ? (
          <p className="mt-3 text-sm text-muted">
            Aucun badge pour l'instant — terminez un parcours pour débloquer votre première
            spécialisation.
          </p>
        ) : (
          <div className="mt-4 flex flex-wrap gap-2">
            {(user.stats?.badges || []).map((badge) => (
              <span key={badge} className="chip border-accent/40 text-accent">
                {badge}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
