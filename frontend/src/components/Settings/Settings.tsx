import React, { useState } from "react";
import { Settings as SettingsIcon, Save, CheckCircle2, AlertCircle, Loader2, Bot, Type } from "lucide-react";
import { api } from "../../lib/api";
import { UserType } from "../../App";

interface SettingsProps {
  user: UserType;
  onUserUpdate: (user: UserType) => void;
}

const PROVIDERS = [
  { id: "fallback", label: "Astatarote (hors-ligne)", hint: "Assistante intégrée, sans clé API" },
  { id: "groq", label: "Groq", hint: "llama-3.3-70b-versatile" },
  { id: "nvidia", label: "NVIDIA NIM", hint: "meta/llama-3.1-70b-instruct" },
  { id: "fireworks", label: "Fireworks AI", hint: "deepseek-v4-flash" },
  { id: "cohere", label: "Cohere", hint: "command-r-plus" },
  { id: "together", label: "Together AI", hint: "Llama-3-70b" },
];

export default function Settings({ user, onUserUpdate }: SettingsProps) {
  const prefs = user.preferences || { provider_ia: "fallback", api_key: "", theme: "dark", font_size: 14 };

  const [provider, setProvider] = useState(prefs.provider_ia || "fallback");
  const [apiKey, setApiKey] = useState("");
  const [fontSize, setFontSize] = useState(prefs.font_size || 14);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [saveStatus, setSaveStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [pwdStatus, setPwdStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [savingPwd, setSavingPwd] = useState(false);

  const savePrefs = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPrefs(true);
    setSaveStatus(null);
    try {
      const updated = await api.put<UserType>("/api/users/me/preferences", {
        provider_ia: provider,
        api_key: apiKey || undefined,
        theme: "dark",
        font_size: fontSize,
      });
      onUserUpdate(updated);
      setApiKey("");
      setSaveStatus({ ok: true, text: "Préférences enregistrées." });
    } catch (err) {
      setSaveStatus({ ok: false, text: err instanceof Error ? err.message : "Erreur." });
    } finally {
      setSavingPrefs(false);
    }
  };

  const savePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPwd(true);
    setPwdStatus(null);
    try {
      await api.put("/api/users/me/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwdStatus({ ok: true, text: "Mot de passe modifié." });
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setPwdStatus({ ok: false, text: err instanceof Error ? err.message : "Erreur." });
    } finally {
      setSavingPwd(false);
    }
  };

  const Status = ({ status }: { status: { ok: boolean; text: string } | null }) =>
    status ? (
      <div
        role="status"
        className={`flex items-center gap-2 rounded-xl border px-4 py-2.5 text-[13px] ${
          status.ok
            ? "border-accent/30 bg-accent/10 text-accent"
            : "border-danger/30 bg-danger/10 text-danger"
        }`}
      >
        {status.ok ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertCircle className="h-4 w-4 shrink-0" />}
        {status.text}
      </div>
    ) : null;

  return (
    <div className="mx-auto w-full max-w-2xl space-y-6 p-4 py-8 sm:px-6 lg:py-10">
      <div>
        <p className="section-title">Paramètres</p>
        <h1 className="mt-1.5 text-2xl font-extrabold tracking-tight sm:text-3xl">
          Préférences du compte
        </h1>
      </div>

      {/* Preferences */}
      <form onSubmit={savePrefs} className="card space-y-5 p-6">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-primary" />
          <h2 className="font-bold">Assistante IA (Nemesis)</h2>
        </div>
        <p className="-mt-3 text-[13px] leading-relaxed text-muted">
          Par défaut, Nemesis fonctionne sans aucune clé. Connectez votre propre fournisseur
          LLM pour des réponses générées en direct (vos clés restent sur votre compte).
        </p>

        <div>
          <label htmlFor="s-provider" className="label">
            Fournisseur
          </label>
          <select
            id="s-provider"
            className="input cursor-pointer"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id} className="bg-surface">
                {p.label} — {p.hint}
              </option>
            ))}
          </select>
        </div>

        {provider !== "fallback" && (
          <div>
            <label htmlFor="s-apikey" className="label">
              Clé API
            </label>
            <input
              id="s-apikey"
              type="password"
              className="input"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={
                prefs.api_key ? "Clé enregistrée (laisser vide pour conserver)" : "sk-..."
              }
            />
          </div>
        )}

        <div>
          <label htmlFor="s-fontsize" className="label flex items-center gap-2">
            <Type className="h-3.5 w-3.5 text-primary" />
            Taille de police du terminal : <span className="font-mono text-primary">{fontSize}px</span>
          </label>
          <input
            id="s-fontsize"
            type="range"
            min={12}
            max={18}
            step={1}
            value={fontSize}
            onChange={(e) => setFontSize(Number(e.target.value))}
            className="w-full cursor-pointer accent-[#6366F1]"
          />
        </div>

        <Status status={saveStatus} />

        <button type="submit" disabled={savingPrefs} className="btn-primary">
          {savingPrefs ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Enregistrer les préférences
        </button>
      </form>

      {/* Password */}
      <form onSubmit={savePassword} className="card space-y-5 p-6">
        <div className="flex items-center gap-2">
          <SettingsIcon className="h-4 w-4 text-primary" />
          <h2 className="font-bold">Sécurité du compte</h2>
        </div>

        <div>
          <label htmlFor="s-curpwd" className="label">
            Mot de passe actuel
          </label>
          <input
            id="s-curpwd"
            type="password"
            className="input"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>
        <div>
          <label htmlFor="s-newpwd" className="label">
            Nouveau mot de passe (8 caractères minimum)
          </label>
          <input
            id="s-newpwd"
            type="password"
            className="input"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength={8}
          />
        </div>

        <Status status={pwdStatus} />

        <button type="submit" disabled={savingPwd} className="btn-secondary">
          {savingPwd ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Modifier le mot de passe
        </button>
      </form>
    </div>
  );
}
