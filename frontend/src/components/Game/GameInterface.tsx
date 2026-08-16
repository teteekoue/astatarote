import React, { useState, useEffect, useCallback } from "react";
import {
  ChevronLeft,
  CheckCircle,
  Terminal as TermIcon,
  MessageSquare,
  Award,
  Compass,
  RotateCcw,
  Cpu,
  Activity,
  ShieldAlert,
  Gauge,
  Trophy,
} from "lucide-react";
import { api } from "../../lib/api";
import { UserType } from "../../App";
import Terminal from "./Terminal";
import Chat from "./Chat";
import LevelInstructions from "./LevelInstructions";

export interface FileCheck {
  path: string;
  perms?: string;
  content_contains?: string;
  content_not_contains?: string;
}

export interface LevelType {
  id: number;
  game_id: number;
  level_index: number;
  title: string;
  description: string;
  objective: string;
  situation_probleme?: string | null;
  consigne?: string | null;
  support_technique?: string | null;
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

interface GameInterfaceProps {
  gameId: number;
  user: UserType;
  onBackToDashboard: () => void;
}

interface ValidationResult {
  success: boolean;
  message: string;
  points_earned: number;
  badge_unlocked: string | null;
  next_level_index: number | null;
}

export default function GameInterface({ gameId, user, onBackToDashboard }: GameInterfaceProps) {
  const [levels, setLevels] = useState<LevelType[]>([]);
  const [selectedLevelIdx, setSelectedLevelIdx] = useState<number>(0);
  const [activeTabMobile, setActiveTabMobile] = useState<"instructions" | "terminal" | "chat">("terminal");
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(600);
  const [sessionStartedAt, setSessionStartedAt] = useState<Date | null>(null);

  const fetchLevels = useCallback(async () => {
    try {
      const data = await api.get<LevelType[]>(`/api/games/${gameId}/levels`);
      setLevels(data);
      const inProgress = data.find(
        (l) => l.status === "available" || l.status === "in_progress"
      );
      const target = inProgress ?? data[0];
      if (target) {
        setSelectedLevelIdx(target.level_index);
        setTimeRemaining(target.time_limit || 600);
      }
      setSessionStartedAt(new Date());
    } catch (err) {
      console.error(err);
    }
  }, [gameId]);

  useEffect(() => {
    fetchLevels();
  }, [fetchLevels]);

  // Real countdown based on level time limit
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleValidateLevel = async () => {
    setValidating(true);
    setValidationResult(null);
    try {
      const result = await api.post<ValidationResult>(
        `/api/games/${gameId}/levels/${selectedLevelIdx}/validate`
      );
      setValidationResult(result);
      if (result.success) {
        await fetchLevels();
      }
    } catch (err) {
      setValidationResult({
        success: false,
        message: err instanceof Error ? err.message : "Erreur lors de la validation.",
        points_earned: 0,
        badge_unlocked: null,
        next_level_index: null,
      });
    } finally {
      setValidating(false);
    }
  };

  const handleResetLevel = async () => {
    try {
      await api.post(`/api/games/${gameId}/levels/${selectedLevelIdx}/reset`);
      setValidationResult(null);
      setSessionStartedAt(new Date());
    } catch (err) {
      console.error(err);
    }
  };

  const selectedLevel = levels.find((l) => l.level_index === selectedLevelIdx);

  if (levels.length === 0 || !selectedLevel) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-ink-base relative overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-asta-green/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="z-10 flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-asta-green"></div>
          <p className="font-mono text-gray-400 text-xs uppercase tracking-widest">
            Provisionnement de la sandbox...
          </p>
        </div>
      </div>
    );
  }

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const sessionMinutes = sessionStartedAt
    ? Math.max(0, Math.floor((Date.now() - sessionStartedAt.getTime()) / 60000))
    : 0;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-ink-base text-gray-200">
      {/* Top bar */}
      <div className="border-b border-ink-line bg-ink-panel/80 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 shrink-0 z-10 shadow-card">
        <div className="flex items-center gap-4">
          <button
            onClick={onBackToDashboard}
            className="p-2.5 bg-ink-deep/60 hover:bg-ink-deep rounded-xl border border-ink-line text-gray-400 hover:text-white transition-all"
            title="Retour au tableau de bord"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          <div className="h-6 w-px bg-ink-line hidden sm:block"></div>

          {/* Level tabs */}
          <div className="flex items-center gap-1.5 bg-ink-deep/60 border border-ink-line/70 p-1 rounded-xl">
            {levels.map((lvl) => {
              const isLocked = lvl.status === "locked";
              const isCompleted = lvl.status === "completed";
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
                      ? "bg-asta-green/20 text-asta-green border border-asta-green/40"
                      : isCompleted
                      ? "bg-emerald-950/30 text-emerald-400 border border-emerald-900/30 hover:bg-emerald-900/20"
                      : isLocked
                      ? "opacity-30 bg-transparent text-gray-600 border border-transparent cursor-not-allowed"
                      : "bg-transparent text-gray-400 border border-transparent hover:bg-ink-deep/40"
                  }`}
                >
                  DÉFI {lvl.level_index + 1}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleResetLevel}
            title="Réinitialiser la sandbox du niveau"
            className="p-2.5 bg-ink-deep/60 hover:bg-ink-deep rounded-xl border border-ink-line text-gray-400 hover:text-asta-amber transition-all"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
          <button
            onClick={handleValidateLevel}
            disabled={validating}
            className="px-5 py-2.5 bg-gradient-to-r from-asta-green to-emerald-500 hover:shadow-glow disabled:opacity-50 text-black font-mono font-extrabold rounded-xl text-xs flex items-center gap-2 transition-all duration-300 shadow-lg"
          >
            {validating ? (
              <span className="inline-block h-3.5 w-3.5 animate-spin border-2 border-black border-t-transparent rounded-full"></span>
            ) : (
              <CheckCircle className="h-4 w-4" />
            )}
            <span>Valider la mission</span>
          </button>
        </div>
      </div>

      {/* Mobile tab nav */}
      <div className="md:hidden flex border-b border-ink-line bg-ink-panel/50">
        <button
          onClick={() => setActiveTabMobile("instructions")}
          className={`flex-1 py-3 text-xs font-mono text-center border-b-2 flex items-center justify-center gap-1.5 ${
            activeTabMobile === "instructions" ? "border-asta-green text-asta-green bg-asta-green/5" : "border-transparent text-gray-400"
          }`}
        >
          <Compass className="h-4 w-4" />
          Consignes
        </button>
        <button
          onClick={() => setActiveTabMobile("terminal")}
          className={`flex-1 py-3 text-xs font-mono text-center border-b-2 flex items-center justify-center gap-1.5 ${
            activeTabMobile === "terminal" ? "border-asta-green text-asta-green bg-asta-green/5" : "border-transparent text-gray-400"
          }`}
        >
          <TermIcon className="h-4 w-4" />
          Terminal
        </button>
        <button
          onClick={() => setActiveTabMobile("chat")}
          className={`flex-1 py-3 text-xs font-mono text-center border-b-2 flex items-center justify-center gap-1.5 ${
            activeTabMobile === "chat" ? "border-asta-green text-asta-green bg-asta-green/5" : "border-transparent text-gray-400"
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Nemesis
        </button>
      </div>

      {/* Main workspace */}
      <div className="flex-1 flex min-h-0 relative overflow-hidden">
        {/* Column 1: Instructions */}
        <div
          className={`w-full md:w-[26%] md:flex flex-col border-r border-ink-line/60 bg-ink-deep/40 min-h-0 min-w-0 ${
            activeTabMobile === "instructions" ? "flex absolute inset-0 z-10" : "hidden"
          }`}
        >
          <LevelInstructions level={selectedLevel} />
        </div>

        {/* Column 2: Terminal + telemetry */}
        <div
          className={`w-full md:w-[48%] md:flex flex-col bg-ink-base min-h-0 min-w-0 ${
            activeTabMobile === "terminal" ? "flex" : "hidden md:flex"
          }`}
        >
          <div className="flex-1 flex flex-col min-h-0 min-w-0">
            <Terminal gameId={gameId} levelIndex={selectedLevelIdx} fontSize={user.preferences.font_size || 14} />
          </div>

          {/* Real telemetry strip */}
          <div className="h-[110px] border-t border-ink-line bg-ink-deep/50 flex flex-col min-h-0 p-4 select-none relative overflow-hidden shrink-0">
            <div className="flex items-center justify-between border-b border-ink-line/50 pb-2 shrink-0">
              <span className="font-mono text-[10px] font-black text-asta-green uppercase tracking-[0.2em] flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5 animate-pulse-glow" />
                Télémétrie de la sandbox
              </span>
              <span className="text-[9px] font-mono text-gray-500 font-bold uppercase tracking-wider">
                Défi {selectedLevel.level_index + 1} / {levels.length}
              </span>
            </div>

            <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-3 items-center min-h-0 py-2">
              <div className="bg-ink-panel/60 border border-ink-line/60 p-2.5 rounded-xl">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">Temps restant</span>
                <span className="text-base font-black font-mono text-asta-amber mt-0.5 block">{formatTimer(timeRemaining)}</span>
              </div>
              <div className="bg-ink-panel/60 border border-ink-line/60 p-2.5 rounded-xl">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">Points en jeu</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Trophy className="h-3.5 w-3.5 text-asta-green" />
                  <span className="text-base font-black font-mono text-asta-green">{selectedLevel.points}</span>
                </div>
              </div>
              <div className="bg-ink-panel/60 border border-ink-line/60 p-2.5 rounded-xl">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">Difficulté</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Gauge className="h-3.5 w-3.5 text-asta-violet" />
                  <span className="text-base font-black font-mono text-asta-violet">{selectedLevel.difficulty}/10</span>
                </div>
              </div>
              <div className="bg-ink-panel/60 border border-ink-line/60 p-2.5 rounded-xl">
                <span className="text-[8px] text-gray-500 font-mono font-bold uppercase tracking-widest">Session</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Cpu className="h-3.5 w-3.5 text-asta-cyan" />
                  <span className="text-base font-black font-mono text-asta-cyan">{sessionMinutes} min</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 3: Chat */}
        <div
          className={`w-full md:w-[26%] md:flex flex-col border-l border-ink-line/60 bg-ink-deep/40 min-h-0 min-w-0 ${
            activeTabMobile === "chat" ? "flex absolute inset-0 z-10" : "hidden"
          }`}
        >
          <Chat gameId={gameId} />
        </div>

        {/* Validation overlay */}
        {validationResult && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4 animate-fade-in select-none">
            <div
              className={`max-w-md w-full bg-ink-panel/95 p-8 rounded-3xl border text-center space-y-6 shadow-card relative overflow-hidden ${
                validationResult.success
                  ? "border-asta-green shadow-glow"
                  : "border-red-500"
              }`}
            >
              <div
                className={`absolute top-0 inset-x-0 mx-auto w-32 h-32 rounded-full blur-2xl pointer-events-none ${
                  validationResult.success ? "bg-asta-green/10" : "bg-red-500/10"
                }`}
              ></div>

              {validationResult.success ? (
                <>
                  <div className="mx-auto w-16 h-14 rounded-2xl bg-emerald-500/10 border border-asta-green/30 flex items-center justify-center text-asta-green shadow-glow">
                    <Award className="h-8 w-8 animate-pulse-glow" />
                  </div>
                  <div className="space-y-1.5">
                    <h4 className="font-display text-xl font-black text-white uppercase tracking-widest">
                      MISSION ACCOMPLIE
                    </h4>
                    <p className="text-[10px] bg-asta-green/15 text-asta-green border border-asta-green/25 px-3 py-1 rounded-full font-black font-mono tracking-widest uppercase inline-block">
                      +{validationResult.points_earned} points crédités
                    </p>
                  </div>
                  <p className="text-xs text-gray-300 font-mono whitespace-pre-wrap leading-relaxed px-2">
                    {validationResult.message}
                  </p>
                  <button onClick={() => setValidationResult(null)} className="btn-primary w-full !py-3.5">
                    Continuer
                  </button>
                </>
              ) : (
                <>
                  <div className="mx-auto w-16 h-14 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-500">
                    <ShieldAlert className="h-8 w-8 animate-pulse-glow" />
                  </div>
                  <div className="space-y-1.5">
                    <h4 className="font-display text-xl font-black text-red-500 uppercase tracking-widest">
                      ÉCHEC DE VÉRIFICATION
                    </h4>
                    <p className="text-[9px] bg-red-500/10 text-red-400 border border-red-500/20 px-2.5 py-1 rounded-full font-black font-mono tracking-widest uppercase inline-block">
                      AUDIT SYSTÈME INVALIDE
                    </p>
                  </div>
                  <div className="text-left bg-ink-deep/60 border border-ink-line p-4 rounded-xl space-y-2 font-mono text-[11px] text-gray-300 leading-relaxed max-h-[140px] overflow-y-auto">
                    <p className="text-red-400 font-bold">Failles détectées :</p>
                    <p className="whitespace-pre-wrap">{validationResult.message}</p>
                  </div>
                  <div className="p-3.5 bg-indigo-500/5 border border-indigo-500/15 rounded-xl text-left space-y-1 select-text">
                    <p className="text-indigo-400 font-bold font-mono text-[10px] uppercase tracking-wider">
                      Conseil d'apprentissage
                    </p>
                    <p className="text-[10px] text-gray-400 font-mono leading-relaxed">
                      L'état de la sandbox n'est pas encore conforme. Relis la{" "}
                      <strong className="text-gray-200">consigne</strong> et le{" "}
                      <strong className="text-gray-200">support technique</strong>, ou demande une piste à{" "}
                      <strong className="text-asta-green">Nemesis</strong>.
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setValidationResult(null)} className="btn-ghost flex-1 !py-3">
                      Corriger dans le terminal
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
