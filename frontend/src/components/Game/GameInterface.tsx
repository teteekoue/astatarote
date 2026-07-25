import React, { useState, useEffect } from 'react';
import { ChevronLeft, CheckCircle, HelpCircle, Send, Play, Terminal as TermIcon, MessageSquare, AlertCircle, Award, Compass, RefreshCw, Cpu, HardDrive, Shield, Activity, ShieldAlert } from 'lucide-react';
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

  // Timer simulation state
  const [timeRemaining, setTimeRemaining] = useState<number>(900);

  const fetchLevels = async () => {
    try {
      const res = await fetch(`/api/games/${gameId}/levels`);
      if (res.ok) {
        const data = await res.json();
        setLevels(data);
        
        const inProgress = data.find((l: LevelType) => l.status === 'available' || l.status === 'in_progress');
        if (inProgress) {
          setSelectedLevelIdx(inProgress.level_index);
          setTimeRemaining(inProgress.time_limit || 900);
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

  // Live countdown timer ticking simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

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
          message: "Échec de connexion ou erreur de script de validation.",
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
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#02040e] relative overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#10B981]/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="z-10 flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#10B981]"></div>
          <p className="font-mono text-gray-400 text-xs uppercase tracking-widest">Démarrage du conteneur d'exercice...</p>
        </div>
      </div>
    );
  }

  // Formatting seconds to MM:SS
  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#02040e] text-gray-200">
      
      {/* Top Header Section */}
      <div className="border-b border-gray-850/80 bg-[#060919] px-6 py-4.5 flex flex-wrap items-center justify-between gap-4 shrink-0 z-10 select-none shadow-[0_4px_25px_rgba(0,0,0,0.3)]">
        <div className="flex items-center space-x-4">
          <button 
            onClick={onBackToDashboard}
            className="p-2.5 bg-gray-900/40 hover:bg-gray-850 rounded-xl border border-gray-800 text-gray-400 hover:text-white transition-all shadow-md"
            title="Retour au Tableau de bord"
          >
            <ChevronLeft className="h-4.5 w-4.5" />
          </button>
          
          <div className="h-6 w-[1px] bg-gray-850 hidden sm:block"></div>
          
          {/* Level indicators */}
          <div className="flex items-center space-x-1.5 bg-gray-950/60 border border-gray-850/60 p-1 rounded-xl">
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
                      ? 'bg-gradient-to-r from-[#10B981]/25 to-emerald-500/10 text-[#10B981] border border-[#10B981]/40'
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
            className="px-5 py-2.5 bg-gradient-to-r from-[#10B981] to-emerald-500 hover:shadow-[0_0_20px_rgba(16,185,129,0.35)] disabled:opacity-50 text-black font-mono font-extrabold rounded-xl text-xs flex items-center space-x-2 transition-all duration-300 shadow-lg"
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
          <span>Nemesis IA</span>
        </button>
      </div>

      {/* Main Workspace (IDE-style 3 Columns: 1/4 - 1/2 - 1/4) */}
      <div className="flex-1 flex min-h-0 relative overflow-hidden">
        
        {/* Column 1: Instructions (1/4 width) */}
        <div className={`w-full md:w-[25%] md:flex flex-col border-r border-gray-850/60 bg-[#050816]/90 min-h-0 ${
          activeTabMobile === 'instructions' ? 'flex absolute inset-0 z-10' : 'hidden'
        }`}>
          <LevelInstructions level={selectedLevel} />
        </div>

        {/* Column 2: Terminal Workspace (1/2 width) */}
        <div className={`w-full md:w-[50%] md:flex flex-col bg-[#02040e] min-h-0 ${
          activeTabMobile === 'terminal' ? 'flex' : 'hidden md:flex'
        }`}>
          {/* Top 3/4: Terminal Sandbox */}
          <div className="h-[72%] flex flex-col min-h-0">
            <Terminal gameId={gameId} levelIndex={selectedLevelIdx} />
          </div>
          
          {/* Bottom 1/4: Telemetry Monitor Dashboard */}
          <div className="h-[28%] border-t border-gray-850 bg-[#050816]/95 flex flex-col min-h-0 p-5 select-none relative overflow-hidden shadow-[inset_0_4px_15px_rgba(0,0,0,0.4)]">
            {/* Ambient cyber light */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#10B981]/3 rounded-full blur-2xl pointer-events-none"></div>
            
            <div className="flex items-center justify-between border-b border-gray-850/60 pb-2.5 shrink-0">
              <span className="font-mono text-[10px] font-black text-[#10B981] uppercase tracking-[0.2em] flex items-center space-x-1.5">
                <Activity className="h-3.5 w-3.5 text-[#10B981] animate-pulse" />
                <span>Console de Télémétrie Cyber-Sandbox</span>
              </span>
              <span className="text-[9px] font-mono text-gray-500 font-bold uppercase tracking-wider">RESEAU: CHROMA_VIRTUAL</span>
            </div>

            <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-4 items-center min-h-0 py-3">
              {/* Telemetry Item 1 */}
              <div className="bg-gray-950/40 border border-gray-850/40 p-3 rounded-xl flex flex-col justify-center">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">TEMPS RESTANT</span>
                <span className="text-sm font-black font-mono text-amber-500 mt-0.5">{formatTimer(timeRemaining)}</span>
              </div>

              {/* Telemetry Item 2 */}
              <div className="bg-gray-950/40 border border-gray-850/40 p-3 rounded-xl flex flex-col justify-center">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">PROCESSEUR VM</span>
                <div className="flex items-center space-x-1.5 mt-0.5">
                  <Cpu className="h-3 w-3 text-emerald-400" />
                  <span className="text-xs font-bold font-mono text-gray-200">0.05% active</span>
                </div>
              </div>

              {/* Telemetry Item 3 */}
              <div className="bg-gray-950/40 border border-gray-850/40 p-3 rounded-xl flex flex-col justify-center">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">MÉMOIRE ALLOCUÉE</span>
                <div className="flex items-center space-x-1.5 mt-0.5">
                  <HardDrive className="h-3 w-3 text-blue-400" />
                  <span className="text-xs font-bold font-mono text-gray-200">24MB / 128MB</span>
                </div>
              </div>

              {/* Telemetry Item 4 */}
              <div className="bg-gray-950/40 border border-gray-850/40 p-3 rounded-xl flex flex-col justify-center">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">MULTIPLIER SCORE</span>
                <div className="flex items-center space-x-1.5 mt-0.5">
                  <Shield className="h-3 w-3 text-amber-400" />
                  <span className="text-xs font-black font-mono text-amber-500">1.25x Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 3: Nemesis AI Chat Panel (1/4 width) */}
        <div className={`w-full md:w-[25%] md:flex flex-col border-l border-gray-850/60 bg-[#050816]/90 min-h-0 ${
          activeTabMobile === 'chat' ? 'flex absolute inset-0 z-10' : 'hidden'
        }`}>
          <Chat gameId={gameId} />
        </div>

        {/* Validation Celebration/Failure Overlay - Designed like a God */}
        {validationResult && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4 animate-fade-in select-none">
            <div className={`max-w-md w-full bg-[#050816]/95 p-8 rounded-3xl border text-center space-y-6 shadow-[0_0_50px_rgba(0,0,0,0.8)] relative overflow-hidden ${
              validationResult.success 
                ? 'border-[#10B981] shadow-[0_0_40px_rgba(16,185,129,0.15)]' 
                : 'border-red-500 shadow-[0_0_40px_rgba(239,68,68,0.15)]'
            }`}>
              {/* Background ambient circular light */}
              <div className={`absolute top-0 inset-x-0 mx-auto w-32 h-32 rounded-full blur-2xl pointer-events-none ${
                validationResult.success ? 'bg-[#10B981]/10' : 'bg-red-500/10'
              }`}></div>

              {validationResult.success ? (
                <>
                  <div className="mx-auto w-16 h-14 rounded-2xl bg-emerald-500/10 border border-[#10B981]/30 flex items-center justify-center text-[#10B981] shadow-[0_0_20px_rgba(16,185,129,0.1)]">
                    <Award className="h-8 w-8 text-[#10B981] animate-pulse" />
                  </div>

                  <div className="space-y-1.5">
                    <h4 className="font-mono text-xl font-black text-white uppercase tracking-[0.1em] text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">
                      MISSION ACCOMPLIE !
                    </h4>
                    <p className="text-[10px] bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/25 px-3 py-1 rounded-full font-black font-mono tracking-widest uppercase inline-block">
                      +{validationResult.points_earned} POINTS CRÉDITÉS
                    </p>
                  </div>

                  <p className="text-xs text-gray-300 font-mono whitespace-pre-wrap leading-relaxed px-2">
                    {validationResult.message}
                  </p>

                  <div className="pt-3">
                    <button
                      onClick={() => setValidationResult(null)}
                      className="w-full py-3.5 bg-gradient-to-r from-[#10B981] to-emerald-500 hover:shadow-[0_4px_15px_rgba(16,185,129,0.3)] text-black font-mono font-black text-xs rounded-xl transition-all duration-300"
                    >
                      CONTINUER VERS LE PROCHAIN LAB
                    </button>
                  </div>
                </>
              ) : (
                <>
                  {/* FAILURE / DETECTED ERRORS SCENARIO PANEL */}
                  <div className="mx-auto w-16 h-14 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-500 shadow-[0_0_20px_rgba(239,68,68,0.1)]">
                    <ShieldAlert className="h-8 w-8 text-red-500 animate-pulse" />
                  </div>

                  <div className="space-y-1.5">
                    <h4 className="font-mono text-xl font-black text-red-500 uppercase tracking-[0.1em]">
                      ÉCHEC DE VÉRIFICATION
                    </h4>
                    <p className="text-[9px] bg-red-500/10 text-red-400 border border-red-500/20 px-2.5 py-1 rounded-full font-black font-mono tracking-widest uppercase inline-block">
                      AUDIT SYSTÈME INVALIDE
                    </p>
                  </div>

                  <div className="text-left bg-black/40 border border-gray-850 p-4 rounded-xl space-y-2 font-mono text-[11px] text-gray-300 leading-relaxed max-h-[140px] overflow-y-auto">
                    <p className="text-red-400 font-bold">⚠️ Failles détectées :</p>
                    <p className="whitespace-pre-wrap">{validationResult.message}</p>
                  </div>

                  <div className="p-3.5 bg-indigo-500/5 border border-indigo-500/15 rounded-xl text-left space-y-1 select-text">
                    <p className="text-indigo-400 font-bold font-mono text-[10px] uppercase tracking-wider">💡 Conseil d'apprentissage :</p>
                    <p className="text-[10px] text-gray-400 font-mono leading-relaxed">
                      L'état de la sandbox n'est pas encore conforme. Veuillez consulter la section <strong className="text-gray-200">"Support Technique"</strong> dans l'onglet de gauche pour étudier les commandes recommandées ou demandez des explications directes à l'assistant <strong className="text-[#10B981]">Nemesis</strong> dans le chat.
                    </p>
                  </div>

                  <div className="pt-3">
                    <button
                      onClick={() => setValidationResult(null)}
                      className="w-full py-3.5 bg-gray-900 hover:bg-gray-850 text-gray-300 border border-gray-800 font-mono font-bold text-xs rounded-xl transition-all duration-200"
                    >
                      CORRIGER MON CODE DANS LE TTY
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
