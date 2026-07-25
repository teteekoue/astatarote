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
      glowClass: "neon-border-blue shadow-[0_0_20px_rgba(59,130,246,0.15)]"
    },
    {
      name: "Network Sentinel",
      description: "Sécurisation réseau, analyse de configurations et gestion des ports de serveurs.",
      iconColor: "text-purple-400 bg-purple-500/10 border-purple-500/20",
      glowClass: "neon-border shadow-[0_0_20px_rgba(16,185,129,0.15)]"
    },
    {
      name: "Defender",
      description: "Application de mesures de sécurité défensives, restriction d'accès et correction de privilèges.",
      iconColor: "text-red-400 bg-red-500/10 border-red-500/20",
      glowClass: "neon-border-red shadow-[0_0_20px_rgba(239,68,68,0.15)]"
    },
    {
      name: "White Hat",
      description: "Esprit éthique, audit proactif et détection responsable de vulnérabilités.",
      iconColor: "text-amber-400 bg-amber-500/10 border-amber-500/20",
      glowClass: "shadow-[0_0_20px_rgba(245,158,11,0.1)]"
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full space-y-8 select-none">
      
      {/* Profile summary header (glassmorphic card) */}
      <div className="bg-[#090D1A]/90 border border-gray-850 p-8 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none"></div>
        <div className="flex items-center space-x-5">
          <div className="h-16 w-16 rounded-2xl bg-[#10B981]/10 border-2 border-[#10B981] flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.15)]">
            <User className="h-8 w-8 text-[#10B981]" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white font-mono tracking-wide">{user.username}</h2>
            <p className="text-xs text-gray-400 font-mono mt-1">Agent cyber-éducatif inscrit le {new Date(user.created_at).toLocaleDateString('fr-FR')}</p>
          </div>
        </div>

        <div className="text-center md:text-right bg-[#040712]/40 px-5 py-3.5 rounded-xl border border-gray-850">
          <p className="text-[10px] text-gray-500 font-mono uppercase tracking-widest font-bold">Grade Global</p>
          <p className="text-xl font-black font-mono text-amber-500 uppercase tracking-widest mt-1">
            {user.stats.rank || "Novice"}
          </p>
        </div>
      </div>

      {/* Grid statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#090D1A]/70 border border-gray-850 p-6 rounded-2xl flex items-center space-x-4 shadow-xl">
          <div className="p-4 bg-[#10B981]/10 rounded-xl border border-[#10B981]/20 text-[#10B981]">
            <Zap className="h-5.5 w-5.5" />
          </div>
          <div>
            <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest font-bold">Points d'Apprentissage</p>
            <p className="text-xl font-black font-mono text-white mt-1">{user.stats.points || 0} pts</p>
          </div>
        </div>

        <div className="bg-[#090D1A]/70 border border-gray-850 p-6 rounded-2xl flex items-center space-x-4 shadow-xl">
          <div className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20 text-blue-400">
            <Layers className="h-5.5 w-5.5" />
          </div>
          <div>
            <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest font-bold">Niveaux complétés</p>
            <p className="text-xl font-black font-mono text-white mt-1">{user.stats.levels_completed || 0} défis</p>
          </div>
        </div>

        <div className="bg-[#090D1A]/70 border border-gray-850 p-6 rounded-2xl flex items-center space-x-4 shadow-xl">
          <div className="p-4 bg-purple-500/10 rounded-xl border border-purple-500/20 text-purple-400">
            <Award className="h-5.5 w-5.5" />
          </div>
          <div>
            <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest font-bold">Badges Obtenus</p>
            <p className="text-xl font-black font-mono text-white mt-1">{(user.stats.badges || []).length} / {allBadges.length}</p>
          </div>
        </div>
      </div>

      {/* Badges and certs list */}
      <div className="space-y-6">
        <div className="border-b border-gray-800/80 pb-3">
          <h3 className="font-mono text-md font-bold text-gray-200 tracking-wide">Badges et Certifications Militaires</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {allBadges.map((badge, idx) => {
            const isUnlocked = (user.stats.badges || []).includes(badge.name);
            return (
              <div 
                key={idx} 
                className={`p-6 rounded-2xl border transition-all duration-300 flex items-start space-x-4 shadow-xl ${
                  isUnlocked 
                    ? `bg-[#090D1A]/90 border-gray-800 ${badge.glowClass}` 
                    : 'bg-[#040712]/30 border-gray-900/40 opacity-40'
                }`}
              >
                <div className={`p-4 rounded-xl border shrink-0 ${
                  isUnlocked ? badge.iconColor : 'bg-gray-900 border-gray-800 text-gray-600'
                }`}>
                  {isUnlocked ? <ShieldCheck className="h-6 w-6" /> : <Lock className="h-6 w-6" />}
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-mono text-xs font-black text-white tracking-wide uppercase">{badge.name}</h4>
                    {isUnlocked && (
                      <span className="text-[8px] bg-[#10B981]/15 text-[#10B981] font-mono px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                        Unlocked
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 font-mono leading-relaxed font-medium">
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
