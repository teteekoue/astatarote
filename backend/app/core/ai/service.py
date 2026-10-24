"""
AI service — pedagogical assistant ("Nemesis").

Since the SaaS pivot, the platform no longer generates games with LLMs
(hallucinations made them unreliable). Games are hand-crafted and frozen in
backend/app/catalog/. The AI now has a single role: helping the player
understand concepts, read errors and get progressive hints — never giving
away the solution.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("astarote.ai")

PROVIDER_MODELS = {
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
    "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", "meta/llama-3.1-70b-instruct"),
    "fireworks": ("https://api.fireworks.ai/inference/v1/chat/completions", "accounts/fireworks/models/deepseek-v4-flash-0731"),
    "cohere": ("https://api.cohere.com/compatibility/v1/chat/completions", "command-r-plus"),
    "together": ("https://api.together.xyz/v1/chat/completions", "meta-llama/Llama-3-70b-chat-hf"),
}


class AIService:
    """Single-purpose assistant: explain, orient, hint — never solve."""

    # ------------------------------------------------------------------
    @staticmethod
    def _call_provider_api(
        provider: str, api_key: str, messages: List[Dict[str, str]]
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
            "temperature": 0.4,
            "max_tokens": 700,
        }
        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Error calling %s API: %s", provider, e)
            raise

    # ------------------------------------------------------------------
    @classmethod
    def assist_chat(
        cls,
        game_name: str,
        level_title: str,
        level_objective: str,
        level_consigne: str,
        level_hints: List[str],
        terminal_history: List[str],
        chat_history: List[Dict[str, Any]],
        user_message: str,
        preferences: Dict[str, Any],
    ) -> str:
        provider = preferences.get("provider_ia", "fallback")
        api_key = preferences.get("api_key")

        if provider == "fallback" or not api_key:
            return cls._fallback_chat(
                level_title, level_objective, level_consigne,
                level_hints, terminal_history, user_message,
            )

        system_prompt = (
            "Tu es Nemesis, l'assistante pédagogique d'Astatarote, une plateforme SaaS "
            "d'apprentissage de Linux et de la cybersécurité.\n"
            "Tu parles français de façon naturelle, motivante et bienveillante.\n"
            "RÈGLES ABSOLUES :\n"
            "- Tu N' DONNES JAMAIS la solution complète d'un défi, ni la séquence exacte de "
            "commandes qui le résout.\n"
            "- Tu expliques les concepts, décryptes les messages d'erreur, proposes des indices "
            "progressifs et vérifies la démarche du joueur.\n"
            "- Le terminal est SIMULÉ et déterministe : pas de vraies commandes réseau, pas "
            "d'éditeur interactif (nano/vim), pas de sed/awk. Oriente vers les commandes "
            "disponibles : ls, cd, cat, grep, find, chmod, chown, ps, kill, echo, mkdir, mv, cp, "
            "rm, touch, head, tail, wc, sort, tree, stat, man, sudo, history, help.\n"
            "- Pour écrire un fichier : echo \"texte\" > fichier (écrase) ou >> (ajoute).\n"
            "- Sois concise : le joueur lit tes réponses dans un panneau à côté du terminal.\n"
            "- Utilise du Markdown simple (gras, listes, `code`)."
        )

        context = (
            f"--- CONTEXTE ---\n"
            f"Parcours : {game_name}\n"
            f"Défi : {level_title}\n"
            f"Objectif : {level_objective}\n"
            f"Consigne : {level_consigne}\n"
        )
        if level_hints:
            context += "Indices officiels (du plus vague au plus précis) :\n"
            context += "\n".join(f"  {i+1}. {h}" for i, h in enumerate(level_hints))
            context += "\n"
        if terminal_history:
            context += (
                "Dernières commandes tapées par le joueur :\n"
                + "\n".join(f"  $ {cmd}" for cmd in terminal_history[-12:])
                + "\n"
            )

        messages = [{"role": "system", "content": system_prompt + "\n\n" + context}]
        for msg in chat_history[-10:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("message", "")})
        messages.append({"role": "user", "content": user_message})

        try:
            return cls._call_provider_api(provider, api_key, messages)
        except Exception as e:
            logger.error("AI chat failed, fallback used: %s", e)
            return cls._fallback_chat(
                level_title, level_objective, level_consigne,
                level_hints, terminal_history, user_message,
            )

    # ------------------------------------------------------------------
    @classmethod
    def _fallback_chat(
        cls,
        level_title: str,
        level_objective: str,
        level_consigne: str,
        level_hints: List[str],
        terminal_history: List[str],
        user_message: str,
    ) -> str:
        """Offline assistant: keyword-driven pedagogy + official hints."""
        msg = user_message.lower()

        def next_hint() -> str:
            asked = sum(1 for m in (terminal_history or []) if "indice" in m.lower())
            if level_hints:
                idx = min(asked, len(level_hints) - 1)
                return f"💡 **Indice {idx + 1}/{len(level_hints)} :** {level_hints[idx]}"
            return "Relis la consigne étape par étape — chaque phrase est une action."

        if any(w in msg for w in ["salut", "bonjour", "hello", "hey", "yo", "coucou", "bonsoir"]):
            return (
                f"Salut ! On travaille ensemble sur **{level_title}**.\n\n"
                "Tu peux me demander :\n"
                "- *« explique-moi la commande X »* — je détaille le concept\n"
                "- *« donne-moi un indice »* — je t'aiguille sans résoudre\n"
                "- *« pourquoi cette erreur ? »* — je décrypte le message\n\n"
                "Où en es-tu ?"
            )

        if any(w in msg for w in ["indice", "hint", "aide", "bloqu", "comprends pas", "perdu"]):
            return next_hint()

        if any(w in msg for w in ["solution", "réponse", "reponse", "donne", "fais le", "comment faire"]):
            return (
                "Je ne donne jamais la solution brute — ce serait te priver du déclic ! 🚫\n\n"
                f"**Rappel de l'objectif :** {level_objective}\n\n"
                + next_hint()
            )

        if "permission denied" in msg or "accès refusé" in msg or "acces refuse" in msg:
            return (
                "**`Permission denied`** signifie que tes droits ne suffisent pas pour cette action.\n\n"
                "Trois questions à te poser :\n"
                "1. Suis-je le **propriétaire** du fichier ? (`ls -l fichier`)\n"
                "2. Quels sont les droits ? (colonne `-rw-r--r--`)\n"
                "3. Ai-je besoin de `sudo` ?\n\n"
                "Un fichier `-rw------- root root` n'est lisible que par root : il te faut `sudo cat ...`."
            )

        if "command not found" in msg:
            return (
                "**`command not found`** : le shell ne connaît pas cette commande.\n\n"
                "Vérifie l'orthographe, ou tape `help` pour la liste des commandes disponibles "
                "dans ce laboratoire. `man <commande>` donne la fiche complète."
            )

        if "no such file" in msg or "introuvable" in msg:
            return (
                "**`No such file or directory`** : le chemin n'existe pas.\n\n"
                "Réflexes :\n"
                "- `pwd` — où suis-je ? (les chemins relatifs partent de là)\n"
                "- `ls` — que contient le dossier courant ?\n"
                "- `find / -name \"nom\"` — cherche partout par nom\n"
                "- Attention aux majuscules : `Documents` ≠ `documents`"
            )

        if any(w in msg for w in ["chmod", "permission", "droits", "rwx", "chown"]):
            return (
                "🔑 **Les permissions Unix en 30 secondes**\n\n"
                "`-rw-r--r--` se lit : type + propriétaire + groupe + autres.\n"
                "En octal : **r=4, w=2, x=1** → 7=rwx, 6=rw-, 5=r-x, 0=---\n\n"
                "- `chmod 600 f` → privé du propriétaire\n"
                "- `chmod 644 f` → lisible par tous\n"
                "- `chmod 750 f` → exécutable pour moi + groupe\n"
                "- `chmod 000 f` → verrouillé pour tous 🔒\n\n"
                "Vérifie avec `ls -l f` ou `stat f`."
            )

        if any(w in msg for w in ["process", "kill", "pid", "cpu", "ps aux"]):
            return (
                "⚙️ **Gérer les processus**\n\n"
                "- `ps aux` — tous les processus (PID en 2e colonne, %CPU juste après)\n"
                "- `ps aux | grep nom` — filtre sur un nom\n"
                "- `top` — trié par CPU\n"
                "- `kill PID` — arrêt propre (SIGTERM)\n"
                "- `kill -9 PID` — forcé (SIGKILL), en dernier recours\n\n"
                "Les processus root ne se tuent pas sans `sudo`."
            )

        if any(w in msg for w in ["grep", "log", "filtrer", "chercher", "compter"]):
            return (
                "🔎 **Chercher et filtrer**\n\n"
                "- `grep \"motif\" fichier` — lignes contenant le motif\n"
                "- `grep -c \"motif\" fichier` — les compter\n"
                "- `grep -i` ignore la casse, `grep -n` numérote, `grep -v` inverse\n"
                "- `head`/`tail -n 20` — début/fin de fichier\n"
                "- Tube : `grep \"x\" f | wc -l` enchaîne les commandes\n"
                "- `find /etc -name \"*.conf\"` — chercher des fichiers"
            )

        if any(w in msg for w in ["echo", "écrire", "ecrire", "créer un fichier", "creer"]):
            return (
                "✍️ **Écrire des fichiers depuis le shell**\n\n"
                "- `echo \"texte\" > fichier` — crée/écrase\n"
                "- `echo \"texte\" >> fichier` — ajoute à la fin\n"
                "- `touch fichier` — fichier vide\n"
                "- `cat fichier` — relis pour vérifier\n\n"
                "L'éditeur interactif n'existe pas ici : la redirection est ton stylo."
            )

        return (
            "Noté ! Pour **{}**, garde en tête l'objectif :\n\n"
            "> {}\n\n"
            "Décompose la consigne en étapes et vérifie après chacune (`ls`, `cat`...).\n"
            "Dis-moi précisément ce qui bloque (commande tapée + résultat obtenu) et je t'oriente.\n\n{}"
        ).format(level_title, level_objective, next_hint())
