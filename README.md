# Astatarote 🛡️

**Astatarote** est une plateforme **SaaS** d'apprentissage de Linux et de la cybersécurité :
des parcours figés et vérifiés, un terminal Linux simulé par un moteur déterministe, et une
assistante IA pédagogique — le tout dans le navigateur, sans aucune installation pour l'apprenant.

> **v3.0 — Le virage SaaS.** La génération de jeux par IA a été retirée (peu fiable, hallucinations) :
> chaque parcours est désormais **rédigé à la main et figé**. L'IA n'intervient plus que comme
> **assistante du joueur**. Le terminal n'exécute plus de vrai bash dans des sandboxes : il est
> simulé par un **moteur Linux déterministe** — réaliste, instantané, et sans saturation de ressources.

---

## 🚀 Ce qui a changé (v3.0)

| Avant (v2) | Maintenant (v3) |
|---|---|
| Jeux générés à la volée par LLM | **Catalogue de parcours figés**, rédigés et testés à la main |
| Vrai bash via PTY + sandboxes sur le disque | **Moteur Linux déterministe** (VFS + 45 commandes + processus simulés) |
| LLM Architecte + LLM tuteur | **Nemesis** : assistante IA uniquement pédagogique (avec mode hors-ligne intégré) |
| Application locale mono-utilisateur (auto-login) | **SaaS multi-utilisateurs** : landing publique, inscription/connexion, catalogue |
| Validation sur le système de fichiers réel | Validation sur **l'état de la machine virtuelle persisté** (anti-triche, hermétique) |

---

## 🧠 Architecture

```text
astatarote/
├── backend/
│   └── app/
│       ├── api/
│       │   ├── routes/           # REST : auth, catalogue, parcours, validation
│       │   └── websockets/       # WS : terminal (moteur déterministe) + chat IA
│       ├── catalog/              # ★ PARCOURS FIGÉS (rédigés à la main)
│       │   ├── __init__.py       #   registre du catalogue
│       │   └── linux_essentials.py  #   parcours n°1 : 8 défis Linux
│       ├── core/
│       │   ├── ai/service.py     #   Nemesis : assistante pédagogique (+ fallback local)
│       │   ├── game/engine.py    #   validation des défis (VFS, perms, processus, commandes)
│       │   └── terminal/engine/  # ★ MOTEUR LINUX DÉTERMINISTE
│       │       ├── vfs.py        #     système de fichiers virtuel POSIX-like
│       │       ├── processes.py  #     table de processus simulée
│       │       ├── commands.py   #     45+ commandes GNU (sorties réalistes)
│       │       ├── shell.py      #     shell : parsing, pipes, redirections, hooks
│       │       └── session.py    #     sessions + persistance (GameState)
│       ├── models/ & schemas/    # SQLAlchemy + Pydantic
│       └── tests/                # 41 tests : moteur, solveabilité de chaque défi, API SaaS
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Landing.tsx       # landing publique SaaS
│       │   ├── Auth/             # connexion / inscription
│       │   ├── Dashboard/        # mes parcours, catalogue
│       │   ├── Game/             # atelier : mission + terminal + Nemesis
│       │   └── ...
│       └── lib/                  # client API, auth, WS
├── Dockerfile                    # image de production (frontend buildé + API)
├── docker-compose.yml            # déploiement SaaS (mono-conteneur)
└── docker-compose.dev.yml        # environnement de développement
```

### Le moteur Linux déterministe

Inspiré des projets de simulation de terminal éducatifs étudiés lors de la conception
([trybash/bash-emulator](https://github.com/trybash/bash-emulator),
[terminal4dummies](https://github.com/jordanbailey00/terminal4dummies),
[terminal_quest](https://github.com/brunozapico/terminal_quest),
[jcubic/fake-linux-terminal](https://github.com/jcubic/fake-linux-terminal)),
mais porté **côté serveur** pour que la validation soit infalsifiable :

- **VFS POSIX-like** : permissions octales/symboliques, propriétaires, liens symboliques, jokers ;
- **45+ commandes** aux sorties fidèles à GNU coreutils (`ls -l`, `chmod`, `ps aux`, `grep -r`…)
  avec les messages d'erreur authentiques (`Permission denied`, `No such file or directory`…) ;
- **Pipes, redirections, `;`, `&&`, `||`**, variables d'environnement, historique, autocomplétion Tab ;
- **Processus simulés** (`ps aux`, `top`, `kill`) avec protections root ;
- **Hooks de réponses par exercice** : chaque niveau peut scripter des sorties déterministes
  pour des commandes spécifiques (`systemctl status backup_loop`, `ss -tulpn`…) ;
- **Déterminisme total** : horloge figée, même scénario + mêmes commandes = même sortie ;
- **Zéro processus système** : une session = un objet Python en mémoire, persisté en base
  après chaque commande — des milliers d'apprenants simultanés sans VM ni conteneur.

### Les parcours figés

Chaque parcours est un module Python dans `backend/app/catalog/` : contexte narratif,
consignes, fiche technique, indices, machine de départ (fichiers, processus) et critères de
validation — tout est déclaré, testé (`test_linux_engine.py` rejoue la solution de chaque défi)
et versionné. Ajouter un parcours = ajouter un module au registre.

### Nemesis, l'assistante IA

Nemesis aide le joueur en direct (WebSocket) : concepts, décryptage d'erreurs, indices
progressifs — jamais la solution brute. Elle fonctionne **sans clé API** (mode hors-ligne à
base de règles pédagogiques) ou avec le fournisseur LLM configuré par l'utilisateur
(Groq, NVIDIA, Fireworks, Cohere, Together).

---

## 🔧 Installation & lancement

### Déploiement SaaS (production)

```bash
docker compose up -d --build
# → http://localhost:8000
```

Variables clés (à surcharger en production) :

| Variable | Défaut | Rôle |
|---|---|---|
| `ASTAROTE_SECRET_KEY` | change-me | signature des JWT |
| `DATABASE_URL` | sqlite:////data/astarote.db | base de données |
| `ASTAROTE_BOOTSTRAP_ADMIN` | false | crée un admin au 1er démarrage (dev) |
| `ASTAROTE_CORS_ORIGINS` | http://localhost:8000 | origines autorisées |

### Développement local (sans Docker)

```bash
# Backend
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# Frontend (Vite, proxy /api et /ws vers :8000)
cd frontend && npm install && npm run dev
```

### Tests

```bash
python -m pytest backend/app/tests/ -q
# 41 tests : moteur déterministe, solveabilité des 8 défis, flux SaaS complet (WS inclus)
```

---

## 🎮 Le premier parcours : *Linux Essentials*

8 défis narratifs chez **Meridian Corp.**, du premier `pwd` au premier incident de sécurité :

1. **Premiers pas dans le terminal** — pwd, ls, whoami, cat
2. **À la recherche du fichier de configuration** — find, cd, echo >
3. **Le log qui en dit long** — grep, head, tail, pipes, wc
4. **Grand nettoyage avant sauvegarde** — mkdir, mv, cp, rm, touch
5. **Verrouiller les accès** — permissions, chmod, stat
6. **Qui suis-je sur ce système ?** — id, /etc/passwd, sudo
7. **Un processus s'est emballé** — ps aux, top, kill
8. **Mission finale : premier incident** — find, kill, quarantaine, chmod 000, rapport

---

## 🗺️ Feuille de route

- [ ] Nouveaux parcours figés : *Réseau & diagnostic*, *Sécurisation SSH*, *Forensique légère*
- [ ] Certificats de fin de parcours téléchargeables
- [ ] Abonnements SaaS (Stripe) et espaces équipes
- [ ] Éditeur de parcours (auteurs externes) avec pipeline de validation

---

## 📜 Licence & éthique

Astatarote est un projet éducatif **éthique** : offensive et défensive s'apprennent dans un
environnement simulé isolé, sans cible réelle. Voir le code de conduite dans la documentation.
