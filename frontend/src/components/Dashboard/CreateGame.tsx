import React, { useState } from 'react';
import { ArrowLeft, Cpu, Sparkles, AlertTriangle, ShieldCheck } from 'lucide-react';
import { UserType } from '../../App';

interface CreateGameProps {
  user: UserType;
  onGameCreated: (gameId: number) => void;
  onCancel: () => void;
}

export default function CreateGame({ user, onGameCreated, onCancel }: CreateGameProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState('linux');
  const [level, setLevel] = useState('beginner');
  const [customPrompt, setCustomPrompt] = useState('');
  
  const [generating, setGenerating] = useState(false);
  const [generatingStep, setGeneratingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const steps = [
    "Analyse de votre demande d'apprentissage...",
    "Appel à l'IA Architecte pour la conception du plan de cours...",
    "Création de la structure de niveaux personnalisée...",
    "Définition des scénarios et des états de fichiers simulés...",
    "Configuration du sandbox virtuel et du gardien de sécurité...",
    "Génération finalisée ! Initialisation du premier défi..."
  ];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.strip) {
      if (!name.trim()) return;
    }
    
    setGenerating(true);
    setGeneratingStep(0);
    setError(null);

    // Dynamic generation simulation step increments
    const interval = setInterval(() => {
      setGeneratingStep((prev) => {
        if (prev < steps.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 1500);

    try {
      const res = await fetch('/api/games', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || `Apprendre ${domain} (${level})`,
          domain,
          level,
          custom_prompt: customPrompt.trim() || undefined
        }),
      });

      clearInterval(interval);

      if (res.ok) {
        const gameData = await res.json();
        // Pause briefly on the final step to make it feel satisfying
        setGeneratingStep(steps.length - 1);
        setTimeout(() => {
          onGameCreated(gameData.id);
        }, 1000);
      } else {
        const errData = await res.json();
        setError(errData.detail || "Échec de la génération du jeu.");
        setGenerating(false);
      }
    } catch (err) {
      clearInterval(interval);
      console.error(err);
      setError("Erreur de communication réseau avec l'IA Architecte.");
      setGenerating(false);
    }
  };

  const handleQuickSelect = (title: string, dom: string, lvl: string, promptText: string) => {
    setName(title);
    setDomain(dom);
    setLevel(lvl);
    setCustomPrompt(promptText);
    setDescription(`Lab adaptatif concentré sur : ${title}`);
  };

  if (generating) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-gradient-to-b from-[#070A13] to-[#0B0F19]">
        <div className="max-w-md w-full bg-[#111827] border border-gray-800 p-8 rounded-2xl text-center space-y-6 shadow-2xl">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#10B981] mx-auto"></div>
            <Cpu className="h-6 w-6 text-[#10B981] absolute inset-0 m-auto animate-pulse" />
          </div>
          
          <div className="space-y-2">
            <h4 className="font-mono text-lg font-bold text-white tracking-wider uppercase">Génération d'Astatarote Lab</h4>
            <p className="text-xs text-gray-500 font-mono">IA: {user.preferences.provider_ia || "fallback"}</p>
          </div>

          <div className="p-4 bg-gray-950 border border-gray-850 rounded-xl">
            <p className="text-sm font-mono text-[#10B981] animate-pulse">
              {steps[generatingStep]}
            </p>
          </div>

          <div className="w-full bg-gray-950 rounded-full h-1 overflow-hidden">
            <div 
              className="bg-[#10B981] h-1 rounded-full transition-all duration-500"
              style={{ width: `${((generatingStep + 1) / steps.length) * 100}%` }}
            ></div>
          </div>

          <p className="text-[11px] text-gray-500 leading-relaxed font-mono">
            Veuillez patienter. L'architecte construit les dossiers, fichiers virtuels, permissions, et configurateurs de logs pour vos défis.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full space-y-6">
      {/* Back button */}
      <button 
        onClick={onCancel}
        className="flex items-center space-x-2 text-gray-400 hover:text-[#10B981] transition font-mono text-sm"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Retour au Tableau de bord</span>
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Creation Form */}
        <div className="lg:col-span-2 bg-[#111827] border border-gray-800 p-6 rounded-2xl space-y-6">
          <div className="flex items-center space-x-3 border-b border-gray-850 pb-4">
            <div className="p-2 bg-[#10B981]/10 rounded-lg border border-[#10B981]/20">
              <Sparkles className="h-5 w-5 text-[#10B981]" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white font-mono">Configurer mon Parcours Adaptatif</h2>
              <p className="text-xs text-gray-400">Décrivez vos objectifs de formation</p>
            </div>
          </div>

          {error && (
            <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center space-x-2.5 text-xs text-red-400 font-mono">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Nom du Laboratoire *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Sécuriser Nginx"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-2.5 rounded-xl text-sm font-mono"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Description courte</label>
                <input
                  type="text"
                  placeholder="Ex: Exercices pratiques pour auditer un site web"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-2.5 rounded-xl text-sm font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Thématique Globale</label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-2.5 rounded-xl text-sm font-mono text-gray-300"
                >
                  <option value="linux">Administration Linux Générale</option>
                  <option value="security">Cybersécurité Offensive & Défensive</option>
                  <option value="network">Réseaux et Protocoles</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono text-gray-400">Niveau de Difficulté Initial</label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-2.5 rounded-xl text-sm font-mono text-gray-300"
                >
                  <option value="beginner">Débutant (Novice à Apprenti)</option>
                  <option value="intermediate">Intermédiaire (Administrateur)</option>
                  <option value="advanced">Avancé (Expert / Reverse Engineer)</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-mono text-gray-400">
                Instruction personnalisée pour l'IA Architecte (Prompt libre)
              </label>
              <textarea
                rows={3}
                placeholder="Ex : Je veux apprendre à configurer les permissions chmod, chown et analyser un historique de logs d'intrusion SSH."
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 focus:border-[#10B981]/60 focus:outline-none p-2.5 rounded-xl text-sm font-mono"
              />
              <p className="text-[10px] text-gray-500 leading-relaxed font-mono">
                L'IA Architecte se servira de cette consigne pour construire sur-mesure vos 3 niveaux de jeu, leurs variables, leurs arborescences de dossiers, et les contrôles automatiques.
              </p>
            </div>

            <button
              type="submit"
              disabled={!name.trim()}
              className="w-full py-3 bg-[#10B981] hover:bg-emerald-600 disabled:opacity-50 text-black font-bold font-mono rounded-xl text-sm flex items-center justify-center space-x-2 transition shadow-lg"
            >
              <Cpu className="h-4 w-4" />
              <span>Générer mes 3 Défis Adaptatifs</span>
            </button>
          </form>
        </div>

        {/* Quick presets list */}
        <div className="bg-gray-900/40 border border-gray-800 p-5 rounded-2xl space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-gray-850">
            <ShieldCheck className="h-4 w-4 text-[#10B981]" />
            <h3 className="font-mono text-sm font-bold text-white">Scénarios Recommandés</h3>
          </div>
          <p className="text-xs text-gray-400 font-mono">Cliquez sur un préréglage pour le charger immédiatement :</p>

          <div className="space-y-2.5">
            <button
              onClick={() => handleQuickSelect(
                "Audit et Permissions", 
                "linux", 
                "beginner", 
                "permissions linux chmod chown secret"
              )}
              className="w-full text-left p-3 rounded-xl bg-gray-900 border border-gray-800 hover:border-[#10B981]/40 hover:bg-gray-850 transition duration-200"
            >
              <p className="font-mono font-bold text-xs text-gray-200">Permissions & Exploration</p>
              <p className="text-[10px] text-gray-400 font-mono mt-1">Débutant - Apprendre chmod, chown et localiser des informations.</p>
            </button>

            <button
              onClick={() => handleQuickSelect(
                "Sécurité Web Apache", 
                "security", 
                "intermediate", 
                "securiser serveur web apache autoindex"
              )}
              className="w-full text-left p-3 rounded-xl bg-gray-900 border border-gray-800 hover:border-[#10B981]/40 hover:bg-gray-850 transition duration-200"
            >
              <p className="font-mono font-bold text-xs text-gray-200">Sécuriser un Serveur Web</p>
              <p className="text-[10px] text-gray-400 font-mono mt-1">Intermédiaire - Désactiver l'indexation de fichiers, configurer des hôtes.</p>
            </button>

            <button
              onClick={() => handleQuickSelect(
                "Analyse logs d'intrusion", 
                "security", 
                "intermediate", 
                "analyser log auth.log brute force"
              )}
              className="w-full text-left p-3 rounded-xl bg-gray-900 border border-gray-800 hover:border-[#10B981]/40 hover:bg-gray-850 transition duration-200"
            >
              <p className="font-mono font-bold text-xs text-gray-200">Audit de Logs SSH</p>
              <p className="text-[10px] text-gray-400 font-mono mt-1">Intermédiaire - Détecter une attaque force brute dans auth.log.</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
