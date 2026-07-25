import React, { useState, useEffect } from 'react';
import { ChevronLeft, CheckCircle, HelpCircle, Send, Play, Terminal as TermIcon, MessageSquare, AlertCircle, Award, Compass } from 'lucide-react';
import { UserType } from '../../App';
import Terminal from './Terminal';
import Chat from './Chat';
import LevelInstructions from './LevelInstructions';

interface GameInterfaceProps {
  gameId: number;
  user: UserType;
  onBackToDashboard: () => void;
}

export interface LevelType {
  id: number;
  game_id: number;
  level_index: number;
  title: string;
  description: string;
  objective: string;
  scenario: {
    type: string;
    initial_state: any;
    expected_state: any;
    commands_allowed?: string[];
    forbidden_commands?: string[];
  };
  hints: string[];
  difficulty: number;
  points: number;
  time_limit: number;
  status: string;
  attempts: number;
}

export default function GameInterface({ gameId, user, onBackToDashboard }: GameInterfaceProps) {
  const [levels, setLevels] = useState<LevelType[]>([]);
  const [selectedLevelIdx, setSelectedLevelIdx] = useState<number>(0);
  const [activeTabMobile, setActiveTabMobile] = useState<'instructions' | 'terminal' | 'chat'>('terminal');
  const [validating, setGenerating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    success: boolean;
    message: string;
    points_earned: number;
    badge_unlocked: string | null;
  } | null>(null);

  const fetchLevels = async () => {
    try {
      const res = await fetch(`/api/games/${gameId}/levels`);
      if (res.ok) {
        const data = await res.json();
        setLevels(data);
        
        const inProgress = data.find((l: LevelType) => l.status === 'available' || l.status === 'in_progress');
        if (inProgress) {
          setSelectedLevelIdx(inProgress.level_index);
        } else {
          setSelectedLevelIdx(0);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchLevels();
  }, [gameId]);

  const handleValidateLevel = async () => {
    setGenerating(true);
    setValidationResult(null);
    try {
      const res = await fetch(`/api/games/${gameId}/levels/${selectedLevelIdx}/validate`, {
        method: 'POST',
      });
      if (res.ok) {
        const result = await res.json();
        setValidationResult(result);
        if (result.success) {
          await fetchLevels();
        }
      } else {
        setValidationResult({
          success: false,
          message: "Erreur de communication avec l'évaluateur Astatarote.",
          points_earned: 0,
          badge_unlocked: null
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const selectedLevel = levels.find(l => l.level_index === selectedLevelIdx);

  if (levels.length === 0 || !selectedLevel) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#030712] relative overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#10B981]/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="z-10 flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#10B981]"></div>
          <p className="font-mono text-gray-400 text-xs uppercase tracking-widest">Démarrage du conteneur d'exercice...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#030712] text-gray-200">
      
      {/* Premium Top Action Bar */}
      <div className="border-b border-gray-850 bg-[#090D1A] px-6 py-4 flex flex-wrap items-center justify-between gap-4 shrink-0 z-10 select-none shadow-[0_4px_20px_rgba(0,0,0,0.25)]">
        <div className="flex items-center space-x-4">
          <button 
            onClick={onBackToDashboard}
            className="p-2 bg-gray-900/50 hover:bg-gray-850 rounded-xl border border-gray-800 text-gray-400 hover:text-white transition-all"
            title="Retour au Tableau de bord"
          >
            <ChevronLeft className="h-4.5 w-4.5" />
          </button>
          
          <div className="h-6 w-[1px] bg-gray-800 hidden sm:block"></div>
          
          {/* Level indicators as pills */}
          <div className="flex items-center space-x-1.5 bg-gray-950/40 border border-gray-850 p-1 rounded-xl">
            {levels.map((lvl) => {
              const isLocked = lvl.status === 'locked';
              const isCompleted = lvl.status === 'completed';
              const isSelected = lvl.level_index === selectedLevelIdx;

              return (
                <button
                  key={lvl.id}
                  disabled={isLocked && !isCompleted}
                  onClick={() => {
                    setSelectedLevelIdx(lvl.level_index);
                    setValidationResult(null);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-black font-mono tracking-wider transition-all ${
                    isSelected
                      ? 'bg-gradient-to-r from-[#10B981]/20 to-emerald-500/10 text-[#10B981] border border-[#10B981]/40'
                      : isCompleted
                      ? 'bg-emerald-950/20 text-emerald-400 border border-emerald-900/30 hover:bg-emerald-900/20'
                      : isLocked
                      ? 'opacity-30 bg-transparent text-gray-600 border border-transparent cursor-not-allowed'
                      : 'bg-transparent text-gray-400 border border-transparent hover:bg-gray-900/40'
                  }`}
                >
                  DÉFI {lvl.level_index + 1}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleValidateLevel}
            disabled={validating}
            className="px-5 py-2.5 bg-gradient-to-r from-[#10B981] to-emerald-500 hover:shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50 text-black font-mono font-extrabold rounded-xl text-xs flex items-center space-x-2 transition-all duration-300"
          >
            {validating ? (
              <span className="inline-block h-3.5 w-3.5 animate-spin border-2 border-black border-t-transparent rounded-full"></span>
            ) : (
              <CheckCircle className="h-4.5 w-4.5" />
            )}
            <span>Soumettre la Solution</span>
          </button>
        </div>
      </div>

      {/* Mobile navigation tab */}
      <div className="md:hidden flex border-b border-gray-850 bg-gray-950">
        <button
          onClick={() => setActiveTabMobile('instructions')}
          className={`flex-1 py-3 text-xs font-mono text-center border-b-2 flex items-center justify-center space-x-1.5 ${
            activeTabMobile === 'instructions' ? 'border-[#10B981] text-[#10B981] bg-[#10B981]/5' : 'border-transparent text-gray-400'
          }`}
        >
          <Compass className="h-4 w-4" />
          <span>Consignes</span>
        </button>
        <button
          onClick={() => setActiveTabMobile('terminal')}
          className={`flex-1 py-3 text-xs font-mono text-center border-b-2 flex items-center justify-center space-x-1.5 ${
            activeTabMobile === 'terminal' ? 'border-[#10B981] text-[#10B981] bg-[#10B981]/5' : 'border-transparent text-gray-400'
          }`}
        >
          <TermIcon className="h-4 w-4" />
          <span>Terminal</span>
        </button>
        <button
          onClick={() => setActiveTabMobile('chat')}
          className={`flex-1 py-3 text-xs font-mono text-center border-b-2 flex items-center justify-center space-x-1.5 ${
            activeTabMobile === 'chat' ? 'border-[#10B981] text-[#10B981] bg-[#10B981]/5' : 'border-transparent text-gray-400'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          <span>Coéquipier</span>
        </button>
      </div>

      {/* Main Workspace (IDE-style 3 Columns) */}
      <div className="flex-1 flex min-h-0 relative overflow-hidden">
        
        {/* Column 1: Instructions */}
        <div className={`w-full md:w-[28%] md:flex flex-col border-r border-gray-850/60 bg-[#090D1A]/85 min-h-0 ${
          activeTabMobile === 'instructions' ? 'flex absolute inset-0 z-10' : 'hidden'
        }`}>
          <LevelInstructions level={selectedLevel} />
        </div>

        {/* Column 2: Terminal */}
        <div className={`w-full md:w-[48%] md:flex flex-col bg-[#030712] min-h-0 ${
          activeTabMobile === 'terminal' ? 'flex' : 'hidden md:flex'
        }`}>
          <Terminal gameId={gameId} levelIndex={selectedLevelIdx} />
        </div>

        {/* Column 3: Chat */}
        <div className={`w-full md:w-[24%] md:flex flex-col border-l border-gray-850/60 bg-[#090D1A]/85 min-h-0 ${
          activeTabMobile === 'chat' ? 'flex absolute inset-0 z-10' : 'hidden'
        }`}>
          <Chat gameId={gameId} />
        </div>

        {/* Celebratory success window overlay with dark glass background */}
        {validationResult && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-fade-in">
            <div className={`max-w-md w-full bg-[#090D1A]/95 p-8 rounded-2xl border text-center space-y-6 shadow-2xl relative overflow-hidden ${
              validationResult.success ? 'border-[#10B981] shadow-[0_0_40px_rgba(16,185,129,0.15)]' : 'border-red-500 shadow-[0_0_40px_rgba(239,68,68,0.15)]'
            }`}>
              {validationResult.success ? (
                <div className="mx-auto w-14 h-12 rounded-2xl bg-emerald-500/10 border border-[#10B981]/30 flex items-center justify-center text-[#10B981]">
                  <Award className="h-7 w-7 text-[#10B981]" />
                </div>
              ) : (
                <div className="mx-auto w-14 h-12 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-500">
                  <AlertCircle className="h-7 w-7 text-red-500" />
                </div>
              )}

              <div className="space-y-1.5">
                <h4 className="font-mono text-xl font-black text-white uppercase tracking-wider">
                  {validationResult.success ? "Mission Validée !" : "Validation Échouée"}
                </h4>
                {validationResult.success && (
                  <p className="text-[10px] bg-[#10B981]/15 text-[#10B981] px-2.5 py-1 rounded-full font-bold font-mono tracking-widest uppercase inline-block">
                    +{validationResult.points_earned} POINTS ACQUIS
                  </p>
                )}
              </div>

              <p className="text-xs text-gray-300 font-mono whitespace-pre-wrap leading-relaxed px-2">
                {validationResult.message}
              </p>

              <div className="pt-3">
                <button
                  onClick={() => setValidationResult(null)}
                  className={`w-full py-3 font-mono text-xs font-bold rounded-xl transition-all duration-200 ${
                    validationResult.success 
                      ? 'bg-[#10B981] hover:bg-emerald-500 text-black shadow-[0_4px_15px_rgba(16,185,129,0.3)]' 
                      : 'bg-red-500 hover:bg-red-600 text-white'
                  }`}
                >
                  {validationResult.success ? "Continuer vers le lab" : "Fermer & Réessayer"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
