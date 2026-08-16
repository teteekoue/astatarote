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
            with httpx.Client(timeout=70.0) as client:
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
        """Generate a complete level using the configured LLM (pure AI, no templates).

        The model receives the system prompt plus the user's own learning goal and
        creates the whole level itself: scenario, filesystem, documents, mission,
        validation checks and the terminal environment.
        """
        provider = preferences.get("provider_ia", "fallback")
        api_key = preferences.get("api_key")

        if provider == "fallback" or not api_key:
            raise RuntimeError(
                "Aucun fournisseur IA configuré : impossible de générer un niveau de jeu."
            )

        domain = (domain or "linux").lower()
        user_level = (user_level or "beginner").lower()

        system_prompt = (
            "Tu es l'Architecte d'Astatarote, une plateforme éthique d'apprentissage de la "
            "cybersécurité et de l'administration Linux. Tu conçois un niveau de jeu COMPLET et "
            "ORIGINAL, de bout en bout, qui répond EXACTEMENT au sujet demandé par l'utilisateur. "
            "Tu es la seule source du scénario, des documents, de l'arborescence des fichiers et de "
            "la mission : ne te contente jamais d'un sujet générique. Exprime ta réponse UNIQUEMENT "
            "en JSON brut (sans balise Markdown autour du JSON, sans commentaire, sans texte "
            "avant/après).\n\n"
            "CONTRAINTES OBLIGATOIRES SUR LA SANDBOX RÉELLE :\n"
            "- L'utilisateur interagira avec un VRAI shell bash dans une sandbox Linux réelle (Debian "
            "minimale). Le shell démarre À LA RACINE de la sandbox : son répertoire courant est la "
            "racine de la machine virtuelle.\n"
            "- Tous les chemins du scénario ('fs', 'consigne', 'support_technique', 'files_checks') "
            "doivent donc être RELATIFS à cette racine, SANS slash initial : 'home/user', "
            "'home/suspect', 'var/log', 'etc', 'etc/ssh', 'tmp'. N'utilise JAMAIS de chemins absolus "
            "commençant par '/'.\n"
            "- Toutes les commandes citées doivent être de vraies commandes bash disponibles sur une "
            "Debian minimale (ls, cd, cat, grep, sed, awk, chmod, chown, ps, kill, echo, touch, mkdir, "
            "rm, cp, mv, tar, find, head, tail, wc, sort, uniq, cut, tr, tee). nano/vim sont absents.\n"
            "- 'scenario.initial_state.fs' décrit l'arborescence de départ avec des clés relatives à "
            "la racine. Exemple : { \"home/user\": { \"note.txt\": { \"content\": \"...\", "
            "\"perms\": \"644\" } } }.\n"
            "- 'scenario.expected_state.files_checks' définit les contrôles automatiques de "
            "validation, avec des chemins relatifs et des valeurs TRÈS PRÉCISES (permissions en octal "
            "sur 3 chiffres, contenu exact attendu). Ne pose qu'une contrainte raisonnable que "
            "l'utilisateur peut réellement réaliser dans le shell.\n"
            "- 'scenario.initial_state.processes' (optionnel) liste des processus à lancer en fond "
            "({pid: 1, name: 'nom_du_processus'}), pour les défis de gestion de processus ; prévois "
            "alors aussi 'expected_state.process_not_running' avec le même nom.\\n\\n"
            "- Pour créer un fichier contenant des caractères spéciaux (HTML, CSS, scripts avec '!' ou "
            "'<'), utilise TOUJOURS des quotes simples autour du contenu dans 'echo' (exemple : "
            "echo '<!DOCTYPE html>...' > fichier) pour éviter toute interprétation par le shell.\\n\\n"
            "RÉDACTION (en français, immersive et professionnelle) :\\n"
            "- 'situation_probleme' : raconte le scénario complet (contexte, enjeu, urgence, mission "
            "confiée) en lien direct avec le sujet demandé.\n"
            "- 'consigne' : un ORDRE DE MISSION structuré, liste numérotée des OBJECTIFS à atteindre "
            "(résultats attendus, chemins relatifs concernés). La consigne explique QUOI faire, jamais "
            "COMMENT : ne donne pas les commandes exactes qui accomplissent la mission.\n"
            "- 'support_technique' : une AIDE PÉDAGOGIQUE (fiche d'appui) avec ILLUSTRATIONS et "
            "explications : rappel des concepts utiles, exemples de syntaxe des commandes disponibles, "
            "schémas simples, liste des outils concernés, pièges à éviter et méthode pour vérifier "
            "soi-même le résultat. Le support doit AIDER à trouver la solution, JAMAIS la donner en "
            "clair : pas la séquence exacte de commandes qui résout la mission, pas le contenu final "
            "attendu des fichiers.\n"
            "- 'objective' : une phrase décrivant ce que l'utilisateur doit réussir.\n"
            "- 'hints' : 3 indices progressifs, du plus général au plus précis, SANS donner la "
            "solution complète.\n"
            "- 'difficulty' : entier 1-10, 'points' : 80-200, 'time_limit' : 300-900.\n\n"
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
            '      ]\n'
            '    },\n'
            '    "commands_allowed": ["ls", "cd", "cat", "chmod"],\n'
            '    "forbidden_commands": []\n'
            "  },\n"
            '  "hints": ["...", "...", "..."],\n'
            '  "difficulty": 3, "points": 100, "time_limit": 600\n'
            "}"
        )

        user_prompt = (
            f"Crée le niveau {level_index + 1} (index {level_index}, 0 = premier) d'un jeu pour un "
            f"utilisateur de niveau '{user_level}', domaine '{domain}'."
        )
        if custom_prompt and custom_prompt.strip():
            user_prompt += (
                f"\n\nSUJET IMPOSÉ PAR L'UTILISATEUR : '{custom_prompt}'.\n"
                "Construis le niveau ENTIÈREMENT autour de ce sujet : le scénario, l'arborescence des "
                "fichiers, les documents, la consigne, le support technique et les contrôles de "
                "validation doivent correspondre EXACTEMENT à ce sujet — jamais un autre. Invente des "
                "fichiers, répertoires, configurations et documents crédibles et cohérents avec ce "
                "sujet.\n"
                f"Ceci est le niveau {level_index + 1} d'une progression sur CE même sujet : si "
                "level_index > 0, poursuis naturellement ce sujet en augmentant légèrement la "
                "difficulté, sans changer de thème."
            )
        else:
            user_prompt += (
                "\n\nInvente un sujet engageant et cohérent avec ce domaine et ce niveau "
                "d'apprentissage."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response_text = cls._call_provider_api(provider, api_key, messages, json_mode=True)
            return cls._validate_and_normalize(response_text)
        except Exception as e:
            logger.error("AI level generation failed: %s", e)
            raise RuntimeError(f"La génération IA du niveau a échoué : {e}")

    @classmethod
    def _validate_and_normalize(cls, response_text: str) -> Dict[str, Any]:
        extracted = cls._extract_json(response_text)
        data = json.loads(extracted)
        validated = LevelData(**data)
        return validated.model_dump(mode="json")

    # ------------------------------------------------------------------
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
