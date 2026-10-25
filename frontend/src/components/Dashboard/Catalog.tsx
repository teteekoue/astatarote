import React, { useEffect, useState } from "react";
import {
  Clock,
  Play,
  Loader2,
  CheckCircle2,
  ChevronRight,
  Compass,
  Layers,
  Zap,
  ArrowRight,
} from "lucide-react";
import { api, CatalogGame } from "../../lib/api";

interface CatalogProps {
  onPlayGame: (gameId: number, gameName: string) => void;
}

const DOMAIN_LABEL: Record<string, string> = {
  linux: "Linux",
  network: "Réseau",
  security: "Sécurité",
};

const LEVEL_LABEL: Record<string, string> = {
  beginner: "Débutant",
  intermediate: "Intermédiaire",
  advanced: "Avancé",
};

function DifficultyBar({ value }: { value: number }) {
  return (
    <span className="flex items-center gap-1" title={`Difficulté ${value}/5`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={`h-1 w-4 rounded-full ${i < value ? "bg-primary" : "bg-border"}`}
        />
      ))}
    </span>
  );
}

export default function Catalog({ onPlayGame }: CatalogProps) {
  const [courses, setCourses] = useState<CatalogGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<CatalogGame[]>("/api/catalog")
      .then((data) => {
        setCourses(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Erreur de chargement.");
        setLoading(false);
      });
  }, []);

  const start = async (slug: string) => {
    setStarting(slug);
    setError(null);
    try {
      const game = await api.post<{ id: number; name: string }>("/api/games", {
        catalog_slug: slug,
      });
      onPlayGame(game.id, game.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de démarrer le parcours.");
      setStarting(null);
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 p-4 py-8 sm:px-6 lg:py-10">
      <div>
        <p className="section-title">Catalogue</p>
        <h1 className="mt-1.5 text-2xl font-extrabold tracking-tight sm:text-3xl">
          Parcours d'apprentissage
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">
          Des parcours <strong className="text-fg">figés et vérifiés</strong>, rédigés à la
          main par l'équipe Astatarote. Chaque défi se joue dans le terminal simulé, avec
          l'assistante Nemesis à vos côtés.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-5 md:grid-cols-2">
          {[0, 1].map((i) => (
            <div key={i} className="card h-64 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {courses.map((course) => (
            <article
              key={course.slug}
              className="card flex flex-col p-6 transition-all duration-300 hover:-translate-y-1 hover:border-primary/40"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10">
                  <Compass className="h-5 w-5 text-primary" />
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <span className="chip">{DOMAIN_LABEL[course.domain] ?? course.domain}</span>
                  <span className="chip">{LEVEL_LABEL[course.level] ?? course.level}</span>
                </div>
              </div>

              <h2 className="mt-4 text-lg font-bold">{course.name}</h2>
              <p className="mt-1 text-sm text-muted">{course.tagline}</p>
              <p className="mt-3 line-clamp-3 text-[13px] leading-relaxed text-muted">
                {course.description}
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className="chip">
                  <Layers className="h-3 w-3" /> {course.total_levels} défis
                </span>
                <span className="chip">
                  <Clock className="h-3 w-3" /> ~{course.duration_minutes} min
                </span>
                <span className="chip">
                  <Zap className="h-3 w-3" /> {course.total_points} pts
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-1.5">
                {course.skills.slice(0, 4).map((skill) => (
                  <span
                    key={skill}
                    className="rounded-lg bg-surface-2/70 px-2 py-1 text-[11.5px] text-muted"
                  >
                    {skill}
                  </span>
                ))}
              </div>

              <div className="mt-auto pt-5">
                <div className="mb-3 flex items-center justify-between">
                  <DifficultyBar value={course.difficulty} />
                  <span className="font-mono text-[11px] text-muted">v{course.version}</span>
                </div>
                {course.enrolled && course.enrollment ? (
                  <button
                    onClick={() =>
                      onPlayGame(course.enrollment!.id, course.enrollment!.name)
                    }
                    className="btn-secondary w-full"
                  >
                    {course.enrollment.status === "completed" ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-accent" /> Parcours terminé — rejouer
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Continuer — {Math.round(course.enrollment.progress)}%
                        <ChevronRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    onClick={() => start(course.slug)}
                    disabled={starting === course.slug}
                    className="btn-primary w-full"
                  >
                    {starting === course.slug ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        Commencer
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                )}
              </div>
            </article>
          ))}

          {courses.length === 0 && !loading && (
            <div className="card col-span-full p-10 text-center text-sm text-muted">
              Aucun parcours disponible pour l'instant. De nouveaux parcours figés
              arrivent bientôt.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
