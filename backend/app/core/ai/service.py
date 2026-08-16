"""AI service: level generation (Architect) and pedagogical chat (Nemesis).

The LLM output is validated against a strict Pydantic schema. On any failure
(missing key, malformed JSON, bad provider) the service falls back to a rich
built-in template generator tuned to the real Linux sandbox.
"""
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("astarote.ai")

# ----------------------------------------------------------------------------
# Strict schema for AI-generated levels
# ----------------------------------------------------------------------------

class FileCheck(BaseModel):
    path: str
    perms: Optional[str] = None
    content_contains: Optional[str] = None
    content_not_contains: Optional[str] = None


class ExpectedState(BaseModel):
    files_checks: List[FileCheck] = Field(default_factory=list)
    process_not_running: Optional[str] = None
    process_running: Optional[str] = None
    file_not_exists: Optional[str] = None


class InitialState(BaseModel):
    cwd: str = "."
    fs: Dict[str, Any] = Field(default_factory=dict)
    processes: List[Dict[str, Any]] = Field(default_factory=list)


class Scenario(BaseModel):
    type: str = "simulation"
    initial_state: InitialState = Field(default_factory=InitialState)
    expected_state: ExpectedState = Field(default_factory=ExpectedState)
    commands_allowed: List[str] = Field(default_factory=list)
    forbidden_commands: List[str] = Field(default_factory=list)


class LevelData(BaseModel):
    title: str
    situation_probleme: str
    consigne: str
    support_technique: str
    objective: str
    scenario: Scenario = Field(default_factory=Scenario)
    hints: List[str] = Field(default_factory=list)
    difficulty: int = 3
    points: int = 100
    time_limit: int = 600


PROVIDER_MODELS = {
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
    "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", "meta/llama-3.1-70b-instruct"),
    "fireworks": ("https://api.fireworks.ai/inference/v1/chat/completions", "accounts/fireworks/models/deepseek-v4-flash-0731"),
    "cohere": ("https://api.cohere.com/compatibility/v1/chat/completions", "command-r-plus"),
    "together": ("https://api.together.xyz/v1/chat/completions", "meta-llama/Llama-3-70b-chat-hf"),
}

# Providers whose OpenAI-compatible API honours {"type": "json_object"}.
JSON_MODE_PROVIDERS = {"groq", "together", "fireworks"}


class AIService:
    # ------------------------------------------------------------------
    @staticmethod
    def _call_provider_api(
        provider: str, api_key: str, messages: List[Dict[str, str]], json_mode: bool = False
    ) -> str:
        spec = PROVIDER_MODELS.get(provider)
        if not spec:
            raise ValueError(f"Fournisseur IA inconnu : {provider}")

        url, model = spec
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096,
        }
        if json_mode and provider in JSON_MODE_PROVIDERS:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Error calling %s API: %s", provider, e)
            raise

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_json(text: str) -> str:
        cleaned = text.strip()
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            return cleaned[first_brace : last_brace + 1]
        return cleaned

    # ------------------------------------------------------------------
    @classmethod
    def generate_level(
        cls,
        domain: str,
        user_level: str,
        level_index: int,
        custom_prompt: Optional[str],
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        provider = preferences.get("provider_ia", "fallback")
        api_key = preferences.get("api_key")
        domain = (domain or "linux").lower()
        user_level = (user_level or "beginner").lower()

        if provider == "fallback" or not api_key:
            return cls._generate_fallback_level(domain, user_level, level_index, custom_prompt)

        system_prompt = (
            "Tu es l'Architecte d'Astatarote, une plateforme éthique d'apprentissage de la cybersécurité "
            "et de l'administration Linux.\n"
            "Tu génères un niveau de jeu adapté à l'utilisateur, exprimé UNIQUEMENT en JSON brut (sans "
            "balise Markdown autour du JSON, sans commentaire, sans texte avant/après).\n\n"
            "CONTRAINTES OBLIGATOIRES SUR LA SANDBOX RÉELLE :\n"
            "- L'utilisateur interagira avec un VRAI shell bash dans une sandbox Linux réelle (Debian "
            "minimale). Le shell démarre À LA RACINE de la sandbox : son répertoire courant est la racine "
            "de la machine virtuelle.\n"
            "- Tous les chemins du scénario ('fs', 'consigne', 'support_technique', 'files_checks') "
            "doivent donc être RELATIFS à cette racine, SANS slash initial : 'home/user', 'home/suspect', "
            "'var/log', 'etc', 'etc/ssh', 'tmp'. N'utilisez JAMAIS de chemins absolus commençant par '/' : "
            "ils ne correspondraient à aucun dossier de la sandbox.\n"
            "- Exemple de commandes valides depuis la racine : 'cd home/user', 'cat home/user/note.txt', "
            "'chmod 600 home/user/note.txt', 'grep Failed password var/log/auth.log', "
            "'echo 1.2.3.4 > home/user/rapport.txt', 'sed -i s/ancien/nouveau/ etc/ssh/sshd_config'.\n"
            "- Toutes les commandes citées doivent être de vraies commandes bash disponibles sur une Debian "
            "minimale (ls, cd, cat, grep, sed, awk, chmod, chown, ps, kill, echo, touch, mkdir, rm, cp, mv, "
            "tar, find, head, tail, wc, sort, uniq, cut, tr, tee). nano/vim sont absents — préférer sed ou "
            "echo pour éditer un fichier.\n"
            "- 'scenario.initial_state.fs' décrit l'arborescence de départ avec des clés relatives à la "
            "racine. Exemple : { \"home/user\": { \"note.txt\": { \"content\": \"...\", \"perms\": \"644\" } } }.\n"
            "- 'scenario.expected_state.files_checks' définit les contrôles automatiques de validation, avec "
            "des chemins relatifs et valeurs TRÈS PRÉCIS (permissions en octal sur 3 chiffres, contenu exact "
            "attendu). Ne posez qu'une contrainte raisonnable que l'utilisateur peut réellement réaliser "
            "dans le shell.\n"
            "- 'scenario.initial_state.processes' (optionnel) liste des processus à lancer en fond "
            "({pid: 1, name: 'nom_du_processus'}). Utilisé seulement pour des défis de gestion de processus ; "
            "dans ce cas, prévoyez aussi 'expected_state.process_not_running' avec le même nom.\n"
            "- 'hints' : 3 indices progressifs, du plus général au plus précis, SANS donner la solution complète.\n"
            "- 'difficulty' : entier 1-10, 'points' : 80-200, 'time_limit' : 300-900.\n\n"
            "RÉDACTION (en français, immersive et professionnelle) :\n"
            "- 'situation_probleme' : raconte le scénario complet (contexte, enjeu, urgence, mission confiée).\n"
            "- 'consigne' : un ORDRE DE MISSION structuré, liste numérotée d'actions PRÉCISES à exécuter "
            "dans le terminal, avec les chemins relatifs exacts et les commandes exactes.\n"
            "- 'support_technique' : un SUPPORT DE MISSION COMPLET (fiche d'appui opérationnel), qui doit "
            "contenir TOUTES les informations nécessaires à la réussite de la mission, structuré avec des "
            "titres Markdown (###), listes et blocs de code (```) :\n"
            "  1. Contexte et objectif de la mission (reformulés pour l'opérateur),\n"
            "  2. Environnement cible : où se trouvent précisément les fichiers/répertoires concernés,\n"
            "  3. Méthodologie détaillée étape par étape avec les commandes exactes à taper (blocs de code),\n"
            "  4. Vérification : comment contrôler soi-même que la mission est réussie (commande + résultat attendu),\n"
            "  5. Critères de validation automatiques (ce que la plateforme contrôle),\n"
            "  6. Pièges à éviter et bonnes pratiques.\n\n"
            "FORMAT JSON EXACT :\n"
            "{\n"
            '  "title": "...",\n'
            '  "situation_probleme": "...",\n'
            '  "consigne": "...",\n'
            '  "support_technique": "...",\n'
            '  "objective": "...",\n'
            '  "scenario": {\n'
            '    "type": "simulation",\n'
            '    "initial_state": {\n'
            '      "cwd": ".",\n'
            '      "fs": { "home/user": { "note.txt": { "content": "...", "perms": "644" } } },\n'
            '      "processes": []\n'
            '    },\n'
            '    "expected_state": {\n'
            '      "files_checks": [\n'
            '        { "path": "home/user/note.txt", "perms": "600", "content_contains": "..." }\n'
            "      ]\n"
            "    },\n"
            '    "commands_allowed": ["ls", "cd", "cat", "chmod"],\n'
            '    "forbidden_commands": []\n'
            "  },\n"
            '  "hints": ["...", "...", "..."],\n'
            '  "difficulty": 3, "points": 100, "time_limit": 600\n'
            "}"
        )

        user_prompt = (
            f"Génère le niveau index {level_index} (0 = premier) pour un jeu sur le domaine "
            f"'{domain}', niveau '{user_level}'."
        )
        if custom_prompt:
            user_prompt += f"\nObjectif pédagogique de l'utilisateur : '{custom_prompt}'.\n"
            user_prompt += (
                "Respecte STRICTEMENT cet objectif dans le thème, l'arborescence des fichiers, la consigne, "
                "le support technique et les contrôles de validation. L'ensemble de la mission et les "
                "commandes demandées doivent correspondre EXACTEMENT au sujet demandé, jamais un autre sujet.\n"
                f"Ceci est le niveau {level_index + 1} d'une progression sur ce même sujet : si level_index > 0, "
                "continue naturellement sur ce sujet en augmentant légèrement la difficulté, en restant centré "
                "sur ce thème."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response_text = cls._call_provider_api(provider, api_key, messages, json_mode=True)
            level_data = cls._validate_and_normalize(response_text)
            return level_data
        except Exception as e:
            logger.error("AI level generation failed, using template fallback: %s", e)
            return cls._generate_fallback_level(domain, user_level, level_index, custom_prompt)

    # ------------------------------------------------------------------
    @classmethod
    def _validate_and_normalize(cls, response_text: str) -> Dict[str, Any]:
        extracted = cls._extract_json(response_text)
        data = json.loads(extracted)
        validated = LevelData(**data)
        return validated.model_dump(mode="json")

    # ------------------------------------------------------------------
    @classmethod
    def _generate_fallback_level(
        cls, domain: str, user_level: str, level_index: int, custom_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Rich, precise built-in levels tuned to the real Linux sandbox."""
        domain = domain if domain in ("linux", "security", "network") else "linux"

        builders = {
            "linux": [
                cls._linux_level_0,
                cls._linux_level_1,
                cls._linux_level_2,
            ],
            "security": [
                cls._security_level_0,
                cls._security_level_1,
                cls._security_level_2,
            ],
            "network": [
                cls._network_level_0,
                cls._network_level_1,
                cls._network_level_2,
            ],
        }

        # A user-provided learning goal must shape the fallback level too. When a
        # goal is present, route to a topic-aware generator so the mission matches
        # what the user asked for instead of a stock Linux/security/network theme.
        if custom_prompt and custom_prompt.strip():
            themed = cls._generate_themed_fallback(domain, user_level, level_index, custom_prompt)
            if themed is not None:
                return themed
            return cls._adapt_fallback_to_goal(builders[domain][level_index % 3](domain, user_level, custom_prompt), custom_prompt)

        builder = builders[domain][level_index % 3]
        return builder(domain, user_level, custom_prompt)

    # ---------------------------------------------------------------
    # Topic-aware fallbacks (respect the user's learning goal)
    # ---------------------------------------------------------------
    @classmethod
    def _generate_themed_fallback(
        cls, domain: str, user_level: str, level_index: int, custom_prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Returns a level built around the user's goal, or None if unknown."""
        goal = custom_prompt.lower()
        topics = [
            ("git" in goal, cls._git_level_0),
            ("web" in goal or "apache" in goal or "nginx" in goal or "http" in goal, cls._web_level_0),
            (
                "base" in goal
                or "database" in goal
                or "sql" in goal
                or "mysql" in goal
                or "postgres" in goal
                or ("db" in goal.split()),
                cls._database_level_0,
            ),
            ("docker" in goal or "conteneur" in goal or "container" in goal, cls._docker_level_0),
            ("bash" in goal or "script" in goal or "shell" in goal, cls._bash_level_0),
            ("réseau" in goal or "network" in goal or "tcp" in goal or "ssh" in goal, cls._network_level_0),
        ]
        for matched, builder in topics:
            if matched:
                return builder(domain, user_level, level_index, custom_prompt)
        return None

    @staticmethod
    def _git_level_0(domain, user_level, level_index, custom_prompt):
        return {
            "title": "Débuter avec Git : versionner mon premier projet",
            "situation_probleme": (
                "Vous rejoignez l'équipe de développement Astatarote. On vous remet un projet en cours "
                "avec plusieurs fichiers non versionnés. Avant de coder, vous devez maîtriser le flux Git "
                "de base : initialiser un dépôt, suivre des fichiers, faire un premier commit, créer une "
                "branche et consulter l'historique. La mission est une mise à niveau obligatoire pour "
                "travailler en équipe sans écraser le travail des autres."
            ),
            "consigne": (
                "1) Placez-vous dans le répertoire du projet déjà présent dans la sandbox : `cd home/user/project`.\n"
                "2) Découvrez son contenu avec `ls -la`.\n"
                "3) Initialisez un dépôt Git : `git init`.\n"
                "4) Ajoutez le fichier `README.md` à l'index : `git add README.md`.\n"
                "5) Créez le premier commit : `git commit -m \"Initial commit\"`.\n"
                "6) Créez une branche `feature` : `git branch feature`.\n"
                "7) Vérifiez l'historique : `git log --oneline`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Découvrir le flux Git essentiel dans un projet réel : `init`, `add`, `commit`, `branch`, "
                "`log`. Objectif : produire un premier commit dans `home/user/project` et une branche "
                "`feature`, tout en enregistrant la preuve de travail dans un fichier de rapport.\n\n"
                "### 2. Environnement cible\n"
                "- `home/user/project/` : votre projet (contient `README.md` et `app.py`).\n"
                "- Dépôt Git : se crée à la racine de ce dossier avec `git init`.\n"
                "- `home/user/git_report.txt` : fichier à rédiger pour la validation automatique.\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "cd home/user/project      # entrer dans le projet\n"
                "git init                  # créer le dépôt (dossier .git)\n"
                "git add README.md         # mettre README.md en zone de staging\n"
                "git commit -m 'Initial commit'   # créer le premier commit\n"
                "git branch feature        # créer la branche feature\n"
                "echo 'initial commit cree et branche feature creee' > home/user/git_report.txt\n"
                "```\n"
                "Après `git commit`, Git crée l'objet commit et met à jour la branche courante, visible "
                "dans `git log --oneline`.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "git log --oneline   # doit afficher un commit '(HEAD -> ...)' de message 'Initial commit'\n"
                "git branch          # doit lister la branche 'feature'\n"
                "cat home/user/git_report.txt\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- Le fichier `home/user/git_report.txt` doit exister et mentionner `initial commit`.\n"
                "- Le fichier `home/user/git_report.txt` doit mentionner `feature`.\n\n"
                "### 6. Pièges à éviter\n"
                "- `git init` doit être lancé DANS le dossier du projet (pas à la racine de la sandbox).\n"
                "- Penser à `git add` avant `git commit`, sinon rien n'est enregistré.\n"
                "- Aucune clé / identité Git n'est demandée : un simple commit fonctionne sans `user.name` "
                "si vous définissez `git config user.email`/`user.name` localement en cas d'erreur.\n"
                "- Les chemins sont relatifs à la racine de la sandbox (pas de `/` initial)."
            ),
            "objective": "Initialiser un dépôt Git, créer un commit et une branche feature, et rédiger le rapport de validation.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "home/user/project": {
                            "README.md": {"content": "# Mon Projet\nBienvenue dans Astatarote.", "perms": "644"},
                            "app.py": {"content": "print('Hello')", "perms": "644"},
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {
                            "path": "home/user/git_report.txt",
                            "content_contains": "initial commit",
                        },
                        {
                            "path": "home/user/git_report.txt",
                            "content_contains": "feature",
                        },
                    ]
                },
                "commands_allowed": [
                    "ls",
                    "cd",
                    "cat",
                    "git",
                    "pwd",
                    "echo",
                    "whoami",
                    "help",
                ],
                "forbidden_commands": [],
            },
            "hints": [
                "Le projet se trouve dans home/user/project.",
                "Initialisez avec `git init` puis `git add README.md` et `git commit -m 'Initial commit'`.",
                "Pour la validation, créez home/user/git_report.txt avec echo mentionnant 'initial commit' et 'feature'.",
            ],
            "difficulty": 2,
            "points": 100,
            "time_limit": 900,
        }

    @staticmethod
    def _web_level_0(domain, user_level, level_index, custom_prompt):
        return {
            "title": "Durcir un serveur web : désactiver l'indexation",
            "situation_probleme": (
                "L'audit de sécurité révèle un serveur web Apache exposant le listing des répertoires : "
                "n'importe quelle ressource de votre site est listable, y compris des fichiers sensibles. "
                "Votre mission : désactiver l'indexation des dossiers et prouver la correction."
            ),
            "consigne": (
                "1) Explorez le serveur : `ls -la etc/apache2`.\n"
                "2) Lisez la configuration : `cat etc/apache2/apache2.conf`.\n"
                "3) Désactivez l'indexation en remplaçant 'Indexes' : `sed -i 's/Indexes/''g' etc/apache2/apache2.conf`.\n"
                "4) Vérifiez qu'aucune occurrence de 'Indexes' ne reste : `grep Indexes etc/apache2/apache2.conf`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Le serveur web liste le contenu des répertoires (option `Indexes` active), exposant des "
                "fichiers sensibles. Objectif : supprimer l'option `Indexes` de la configuration Apache.\n\n"
                "### 2. Environnement cible\n"
                "- `etc/apache2/apache2.conf` : configuration principale du serveur web.\n"
                "- On y trouve l'option `Indexes` (listing des dossiers) à retirer.\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "cat etc/apache2/apache2.conf                     # repérer la ligne 'Options Indexes'\n"
                "sed -i 's/Options Indexes/Options ''g' etc/apache2/apache2.conf\n"
                "echo 'indexation désactivée' > home/user/web_report.txt\n"
                "```\n"
                "`sed -i 's/Options Indexes/Options/' fichier` remplace 'Options Indexes' par 'Options' "
                "dans le fichier, retirant le mot 'Indexes'.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "grep Indexes etc/apache2/apache2.conf   # aucun résultat attendu\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `etc/apache2/apache2.conf` ne doit plus contenir `Indexes`.\n"
                "- `home/user/web_report.txt` doit mentionner `désactivée`.\n\n"
                "### 6. Pièges à éviter\n"
                "- `sed` est sensible à la casse : 'Indexes' avec majuscule.\n"
                "- Vérifier le fichier après édition, le serveur doit être rechargé pour appliquer.\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Retirer l'option Indexes de la configuration Apache et rédiger le rapport.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "etc/apache2": {
                            "apache2.conf": {
                                "content": (
                                    "# Astatarote apache2.conf\n"
                                    "ServerRoot \"/etc/apache2\"\n"
                                    "Options Indexes FollowSymLinks\n"
                                    "DirectoryIndex index.html index.php\n"
                                ),
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "etc/apache2/apache2.conf", "content_not_contains": "Indexes"},
                        {"path": "home/user/web_report.txt", "content_contains": "désactivée"},
                    ]
                },
                "commands_allowed": ["ls", "cat", "sed", "grep", "echo", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "L'option à retirer est 'Indexes' dans etc/apache2/apache2.conf.",
                "Utilisez `sed -i 's/Options Indexes/Options/'` pour la retirer.",
                "Créez home/user/web_report.txt mentionnant 'désactivée' pour valider.",
            ],
            "difficulty": 3,
            "points": 150,
            "time_limit": 900,
        }

    @staticmethod
    def _database_level_0(domain, user_level, level_index, custom_prompt):
        return {
            "title": "Interroger une base : le fichier clients.csv",
            "situation_probleme": (
                "Le service conformité a exporté une base de clients dans un fichier texte. On vous demande "
                "d'en extraire les informations demandées (filtrage, comptage) et de consigner le résultat "
                "dans un rapport, comme si vous interrogeiez un entrepôt de données."
            ),
            "consigne": (
                "1) Explorez la base : `ls -la var/data`.\n"
                "2) Lisez le début : `head -5 var/data/clients.csv`.\n"
                "3) Comptez les lignes : `wc -l var/data/clients.csv`.\n"
                "4) Filtrez les clients actifs : `grep -c ',ACTIVE' var/data/clients.csv`.\n"
                "5) Rédigez le rapport : `echo 'clients actifs: <N>' > home/user/db_report.txt`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Extraire des informations d'un export de base de données (`clients.csv`). Objectif : compter "
                "les clients actifs et écrire le résultat dans le rapport.\n\n"
                "### 2. Environnement cible\n"
                "- `var/data/clients.csv` : export tabulaire (en-tête + lignes, colonnes séparées par des "
                "virgules, statut du client en dernière colonne).\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "head -5 var/data/clients.csv            # inspecter la structure\n"
                "wc -l var/data/clients.csv             # nombre total de lignes\n"
                "grep -c ',ACTIVE' var/data/clients.csv  # compter les clients actifs\n"
                "echo 'clients actifs: 5' > home/user/db_report.txt\n"
                "```\n"
                "`grep -c` compte les occurrences : c'est le nombre de clients au statut ACTIVE.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "cat home/user/db_report.txt   # doit afficher 'clients actifs: 5'\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `home/user/db_report.txt` doit contenir `clients actifs`.\n"
                "- `home/user/db_report.txt` doit contenir `5`.\n\n"
                "### 6. Pièges à éviter\n"
                "- `grep ',ACTIVE'` doit matcher la fin de ligne (pas le statut INACTIVE).\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Filtrer les clients actifs depuis var/data/clients.csv et rédiger le rapport.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "var/data": {
                            "clients.csv": {
                                "content": (
                                    "id,nom,statut\n"
                                    "1,Alice,ACTIVE\n"
                                    "2,Bob,INACTIVE\n"
                                    "3,Carol,ACTIVE\n"
                                    "4,Dave,ACTIVE\n"
                                    "5,Erin,ACTIVE\n"
                                    "6,Frank,INACTIVE\n"
                                ),
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "home/user/db_report.txt", "content_contains": "clients actifs"},
                        {"path": "home/user/db_report.txt", "content_contains": "5"},
                    ]
                },
                "commands_allowed": ["ls", "cat", "grep", "wc", "head", "echo", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "La base se trouve dans var/data/clients.csv.",
                "`grep -c ',ACTIVE'` compte les clients actifs (le nombre attendu est 5).",
                "Créez home/user/db_report.txt avec echo mentionnant 'clients actifs' et '5'.",
            ],
            "difficulty": 2,
            "points": 100,
            "time_limit": 600,
        }

    @staticmethod
    def _docker_level_0(domain, user_level, level_index, custom_prompt):
        return {
            "title": "Conteneur : comprendre un contexte de build",
            "situation_probleme": (
                "L'équipe DevOps prépare une image conteneur et doit vérifier le Dockerfile avant qu'il ne "
                "propage une mauvaise configuration. Analysez le fichier Dockerfile fourni, repérez l'image "
                "de base utilisée et consignez vos observations dans un rapport."
            ),
            "consigne": (
                "1) Explorez le projet : `ls -la home/user/app`.\n"
                "2) Lisez le Dockerfile : `cat home/user/app/Dockerfile`.\n"
                "3) Identifiez l'instruction FROM (image de base).\n"
                "4) Rédigez le rapport : `echo 'base: <image>' > home/user/docker_report.txt`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Analyser un `Dockerfile` pour identifier l'image de base (instruction `FROM`). Objectif : "
                "extraire cette information et la consigner dans le rapport.\n\n"
                "### 2. Environnement cible\n"
                "- `home/user/app/Dockerfile` : fichier de définition du conteneur.\n"
                "- L'instruction `FROM` en première ligne indique l'image de base.\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "cat home/user/app/Dockerfile                        # lire le Dockerfile\n"
                "grep -i '^FROM' home/user/app/Dockerfile             # isoler l'image de base\n"
                "echo 'base: python:3.11-slim' > home/user/docker_report.txt\n"
                "```\n"
                "`grep -i '^FROM'` filtre les lignes commençant par FROM (image de base du conteneur).\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "cat home/user/docker_report.txt   # doit afficher 'base: python:3.11-slim'\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `home/user/docker_report.txt` doit contenir `base:`.\n"
                "- `home/user/docker_report.txt` doit contenir `python`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Toujours vérifier l'orthographe exacte du nom d'image.\n"
                "- L'instruction FROM doit être lue avec `grep -i` car elle est sensible à la casse "
                "uniquement pour le nom de l'instruction (FROM).\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Lire le Dockerfile et rédiger un rapport mentionnant l'image de base (python).",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "home/user/app": {
                            "Dockerfile": {
                                "content": (
                                    "FROM python:3.11-slim\n"
                                    "WORKDIR /app\n"
                                    "COPY . .\n"
                                    "RUN pip install -r requirements.txt\n"
                                ),
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "home/user/docker_report.txt", "content_contains": "base:"},
                        {"path": "home/user/docker_report.txt", "content_contains": "python"},
                    ]
                },
                "commands_allowed": ["ls", "cat", "grep", "echo", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Le Dockerfile se trouve dans home/user/app.",
                "L'image de base est donnée par l'instruction FROM, visitez `grep -i '^FROM'`.",
                "Créez home/user/docker_report.txt mentionnant 'base:' et 'python'.",
            ],
            "difficulty": 2,
            "points": 100,
            "time_limit": 600,
        }

    @staticmethod
    def _bash_level_0(domain, user_level, level_index, custom_prompt):
        return {
            "title": "Écriture d'un script Bash automatisé",
            "situation_probleme": (
                "L'équipe souhaite automatiser une tâche répétitive : générer un rapport quotidien. Vous devez "
                "écrire un script Bash simple qui lit un fichier source, compte ses lignes et écrit le "
                "résultat dans un rapport. Ce mini-script est votre introduction à la programmation shell."
            ),
            "consigne": (
                "1) Explorez le répertoire : `ls -la home/user`.\n"
                "2) Lisez le fichier source : `cat home/user/source.txt`.\n"
                "3) Créez le script : `echo '#!/bin/bash' > home/user/mon_script.sh`.\n"
                "4) Ajoutez la logique : `echo 'wc -l < home/user/source.txt >> home/user/bash_report.txt' >> home/user/mon_script.sh`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Écrire un script Bash qui compte les lignes d'un fichier source. Objectif : créer "
                "`home/user/mon_script.sh` et produire le rapport via la commande dans le script.\n\n"
                "### 2. Environnement cible\n"
                "- `home/user/source.txt` : fichier source à analyser.\n"
                "- `home/user/mon_script.sh` : script à créer.\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "echo '#!/bin/bash' > home/user/mon_script.sh\n"
                "echo 'wc -l < home/user/source.txt' >> home/user/mon_script.sh\n"
                "bash home/user/mon_script.sh\n"
                "```\n"
                "`>>` ajoute une ligne à la fin du fichier ; on exécute ensuite le script avec `bash`.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "cat home/user/mon_script.sh   # doit contenir la commande wc -l\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `home/user/bash_report.txt` doit contenir le compte de lignes (`4`).\n"
                "- `home/user/mon_script.sh` doit exister et contenir `wc -l`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Bien distinguer `>` (écrasement) de `>>` (ajout).\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Créer un script Bash qui compte les lignes de source.txt et produit le rapport.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {
                            "source.txt": {"content": "ligne1\nligne2\nligne3\nligne4\n", "perms": "644"}
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "home/user/mon_script.sh", "content_contains": "wc -l"},
                        {"path": "home/user/bash_report.txt", "content_contains": "4"},
                    ]
                },
                "commands_allowed": ["ls", "cat", "echo", "wc", "bash", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Créez le script avec `echo '#!/bin/bash' > home/user/mon_script.sh`.",
                "Ajoutez `wc -l < home/user/source.txt >> home/user/bash_report.txt` puis exécutez `bash`.",
                "Le fichier source a 4 lignes, donc le rapport doit contenir 4.",
            ],
            "difficulty": 2,
            "points": 100,
            "time_limit": 600,
        }

    @staticmethod
    def _adapt_fallback_to_goal(level: Dict[str, Any], custom_prompt: str) -> Dict[str, Any]:
        """Crafts a still-valid copy of a stock fallback level around the user goal."""
        goal = custom_prompt.strip()
        level = dict(level)
        level["title"] = f"{level.get('title', 'Mission')} — {goal}"
        level["situation_probleme"] = (
            f"Objectif pédagogique : {goal}.\n\n" + level.get("situation_probleme", "")
        )
        level["objective"] = f"{goal}. " + level.get("objective", "")
        return level

    # ---------------------------------------------------------------
    # Linux fallback levels
    # ---------------------------------------------------------------
    @staticmethod
    def _linux_level_0(domain, user_level, custom_prompt):
        return {
            "title": "Exploration système et verrouillage des permissions",
            "situation_probleme": (
                "L'audit SOC détecte une fuite de données : un fichier contenant une clé de sauvegarde "
                "classifiée est lisible par tous les utilisateurs sur la machine 'prod-1'. Vous êtes dépêché "
                "sur place. Explorez le système, localisez le fichier sensible et verrouillez immédiatement "
                "ses permissions pour stopper l'exposition. La mission est urgente : chaque minute d'accès "
                "non contrôlé augmente le risque d'exfiltration."
            ),
            "consigne": (
                "1) Depuis la racine de la machine, listez les répertoires avec `ls -la`.\n"
                "2) Entrez dans le dossier du compte suspect : `cd home/suspect`.\n"
                "3) Listez son contenu avec `ls -la` et lisez `secret.txt` avec `cat secret.txt`.\n"
                "4) Restreignez l'accès au fichier au seul propriétaire : `chmod 600 secret.txt`.\n"
                "5) Vérifiez le résultat avec `ls -l secret.txt` (les permissions doivent afficher -rw-------)."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Une clé de sauvegarde classifiée (secret.txt) est lisible par tous sur 'prod-1'. "
                "Votre mission : rendre ce fichier accessible au seul propriétaire (mode 600).\n\n"
                "### 2. Environnement cible\n"
                "Vous démarrez à la racine de la sandbox. Les répertoires concernés :\n"
                "- `home/user/` : votre répertoire personnel (vide au départ).\n"
                "- `home/suspect/` : contient `secret.txt` (mode 644 : lisible par tout le monde).\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "ls -la                    # explorer la racine de la machine\n"
                "cd home/suspect           # entrer dans le dossier suspect\n"
                "ls -la                    # lister les fichiers (perm 644 attendue)\n"
                "cat secret.txt            # confirmer le contenu classifié\n"
                "chmod 600 secret.txt      # verrouiller au seul propriétaire\n"
                "```\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "ls -l secret.txt          # doit afficher -rw-------\n"
                "```\n"
                "Le premier groupe `rw-` = lecture + écriture pour le propriétaire ; les deux autres "
                "groupes (groupe, autres) affichent `---`.\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `home/suspect/secret.txt` doit avoir les permissions `600`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Ne pas utiliser `chmod 777` (trop permissif, nouvelle faille).\n"
                "- Ne pas confondre le dossier et le fichier : on verrouille `secret.txt`, pas son dossier.\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Localiser le fichier secret et verrouiller ses permissions à 600.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "home/suspect": {
                            "secret.txt": {
                                "content": "CONFIDENTIEL: clé de sauvegarde B64_AstaSecure!",
                                "perms": "644",
                            },
                            "notes.txt": {"content": "Penser à sécuriser le fichier secret.", "perms": "644"},
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [{"path": "home/suspect/secret.txt", "perms": "600"}]
                },
                "commands_allowed": ["ls", "cd", "cat", "chmod", "pwd", "whoami", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Un fichier suspect se trouve dans le dossier home/suspect.",
                "Utilisez `ls -la home/suspect` pour révéler tous les fichiers.",
                "La commande `chmod 600 secret.txt` (depuis home/suspect) restreint l'accès au seul propriétaire.",
            ],
            "difficulty": 2,
            "points": 100,
            "time_limit": 600,
        }

    @staticmethod
    def _linux_level_1(domain, user_level, custom_prompt):
        return {
            "title": "Analyse de logs et détection d'intrusion",
            "situation_probleme": (
                "Le service SSH subit une attaque par force brute : des milliers de tentatives de connexion "
                "échouées proviennent de la même adresse. L'administrateur vous demande d'analyser le journal "
                "d'authentification, d'identifier l'IP attaquante et de consigner la preuve dans un rapport "
                "pour l'escalade auprès du CERT."
            ),
            "consigne": (
                "1) Listez le dossier `var/log` et repérez `auth.log` : `ls var/log`.\n"
                "2) Analysez les échecs : `grep 'Failed password' var/log/auth.log`.\n"
                "3) Comptez les échecs par IP :\n"
                "   `grep 'Failed password' var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn`\n"
                "4) L'IP la plus fréquente est l'attaquant (192.168.1.150).\n"
                "5) Écrivez le rapport : `echo 192.168.1.150 > home/user/attacker_ip.txt`.\n"
                "6) Vérifiez : `cat home/user/attacker_ip.txt`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Une force brute SSH est en cours. Objectif : extraire l'IP de l'attaquant depuis "
                "`var/log/auth.log` et l'écrire dans `home/user/attacker_ip.txt`.\n\n"
                "### 2. Environnement cible\n"
                "- `var/log/auth.log` : journal d'authentification (les lignes 'Failed password' indiquent "
                "des échecs).\n"
                "- `home/user/attacker_ip.txt` : rapport à créer (il n'existe pas encore).\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "ls var/log                                             # localiser le journal\n"
                "grep 'Failed password' var/log/auth.log                # filtrer les échecs\n"
                "grep 'Failed password' var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn\n"
                "echo 192.168.1.150 > home/user/attacker_ip.txt         # écrire le rapport\n"
                "```\n"
                "Le pipeline `awk '{print $11}'` extrait l'adresse IP (11e champ), `sort | uniq -c` la "
                "compte, `sort -rn` classe par ordre décroissant : la première ligne est l'attaquant.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "cat home/user/attacker_ip.txt   # doit afficher 192.168.1.150\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- Le fichier `home/user/attacker_ip.txt` doit exister et contenir `192.168.1.150`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Ne pas confondre avec la ligne 'Accepted publickey' (connexion légitime).\n"
                "- Utiliser un seul `>` (écrasement), pas `>>` (ajout).\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Identifier l'IP de l'attaquant et écrire home/user/attacker_ip.txt contenant 192.168.1.150.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "var/log": {
                            "auth.log": {
                                "content": (
                                    "Jul 25 10:01:22 server sshd[1204]: Failed password for invalid user admin from 192.168.1.150 port 49152 ssh2\n"
                                    "Jul 25 10:01:25 server sshd[1204]: Failed password for invalid user admin from 192.168.1.150 port 49155 ssh2\n"
                                    "Jul 25 10:01:28 server sshd[1204]: Failed password for invalid user root from 192.168.1.150 port 49158 ssh2\n"
                                    "Jul 25 10:02:10 server sshd[1210]: Accepted publickey for user admin from 192.168.1.10 port 49200 ssh2\n"
                                    "Jul 25 10:02:11 server sshd[1211]: Failed password for invalid user ubuntu from 10.0.0.7 port 50001 ssh2\n"
                                    "Jul 25 10:02:12 server sshd[1211]: Failed password for invalid user oracle from 10.0.0.7 port 50002 ssh2\n"
                                    "Jul 25 10:02:13 server sshd[1211]: Failed password for invalid user pi from 10.0.0.7 port 50003 ssh2\n"
                                ),
                                "perms": "640",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "home/user/attacker_ip.txt", "content_contains": "192.168.1.150"}
                    ]
                },
                "commands_allowed": ["ls", "cd", "cat", "grep", "awk", "sort", "uniq", "echo", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Le journal se trouve dans var/log/auth.log.",
                "Comptez les 'Failed password' par IP avec `sort | uniq -c`.",
                "L'adresse qui revient le plus souvent est 192.168.1.150 — écrivez-la avec echo.",
            ],
            "difficulty": 3,
            "points": 150,
            "time_limit": 900,
        }

    @staticmethod
    def _linux_level_2(domain, user_level, custom_prompt):
        return {
            "title": "Chasse au processus malveillant",
            "situation_probleme": (
                "Un script de minage de crypto-monnaie non autorisé tourne en tâche de fond sous le nom "
                "'miner_script' et consomme les ressources du serveur de production. Localisez-le, identifiez "
                "son PID et éliminez-le proprement, puis supprimez son exécutable pour éviter tout redémarrage."
            ),
            "consigne": (
                "1) Listez les processus avec `ps aux` et repérez `miner_script`.\n"
                "2) Notez son PID (2e colonne) puis arrêtez-le : `kill <PID>`.\n"
                "3) Supprimez son exécutable resté dans /tmp : `rm tmp/miner_script`.\n"
                "4) Vérifiez qu'il a disparu : `ps aux | grep miner` (aucun résultat attendu)."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Un mineur de crypto non autorisé consomme les ressources du serveur. Mission : arrêter le "
                "processus `miner_script` (par son PID) et supprimer son exécutable `tmp/miner_script`.\n\n"
                "### 2. Environnement cible\n"
                "- Le processus `miner_script` tourne en arrière-plan (PID de la liste `ps aux`).\n"
                "- `tmp/miner_script` : l'exécutable malveillant à supprimer.\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "ps aux                    # lister tous les processus\n"
                "ps aux | grep miner       # localiser miner_script et son PID\n"
                "kill <PID>                # arrêter (SIGTERM = arrêt propre)\n"
                "rm tmp/miner_script       # supprimer l'exécutable\n"
                "```\n"
                "`ps aux` affiche le PID en 2e colonne. Si le processus résiste, `kill -9 <PID>` (SIGKILL) "
                "force l'arrêt.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "ps aux | grep miner       # aucun résultat attendu\n"
                "ls tmp                    # miner_script absent\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- Le processus `miner_script` ne doit plus tourner.\n"
                "- Le fichier `tmp/miner_script` doit être supprimé.\n\n"
                "### 6. Pièges à éviter\n"
                "- Tuer le mauvais PID (vérifier avant de `kill`).\n"
                "- Ne pas `rm` un dossier du système : ciblez uniquement `tmp/miner_script`.\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Arrêter le processus miner_script et supprimer tmp/miner_script.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "tmp": {
                            "miner_script": {
                                "content": "#!/bin/bash\nwhile true; do echo 'mining...'; sleep 1; done",
                                "perms": "755",
                            }
                        },
                    },
                    "processes": [{"pid": 451, "name": "miner_script", "ppid": 101}],
                },
                "expected_state": {
                    "process_not_running": "miner_script",
                    "file_not_exists": "tmp/miner_script",
                },
                "commands_allowed": ["ls", "ps", "grep", "kill", "rm", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Utilisez `ps aux` puis filtrez avec `grep miner` pour trouver miner_script.",
                "Le PID du processus est la deuxième colonne de `ps aux`.",
                "Après `kill <PID>`, supprimez l'exécutable : `rm tmp/miner_script`.",
            ],
            "difficulty": 4,
            "points": 180,
            "time_limit": 600,
        }

    # ---------------------------------------------------------------
    # Security fallback levels
    # ---------------------------------------------------------------
    @staticmethod
    def _security_level_0(domain, user_level, custom_prompt):
        return {
            "title": "Verrouillage d'un coffre de sauvegarde exposé",
            "situation_probleme": (
                "Une sauvegarde chiffrée 'vault.db' a été laissée lisible par tous sur le serveur de staging. "
                "Tout utilisateur local peut la lire et potentiellement l'exfiltrer. Restaurez immédiatement "
                "la confidentialité de ce fichier avant la fin du créneau de maintenance."
            ),
            "consigne": (
                "1) Observez les permissions du fichier avec `ls -l home/user/vault.db`.\n"
                "2) Confirmez l'exposition en le lisant : `cat home/user/vault.db`.\n"
                "3) Restreignez l'accès au seul propriétaire : `chmod 600 home/user/vault.db`.\n"
                "4) Vérifiez le changement : `ls -l home/user/vault.db`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Le coffre de sauvegarde `home/user/vault.db` est lisible par tous (mode 644). Mission : le "
                "rendre accessible au seul propriétaire (mode 600).\n\n"
                "### 2. Environnement cible\n"
                "- `home/user/vault.db` : fichier chiffré contenant la clé AES et la passphrase de sauvegarde "
                "(mode actuel 644 = tout le monde peut lire).\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "ls -l home/user/vault.db     # constater l'exposition (mode 644)\n"
                "cat home/user/vault.db       # confirmer le contenu sensible\n"
                "chmod 600 home/user/vault.db # restreindre au seul propriétaire\n"
                "```\n"
                "En notation octale : propriétaire=6 (rw-), groupe=0 (---), autres=0 (---).\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "ls -l home/user/vault.db     # doit afficher -rw-------\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `home/user/vault.db` doit avoir les permissions `600`.\n\n"
                "### 6. Pièges à éviter et bonnes pratiques\n"
                "- Ne jamais laisser un secret en mode 644 dans un répertoire accessible.\n"
                "- Adopter un `umask 077` par défaut et chiffrer les sauvegardes.\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Restreindre les permissions de home/user/vault.db à 600.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {
                            "vault.db": {
                                "content": "BACKUP_AES_KEY=a3f9c21d88b4e7...\nBACKUP_PASSPHRASE=SuperSecure!42",
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [{"path": "home/user/vault.db", "perms": "600"}]
                },
                "commands_allowed": ["ls", "cat", "chmod", "pwd", "whoami", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Le fichier vault.db se trouve dans home/user, votre répertoire personnel.",
                "`ls -l home/user/vault.db` affiche les permissions actuelles.",
                "La commande `chmod 600 home/user/vault.db` rend le fichier lisible uniquement par son propriétaire.",
            ],
            "difficulty": 2,
            "points": 100,
            "time_limit": 600,
        }

    @staticmethod
    def _security_level_1(domain, user_level, custom_prompt):
        return {
            "title": "Audit SSH : cartographie d'une force brute",
            "situation_probleme": (
                "Le pare-feu log des connexions suspectes. L'équipe doit identifier l'attaquant qui tente de "
                "forcer l'accès SSH avant de le bannir. Analysez le journal d'authentification et produisez "
                "le rapport d'alerte demandé pour l'escalade sécurité."
            ),
            "consigne": (
                "1) Analysez le journal : `grep 'Failed password' var/log/auth.log`.\n"
                "2) Comptez les échecs par IP :\n"
                "   `grep 'Failed password' var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn`\n"
                "3) Déterminez l'IP de l'attaquant (le plus grand nombre d'échecs).\n"
                "4) Écrivez le rapport : `echo 192.168.1.150 > home/user/attacker_ip.txt`.\n"
                "5) Vérifiez : `cat home/user/attacker_ip.txt`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Une force brute SSH est en cours. Objectif : identifier l'IP attaquante et produire le "
                "rapport `home/user/attacker_ip.txt`.\n\n"
                "### 2. Environnement cible\n"
                "- `var/log/auth.log` : journal d'authentification contenant les échecs 'Failed password'.\n"
                "- `home/user/attacker_ip.txt` : rapport à créer.\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "grep 'Failed password' var/log/auth.log\n"
                "grep 'Failed password' var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn\n"
                "echo 192.168.1.150 > home/user/attacker_ip.txt\n"
                "```\n"
                "Le pipeline compte les occurrences de chaque IP : la première ligne du résultat (compteur le "
                "plus élevé) désigne l'attaquant.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "cat home/user/attacker_ip.txt   # doit afficher 192.168.1.150\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `home/user/attacker_ip.txt` doit contenir `192.168.1.150`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Ignorer les lignes 'Accepted' (connexions légitimes).\n"
                "- En production, l'IP serait ensuite bannie (fail2ban / règle de pare-feu).\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Écrire home/user/attacker_ip.txt contenant l'IP de l'attaquant (192.168.1.150).",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "var/log": {
                            "auth.log": {
                                "content": (
                                    "Jul 25 10:01:22 server sshd[1204]: Failed password for invalid user admin from 192.168.1.150 port 49152 ssh2\n"
                                    "Jul 25 10:01:25 server sshd[1204]: Failed password for invalid user admin from 192.168.1.150 port 49155 ssh2\n"
                                    "Jul 25 10:01:28 server sshd[1204]: Failed password for invalid user root from 192.168.1.150 port 49158 ssh2\n"
                                    "Jul 25 10:02:10 server sshd[1210]: Accepted publickey for user admin from 192.168.1.10 port 49200 ssh2\n"
                                    "Jul 25 10:02:11 server sshd[1211]: Failed password for invalid user root from 10.0.0.7 port 50001 ssh2\n"
                                    "Jul 25 10:02:12 server sshd[1211]: Failed password for invalid user root from 10.0.0.7 port 50002 ssh2\n"
                                    "Jul 25 10:02:13 server sshd[1211]: Failed password for invalid user root from 10.0.0.7 port 50003 ssh2\n"
                                    "Jul 25 10:02:14 server sshd[1211]: Failed password for invalid user root from 10.0.0.7 port 50004 ssh2\n"
                                ),
                                "perms": "640",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "home/user/attacker_ip.txt", "content_contains": "192.168.1.150"}
                    ]
                },
                "commands_allowed": ["ls", "cd", "cat", "grep", "awk", "sort", "uniq", "echo", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Les échecs de connexion sont marqués 'Failed password' dans var/log/auth.log.",
                "Combinez grep + awk + sort + uniq -c pour compter les IP.",
                "L'IP la plus fréquente est 192.168.1.150 — écrivez-la avec echo.",
            ],
            "difficulty": 3,
            "points": 150,
            "time_limit": 900,
        }

    @staticmethod
    def _security_level_2(domain, user_level, custom_prompt):
        return {
            "title": "Durcissement de la configuration SSH",
            "situation_probleme": (
                "L'audit de conformité révèle que le serveur SSH autorise la connexion root avec mot de passe "
                "— une faille critique. Vous devez durcir `etc/ssh/sshd_config` en désactivant ces deux "
                "options dangereuses, comme le prescrit la politique de sécurité interne."
            ),
            "consigne": (
                "1) Lisez la configuration : `cat etc/ssh/sshd_config`.\n"
                "2) Remplacez 'PermitRootLogin yes' par 'no' :\n"
                "   `sed -i 's/PermitRootLogin yes/PermitRootLogin no/' etc/ssh/sshd_config`\n"
                "3) Remplacez 'PasswordAuthentication yes' par 'no' :\n"
                "   `sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' etc/ssh/sshd_config`\n"
                "4) Vérifiez le résultat :\n"
                "   `grep -E 'PermitRootLogin|PasswordAuthentication' etc/ssh/sshd_config`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Le serveur SSH autorise le login root et l'authentification par mot de passe, ce qui expose "
                "le serveur aux attaques par force brute. Mission : durcir `etc/ssh/sshd_config` en passant "
                "les deux options à `no`.\n\n"
                "### 2. Environnement cible\n"
                "- `etc/ssh/sshd_config` : fichier de configuration du serveur SSH (lignes `PermitRootLogin "
                "yes` et `PasswordAuthentication yes` à modifier).\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "cat etc/ssh/sshd_config                                          # lire la config\n"
                "sed -i 's/PermitRootLogin yes/PermitRootLogin no/' etc/ssh/sshd_config\n"
                "sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' etc/ssh/sshd_config\n"
                "```\n"
                "`sed -i 's/ancien/nouveau/' fichier` remplace la première occurrence directement dans le "
                "fichier (-i = in place). Ajoutez `g` en fin d'expression pour toutes les occurrences.\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "grep -E 'PermitRootLogin|PasswordAuthentication' etc/ssh/sshd_config\n"
                "# Résultat attendu : PermitRootLogin no et PasswordAuthentication no\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `etc/ssh/sshd_config` ne doit plus contenir `PermitRootLogin yes`.\n"
                "- `etc/ssh/sshd_config` ne doit plus contenir `PasswordAuthentication yes`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Vérifier l'orthographe exacte des options (majuscules/minuscules).\n"
                "- Toujours contrôler le fichier avec `cat` ou `grep` après édition.\n"
                "- En production, l'authentification se fait alors par clés publiques (`PubkeyAuthentication yes`)."
            ),
            "objective": "Modifier sshd_config pour désactiver le login root et l'authentification par mot de passe.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "etc/ssh": {
                            "sshd_config": {
                                "content": (
                                    "# Astatarote default sshd_config\n"
                                    "Port 22\n"
                                    "PermitRootLogin yes\n"
                                    "PasswordAuthentication yes\n"
                                    "PubkeyAuthentication yes\n"
                                    "MaxAuthTries 6\n"
                                ),
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "etc/ssh/sshd_config", "content_not_contains": "PermitRootLogin yes"},
                        {"path": "etc/ssh/sshd_config", "content_not_contains": "PasswordAuthentication yes"},
                    ]
                },
                "commands_allowed": ["ls", "cat", "sed", "grep", "echo", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Le fichier à modifier est etc/ssh/sshd_config.",
                "Utilisez `sed -i` pour remplacer 'yes' par 'no' dans le fichier.",
                "Il faut traiter les lignes PermitRootLogin et PasswordAuthentication.",
            ],
            "difficulty": 4,
            "points": 180,
            "time_limit": 900,
        }

    # ---------------------------------------------------------------
    # Network fallback levels
    # ---------------------------------------------------------------
    @staticmethod
    def _network_level_0(domain, user_level, custom_prompt):
        return {
            "title": "Cartographie des hôtes et services internes",
            "situation_probleme": (
                "En préparation d'un pentest interne autorisé, vous devez cartographier les hôtes du réseau "
                "d'entreprise. Le fichier `etc/hosts` référence les machines connues. Localisez l'adresse de "
                "la base de données 'db.internal' et consignez-la dans votre rapport."
            ),
            "consigne": (
                "1) Lisez le fichier de résolution : `cat etc/hosts`.\n"
                "2) Identifiez l'entrée correspondant à 'db.internal'.\n"
                "3) Extrayez son adresse IP : `grep db.internal etc/hosts | awk '{print $1}'`.\n"
                "4) Écrivez le rapport : `echo 10.10.2.15 > home/user/db_ip.txt`.\n"
                "5) Vérifiez : `cat home/user/db_ip.txt`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Cartographier le réseau interne. Objectif : extraire l'IP de la base de données `db.internal` "
                "depuis `etc/hosts` et l'écrire dans `home/user/db_ip.txt`.\n\n"
                "### 2. Environnement cible\n"
                "- `etc/hosts` : table de résolution locale (IP <TAB> nom), utilisée avant le DNS.\n"
                "- `home/user/db_ip.txt` : rapport à créer (il n'existe pas encore).\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "cat etc/hosts                          # lire la table de résolution\n"
                "grep db.internal etc/hosts             # isoler la ligne de la base de données\n"
                "grep db.internal etc/hosts | awk '{print $1}'   # extraire l'IP (1er champ)\n"
                "echo 10.10.2.15 > home/user/db_ip.txt  # écrire le rapport\n"
                "```\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "cat home/user/db_ip.txt   # doit afficher 10.10.2.15\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `home/user/db_ip.txt` doit contenir `10.10.2.15`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Ne pas confondre avec `web.internal` (10.10.1.20) ou `mail.internal` (10.10.3.11).\n"
                "- `awk '{print $1}'` extrait bien la première colonne (l'adresse IP).\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Écrire home/user/db_ip.txt contenant l'IP de db.internal (10.10.2.15).",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "etc": {
                            "hosts": {
                                "content": (
                                    "127.0.0.1   localhost\n"
                                    "10.10.0.1   gateway.internal\n"
                                    "10.10.1.20  web.internal\n"
                                    "10.10.2.15  db.internal\n"
                                    "10.10.3.11  mail.internal\n"
                                ),
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "home/user/db_ip.txt", "content_contains": "10.10.2.15"}
                    ]
                },
                "commands_allowed": ["ls", "cat", "grep", "awk", "echo", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Le fichier etc/hosts liste les hôtes connus du réseau.",
                "La ligne de db.internal commence par son adresse IP (1er champ).",
                "`grep db.internal etc/hosts | awk '{print $1}'` donne l'IP : 10.10.2.15.",
            ],
            "difficulty": 2,
            "points": 100,
            "time_limit": 600,
        }

    @staticmethod
    def _network_level_1(domain, user_level, custom_prompt):
        return {
            "title": "Correction d'une résolution DNS détournée",
            "situation_probleme": (
                "Le fichier `etc/hosts` de l'hôte a été altéré : la résolution de 'gateway.internal' pointe "
                "vers une IP inconnue, cassant la connectivité. Restaurez la bonne adresse (10.10.0.1) pour "
                "rétablir le routage interne."
            ),
            "consigne": (
                "1) Affichez la configuration : `cat etc/hosts`.\n"
                "2) Repérez la ligne incorrecte de 'gateway.internal'.\n"
                "3) Corrigez-la : `sed -i 's/10.10.0.99/10.10.0.1/' etc/hosts`.\n"
                "4) Vérifiez : `grep gateway.internal etc/hosts`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "La résolution de `gateway.internal` a été détournée vers une IP inconnue. Mission : restaurer "
                "`10.10.0.1` dans `etc/hosts` pour rétablir le routage.\n\n"
                "### 2. Environnement cible\n"
                "- `etc/hosts` : table de résolution locale corrompue (ligne fautive `10.10.0.99 gateway.internal`).\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "cat etc/hosts                                   # identifier la ligne fautive\n"
                "sed -i 's/10.10.0.99/10.10.0.1/' etc/hosts      # corriger l'adresse\n"
                "```\n"
                "Une entrée `etc/hosts` corrompue peut rediriger un service vers un serveur malveillant "
                "(détournement DNS local).\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "grep gateway.internal etc/hosts   # doit afficher 10.10.0.1 gateway.internal\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- `etc/hosts` doit contenir `10.10.0.1 gateway.internal`.\n"
                "- `etc/hosts` ne doit plus contenir `10.10.0.99`.\n\n"
                "### 6. Pièges à éviter\n"
                "- Ne pas introduire d'espace/onglet en trop dans la ligne corrigée.\n"
                "- Vérifier toujours le fichier après édition.\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Corriger etc/hosts pour que gateway.internal résolve vers 10.10.0.1.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "etc": {
                            "hosts": {
                                "content": (
                                    "127.0.0.1   localhost\n"
                                    "10.10.0.99  gateway.internal\n"
                                    "10.10.1.20  web.internal\n"
                                    "10.10.2.15  db.internal\n"
                                ),
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [],
                },
                "expected_state": {
                    "files_checks": [
                        {"path": "etc/hosts", "content_contains": "10.10.0.1  gateway.internal"},
                        {"path": "etc/hosts", "content_not_contains": "10.10.0.99"},
                    ]
                },
                "commands_allowed": ["ls", "cat", "sed", "grep", "echo", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "La ligne fautive pointe gateway.internal vers 10.10.0.99.",
                "Utilisez `sed -i` pour remplacer la mauvaise adresse dans etc/hosts.",
                "La bonne adresse du gateway est 10.10.0.1.",
            ],
            "difficulty": 3,
            "points": 150,
            "time_limit": 900,
        }

    @staticmethod
    def _network_level_2(domain, user_level, custom_prompt):
        return {
            "title": "Désactivation d'un relais de spam indésirable",
            "situation_probleme": (
                "Un processus 'spam_relay' envoie du courrier non sollicité depuis la machine. Il a été lancé "
                "par un utilisateur compromis et son fichier de configuration se trouve dans `etc`. Arrêtez le "
                "processus et supprimez la configuration compromise."
            ),
            "consigne": (
                "1) Repérez le processus : `ps aux | grep spam_relay`.\n"
                "2) Identifiez son PID et arrêtez-le : `kill <PID>`.\n"
                "3) Supprimez la configuration compromise : `rm etc/spam_relay.conf`.\n"
                "4) Vérifiez qu'aucun processus ne subsiste : `ps aux | grep spam`."
            ),
            "support_technique": (
                "### 1. Contexte et objectif\n"
                "Un relais de spam (`spam_relay`) est actif sur la machine. Mission : arrêter le processus "
                "(par son PID) et supprimer la configuration compromise `etc/spam_relay.conf`.\n\n"
                "### 2. Environnement cible\n"
                "- Le processus `spam_relay` tourne en arrière-plan.\n"
                "- `etc/spam_relay.conf` : configuration du relais à supprimer.\n\n"
                "### 3. Méthodologie étape par étape\n"
                "```bash\n"
                "ps aux | grep spam_relay    # trouver le processus et son PID\n"
                "kill <PID>                  # arrêter le relais\n"
                "rm etc/spam_relay.conf      # supprimer la configuration\n"
                "```\n\n"
                "### 4. Vérification\n"
                "```bash\n"
                "ps aux | grep spam          # aucun résultat attendu\n"
                "ls etc/spam_relay.conf      # doit afficher 'No such file'\n"
                "```\n\n"
                "### 5. Critères de validation automatiques\n"
                "- Le processus `spam_relay` ne doit plus tourner.\n"
                "- Le fichier `etc/spam_relay.conf` doit être supprimé.\n\n"
                "### 6. Pièges à éviter\n"
                "- Vérifier le PID avant de `kill` (ne pas tuer un autre processus).\n"
                "- Cibler uniquement `etc/spam_relay.conf`, pas d'autres fichiers de configuration.\n"
                "- Les chemins sont relatifs à la racine (pas de `/` initial)."
            ),
            "objective": "Arrêter le processus spam_relay et supprimer etc/spam_relay.conf.",
            "scenario": {
                "type": "simulation",
                "initial_state": {
                    "cwd": ".",
                    "fs": {
                        "home/user": {},
                        "etc": {
                            "spam_relay.conf": {
                                "content": "relay_host=mail.spam-zone.net\nrelay_port=25\nenabled=1",
                                "perms": "644",
                            }
                        },
                    },
                    "processes": [{"pid": 783, "name": "spam_relay", "ppid": 1}],
                },
                "expected_state": {
                    "process_not_running": "spam_relay",
                    "file_not_exists": "etc/spam_relay.conf",
                },
                "commands_allowed": ["ls", "ps", "grep", "kill", "rm", "pwd", "help"],
                "forbidden_commands": [],
            },
            "hints": [
                "Le processus spam_relay est visible dans `ps aux`.",
                "Notez son PID (deuxième colonne) puis `kill <PID>`.",
                "Supprimez enfin etc/spam_relay.conf.",
            ],
            "difficulty": 4,
            "points": 180,
            "time_limit": 600,
        }

    # ------------------------------------------------------------------
    # Pedagogical chat (Nemesis)
    # ------------------------------------------------------------------
    @classmethod
    def assist_chat(
        cls,
        game_id: int,
        level_title: str,
        level_objective: str,
        level_consigne: str,
        current_state: Dict[str, Any],
        chat_history: List[Dict[str, Any]],
        user_message: str,
        preferences: Dict[str, Any],
    ) -> str:
        provider = preferences.get("provider_ia", "fallback")
        api_key = preferences.get("api_key")

        if provider == "fallback" or not api_key:
            return cls._generate_fallback_chat(
                level_title, level_objective, level_consigne, current_state, user_message
            )

        system_prompt = (
            "Tu es Nemesis, le coéquipier d'apprentissage d'Astatarote.\n"
            "Tu es un assistant pédagogique d'élite dans un terminal Linux réel, parlant français de façon "
            "naturelle, motivante et amicale.\n"
            "Ton but est d'aider l'utilisateur sans jamais donner la solution brute. Tu expliques les "
            "concepts, proposes des indices progressifs et vérifies la démarche.\n"
            "Si l'utilisateur est bloqué depuis longtemps, tu peux devenir plus explicite.\n"
            "Sois concis : l'utilisateur lit tes réponses dans un volet de chat à côté de son terminal.\n"
            "Utilise les conventions Markdown simples (gras, listes, blocs de code avec la commande exacte)."
        )

        context = (
            f"--- CONTEXTE DU DÉFI ACTUEL ---\n"
            f"Défi : {level_title}\n"
            f"Objectif : {level_objective}\n"
            f"Consigne : {level_consigne}\n"
        )

        messages = [{"role": "system", "content": system_prompt + "\n\n" + context}]
        for msg in chat_history[-10:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("message", "")})
        messages.append({"role": "user", "content": user_message})

        try:
            return cls._call_provider_api(provider, api_key, messages)
        except Exception as e:
            logger.error("Error calling AI for chat, fallback used: %s", e)
            return cls._generate_fallback_chat(
                level_title, level_objective, level_consigne, current_state, user_message
            )

    # ------------------------------------------------------------------
    @classmethod
    def _generate_fallback_chat(
        cls,
        level_title: str,
        level_objective: str,
        level_consigne: str,
        current_state: Dict[str, Any],
        user_message: str,
    ) -> str:
        msg = user_message.lower()

        if any(w in msg for w in ["salut", "bonjour", "hello", "hey", "yo", "coucou"]):
            return (
                "Salut ! Je suis Nemesis, ton coéquipier cyber. On attaque le défi **'%s'** ensemble.\n"
                "Besoin d'un indice, d'une explication ou d'une relecture de ta démarche ?"
            ) % level_title

        if any(w in msg for w in ["solution", "réponse", "reponse", "donne", "comment faire"]):
            return (
                "Je ne te donne pas la solution brute — ce serait gâcher l'apprentissage ! Voici le cadre :\n\n"
                "**Objectif :** %s\n\n"
                "**Point de départ :** lis bien la consigne ci-dessous et découpe-la en étapes.\n\n"
                "```\n%s\n```\n\n"
                "Propose-moi ce que tu as déjà essayé, je t'oriente vers la bonne commande."
            ) % (level_objective, level_consigne)

        if "commande" in msg or "commandes" in msg or "outil" in msg:
            return (
                "Dans cette sandbox Linux réelle, tu disposes de tout l'outillage standard : `ls`, `cd`, "
                "`cat`, `grep`, `sed`, `awk`, `chmod`, `chown`, `ps`, `kill`, `find`, `head`, `tail`, `sort`, "
                "`uniq`, `wc`, `tar`...\n\n"
                "Tape `man <commande>` pour la documentation, ou `help` pour la liste des aides disponibles."
            )

        if "permission" in msg or "chmod" in msg or "chown" in msg:
            return (
                "Les permissions Linux se lisent en 3 groupes : propriétaire / groupe / autres.\n\n"
                "- `chmod 600 fichier` : lecture+écriture pour le propriétaire, rien pour les autres.\n"
                "- `chmod 644 fichier` : lecture pour tous, écriture propriétaire (par défaut).\n"
                "- `chmod 755 dossier` : droits complets propriétaire, lecture+exécution pour les autres.\n"
                "- `chown user:group fichier` : change le propriétaire et le groupe.\n\n"
                "En notation octale : r=4, w=2, x=1 (la somme compose le chiffre)."
            )

        if "process" in msg or "kill" in msg or "ps" in msg or "pid" in msg:
            return (
                "Pour gérer les processus :\n\n"
                "- `ps aux` liste tous les processus avec leur PID (2e colonne).\n"
                "- `kill <PID>` envoie SIGTERM (arrêt propre).\n"
                "- `kill -9 <PID>` envoie SIGKILL (arrêt forcé).\n\n"
                "Astuce : `ps aux | grep <nom>` filtre la liste pour trouver le processus recherché."
            )

        if "log" in msg or "auth.log" in msg or "journal" in msg or "grep" in msg:
            return (
                "Pour analyser des logs efficacement (les chemins sont relatifs à la racine de la sandbox) :\n\n"
                "- `cat var/log/auth.log` affiche tout le journal.\n"
                "- `grep 'Failed password' var/log/auth.log` filtre les échecs.\n"
                "- `grep 'Failed' var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn` "
                "compte les IP fautives par fréquence.\n\n"
                "La première ligne de ce dernier résultat est généralement l'attaquant."
            )

        if "sed" in msg or "editer" in msg or "modifier" in msg or "remplacer" in msg:
            return (
                "Pour modifier un fichier de configuration depuis le shell :\n\n"
                "- `sed -i 's/ancien/nouveau/' fichier` remplace la 1ère occurrence in-place.\n"
                "- `sed -i 's/ancien/nouveau/g' fichier` remplace toutes les occurrences.\n"
                "- `echo 'texte' >> fichier` ajoute une ligne à la fin.\n"
                "- `echo 'texte' > fichier` écrase le fichier.\n\n"
                "Toujours vérifier avec `cat fichier` ou `grep motcle fichier` après édition."
            )

        return (
            "Intéressant ! Pour avancer sur **'%s'**, rappelle-toi l'objectif : %s.\n\n"
            "Décompose la consigne en petites étapes et vérifie ton travail après chacune. "
            "Dis-moi précisément où tu bloques (quelle commande, quel résultat), et je t'aiguille."
        ) % (level_title, level_objective)
