import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  TerminalSquare,
  Sparkles,
  Lock,
  Trophy,
  ArrowRight,
  CheckCircle2,
  BookOpen,
  Cpu,
  GraduationCap,
} from "lucide-react";
import { api, CatalogGame } from "../lib/api";
import { isAuthenticated } from "../lib/auth";

const FEATURES = [
  {
    icon: TerminalSquare,
    title: "Terminal Linux simulé",
    text: "Un moteur déterministe reproduit le comportement réel de bash et de 45+ commandes GNU. Aucune VM, aucun risque, aucune ressource gaspillée.",
  },
  {
    icon: Lock,
    title: "Parcours figés & vérifiés",
    text: "Chaque défi est rédigé et testé à la main. Fini les exercices hallucinés par une IA : ici, tout est cohérent et solvable.",
  },
  {
    icon: Sparkles,
    title: "Assistante IA pédagogique",
    text: "Nemesis vous accompagne en direct : elle explique les concepts, décrypte vos erreurs et donne des indices progressifs — jamais la solution.",
  },
  {
    icon: Trophy,
    title: "Progression gamifiée",
    text: "Points, grades (Novice → Maître) et badges de spécialisation récompensent chaque défi validé.",
  },
  {
    icon: ShieldCheck,
    title: "Éthique by design",
    text: "Apprentissage offensif et défensif dans un environnement entièrement isolé. Rien ne sort du laboratoire.",
  },
  {
    icon: GraduationCap,
    title: "Du concret, tout de suite",
    text: "Navigation, permissions, processus, analyse de logs, réponse à incident : des compétences directement transférables en production.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Créez votre compte",
    text: "30 secondes suffisent. Aucune installation, aucune configuration.",
  },
  {
    n: "02",
    title: "Choisissez un parcours",
    text: "Un catalogue de défis figés, du premier pwd jusqu'à la gestion d'incident.",
  },
  {
    n: "03",
    title: "Pratiquez dans le terminal",
    text: "Résolvez des missions réalistes, validez vos acquis, montez en grade.",
  },
];

export default function Landing({ onEnter }: { onEnter: () => void }) {
  const [catalog, setCatalog] = useState<CatalogGame[]>([]);

  useEffect(() => {
    api
      .get<CatalogGame[]>("/api/catalog")
      .then(setCatalog)
      .catch(() => setCatalog([]));
  }, []);

  const cta = isAuthenticated() ? "Ouvrir mon espace" : "Commencer gratuitement";

  return (
    <div className="min-h-screen bg-bg text-fg">
      {/* ------------------------------ Nav ------------------------------ */}
      <header className="sticky top-0 z-40 border-b border-border/70 bg-bg/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <a href="#" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-primary/30 bg-primary/10">
              <ShieldCheck className="h-5 w-5 text-primary" />
            </div>
            <div className="leading-tight">
              <span className="block text-[15px] font-extrabold tracking-tight">Astatarote</span>
              <span className="block font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
                Linux & Cyber Lab
              </span>
            </div>
          </a>
          <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
            <a href="#features" className="transition-colors hover:text-fg">Fonctionnalités</a>
            <a href="#parcours" className="transition-colors hover:text-fg">Parcours</a>
            <a href="#how" className="transition-colors hover:text-fg">Comment ça marche</a>
          </nav>
          <button onClick={onEnter} className="btn-primary">
            {isAuthenticated() ? "Mon espace" : "Se connecter"}
          </button>
        </div>
      </header>

      {/* ------------------------------ Hero ------------------------------ */}
      <section className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 opacity-60"
          style={{
            background:
              "radial-gradient(600px circle at 20% -10%, rgba(99,102,241,0.16), transparent 60%), radial-gradient(500px circle at 85% 20%, rgba(16,185,129,0.08), transparent 60%)",
          }}
        />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-2">
          <div className="animate-fade-up">
            <div className="chip mb-6">
              <Sparkles className="h-3 w-3 text-accent" />
              Nouveau · moteur de terminal déterministe
            </div>
            <h1 className="text-balance text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl">
              Maîtrisez Linux en{" "}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                pratiquant
              </span>{" "}
              pour de vrai.
            </h1>
            <p className="mt-5 max-w-lg text-pretty text-[17px] leading-relaxed text-muted">
              Astatarote vous plonge dans des scénarios d'administration système et de
              cybersécurité réalistes. Un terminal Linux simulé, des défis conçus à la
              main, une assistante IA à vos côtés — directement dans votre navigateur.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <button onClick={onEnter} className="btn-primary px-6 py-3 text-[15px]">
                {cta}
                <ArrowRight className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-2 text-sm text-muted">
                <CheckCircle2 className="h-4 w-4 text-accent" />
                Gratuit pendant la bêta — sans carte bancaire
              </div>
            </div>
            <div className="mt-8 flex flex-wrap gap-x-8 gap-y-3 text-[13px] text-muted">
              <span className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-primary" /> {catalog.length || "—"} parcours figés
              </span>
              <span className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-primary" /> 45+ commandes simulées
              </span>
              <span className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-primary" /> 100% navigateur
              </span>
            </div>
          </div>

          {/* Terminal mock */}
          <div className="animate-fade-up [animation-delay:120ms]">
            <div className="card overflow-hidden shadow-pop">
              <div className="flex items-center gap-2 border-b border-border bg-surface-2/50 px-4 py-3">
                <span className="h-3 w-3 rounded-full bg-danger/80" />
                <span className="h-3 w-3 rounded-full bg-warning/80" />
                <span className="h-3 w-3 rounded-full bg-accent/80" />
                <span className="ml-3 font-mono text-[11px] text-muted">user@meridian: ~/incident</span>
              </div>
              <div className="space-y-1.5 p-5 font-mono text-[13px] leading-relaxed">
                <p className="text-muted">$ <span className="text-fg">ps aux | grep backdoor</span></p>
                <p className="text-fg/80">user  2387  0.9  /var/tmp/.hidden_service/backdoor.sh</p>
                <p className="text-muted">$ <span className="text-fg">kill -9 2387</span></p>
                <p className="text-muted">$ <span className="text-fg">mv backdoor.sh quarantine/ && chmod 000 quarantine/backdoor.sh</span></p>
                <p className="text-accent">✓ Menace neutralisée. +300 pts</p>
                <p className="text-muted">
                  $ <span className="text-fg">echo "Incident clos" &gt; rapport.txt</span>
                  <span className="ml-1 inline-block h-4 w-2 translate-y-0.5 animate-blink bg-accent" />
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------ Features ------------------------------ */}
      <section id="features" className="border-t border-border/60 py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="section-title">Pourquoi Astatarote</p>
          <h2 className="mt-2 max-w-xl text-balance text-3xl font-extrabold tracking-tight">
            Une salle de machines complète, sans la salle de machines.
          </h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="card group p-6 transition-all duration-300 hover:-translate-y-1 hover:border-primary/40"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-surface-2 transition-colors duration-300 group-hover:border-primary/40">
                  <f.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mt-4 text-[15px] font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------ Parcours ------------------------------ */}
      <section id="parcours" className="border-t border-border/60 bg-surface/30 py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="section-title">Le catalogue</p>
          <h2 className="mt-2 text-balance text-3xl font-extrabold tracking-tight">
            Des parcours figés, écrits pour durer.
          </h2>
          <div className="mt-10 grid gap-5 md:grid-cols-2">
            {(catalog.length ? catalog : []).map((course) => (
              <div key={course.slug} className="card p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-bold">{course.name}</h3>
                    <p className="mt-1 text-sm text-muted">{course.tagline}</p>
                  </div>
                  <span className="chip shrink-0">{course.level}</span>
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  <span className="chip">{course.total_levels} défis</span>
                  <span className="chip">{course.duration_minutes} min</span>
                  <span className="chip">{course.total_points} pts</span>
                </div>
              </div>
            ))}
            {catalog.length === 0 && (
              <div className="card p-6 text-sm text-muted">
                Le catalogue charge… (le serveur doit être démarré)
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ------------------------------ How ------------------------------ */}
      <section id="how" className="border-t border-border/60 py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="section-title">Comment ça marche</p>
          <h2 className="mt-2 text-balance text-3xl font-extrabold tracking-tight">
            Trois étapes, zéro installation.
          </h2>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="card p-6">
                <span className="font-mono text-2xl font-bold text-primary/60">{s.n}</span>
                <h3 className="mt-3 text-[15px] font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{s.text}</p>
              </div>
            ))}
          </div>
          <div className="mt-12 flex justify-center">
            <button onClick={onEnter} className="btn-primary px-8 py-3.5 text-[15px]">
              {cta}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ------------------------------ Footer ------------------------------ */}
      <footer className="border-t border-border/60 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-[13px] text-muted sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <span>Astatarote — apprendre Linux et la cybersécurité, éthiquement.</span>
          </div>
          <span className="font-mono">v3.0 · moteur déterministe</span>
        </div>
      </footer>
    </div>
  );
}
