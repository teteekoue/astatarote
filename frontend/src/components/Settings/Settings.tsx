import React, { useState } from 'react';
import { Save, Shield, Settings as SettingsIcon, Sliders, CheckCircle2, Key } from 'lucide-react';
import { UserType } from '../../App';

interface SettingsProps {
  user: UserType;
  onPreferencesUpdated: (updatedUser: UserType) => void;
}

export default function Settings({ user, onPreferencesUpdated }: SettingsProps) {
  const [provider, setProvider] = useState<string>(user.preferences.provider_ia || 'fallback');
  const [apiKey, setApiKey] = useState<string>(user.preferences.api_key || '');
  const [theme, setTheme] = useState<string>(user.preferences.theme || 'dark');
  const [fontSize, setFontSize] = useState<number>(user.preferences.font_size || 14);
  const [terminalType, setTerminalType] = useState<string>(user.preferences.terminal_type || 'simulation');
  
  const [saving, setSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    setError(null);

    try {
      const res = await fetch('/api/users/me/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider_ia: provider,
          api_key: apiKey,
          theme,
          font_size: fontSize,
          terminal_type: terminalType
        }),
      });

      if (res.ok) {
        const updatedUser = await res.json();
        onPreferencesUpdated(updatedUser);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        const errData = await res.json();
        setError(errData.detail || "Échec de l'enregistrement.");
      }
    } catch (err) {
      console.error(err);
      setError("Erreur réseau de communication.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full space-y-8 select-none">
      <div className="flex items-center space-x-3 border-b border-gray-800/80 pb-4">
        <div className="p-2 bg-[#10B981]/10 rounded-xl border border-[#10B981]/20">
          <SettingsIcon className="h-5 w-5 text-[#10B981]" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white font-mono tracking-wide">Paramètres Généraux</h2>
          <p className="text-xs text-gray-400">Configurez votre environnement d'apprentissage et vos clés d'API d'Intelligence Artificielle</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {saveSuccess && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-[#10B981] font-mono text-xs rounded-2xl flex items-center space-x-2.5 shadow-md">
            <CheckCircle2 className="h-4.5 w-4.5 shrink-0" />
            <span>Vos préférences ont été sauvegardées avec succès !</span>
          </div>
        )}
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 font-mono text-xs rounded-2xl">
            <span>{error}</span>
          </div>
        )}

        {/* AI API Configuration */}
        <div className="bg-[#090D1A]/90 border border-gray-850 p-6 rounded-2xl space-y-4 shadow-xl">
          <h3 className="font-mono text-sm font-bold text-white flex items-center space-x-2.5">
            <Key className="h-4.5 w-4.5 text-[#10B981]" />
            <span>Moteur d'Intelligence Artificielle</span>
          </h3>
          <p className="text-xs text-gray-400 font-mono leading-relaxed bg-[#040712]/30 p-4 rounded-xl border border-gray-850/50">
            Astatarote s'interface avec plusieurs fournisseurs d'IA LLM pour générer vos scénarios à la volée. 
            Sélectionnez <strong>simulateur intégré</strong> si vous n'avez pas de clé API (les défis seront générés par notre simulateur de règles intégré, 100% opérationnel !).
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-400">Fournisseur d'IA</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-[#040712] border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-3 rounded-xl text-sm font-mono text-gray-300"
              >
                <option value="fallback">Simulateur Intégré (Local / Fallback)</option>
                <option value="nvidia">NVIDIA AI Foundation</option>
                <option value="groq">Groq AI (Llama 3)</option>
                <option value="fireworks">Fireworks AI</option>
                <option value="cohere">Cohere API</option>
                <option value="together">Together AI</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-400">Clé API Secrète</label>
              <input
                type="password"
                placeholder={provider === 'fallback' ? "Non requise en mode simulé" : "Entrez votre clé d'API"}
                disabled={provider === 'fallback'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-[#040712] border border-gray-800 disabled:opacity-40 focus:border-[#10B981]/60 focus:outline-none p-3 rounded-xl text-sm font-mono"
              />
            </div>
          </div>
        </div>

        {/* Display & Terminal configs */}
        <div className="bg-[#090D1A]/90 border border-gray-850 p-6 rounded-2xl space-y-4 shadow-xl">
          <h3 className="font-mono text-sm font-bold text-white flex items-center space-x-2.5">
            <Sliders className="h-4.5 w-4.5 text-[#10B981]" />
            <span>Affichage & Terminaux</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-400">Thème de l'interface</label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="w-full bg-[#040712] border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-3 rounded-xl text-sm font-mono text-gray-300"
              >
                <option value="dark">Cyber Dark (Sombre)</option>
                <option value="light">Solarized Light (Clair)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-400">Taille de police du terminal</label>
              <select
                value={fontSize}
                onChange={(e) => setFontSize(parseInt(e.target.value))}
                className="w-full bg-[#040712] border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-3 rounded-xl text-sm font-mono text-gray-300"
              >
                <option value={12}>12px (Compact)</option>
                <option value={14}>14px (Standard)</option>
                <option value={16}>16px (Grand)</option>
                <option value={18}>18px (Trés grand)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-400">Type de terminal par défaut</label>
              <select
                value={terminalType}
                onChange={(e) => setTerminalType(e.target.value)}
                className="w-full bg-[#040712] border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-3 rounded-xl text-sm font-mono text-gray-300"
              >
                <option value="simulation">Simulé par l'IA (Recommandé)</option>
                <option value="docker">Sandbox Docker isolée</option>
                <option value="reel">Terminal Réel sécurisé</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <button
          type="submit"
          disabled={saving}
          className="px-6 py-3 bg-[#10B981] hover:bg-emerald-500 hover:shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50 text-black font-bold font-mono rounded-xl text-xs flex items-center justify-center space-x-2 transition-all duration-300 shadow-md"
        >
          <Save className="h-4 w-4" />
          <span>Enregistrer les préférences</span>
        </button>
      </form>
    </div>
  );
}
