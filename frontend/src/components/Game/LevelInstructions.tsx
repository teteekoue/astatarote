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

  // Convert seconds to minutes/seconds format
  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins}m ${remainingSecs > 0 ? remainingSecs + 's' : ''}`;
  };

  const subObjectives = level.scenario?.expected_state?.files_checks || [];

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#0B0F19]">
      {/* Scrollable pane */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        
        {/* Title, Badge & Meta */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded uppercase tracking-wider">
              Défi Actif
            </span>
            <span className="text-xs text-gray-500 font-mono">Difficulté : {level.difficulty}/10</span>
          </div>
          <h2 className="text-lg font-bold text-white font-mono leading-tight">{level.title}</h2>
        </div>

        {/* Challenge rewards */}
        <div className="grid grid-cols-2 gap-3 p-3 bg-gray-950/40 rounded-xl border border-gray-850">
          <div className="flex items-center space-x-2">
            <Award className="h-4 w-4 text-amber-500" />
            <div>
              <p className="text-[10px] text-gray-500 font-mono uppercase">Récompense</p>
              <p className="text-xs font-mono text-gray-200 font-bold">{level.points} pts</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-blue-400" />
            <div>
              <p className="text-[10px] text-gray-500 font-mono uppercase">Temps estimé</p>
              <p className="text-xs font-mono text-gray-200 font-bold">{formatTime(level.time_limit)}</p>
            </div>
          </div>
        </div>

        {/* Mission details */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold font-mono uppercase text-gray-400">Le Contexte</h3>
          <p className="text-xs text-gray-300 font-mono leading-relaxed whitespace-pre-wrap">
            {level.description}
          </p>
        </div>

        {/* Main objective */}
        <div className="p-3.5 bg-[#10B981]/5 border border-[#10B981]/20 rounded-xl space-y-2">
          <h3 className="text-xs font-bold font-mono uppercase text-[#10B981] flex items-center space-x-1.5">
            <ShieldCheck className="h-4 w-4" />
            <span>Objectif Principal</span>
          </h3>
          <p className="text-xs text-gray-200 font-mono leading-relaxed">
            {level.objective}
          </p>
        </div>

        {/* Sub-objectives Checklist */}
        {subObjectives.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-xs font-bold font-mono uppercase text-gray-400">Critères de validation</h3>
            <div className="space-y-2">
              {subObjectives.map((check: any, idx: number) => {
                const targetPath = check.path || "Fichier";
                const isPerm = check.perms ? ` avec permissions ${check.perms}` : "";
                const isContent = check.content_contains ? ` contenant une configuration spécifique` : "";
                
                return (
                  <div key={idx} className="flex items-start space-x-2.5 p-2 bg-gray-950/60 border border-gray-850 rounded-lg">
                    <div className="h-4 w-4 rounded-full border border-gray-700 bg-gray-950 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-[10px] font-mono font-bold text-gray-500">{idx + 1}</span>
                    </div>
                    <div>
                      <p className="text-xs font-mono text-gray-300">Vérifier l'existence de : `{targetPath}`{isPerm}{isContent}</p>
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
            <h3 className="text-xs font-bold font-mono uppercase text-gray-400 flex items-center space-x-1.5">
              <HelpCircle className="h-4 w-4 text-indigo-400" />
              <span>Indices disponibles ({level.hints.length})</span>
            </h3>
            
            <div className="space-y-2">
              {level.hints.map((hint, idx) => {
                const isRevealed = revealedHints[idx];
                return (
                  <div 
                    key={idx} 
                    className="bg-gray-950/80 border border-gray-850 rounded-xl overflow-hidden transition"
                  >
                    <button
                      onClick={() => toggleHint(idx)}
                      className="w-full px-4 py-2.5 flex items-center justify-between text-left text-xs font-mono font-bold text-gray-400 hover:text-white hover:bg-gray-850/30"
                    >
                      <span>Indice #{idx + 1}</span>
                      {isRevealed ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                    </button>
                    {isRevealed && (
                      <div className="px-4 pb-3.5 pt-1.5 border-t border-gray-850/50 text-[11px] font-mono text-gray-300 leading-relaxed bg-gray-950">
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
