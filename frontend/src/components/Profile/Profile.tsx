import React, { useState } from "react";
import { UserRound, Camera, ShieldAlert, CheckCircle2, AlertTriangle } from "lucide-react";
import { UserType } from "../../App";
import { api } from "../../lib/api";

interface ProfileProps {
  user: UserType;
  onUserUpdate: (u: UserType) => void;
}

export default function Profile({ user, onUserUpdate }: ProfileProps) {
  const [username, setUsername] = useState(user.username);
  const [email, setEmail] = useState(user.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const handleProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;
    setSaving(true);
    setMessage(null);
    try {
      const updated = await api.put<UserType>("/api/users/me", { username: username.trim(), email: email.trim() || undefined });
      onUserUpdate(updated);
      setMessage({ type: "success", text: "Profil mis à jour avec succès." });
    } catch (err) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Erreur lors de la mise à jour." });
    } finally {
      setSaving(false);
    }
  };

  const handlePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) {
      setMessage({ type: "error", text: "Renseigne le mot de passe actuel et le nouveau mot de passe." });
      return;
    }
    if (newPassword.length < 8) {
      setMessage({ type: "error", text: "Le nouveau mot de passe doit contenir au moins 8 caractères." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setMessage({ type: "error", text: "La confirmation du nouveau mot de passe ne correspond pas." });
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      const updated = await api.put<UserType>("/api/users/me/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      onUserUpdate(updated);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage({ type: "success", text: "Mot de passe modifié avec succès." });
    } catch (err) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Erreur lors du changement de mot de passe." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-3xl mx-auto w-full">
      <div className="flex items-center gap-3 border-b border-ink-line/70 pb-4">
        <div className="p-2.5 bg-asta-green/10 rounded-xl border border-asta-green/20">
          <UserRound className="h-5 w-5 text-asta-green" />
        </div>
        <div>
          <h2 className="text-xl font-display font-bold text-white tracking-wide">Profil de l'agent</h2>
          <p className="text-xs text-gray-400">Identité, coordonnées et sécurité du compte.</p>
        </div>
      </div>

      {message && (
        <div
          className={`p-3.5 rounded-xl border flex items-center gap-2.5 text-xs font-mono ${
            message.type === "success"
              ? "bg-asta-green/10 border-asta-green/20 text-asta-green"
              : "bg-red-500/10 border-red-500/20 text-red-400"
          }`}
        >
          {message.type === "success" ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertTriangle className="h-4 w-4 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Avatar */}
      <div className="panel p-6 flex items-center gap-6 shadow-card">
        <div className="relative">
          <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-asta-green to-asta-violet flex items-center justify-center shadow-glow-sm">
            <span className="text-2xl font-black font-mono text-white">
              {user.username.charAt(0).toUpperCase()}
            </span>
          </div>
          <button className="absolute -bottom-1.5 -right-1.5 p-1.5 bg-ink-deep border border-ink-line rounded-lg text-gray-400 hover:text-asta-green transition">
            <Camera className="h-3.5 w-3.5" />
          </button>
        </div>
        <div>
          <h3 className="text-lg font-mono font-bold text-white">{user.username}</h3>
          <p className="text-xs text-gray-400 font-mono">
            Grade : <span className="text-asta-green font-bold">{user.stats.rank || "Novice"}</span> ·{" "}
            {user.stats.points || 0} points
          </p>
        </div>
      </div>

      {/* Identité */}
      <form onSubmit={handleProfile} className="panel p-6 space-y-5 shadow-card">
        <h4 className="section-title">
          <UserRound className="h-4 w-4 text-asta-green" />
          Identité
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-mono text-gray-400">Nom d'utilisateur *</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} className="input-field" />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-mono text-gray-400">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="agent@astatarote.dev"
              className="input-field"
            />
          </div>
        </div>
        <button type="submit" disabled={saving} className="btn-primary">
          {saving ? "Enregistrement..." : "Enregistrer le profil"}
        </button>
      </form>

      {/* Sécurité */}
      <form onSubmit={handlePassword} className="panel p-6 space-y-5 shadow-card border-red-500/10">
        <h4 className="section-title">
          <ShieldAlert className="h-4 w-4 text-asta-amber" />
          Sécurité du compte
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-mono text-gray-400">Mot de passe actuel *</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              className="input-field"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-mono text-gray-400">Nouveau mot de passe *</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="8 caractères min."
              className="input-field"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-mono text-gray-400">Confirmation *</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Répète le nouveau"
              className="input-field"
            />
          </div>
        </div>
        <button type="submit" disabled={saving} className="btn-primary !bg-asta-amber/90 hover:!bg-asta-amber text-ink-deep">
          Modifier le mot de passe
        </button>
      </form>
    </div>
  );
}
