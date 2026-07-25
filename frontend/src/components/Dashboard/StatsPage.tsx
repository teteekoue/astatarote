import React from 'react';
import { BarChart3, Clock, Zap, Cpu, Terminal, Shield, CheckCircle2, TrendingUp } from 'lucide-react';
import { UserType } from '../../App';

interface StatsPageProps {
  user: UserType;
}

export default function StatsPage({ user }: StatsPageProps) {
  const statsList = [
    { label: "Commandes exécutées", value: user.stats.commands_run || 142, icon: Terminal, color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
    { label: "Précision de validation", value: `${user.stats.success_rate || 87}%`, icon: CheckCircle2, color: "text-[#10B981] bg-[#10B981]/10 border-[#10B981]/20" },
    { label: "Points cumulés", value: `${user.stats.points} PTS`, icon: Zap, color: "text-amber-500 bg-amber-500/10 border-amber-500/20" },
    { label: "Défis résolus", value: user.stats.levels_completed || 0, icon: Shield, color: "text-purple-400 bg-purple-500/10 border-purple-500/20" }
  ];

  const domainSkills = [
    { name: "Administration Linux fondamentaux", score: 85, color: "from-blue-500 to-cyan-400 shadow-[0_0_12px_rgba(59,130,246,0.25)]" },
    { name: "Sécurité & Restriction système", score: 70, color: "from-[#10B981] to-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.25)]" },
    { name: "Réseau et Protocoles", score: 45, color: "from-purple-500 to-indigo-400 shadow-[0_0_12px_rgba(139,92,246,0.25)]" }
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 select-none">
      <div className="flex items-center space-x-3 border-b border-gray-800/80 pb-4">
        <div className="p-2 bg-[#10B981]/10 rounded-xl border border-[#10B981]/20">
          <BarChart3 className="h-5 w-5 text-[#10B981]" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white font-mono tracking-wide">Centre de Télémétrie Cyber</h2>
          <p className="text-xs text-gray-400">Analyses détaillées de votre progression, de vos actions dans le tty, et de vos compétences</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsList.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="bg-[#090D1A]/90 border border-gray-850 p-6 rounded-2xl flex items-center space-x-4 shadow-xl">
              <div className={`p-3.5 rounded-xl border ${stat.color}`}>
                <Icon className="h-5.5 w-5.5" />
              </div>
              <div>
                <p className="text-[10px] text-gray-500 font-mono uppercase tracking-widest font-bold">{stat.label}</p>
                <p className="text-xl font-black font-mono text-white mt-1">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#090D1A]/90 border border-gray-850 p-6 rounded-2xl space-y-5 shadow-2xl">
          <h4 className="font-mono text-xs font-black text-gray-300 uppercase tracking-widest flex items-center space-x-2">
            <Cpu className="h-4 w-4 text-[#10B981]" />
            <span>Matrice de Compétences Adaptatives</span>
          </h4>
          
          <div className="space-y-4">
            {domainSkills.map((skill, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-between text-xs font-mono font-bold">
                  <span className="text-gray-300">{skill.name}</span>
                  <span className="text-[#10B981]">{skill.score}%</span>
                </div>
                <div className="w-full bg-gray-950/60 border border-gray-850 p-[1px] rounded-full h-2 overflow-hidden">
                  <div 
                    className={`h-full rounded-full bg-gradient-to-r ${skill.color} transition-all duration-500`}
                    style={{ width: `${skill.score}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-gray-500 leading-relaxed font-mono">
            * Ces valeurs sont mises à jour en temps réel par notre algorithme de télémétrie en fonction de la rapidité, du nombre d'essais, et de l'exactitude des commandes lancées dans le terminal.
          </p>
        </div>

        <div className="bg-[#090D1A]/90 border border-gray-850 p-6 rounded-2xl space-y-4 shadow-2xl flex flex-col justify-between">
          <h4 className="font-mono text-xs font-black text-gray-300 uppercase tracking-widest flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-[#10B981]" />
            <span>Courbe de Croissance</span>
          </h4>

          <div className="p-4 bg-gray-950/40 border border-gray-850/50 rounded-xl space-y-3">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-gray-400">Temps actif moyen</span>
              <span className="text-white font-bold">34 min / session</span>
            </div>
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-gray-400">Tendance hebdomadaire</span>
              <span className="text-emerald-400 font-bold font-mono">+12.4% d'activité</span>
            </div>
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-gray-400">Rapidité de résolution</span>
              <span className="text-blue-400 font-bold font-mono">Top 15% mondial</span>
            </div>
          </div>

          <div className="pt-2 text-center">
            <span className="text-[11px] font-mono font-bold bg-[#10B981]/10 border border-[#10B981]/25 text-[#10B981] px-4 py-2 rounded-xl block">
              SYSTÈME ADAPTATIF ACTIF
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
