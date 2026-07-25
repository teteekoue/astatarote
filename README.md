# Astatarote 🛡️

**Astatarote** est une plateforme éducative gamifiée, open-source et adaptative, conçue pour l'apprentissage de l'administration système Linux et de la cybersécurité (offensive et défensive) de manière éthique.

Le cœur d'Astatarote réside dans son intégration profonde de l'Intelligence Artificielle (IA). L'IA Architecte génère dynamiquement des scénarios, des arborescences de fichiers, des permissions et des contrôles automatiques personnalisés selon le niveau et l'objectif d'apprentissage de l'utilisateur.

---

## 🚀 Philosophie & Fonctionnalités Clés

1. **Rien n'est Statique, Tout est Personnalisé** : L'utilisateur décrit ce qu'il souhaite apprendre (ex: "Sécuriser SSH", "Détecter des forces brutes", "Auditer Apache"). L'IA Architecte construit à la volée des exercices graduels et adaptés.
2. **Terminal Interactif Virtuel** : Une émulation de shell Unix s'exécutant directement dans le navigateur (propulsée par xterm.js) permettant d'interagir avec un système de fichiers virtuel ou des conteneurs isolés.
3. **Coéquipier IA Pédagogique** : Un chat en temps réel (via WebSockets) avec un assistant IA bienveillant qui explique les concepts, propose des indices progressifs et valide les travaux sans jamais donner la solution brute.
4. **Système de Progression Gamifié** : Acquisition de points, grades d'avancement militaires (Novice, Apprenti, Administrateur, Expert, Maître) et déblocage de badges de spécialisation (Linux Ninja, Network Sentinel, Defender, White Hat).

---

## 🏗️ Architecture Technique

La plateforme repose sur une stack moderne, légère et sécurisée :

- **Backend** : Python 3.10+ avec FastAPI, SQLAlchemy (modèles de données relationnels), et WebSockets en temps réel.
- **Frontend** : React 18+, TypeScript, Tailwind CSS pour une interface sombre/cyber immersive, et xterm.js pour le terminal.
- **Base de données** : SQLite (par défaut pour un déploiement zéro-config immédiat).
- **Conteneurisation** : Docker & Docker Compose pour orchestres l'ensemble des services de développement.
- **Support des APIs IA** : Intégration flexible pour NVIDIA, Groq, Fireworks, Cohere, et Together AI.

---

## 📂 Structure du Projet

```text
astarote/
├── backend/
│   ├── app/
│   │   ├── main.py              # Point d'entrée FastAPI & configuration CORS/WebSockets
│   │   ├── api/
│   │   │   ├── routes/          # Routes API REST (jeux, niveaux, préférences)
│   │   │   └── websockets/      # Sockets temps réel (terminal simulé, coéquipier chat)
│   │   ├── core/
│   │   │   ├── ai/              # Connecteurs LLM (NVIDIA, Groq, Together, fallback)
│   │   │   ├── game/            # Moteur de validation des défis & calcul des points/grades
│   │   │   ├── terminal/        # Simulateur de shell Unix et gestionnaire de sandbox
│   │   │   └── database/        # Session et configuration SQLite/SQLAlchemy
│   │   ├── models/              # Schémas de base de données relationnelle
│   │   └── schemas/             # Modèles de données de validation Pydantic
│   ├── requirements.txt         # Dépendances Python
│   └── Dockerfile               # Dockerfile du serveur d'API
├── frontend/
│   ├── src/
│   │   ├── components/          # Vues & Panneaux (Dashboard, GameInterface, Chat, Terminal)
│   │   ├── index.css            # Styles généraux, scrollbars et effets rétro/néon
│   │   ├── App.tsx              # Routage et état d'affichage principal
│   │   └── main.tsx             # Point d'entrée React / TypeScript
│   ├── package.json             # Dépendances Node.js (xterm, lucide-react, vite)
│   └── Dockerfile               # Dockerfile du serveur de développement Web
├── docker-compose.yml           # Fichier d'orchestration multi-conteneurs
└── README.md                    # Cette documentation
```

---

## 🔧 Installation & Lancement

L'application est **prête à l'emploi dès le premier lancement** via Docker Compose. Si aucune clé d'API d'IA n'est configurée, l'application utilise automatiquement un simulateur de règles local ultra-réaliste pour générer des niveaux d'apprentissage complets.

### Prérequis
- Docker et Docker Compose installés sur votre machine.

### Étape 1 : Cloner le dépôt et configurer l'environnement
Créez un fichier de variables d'environnement `.env` à la racine si vous souhaitez brancher vos services d'IA :

```env
# .env (Optionnel)
DATABASE_URL=sqlite://///home/user/astarote/astarote.db
```

### Étape 2 : Lancer avec Docker Compose
Exécutez la commande suivante à la racine du projet pour construire et démarrer les conteneurs :

```bash
docker-compose up --build
```

Cette commande démarre :
- Le **Frontend** sur [http://localhost:3000](http://localhost:3000)
- Le **Backend FastAPI** sur [http://localhost:8000](http://localhost:8000)

---

## 🎮 Guide d'Utilisation

1. **Tableau de Bord** : Dès l'ouverture, visualisez vos statistiques globales, votre grade d'apprentissage et la liste de vos laboratoires actifs.
2. **Créer un Jeu** : Allez dans "Créer mon Jeu", entrez un nom et décrivez vos objectifs d'apprentissage sous forme textuelle ou cliquez sur un bouton de préréglage recommandés.
3. **Le Terminal Virtuel** : Tapez `ls`, `cd`, `cat`, `chmod`, `touch`, `mkdir`, `ps` pour interagir avec le système de fichiers virtuel. Utilisez des flux d'écriture standard comme `echo "texte" > fichier.txt` pour modifier les configurations système.
4. **Dialogue Coéquipier** : Si vous êtes bloqué, cliquez sur les suggestions de raccourcis du chat (ex: "Donne-moi un indice") ou tapez directement vos questions pour obtenir une explication sur-mesure de la part de l'IA.
5. **Validation** : Une fois les consignes exécutées, cliquez sur **"Soumettre la Solution"** en haut à droite. Si vos modifications système sont correctes, le défi est validé, les points sont crédités et le niveau suivant se déverrouille !

---

## 🛡️ Sécurité & Isolation

- **Simulation Locale** : Les commandes exécutées dans le terminal virtuels sont confinées dans une mémoire locale modélisée en base de données, évitant tout risque d'altération du système d'exploitation hôte.
- **Liste Noire de Commandes** : Un filtre strict bloque les commandes jugées dangereuses (`rm -rf /`, `dd`, `mkfs`) pour enseigner de bonnes pratiques d'ingénierie et de sécurité.
- **Support Docker** : Pour les cours avancés, les conteneurs d'exercices sont confinés de manière isolée sans privilèges (`cap_drop`), avec des limites drastiques de mémoire (128 Mo) et de CPU (0.5 max).

---

## 🛠️ API & Documentation (Swagger)

Le backend FastAPI génère automatiquement une documentation interactive complète et conforme aux spécifications OpenAPI.
Une fois le backend démarré, vous pouvez y accéder à l'adresse suivante :
- **Swagger UI** : [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc** : [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🤝 Contribution

Les contributions éthiques et pédagogiques sont les bienvenues ! Pour proposer des améliorations :
1. Créez un fork du projet.
2. Implémentez vos modifications dans une branche dédiée.
3. Rédigez des tests pour vos modifications critiques.
4. Soumettez une Pull Request claire et détaillée.
