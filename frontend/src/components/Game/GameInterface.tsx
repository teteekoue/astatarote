import React, { useState, useEffect } from 'react';
import { ChevronLeft, CheckCircle, HelpCircle, Send, Play, Terminal as TermIcon, MessageSquare, AlertCircle, Award } from 'lucide-react';
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
        
        # Default to the current game level
        const inProgress = data.find((l: LevelType) => l.status === 'available' || l.status === 'in_progress');
        if (inProgress) {
          setSelectedLevelIdx(inProgress.level_index);
        } else {
          // If all completed or none in progress, select last or first
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
          // Re-fetch levels to update completion and locks
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
      <div className="flex-1 flex flex-col items-center justify-center font-mono">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#10B981] mb-2"></div>
        <p className="text-gray-400 text-xs">Chargement de votre sandbox...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#070A13] text-gray-200">
      
      {/* Top action bar */}
      <div className="border-b border-gray-800 bg-[#0B0F19] px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center space-x-3">
          <button 
            onClick={onBackToDashboard}
            className="p-1.5 hover:bg-gray-850 rounded-lg text-gray-400 hover:text-white transition"
            title="Retour au dashboard"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <div className="h-4 w-[1px] bg-gray-800 hidden sm:block"></div>
          
          {/* Level Selector */}
          <div className="flex items-center space-x-1">
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
                  className={`px-3 py-1 rounded text-xs font-mono font-bold border transition ${
                    isSelected
                      ? 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/60'
                      : isCompleted
                      ? 'bg-emerald-950/20 text-emerald-500 border-emerald-900 hover:bg-emerald-900/10'
                      : isLocked
                      ? 'opacity-40 bg-gray-950 text-gray-600 border-gray-900 cursor-not-allowed'
                      : 'bg-gray-900 text-gray-400 border-gray-800 hover:bg-gray-850'
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
            className="px-4 py-1.5 bg-[#10B981] hover:bg-emerald-600 disabled:opacity-50 text-black font-mono font-bold rounded-lg text-xs flex items-center space-x-1.5 shadow-md transition"
          >
            {validating ? (
              <span className="inline-block h-3.5 w-3.5 animate-spin border-2 border-black border-t-transparent rounded-full"></span>
            ) : (
              <CheckCircle className="h-4 w-4" />
            )}
            <span>Soumettre la Solution</span>
          </button>
        </div>
      </div>

      {/* Mobile Tab bar */}
      <div className="md:hidden flex border-b border-gray-850 bg-gray-950">
        <button
          onClick={() => setActiveTabMobile('instructions')}
          className={`flex-1 py-3 text-xs font-mono text-center border-b-2 flex items-center justify-center space-x-1.5 ${
            activeTabMobile === 'instructions' ? 'border-[#10B981] text-[#10B981] bg-[#10B981]/5' : 'border-transparent text-gray-400'
          }`}
        >
          <HelpCircle className="h-4 w-4" />
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

      {/* Main 3-Column Workspace */}
      <div className="flex-1 flex min-h-0 relative">
        
        {/* Column 1: Instructions (Zone 1) */}
        <div className={`w-full md:w-[28%] md:flex flex-col border-r border-gray-800 bg-[#0B0F19] min-h-0 ${
          activeTabMobile === 'instructions' ? 'flex absolute inset-0 z-10' : 'hidden'
        }`}>
          <LevelInstructions level={selectedLevel} />
        </div>

        {/* Column 2: Terminal (Zone 2) */}
        <div className={`w-full md:w-[48%] md:flex flex-col bg-gray-950 min-h-0 ${
          activeTabMobile === 'terminal' ? 'flex' : 'hidden md:flex'
        }`}>
          <Terminal gameId={gameId} levelIndex={selectedLevelIdx} />
        </div>

        {/* Column 3: Pedagogical Chat (Zone 3) */}
        <div className={`w-full md:w-[24%] md:flex flex-col border-l border-gray-800 bg-[#0B0F19] min-h-0 ${
          activeTabMobile === 'chat' ? 'flex absolute inset-0 z-10' : 'hidden'
        }`}>
          <Chat gameId={gameId} />
        </div>

        {/* Celebratory Overlay for level validation success / failure */}
        {validationResult && (
          <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
            <div className={`max-w-md w-full bg-[#111827] p-8 rounded-2xl border text-center space-y-5 shadow-2xl transition duration-300 ${
              validationResult.success ? 'border-[#10B981] neon-border' : 'border-red-500 neon-border-red'
            }`}>
              {validationResult.success ? (
                <div className="mx-auto w-12 h-12 rounded-full bg-emerald-500/10 border border-[#10B981]/30 flex items-center justify-center text-[#10B981]">
                  <Award className="h-6 w-6 text-[#10B981]" />
                </div>
              ) : (
                <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
                  <AlertCircle className="h-6 w-6 text-red-500" />
                </div>
              )}

              <div className="space-y-1">
                <h4 className="font-mono text-lg font-bold text-white uppercase tracking-wider">
                  {validationResult.success ? "Mission Validée !" : "Validation Échouée"}
                </h4>
                {validationResult.success && (
                  <p className="text-xs text-[#10B981] font-mono">+{validationResult.points_earned} POINTS ACQUIS</p>
                )}
              </div>

              <p className="text-sm text-gray-300 font-mono whitespace-pre-wrap leading-relaxed">
                {validationResult.message}
              </p>

              <div className="pt-2">
                <button
                  onClick={() => setValidationResult(null)}
                  className={`w-full py-2.5 font-mono text-xs font-bold rounded-xl transition ${
                    validationResult.success 
                      ? 'bg-[#10B981] hover:bg-emerald-600 text-black' 
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
