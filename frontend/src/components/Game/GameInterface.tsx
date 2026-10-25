import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  ChevronLeft,
  CheckCircle2,
  Circle,
  Lock,
  Play,
  TerminalSquare,
  MessageSquare,
  Compass,
  RotateCcw,
  Trophy,
  Clock,
  AlertTriangle,
  X,
  ListChecks,
} from "lucide-react";
import { api } from "../../lib/api";
import { UserType } from "../../App";
import Terminal from "./Terminal";
import Chat from "./Chat";
import LevelInstructions, { LevelType } from "./LevelInstructions";

interface GameInterfaceProps {
  gameId: number;
  gameName: string;
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

type MobileTab = "mission" | "terminal" | "assistant";

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60).toString().padStart(2, "0");
  const s = (sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export default function GameInterface({ gameId, gameName, user, onBackToDashboard }: GameInterfaceProps) {
  const [levels, setLevels] = useState<LevelType[]>([]);
  const [selectedLevelIdx, setSelectedLevelIdx] = useState(0);
  const [activeTab, setActiveTab] = useState<MobileTab>("terminal");
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(600);
  const [resetKey, setResetKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [assistantOpen, setAssistantOpen] = useState(false);

  const fetchLevels = useCallback(async () => {
    try {
      const data = await api.get<LevelType[]>(`/api/games/${gameId}/levels`);
      setLevels(data);
      setLoading(false);
      const inProgress =
        data.find((l) => l.status === "available" || l.status === "in_progress") ?? data[0];
      if (inProgress) {
        setSelectedLevelIdx(inProgress.level_index);
        setTimeRemaining(inProgress.time_limit || 600);
      }
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    fetchLevels();
  }, [fetchLevels]);

  const selectedLevel = useMemo(
    () => levels.find((l) => l.level_index === selectedLevelIdx) ?? levels[0],
    [levels, selectedLevelIdx]
  );

  const completedCount = levels.filter((l) => l.status === "completed").length;
  const progress = levels.length ? Math.round((completedCount / levels.length) * 100) : 0;

  const selectLevel = (idx: number) => {
    const level = levels.find((l) => l.level_index === idx);
    if (!level || level.status === "locked") return;
    setSelectedLevelIdx(idx);
    setTimeRemaining(level.time_limit || 600);
    setValidationResult(null);
  };

  useEffect(() => {
    if (!selectedLevel) return;
    const interval = setInterval(() => {
      setTimeRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [selectedLevel?.level_index]);

  const handleValidate = async () => {
    if (!selectedLevel) return;
    setValidating(true);
    setValidationResult(null);
    try {
      const result = await api.post<ValidationResult>(
        `/api/games/${gameId}/levels/${selectedLevel.level_index}/validate`
      );
      setValidationResult(result);
      if (result.success) {
        await fetchLevels();
        if (result.next_level_index !== null) {
          setSelectedLevelIdx(result.next_level_index);
          const next = levels.find((l) => l.level_index === result.next_level_index);
          if (next) setTimeRemaining(next.time_limit || 600);
        }
      }
    } catch (err) {
      setValidationResult({
        success: false,
        message: err instanceof Error ? err.message : "Erreur de validation.",
        points_earned: 0,
        badge_unlocked: null,
        next_level_index: null,
      });
    } finally {
      setValidating(false);
    }
  };

  const handleReset = async () => {
    if (!selectedLevel) return;
    try {
      await api.post(`/api/games/${gameId}/levels/${selectedLevel.level_index}/reset`);
      setResetKey((k) => k + 1);
      setValidationResult(null);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-bg">
        <div className="text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="mt-4 font-mono text-[11px] uppercase tracking-widest text-muted">
            Chargement du laboratoire…
          </p>
        </div>
      </div>
    );
  }

  if (!levels.length || !selectedLevel) {
    return (
      <div className="flex h-full items-center justify-center bg-bg p-6">
        <div className="card max-w-md p-8 text-center">
          <AlertTriangle className="mx-auto h-8 w-8 text-warning" />
          <p className="mt-3 text-sm text-muted">
            Impossible de charger les niveaux de ce parcours.
          </p>
          <button onClick={onBackToDashboard} className="btn-secondary mt-5">
            <ChevronLeft className="h-4 w-4" /> Retour au tableau de bord
          </button>
        </div>
      </div>
    );
  }

  const levelUnlocked = selectedLevel.status !== "locked";

  return (
    <div className="flex h-full min-h-0 flex-col bg-bg">
      {/* ------------------------------ Topbar ------------------------------ */}
      <header className="shrink-0 border-b border-border bg-surface/70 backdrop-blur-xl">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-3 px-4 py-3 sm:px-5">
          <button onClick={onBackToDashboard} className="btn-ghost -ml-2 !px-2.5">
            <ChevronLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Retour</span>
          </button>

          <div className="hidden min-w-0 items-center gap-3 md:flex">
            <div className="min-w-0 leading-tight">
              <p className="truncate text-[13px] font-bold">{gameName}</p>
              <p className="font-mono text-[11px] text-muted">
                {completedCount}/{levels.length} défis · {progress}%
              </p>
            </div>
            <div className="h-8 w-px bg-border" />
          </div>

          {/* Level pills */}
          <nav className="flex min-w-0 flex-1 items-center gap-1.5 overflow-x-auto pb-0.5" aria-label="Liste des défis">
            {levels.map((l) => {
              const isCurrent = l.level_index === selectedLevel.level_index;
              const done = l.status === "completed";
              const locked = l.status === "locked";
              return (
                <button
                  key={l.id}
                  onClick={() => selectLevel(l.level_index)}
                  disabled={locked}
                  title={l.title}
                  className={`flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border font-mono text-[12px] font-bold transition-all duration-200 ${
                    isCurrent
                      ? "border-primary bg-primary/15 text-primary"
                      : done
                        ? "border-accent/40 bg-accent/10 text-accent hover:border-accent/70"
                        : locked
                          ? "cursor-not-allowed border-border bg-surface text-muted/40"
                          : "border-border bg-surface text-muted hover:border-muted/50 hover:text-fg"
                  }`}
                >
                  {done ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : locked ? (
                    <Lock className="h-3.5 w-3.5" />
                  ) : (
                    l.level_index + 1
                  )}
                </button>
              );
            })}
          </nav>

          <div className="flex items-center gap-2">
            <span
              className={`chip ${timeRemaining < 60 ? "border-warning/40 text-warning" : ""}`}
              title="Temps conseillé"
            >
              <Clock className="h-3 w-3" />
              {formatTime(timeRemaining)}
            </span>
            <button
              onClick={handleReset}
              className="btn-ghost !px-2.5"
              title="Réinitialiser l'environnement du défi"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
            <button
              onClick={() => setAssistantOpen(true)}
              className="btn-ghost hidden !px-2.5 lg:inline-flex xl:hidden"
              title="Ouvrir l'assistante Nemesis"
            >
              <MessageSquare className="h-4 w-4 text-primary" />
            </button>
            <button
              onClick={handleValidate}
              disabled={validating || !levelUnlocked}
              className="btn-primary"
            >
              {validating ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              ) : (
                <ListChecks className="h-4 w-4" />
              )}
              Valider
            </button>
          </div>
        </div>

        {/* progress bar */}
        <div className="h-0.5 w-full bg-border/50">
          <div
            className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </header>

      {/* Validation result banner */}
      {validationResult && (
        <div
          className={`shrink-0 animate-fade-up border-b px-4 py-3 sm:px-5 ${
            validationResult.success
              ? "border-accent/30 bg-accent/10"
              : "border-warning/30 bg-warning/10"
          }`}
        >
          <div className="mx-auto flex max-w-7xl items-start gap-3">
            {validationResult.success ? (
              <Trophy className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
            ) : (
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-warning" />
            )}
            <div className="min-w-0 flex-1 whitespace-pre-line text-sm leading-relaxed">
              {validationResult.message}
            </div>
            <button
              onClick={() => setValidationResult(null)}
              className="btn-ghost !p-1.5"
              aria-label="Fermer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* ------------------------------ Mobile tabs ------------------------------ */}
      <div className="flex shrink-0 gap-1 border-b border-border bg-surface/50 px-4 py-2 lg:hidden">
        {(
          [
            { id: "mission" as MobileTab, label: "Mission", icon: Compass },
            { id: "terminal" as MobileTab, label: "Terminal", icon: TerminalSquare },
            { id: "assistant" as MobileTab, label: "Nemesis", icon: MessageSquare },
          ]
        ).map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors duration-200 ${
              activeTab === t.id
                ? "bg-primary/15 text-primary"
                : "text-muted hover:bg-surface-2 hover:text-fg"
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* ------------------------------ Workspace ------------------------------ */}
      <div className="grid min-h-0 flex-1 gap-4 p-4 lg:grid-cols-[minmax(340px,380px)_1fr] xl:grid-cols-[minmax(340px,380px)_1fr_360px]">
        {/* Mission panel */}
        <section
          className={`card min-h-0 ${activeTab === "mission" ? "flex" : "hidden"} flex-col lg:flex`}
          aria-label="Mission du défi"
        >
          <LevelInstructions level={selectedLevel} />
        </section>

        {/* Terminal */}
        <section
          className={`min-h-0 ${activeTab === "terminal" ? "flex" : "hidden"} flex-col lg:flex`}
          aria-label="Terminal"
        >
          <Terminal
            key={`${gameId}-${selectedLevel.level_index}-${resetKey}`}
            gameId={gameId}
            levelIndex={selectedLevel.level_index}
            fontSize={user.preferences?.font_size || 14}
          />
        </section>

        {/* AI assistant (third column on xl+) */}
        <section
          className="min-h-0 hidden flex-col xl:flex"
          aria-label="Assistante IA"
        >
          <Chat gameId={gameId} levelIndex={selectedLevel.level_index} />
        </section>
      </div>

      {/* Assistant slide-over for the lg→xl range */}
      {assistantOpen && (
        <div className="fixed inset-0 z-50 hidden lg:block xl:hidden" role="dialog" aria-label="Assistante IA">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setAssistantOpen(false)}
          />
          <div className="absolute bottom-4 right-4 top-4 flex w-[400px] max-w-[calc(100vw-2rem)] flex-col">
            <Chat gameId={gameId} levelIndex={selectedLevel.level_index} />
          </div>
        </div>
      )}
    </div>
  );
}
