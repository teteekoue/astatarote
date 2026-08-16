import React, { useState } from "react";
import { Settings2, Cpu, Terminal, Palette, CheckCircle2, AlertTriangle, KeyRound } from "lucide-react";
import { UserType } from "../../App";
import { api } from "../../lib/api";

interface SettingsProps {
  user: UserType;
  onUserUpdate: (u: UserType) => void;
}

const PROVIDERS = [
  { id: "fallback", label: "Moteur local", desc: "Scénarios intégrés, aucune clé requise" },
  { id: "nvidia", label: "NVIDIA NIM", desc: "IA accélérée GPU via API" },
  { id: "groq", label: "Groq", desc: "Inférence ultra-rapide" },
  { id: "fireworks", label: "Fireworks AI", desc: "Modèles open-source en production" },
  { id: "cohere", label: "Cohere", desc: "Génération d'entreprise" },
  { id: "together", label: "Together AI", desc: "Clusters de modèles ouverts" },
];

const THEMES = [
  { id: "dark", label: "Noir opérateur", swatch: "bg-ink-base" },
  { id: "green", label: "Vert phosphore", swatch: "bg-asta-green" },
  { id: "violet", label: "Violet néon", swatch: "bg-asta-violet" },
];

const TERMINAL_TYPES = [
  {
    id: "reel",
    label: "Terminal réel",
    desc: "Vrai bash dans un PTY sur une sandbox réelle sous /tmp/astarote",
    icon: Terminal,
  },
  {
    id: "simulation",
    label: "Simulation",
    desc: "Interpréteur simulé (léger, pour démo)",
    icon: Cpu,
  },
];

export default function Settings({ user, onUserUpdate }: SettingsProps) {
  const [provider, setProvider] = useState(user.preferences?.provider_ia || "fallback");
  const [apiKey, setApiKey] = useState("");
  const [theme, setTheme] = useState(user.preferences?.theme || "dark");
  const [fontSize, setFontSize] = useState(user.preferences?.font_size || 14);
  const [terminalType, setTerminalType] = useState(user.preferences?.terminal_type || "reel");
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const storedKey = user.preferences?.api_key;
  const hasStoredKey = Boolean(storedKey);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const updated = await api.put<UserType>("/api/users/me/preferences", {
        provider_ia: provider,
        api_key: apiKey.trim() || undefined,
        theme,
        font_size: fontSize,
        terminal_type: terminalType,
      });
      onUserUpdate(updated);
      setApiKey("");
      setMessage({ type: "success", text: "Préférences enregistrées. Sandbox et terminal synchronisés." });
    } catch (err) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Erreur lors de l'enregistrement." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-3xl mx-auto w-full">
      <div className="flex items-center gap-3 border-b border-ink-line/70 pb-4">
        <div className="p-2.5 bg-asta-green/10 rounded-xl border border-asta-green/20">
          <Settings2 className="h-5 w-5 text-asta-green" />
        </div>
        <div>
          <h2 className="text-xl font-display font-bold text-white tracking-wide">Paramètres du laboratoire</h2>
          <p className="text-xs text-gray-400">Moteur d'IA, environnement d'exécution et apparence.</p>
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

      <form onSubmit={handleSave} className="space-y-6">
        {/* Moteur IA */}
        <div className="panel p-6 space-y-4 shadow-card">
          <h4 className="section-title">
            <Cpu className="h-4 w-4 text-asta-green" />
            Moteur d'intelligence de l'Architecte
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {PROVIDERS.map((p) => {
              const active = provider === p.id;
              return (
                <button
                  type="button"
                  key={p.id}
                  onClick={() => setProvider(p.id)}
                  className={`text-left p-3.5 rounded-xl border transition-all duration-200 ${
                    active
                      ? "bg-asta-green/10 border-asta-green/40 shadow-glow-sm"
                      : "bg-ink-deep/50 border-ink-line hover:border-ink-hover"
                  }`}
                >
                  <p className={`font-mono text-sm font-bold ${active ? "text-asta-green" : "text-gray-200"}`}>
                    {p.label}
                  </p>
                  <p className="text-[10px] text-gray-500 font-mono mt-1 leading-relaxed">{p.desc}</p>
                </button>
              );
            })}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono text-gray-400 flex items-center gap-1.5">
              <KeyRound className="h-3 w-3" />
              Clé API du fournisseur
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={hasStoredKey ? `Clé actuelle : ${storedKey}` : "Laisse vide pour utiliser le moteur local"}
              className="input-field font-mono"
            />
            <p className="text-[10px] text-gray-500 font-mono">
              {hasStoredKey
                ? "Ta clé actuelle est conservée si tu laisses le champ vide. Elle n'est jamais renvoyée en clair."
                : "La clé est stockée de façon sécurisée et jamais exposée dans les réponses."}
            </p>
          </div>
        </div>

        {/* Environnement d'exécution */}
        <div className="panel p-6 space-y-4 shadow-card">
          <h4 className="section-title">
            <Terminal className="h-4 w-4 text-asta-green" />
            Environnement d'exécution
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {TERMINAL_TYPES.map((t) => {
              const Icon = t.icon;
              const active = terminalType === t.id;
              return (
                <button
                  type="button"
                  key={t.id}
                  onClick={() => setTerminalType(t.id)}
                  className={`text-left p-4 rounded-xl border transition-all duration-200 flex items-start gap-3 ${
                    active
                      ? "bg-asta-green/10 border-asta-green/40 shadow-glow-sm"
                      : "bg-ink-deep/50 border-ink-line hover:border-ink-hover"
                  }`}
                >
                  <Icon className={`h-5 w-5 mt-0.5 ${active ? "text-asta-green" : "text-gray-500"}`} />
                  <span>
                    <p className={`font-mono text-sm font-bold ${active ? "text-asta-green" : "text-gray-200"}`}>
                      {t.label}
                    </p>
                    <p className="text-[10px] text-gray-500 font-mono mt-1 leading-relaxed">{t.desc}</p>
                  </span>
                </button>
              );
            })}
          </div>
          <p className="text-[10px] text-gray-500 font-mono leading-relaxed">
            Le mode « Terminal réel » matérialise une arborescence de fichiers sur le disque ({`/tmp/astarote`}) et
            exécute un vrai bash dans un pseudo-terminal. Chaque défi reçoit sa propre sandbox isolée.
          </p>
        </div>

        {/* Apparence */}
        <div className="panel p-6 space-y-4 shadow-card">
          <h4 className="section-title">
            <Palette className="h-4 w-4 text-asta-green" />
            Apparence
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-gray-400">Thème</label>
              <div className="flex gap-3">
                {THEMES.map((t) => (
                  <button
                    type="button"
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-xl border font-mono text-xs transition-all duration-200 ${
                      theme === t.id
                        ? "border-asta-green/50 text-asta-green bg-asta-green/10"
                        : "border-ink-line text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    <span className={`h-3 w-3 rounded-full ${t.swatch} border border-ink-line`} />
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-gray-400">Taille de police du terminal ({fontSize}px)</label>
              <input
                type="range"
                min={11}
                max={18}
                value={fontSize}
                onChange={(e) => setFontSize(Number(e.target.value))}
                className="w-full accent-[#22c55e]"
              />
            </div>
          </div>
        </div>

        <button type="submit" disabled={saving} className="btn-primary w-full !py-3">
          {saving ? "Synchronisation..." : "Enregistrer les paramètres"}
        </button>
      </form>
    </div>
  );
}
