import React, { useState } from "react";
import {
  ArrowLeft,
  Cpu,
  Sparkles,
  AlertTriangle,
  ShieldCheck,
  Wifi,
  Lock,
  Terminal,
  Wand2,
} from "lucide-react";
import { api } from "../../lib/api";
import { UserType } from "../../App";

interface CreateGameProps {
  user: UserType;
  onGameCreated: (gameId: number) => void;
  onCancel: () => void;
}

interface GameCreated {
  id: number;
}

const STEPS = [
  "Analyse de ta demande d'apprentissage...",
  "Conception du plan de cours par l'IA Architecte...",
  "Génération des scénarios et des consignes précises...",
  "Provisionnement de l'arborescence des fichiers réels...",
  "Verrouillage de la sandbox et des contrôles de validation...",
  "Laboratoire prêt. Initialisation du premier défi...",
];

const DOMAINS = [
  {
    id: "linux",
    label: "Administration Linux",
    icon: Terminal,
    color: "text-blue-400 border-blue-500/25 bg-blue-500/10",
  },
  {
    id: "security",
    label: "Cybersécurité",
    icon: Lock,
    color: "text-red-400 border-red-500/25 bg-red-500/10",
  },
  {
    id: "network",
    label: "Réseaux",
    icon: Wifi,
    color: "text-asta-violet border-asta-violet/25 bg-asta-violet/10",
  },
];

const PRESETS = [
  {
    title: "Permissions & Exploration",
    domain: "linux",
    level: "beginner",
    prompt: "apprendre les permissions linux chmod chown et explorer le système de fichiers",
    description: "Débutant — chmod, chown, localisation d'informations sensibles.",
  },
  {
    title: "Sécuriser un serveur web",
    domain: "security",
    level: "intermediate",
    prompt: "durcir la configuration d'un serveur web apache et désactiver l'indexation des dossiers",
    description: "Intermédiaire — durcissement de configuration et bonnes pratiques.",
  },
  {
    title: "Audit de logs SSH",
    domain: "security",
    level: "intermediate",
    prompt: "analyser un fichier auth.log pour détecter une attaque par force brute ssh",
    description: "Intermédiaire — analyse de logs et détection d'intrusion.",
  },
  {
    title: "Cartographie réseau",
    domain: "network",
    level: "beginner",
    prompt: "cartographier les hôtes et services d'un réseau interne via les fichiers de configuration",
    description: "Débutant — résolution de noms, hôtes et services.",
  },
];

export default function CreateGame({ user, onGameCreated, onCancel }: CreateGameProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [domain, setDomain] = useState("linux");
  const [level, setLevel] = useState("beginner");
  const [customPrompt, setCustomPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generatingStep, setGeneratingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setGenerating(true);
    setGeneratingStep(0);
    setError(null);

    const interval = setInterval(() => {
      setGeneratingStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 1400);

    try {
      const game = await api.post<GameCreated>("/api/games", {
        name: name.trim(),
        description: description.trim() || `Apprendre ${domain} (${level})`,
        domain,
        level,
        custom_prompt: customPrompt.trim() || undefined,
      });
      clearInterval(interval);
      setGeneratingStep(STEPS.length - 1);
      setTimeout(() => onGameCreated(game.id), 900);
    } catch (err) {
      clearInterval(interval);
      setError(err instanceof Error ? err.message : "Erreur réseau avec l'IA Architecte.");
      setGenerating(false);
    }
  };

  const handlePreset = (p: (typeof PRESETS)[number]) => {
    setName(p.title);
    setDomain(p.domain);
    setLevel(p.level);
    setCustomPrompt(p.prompt);
    setDescription(p.description);
  };

  if (generating) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-gradient-to-b from-ink-deep to-ink-base">
        <div className="max-w-md w-full panel p-8 text-center space-y-6 shadow-card animate-fade-in">
          <div className="relative mx-auto w-fit">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-asta-green"></div>
            <Cpu className="h-6 w-6 text-asta-green absolute inset-0 m-auto animate-pulse-glow" />
          </div>

          <div className="space-y-2">
            <h4 className="font-display text-lg font-bold text-white tracking-wider uppercase">
              Génération du laboratoire
            </h4>
            <p className="text-xs text-gray-500 font-mono">Moteur : {user.preferences.provider_ia || "fallback"}</p>
          </div>

          <div className="p-4 bg-ink-deep/70 border border-ink-line rounded-xl">
            <p className="text-sm font-mono text-asta-green animate-pulse">{STEPS[generatingStep]}</p>
          </div>

          <div className="w-full bg-ink-deep rounded-full h-1 overflow-hidden">
            <div
              className="bg-asta-green h-1 rounded-full transition-all duration-500 shadow-glow-sm"
              style={{ width: `${((generatingStep + 1) / STEPS.length) * 100}%` }}
            ></div>
          </div>

          <p className="text-[11px] text-gray-500 leading-relaxed font-mono">
            L'Architecte construit l'arborescence, les permissions, les fichiers sources et les contrôles
            de validation du premier défi.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-5xl mx-auto w-full space-y-6">
      <button onClick={onCancel} className="flex items-center gap-2 text-gray-400 hover:text-asta-green transition font-mono text-sm">
        <ArrowLeft className="h-4 w-4" />
        Retour au tableau de bord
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <div className="lg:col-span-2 panel p-7 space-y-6 animate-fade-in">
          <div className="flex items-center gap-3 border-b border-ink-line pb-4">
            <div className="p-2.5 bg-asta-green/10 rounded-lg border border-asta-green/20">
              <Wand2 className="h-5 w-5 text-asta-green" />
            </div>
            <div>
              <h2 className="text-lg font-display font-bold text-white">Configurer mon parcours adaptatif</h2>
              <p className="text-xs text-gray-400">Décris ton objectif de formation — l'IA bâtit les défis.</p>
            </div>
          </div>

          {error && (
            <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-2.5 text-xs text-red-400 font-mono">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleCreate} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Nom du laboratoire *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex : Durcir un serveur SSH"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-field"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Description courte</label>
                <input
                  type="text"
                  placeholder="Ex : Exercices sur les permissions et les logs"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="input-field"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-mono text-gray-400">Thématique</label>
              <div className="grid grid-cols-3 gap-2.5">
                {DOMAINS.map((d) => {
                  const Icon = d.icon;
                  const active = domain === d.id;
                  return (
                    <button
                      type="button"
                      key={d.id}
                      onClick={() => setDomain(d.id)}
                      className={`p-3 rounded-xl border font-mono text-xs font-bold flex flex-col items-center gap-2 transition-all duration-200 ${
                        active
                          ? `${d.color} border-current`
                          : "bg-ink-deep/50 border-ink-line text-gray-500 hover:text-gray-300"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {d.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-mono text-gray-400">Niveau de difficulté initial</label>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="input-field text-gray-300"
              >
                <option value="beginner">Débutant — Novice à Apprenti</option>
                <option value="intermediate">Intermédiaire — Administrateur</option>
                <option value="advanced">Avancé — Expert</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-mono text-gray-400">
                Instruction personnalisée pour l'IA (facultatif)
              </label>
              <textarea
                rows={3}
                placeholder="Ex : Je veux apprendre à analyser auth.log, détecter une force brute, puis durcir sshd_config."
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                className="input-field resize-none"
              />
              <p className="text-[10px] text-gray-500 leading-relaxed font-mono">
                L'IA Architecte s'appuie sur cette consigne pour générer 3 défis cohérents, avec des fichiers
                réels, des consignes précises et des contrôles de validation automatiques.
              </p>
            </div>

            <button type="submit" disabled={!name.trim()} className="btn-primary w-full !py-3">
              <Sparkles className="h-4 w-4" />
              Générer mes 3 défis adaptatifs
            </button>
          </form>
        </div>

        {/* Presets */}
        <div className="panel p-5 space-y-4 h-fit animate-fade-in">
          <div className="flex items-center gap-2 pb-2 border-b border-ink-line">
            <ShieldCheck className="h-4 w-4 text-asta-green" />
            <h3 className="font-mono text-sm font-bold text-white">Scénarios recommandés</h3>
          </div>
          <p className="text-xs text-gray-400 font-mono">Clique sur un préréglage pour le charger :</p>

          <div className="space-y-2.5">
            {PRESETS.map((p, i) => (
              <button
                key={i}
                onClick={() => handlePreset(p)}
                className="w-full text-left p-3 rounded-xl bg-ink-deep/50 border border-ink-line hover:border-asta-green/40 hover:bg-ink-deep transition-all duration-200"
              >
                <p className="font-mono font-bold text-xs text-gray-200">{p.title}</p>
                <p className="text-[10px] text-gray-500 font-mono mt-1">{p.description}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
