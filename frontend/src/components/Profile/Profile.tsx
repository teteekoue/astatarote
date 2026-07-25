import React from 'react';
import { Award, ShieldCheck, Zap, Layers, User, Lock } from 'lucide-react';
import { UserType } from '../../App';

interface ProfileProps {
  user: UserType;
}

export default function Profile({ user }: ProfileProps) {
  const allBadges = [
    {
      name: "Linux Ninja",
      description: "Maîtrise des commandes Linux fondamentales et manipulation sécurisée des répertoires.",
      iconColor: "text-blue-400 bg-blue-500/10 border-blue-500/20",
      glowClass: "neon-border-blue"
    },
    {
      name: "Network Sentinel",
      description: "Sécurisation réseau, analyse de configurations et gestion des ports de serveurs.",
      iconColor: "text-purple-400 bg-purple-500/10 border-purple-500/20",
      glowClass: "neon-border"
    },
    {
      name: "Defender",
      description: "Application de mesures de sécurité défensives, restriction d'accès et correction de privilèges.",
      iconColor: "text-red-400 bg-red-500/10 border-red-500/20",
      glowClass: "neon-border-red"
    },
    {
      name: "White Hat",
      description: "Esprit éthique, audit proactif et détection responsable de vulnérabilités.",
      iconColor: "text-amber-400 bg-amber-500/10 border-amber-500/20",
      glowClass: ""
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full space-y-8">
      {/* Profile summary header */}
      <div className="bg-[#111827] border border-gray-800 p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-4">
          <div className="h-16 w-16 rounded-full bg-[#10B981]/10 border-2 border-[#10B981] flex items-center justify-center">
            <User className="h-8 w-8 text-[#10B981]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-mono">{user.username}</h2>
            <p className="text-xs text-gray-400 font-mono">Agent cyber-éducatif inscrit le {new Date(user.created_at).toLocaleDateString('fr-FR')}</p>
          </div>
        </div>

        <div className="text-center md:text-right">
          <p className="text-xs text-gray-500 font-mono uppercase">Grade Global</p>
          <p className="text-2xl font-black font-mono text-amber-500 uppercase tracking-widest mt-1">
            {user.stats.rank || "Novice"}
          </p>
        </div>
      </div>

      {/* Grid statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-[#10B981]/10 rounded-lg border border-[#10B981]/20 text-[#10B981]">
            <Zap className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono uppercase">Points d'Apprentissage</p>
            <p className="text-xl font-bold font-mono text-white">{user.stats.points || 0} pts</p>
          </div>
        </div>

        <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20 text-blue-400">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono uppercase">Niveaux complétés</p>
            <p className="text-xl font-bold font-mono text-white">{user.stats.levels_completed || 0} défis</p>
          </div>
        </div>

        <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20 text-purple-400">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono uppercase">Badges Obtenus</p>
            <p className="text-xl font-bold font-mono text-white">{(user.stats.badges || []).length} / {allBadges.length}</p>
          </div>
        </div>
      </div>

      {/* Badges and certs list */}
      <div className="space-y-4">
        <div className="border-b border-gray-800 pb-3">
          <h3 className="font-mono text-md font-bold text-gray-200">Badges et Certifications Militaires</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {allBadges.map((badge, idx) => {
            const isUnlocked = (user.stats.badges || []).includes(badge.name);
            return (
              <div 
                key={idx} 
                className={`p-5 rounded-xl border transition flex items-start space-x-4 ${
                  isUnlocked 
                    ? `bg-[#111827] border-gray-800 ${badge.glowClass}` 
                    : 'bg-gray-950/40 border-gray-900 opacity-50'
                }`}
              >
                <div className={`p-4 rounded-xl border shrink-0 ${
                  isUnlocked ? badge.iconColor : 'bg-gray-900 border-gray-800 text-gray-600'
                }`}>
                  {isUnlocked ? <ShieldCheck className="h-6 w-6" /> : <Lock className="h-6 w-6" />}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-mono text-sm font-bold text-white">{badge.name}</h4>
                    {isUnlocked && (
                      <span className="text-[9px] bg-[#10B981]/15 text-[#10B981] font-mono px-1.5 py-0.5 rounded uppercase tracking-wider">
                        Débloqué
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 font-mono leading-relaxed">
                    {badge.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
