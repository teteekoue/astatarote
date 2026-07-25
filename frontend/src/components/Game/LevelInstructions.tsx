import React, { useState } from 'react';
import { ShieldCheck, HelpCircle, Eye, EyeOff, Award, Clock } from 'lucide-react';
import { LevelType } from './GameInterface';

interface LevelInstructionsProps {
  level: LevelType;
}

export default function LevelInstructions({ level }: LevelInstructionsProps) {
  const [revealedHints, setRevealedHints] = useState<Record<number, boolean>>({});

  const toggleHint = (index: number) => {
    setRevealedHints(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins}m ${remainingSecs > 0 ? remainingSecs + 's' : ''}`;
  };

  const subObjectives = level.scenario?.expected_state?.files_checks || [];

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#090D1A]/50 select-none">
      
      {/* Scrollable pane */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {/* Title, Badge & Meta */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-black font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2.5 py-1 rounded-full uppercase tracking-wider">
              Défi Actif
            </span>
            <span className="text-[10px] text-gray-500 font-mono font-bold uppercase tracking-wider">Difficulté : {level.difficulty}/10</span>
          </div>
          <h2 className="text-md font-black text-white font-mono leading-snug tracking-wide select-text">{level.title}</h2>
        </div>

        {/* Challenge rewards (glowing stats) */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-[#040712] rounded-2xl border border-gray-850">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-amber-500/10 rounded-xl border border-amber-500/20 text-amber-400">
              <Award className="h-4.5 w-4.5" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest font-bold">Récompense</p>
              <p className="text-xs font-black font-mono text-gray-200 mt-0.5">{level.points} pts</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/10 rounded-xl border border-blue-500/20 text-blue-400">
              <Clock className="h-4.5 w-4.5" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-mono uppercase tracking-widest font-bold">Temps estimé</p>
              <p className="text-xs font-black font-mono text-gray-200 mt-0.5">{formatTime(level.time_limit)}</p>
            </div>
          </div>
        </div>

        {/* Mission details */}
        <div className="space-y-2">
          <h3 className="text-[10px] font-black font-mono uppercase tracking-widest text-gray-500">Le Contexte</h3>
          <p className="text-xs text-gray-300 font-mono leading-relaxed select-text bg-[#040712]/30 p-4 rounded-xl border border-gray-850/40">
            {level.description}
          </p>
        </div>

        {/* Main objective */}
        <div className="p-4 bg-[#10B981]/5 border border-[#10B981]/20 rounded-2xl space-y-2 shadow-[inset_0_1px_1px_rgba(16,185,129,0.02)]">
          <h3 className="text-[10px] font-black font-mono uppercase tracking-widest text-[#10B981] flex items-center space-x-1.5">
            <ShieldCheck className="h-4.5 w-4.5 animate-pulse" />
            <span>Objectif Principal</span>
          </h3>
          <p className="text-xs text-gray-200 font-mono leading-relaxed select-text">
            {level.objective}
          </p>
        </div>

        {/* Sub-objectives Checklist */}
        {subObjectives.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-[10px] font-black font-mono uppercase tracking-widest text-gray-500">Critères de validation</h3>
            <div className="space-y-2.5">
              {subObjectives.map((check: any, idx: number) => {
                const targetPath = check.path || "Fichier";
                const isPerm = check.perms ? ` avec permissions ${check.perms}` : "";
                const isContent = check.content_contains ? ` contenant une configuration spécifique` : "";
                
                return (
                  <div key={idx} className="flex items-start space-x-3 p-3 bg-[#040712] border border-gray-850/80 rounded-xl">
                    <div className="h-5 w-5 rounded-lg border border-gray-800 bg-gray-950 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-[9px] font-black font-mono text-gray-500">{idx + 1}</span>
                    </div>
                    <div>
                      <p className="text-xs font-mono text-gray-300 select-text leading-relaxed">Vérifier l'existence de : `{targetPath}`{isPerm}{isContent}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Dynamic Hints Dropdown */}
        {level.hints && level.hints.length > 0 && (
          <div className="space-y-3 pt-2">
            <h3 className="text-[10px] font-black font-mono uppercase tracking-widest text-gray-500 flex items-center space-x-1.5">
              <HelpCircle className="h-4 w-4 text-indigo-400" />
              <span>Indices disponibles ({level.hints.length})</span>
            </h3>
            
            <div className="space-y-2">
              {level.hints.map((hint, idx) => {
                const isRevealed = revealedHints[idx];
                return (
                  <div 
                    key={idx} 
                    className="bg-[#040712] border border-gray-850 rounded-xl overflow-hidden transition-all duration-200"
                  >
                    <button
                      onClick={() => toggleHint(idx)}
                      className="w-full px-4 py-3 flex items-center justify-between text-left text-xs font-mono font-bold text-gray-400 hover:text-white hover:bg-gray-900/30"
                    >
                      <span>Indice #{idx + 1}</span>
                      {isRevealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                    {isRevealed && (
                      <div className="px-4 pb-4 pt-2 border-t border-gray-850/50 text-[11px] font-mono text-gray-300 leading-relaxed bg-[#040712]/50 select-text">
                        {hint}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
