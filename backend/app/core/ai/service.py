import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("astarote.ai")

# Fallback levels for common topics if AI keys are not available
FALLBACK_LEVELS = {
    "linux": {
        "beginner": [
            {
                "title": "Exploration du système et permissions",
                "description": "Bienvenue dans Astatarote ! Dans ce premier défi, vous devez localiser un fichier confidentiel dans le répertoire d'un utilisateur suspect et corriger ses permissions d'accès.",
                "objective": "Trouvez le fichier secret.txt sous /home/suspect et changez ses permissions pour que seul le propriétaire puisse le lire et l'écrire (chmod 600).",
                "sub_objectives": [
                    "Localiser le fichier secret.txt dans /home/suspect",
                    "Changer les permissions du fichier secret.txt en 600"
                ],
                "scenario": {
                    "type": "simulation",
                    "initial_state": {
                        "cwd": "/home/user",
                        "fs": {
                            "/home/user": {},
                            "/home/suspect": {
                                "secret.txt": {
                                    "content": "CONFIDENTIEL: Le mot de passe de sauvegarde est B64_AstaSecure!",
                                    "perms": "644",
                                    "owner": "suspect"
                                },
                                "notes.txt": {
                                    "content": "Penser à sécuriser le fichier secret.",
                                    "perms": "644",
                                    "owner": "suspect"
                                }
                            }
                        }
                    },
                    "expected_state": {
                        "files_checks": [
                            {"path": "/home/suspect/secret.txt", "perms": "600"}
                        ]
                    },
                    "commands_allowed": ["ls", "cd", "cat", "chmod", "pwd", "whoami", "help"],
                    "forbidden_commands": ["rm", "mv"]
                },
                "hints": [
                    "Utilisez 'cd /home/suspect' pour vous déplacer.",
                    "Tapez 'ls -la' pour voir les fichiers et leurs permissions.",
                    "La commande 'chmod 600 secret.txt' permet de restreindre l'accès au propriétaire uniquement."
                ],
                "difficulty": 2,
                "points": 100,
                "time_limit": 600
            },
            {
                "title": "Analyse de logs et détection d'intrusion",
                "description": "Un attaquant a tenté de se connecter par force brute. Vous devez analyser le fichier d'authentification pour identifier l'adresse IP de l'attaquant.",
                "objective": "Créez un fichier sous /home/user/attacker_ip.txt contenant uniquement l'adresse IP de l'attaquant qui a échoué le plus de fois.",
                "sub_objectives": [
                    "Trouver l'adresse IP suspecte dans /var/log/auth.log",
                    "Écrire cette adresse IP dans /home/user/attacker_ip.txt"
                ],
                "scenario": {
                    "type": "simulation",
                    "initial_state": {
                        "cwd": "/home/user",
                        "fs": {
                            "/home/user": {},
                            "/var/log": {
                                "auth.log": {
                                    "content": "Jul 25 10:01:22 server sshd[1204]: Failed password for invalid user admin from 192.168.1.150 port 49152 ssh2\nJul 25 10:01:25 server sshd[1204]: Failed password for invalid user admin from 192.168.1.150 port 49155 ssh2\nJul 25 10:01:28 server sshd[1204]: Failed password for invalid user root from 192.168.1.150 port 49158 ssh2\nJul 25 10:02:10 server sshd[1210]: Accepted publickey for user admin from 192.168.1.10 port 49200 ssh2",
                                    "perms": "640",
                                    "owner": "root"
                                }
                            }
                        }
                    },
                    "expected_state": {
                        "files_checks": [
                            {"path": "/home/user/attacker_ip.txt", "content_contains": "192.168.1.150"}
                        ]
                    },
                    "commands_allowed": ["ls", "cd", "cat", "grep", "echo", "pwd", "help"],
                    "forbidden_commands": []
                },
                "hints": [
                    "Regardez dans le dossier /var/log et lisez le fichier auth.log.",
                    "L'adresse IP qui a échoué à se connecter est 192.168.1.150.",
                    "Utilisez 'echo 192.168.1.150 > /home/user/attacker_ip.txt' pour créer le fichier attendu."
                ],
                "difficulty": 3,
                "points": 150,
                "time_limit": 900
            },
            {
                "title": "Gestion des processus et services",
                "description": "Un processus malveillant tourne en tâche de fond et consomme des ressources. Vous devez l'identifier et l'arrêter.",
                "objective": "Arrêtez le processus malveillant nommé 'miner_script' et supprimez son exécutable de /tmp/miner_script.",
                "sub_objectives": [
                    "Identifier le PID du processus 'miner_script' avec ps",
                    "Tuer le processus avec kill",
                    "Supprimer le fichier temporaire /tmp/miner_script"
                ],
                "scenario": {
                    "type": "simulation",
                    "initial_state": {
                        "cwd": "/home/user",
                        "fs": {
                            "/home/user": {},
                            "/tmp": {
                                "miner_script": {
                                    "content": "#!/bin/bash\nwhile true; do echo 'mining...'; sleep 1; done",
                                    "perms": "755",
                                    "owner": "suspect"
                                }
                            }
                        },
                        "processes": [
                            {"pid": 101, "name": "systemd", "ppid": 0},
                            {"pid": 451, "name": "miner_script", "ppid": 101}
                        ]
                    },
                    "expected_state": {
                        "process_not_running": "miner_script",
                        "file_not_exists": "/tmp/miner_script"
                    },
                    "commands_allowed": ["ls", "ps", "kill", "rm", "pwd", "help"],
                    "forbidden_commands": []
                },
                "hints": [
                    "Utilisez 'ps' pour voir les processus en cours d'exécution.",
                    "Le PID de 'miner_script' est 451. Utilisez la commande 'kill 451' pour le tuer.",
                    "Enfin, tapez 'rm /tmp/miner_script' pour nettoyer l'environnement."
                ],
                "difficulty": 4,
                "points": 180,
                "time_limit": 600
            }
        ]
    }
}

class AIService:
    @staticmethod
    def _call_provider_api(provider: str, api_key: str, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Helper function to call different LLM Providers."""
        headers = {}
        payload = {}
        url = ""

        # Set default system messages or adjust based on provider
        if provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-70b-versatile",
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"} if json_mode else {"type": "text"}
            }
        elif provider == "nvidia":
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta/llama-3.1-70b-instruct",
                "messages": messages,
                "temperature": 0.2
            }
        elif provider == "fireworks":
            url = "https://api.fireworks.ai/inference/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "accounts/fireworks/models/llama-v3-70b-instruct",
                "messages": messages,
                "temperature": 0.2
            }
        elif provider == "cohere":
            # Cohere API uses separate format, but we can call cohere chat or standard compatibility
            url = "https://api.cohere.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "command-r-plus",
                "messages": messages,
                "temperature": 0.3
            }
        elif provider == "together":
            url = "https://api.together.xyz/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta-llama/Llama-3-70b-chat-hf",
                "messages": messages,
                "temperature": 0.2
            }
        else:
            raise ValueError(f"Unknown API Provider: {provider}")

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling {provider} API: {str(e)}")
            raise e

    @classmethod
    def generate_level(
        cls,
        domain: str,
        user_level: str,
        level_index: int,
        custom_prompt: Optional[str],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calls the Architect AI to generate a level. 
        Falls back to a structured template-based level generator if no API keys are provided or if call fails.
        """
        provider = preferences.get("provider_ia", "fallback")
        api_key = preferences.get("api_key")

        # Let's clean up user inputs to be safe
        domain = domain.lower() if domain else "linux"
        user_level = user_level.lower() if user_level else "beginner"

        # Check if we should use fallback
        if provider == "fallback" or not api_key:
            return cls._generate_fallback_level(domain, user_level, level_index, custom_prompt)

        # Build prompt for AI Architect
        system_prompt = (
            "Tu es l'Architecte d'Astatarote, une plateforme d'apprentissage de la cybersécurité et de l'administration Linux.\n"
            "Ton rôle est de créer des niveaux de jeu adaptés à l'utilisateur sous forme de JSON structuré.\n"
            "Tu dois être créatif, pédagogique et maintenir une difficulté progressive.\n"
            "Les scénarios doivent être réalistes mais sécurisés (pas de commandes destructrices réelles).\n"
            "Le JSON doit obligatoirement suivre cette structure exacte :\n"
            "{\n"
            '  "title": "Intitulé du défi",\n'
            '  "description": "Description du contexte",\n'
            '  "objective": "Objectif principal à atteindre",\n'
            '  "sub_objectives": ["Sous-objectif 1", "Sous-objectif 2"],\n'
            '  "scenario": {\n'
            '    "type": "simulation",\n'
            '    "initial_state": {\n'
            '      "cwd": "/home/user",\n'
            '      "fs": {\n'
            '        "/home/user": {}\n'
            '      },\n'
            '      "processes": []\n'
            '    },\n'
            '    "expected_state": {\n'
            '      "files_checks": [\n'
            '        {"path": "/home/user/secret.txt", "perms": "600", "content_contains": "something"}\n'
            '      ]\n'
            '    },\n'
            '    "commands_allowed": ["ls", "cd", "cat", "chmod", "pwd", "whoami", "help"],\n'
            '    "forbidden_commands": ["rm -rf /"]\n'
            '  },\n'
            '  "hints": ["Indice 1", "Indice 2", "Indice 3"],\n'
            '  "difficulty": 3,\n'
            '  "points": 100,\n'
            '  "time_limit": 600\n'
            "}\n"
            "Réponds UNIQUEMENT avec le code JSON brut, sans balise de bloc de code Markdown, sans autre texte d'introduction ni de conclusion."
        )

        user_prompt = (
            f"Génère le niveau index {level_index} pour un jeu sur le thème '{domain}' "
            f"de niveau '{user_level}'. "
        )
        if custom_prompt:
            user_prompt += f"L'utilisateur a spécifié cet objectif particulier : '{custom_prompt}'"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response_text = cls._call_provider_api(provider, api_key, messages, json_mode=True)
            # Bulletproof JSON extraction
            cleaned_text = response_text.strip()
            first_brace = cleaned_text.find("{")
            last_brace = cleaned_text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                cleaned_text = cleaned_text[first_brace:last_brace+1]
            
            level_data = json.loads(cleaned_text)
            return level_data
        except Exception as e:
            logger.error(f"Failed to generate level using AI. Falling back to template. Error: {str(e)}")
            return cls._generate_fallback_level(domain, user_level, level_index, custom_prompt)

    @classmethod
    def _generate_fallback_level(cls, domain: str, user_level: str, level_index: int, custom_prompt: Optional[str]) -> Dict[str, Any]:
        """Generates dynamic levels based on user prompt, or falls back to template presets."""
        # Let's generate a highly tailored level if custom_prompt is provided!
        if custom_prompt:
            # Let's customize!
            title = f"Défi personnalisé: {custom_prompt[:40]}"
            if len(custom_prompt) > 40:
                title += "..."
            
            # Simple custom level generation depending on words in the prompt
            prompt_lower = custom_prompt.lower()
            if "apache" in prompt_lower or "web" in prompt_lower or "nginx" in prompt_lower:
                return {
                    "title": "Sécurisation d'un Serveur Web",
                    "description": f"Vous avez demandé d'apprendre à : '{custom_prompt}'. Dans ce scénario, vous devez sécuriser la configuration d'un serveur web simulé qui expose des répertoires sensibles.",
                    "objective": "Modifiez la configuration dans /etc/nginx/nginx.conf pour désactiver l'affichage d'index ('autoindex off') et assurez-vous que les permissions de /var/www/html sont à 755.",
                    "sub_objectives": [
                        "Désactiver autoindex dans /etc/nginx/nginx.conf",
                        "Changer les permissions de /var/www/html à 755"
                    ],
                    "scenario": {
                        "type": "simulation",
                        "initial_state": {
                            "cwd": "/home/user",
                            "fs": {
                                "/home/user": {},
                                "/etc/nginx": {
                                    "nginx.conf": {
                                        "content": "server {\n    listen 80;\n    root /var/www/html;\n    autoindex on;\n}",
                                        "perms": "644",
                                        "owner": "root"
                                    }
                                },
                                "/var/www/html": {
                                    "index.html": {
                                        "content": "<h1>Bienvenue sur mon serveur Web</h1>",
                                        "perms": "777",
                                        "owner": "www-data"
                                    }
                                }
                            }
                        },
                        "expected_state": {
                            "files_checks": [
                                {"path": "/etc/nginx/nginx.conf", "content_contains": "autoindex off"},
                                {"path": "/var/www/html", "perms": "755"}
                            ]
                        },
                        "commands_allowed": ["ls", "cd", "cat", "echo", "chmod", "pwd", "grep", "help"],
                        "forbidden_commands": []
                    },
                    "hints": [
                        "Examinez le fichier /etc/nginx/nginx.conf avec 'cat'.",
                        "Vous devez modifier 'autoindex on;' en 'autoindex off;'. Vous pouvez utiliser echo pour réécrire le fichier.",
                        "Utilisez 'chmod 755 /var/www/html' pour sécuriser le dossier web."
                    ],
                    "difficulty": 4,
                    "points": 150,
                    "time_limit": 900
                }
            elif "ssh" in prompt_lower or "connexion" in prompt_lower or "port" in prompt_lower:
                return {
                    "title": "Sécurisation du service SSH",
                    "description": f"En réponse à : '{custom_prompt}'. Sécurisons le démon SSH en désactivant la connexion root et en modifiant le port par défaut.",
                    "objective": "Modifiez /etc/ssh/sshd_config pour mettre le port à 2222 et désactiver la connexion root (PermitRootLogin no).",
                    "sub_objectives": [
                        "Changer le port SSH à 2222 dans /etc/ssh/sshd_config",
                        "Désactiver PermitRootLogin dans /etc/ssh/sshd_config"
                    ],
                    "scenario": {
                        "type": "simulation",
                        "initial_state": {
                            "cwd": "/home/user",
                            "fs": {
                                "/home/user": {},
                                "/etc/ssh": {
                                    "sshd_config": {
                                        "content": "Port 22\nPermitRootLogin yes\nPasswordAuthentication yes",
                                        "perms": "644",
                                        "owner": "root"
                                    }
                                }
                            }
                        },
                        "expected_state": {
                            "files_checks": [
                                {"path": "/etc/ssh/sshd_config", "content_contains": "Port 2222"},
                                {"path": "/etc/ssh/sshd_config", "content_contains": "PermitRootLogin no"}
                            ]
                        },
                        "commands_allowed": ["ls", "cd", "cat", "echo", "pwd", "grep", "help"],
                        "forbidden_commands": []
                    },
                    "hints": [
                        "Lisez le fichier de configuration dans /etc/ssh/sshd_config.",
                        "Vous devez changer 'Port 22' par 'Port 2222' et 'PermitRootLogin yes' par 'PermitRootLogin no'.",
                        "Réécrivez le fichier avec la commande echo ou d'autres utilitaires simulés."
                    ],
                    "difficulty": 3,
                    "points": 120,
                    "time_limit": 600
                }

        # General fallbacks
        domain_levels = FALLBACK_LEVELS.get(domain, FALLBACK_LEVELS["linux"])
        level_list = domain_levels.get(user_level, domain_levels["beginner"])
        
        # Select level modulo list length to support infinite progression
        selected = level_list[level_index % len(level_list)]
        
        # If it's the second level or more, make sure it has slightly increased difficulty/index
        ret = selected.copy()
        if level_index > 0:
            ret["title"] = f"Niveau {level_index + 1} - " + ret["title"]
            ret["difficulty"] = min(10, ret["difficulty"] + level_index)
            ret["points"] = ret["points"] + (level_index * 20)
        return ret

    @classmethod
    def assist_chat(
        cls,
        game_id: int,
        level_title: str,
        level_objective: str,
        current_state: Dict[str, Any],
        chat_history: List[Dict[str, Any]],
        user_message: str,
        preferences: Dict[str, Any]
    ) -> str:
        """
        Calls the Coéquipier (Teammate) AI to talk with the user.
        Provides rich, pedagogical tips and encouragement in French.
        """
        provider = preferences.get("provider_ia", "fallback")
        api_key = preferences.get("api_key")

        if provider == "fallback" or not api_key:
            return cls._generate_fallback_chat(level_title, level_objective, current_state, user_message)

        system_prompt = (
            "Tu es le Coéquipier d'Astatarote.\n"
            "Tu es un assistant pédagogique dans le terminal pour l'apprentissage Linux et Cybersécurité.\n"
            "Tu parles en français de manière naturelle, motivante et amicale.\n"
            "Ton but est d'aider l'utilisateur sans lui donner la solution directement.\n"
            "Tu l'encourages, lui donnes des indices, expliques les concepts.\n"
            "Tu es patient et t'adaptes au rythme de l'utilisateur.\n"
            "Si l'utilisateur est bloqué depuis longtemps, tu deviens plus explicite.\n"
            "Tu peux vérifier son travail et lui suggérer des améliorations.\n"
            "Sois concis, car l'utilisateur lit cela dans un petit volet de chat à côté de son terminal."
        )

        # Format context about level
        context = (
            f"--- CONTEXTE DU DÉFI ACTUEL ---\n"
            f"Défi : {level_title}\n"
            f"Objectif : {level_objective}\n"
            f"Répertoire de travail actuel : {current_state.get('cwd', '/home/user')}\n"
            f"Structure des fichiers actuels : {list(current_state.get('fs', {}).keys())}\n"
        )

        messages = [{"role": "system", "content": system_prompt + "\n\n" + context}]
        
        # Add historical conversation
        for msg in chat_history[-10:]:  # Keep last 10 messages for context
            role = "user" if msg["sender"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["message"]})

        messages.append({"role": "user", "content": user_message})

        try:
            return cls._call_provider_api(provider, api_key, messages)
        except Exception as e:
            logger.error(f"Error calling AI for chat, fallback used: {str(e)}")
            return cls._generate_fallback_chat(level_title, level_objective, current_state, user_message)

    @classmethod
    def _generate_fallback_chat(cls, level_title: str, level_objective: str, current_state: Dict[str, Any], user_message: str) -> str:
        """Fallback chat engine using pattern-matching to respond in French as a cool cyber teammate."""
        msg = user_message.lower()
        cwd = current_state.get("cwd", "/home/user")
        
        # Greeting
        if any(w in msg for w in ["salut", "bonjour", "hello", "hey", "yo"]):
            return "Salut ! Prêt à relever le défi ? Je suis là pour t'accompagner. N'hésite pas si tu as besoin d'un indice ou si tu ne comprends pas une commande."

        # Asking for solutions or direct help
        if any(w in msg for w in ["solution", "réponse", "comment faire", "bloqué", "aide", "aider"]):
            return (
                f"Je ne peux pas te donner la solution brute, mais voici un bon point de départ : \n"
                f"Tu es actuellement dans le dossier `{cwd}`. "
                f"L'objectif principal est : *{level_objective}*.\n\n"
                "Essaie d'utiliser la commande `ls -la` pour inspecter ton environnement, puis examine les fichiers présents !"
            )

        # Asking what commands are available
        if "commande" in msg or "commandes" in msg:
            return (
                "Dans ce terminal simulé, tu as accès aux commandes classiques comme `ls`, `cd`, `cat`, `chmod`, `echo` et `pwd`.\n"
                "Tape `help` pour lister les fonctions d'aide supplémentaires."
            )

        # Permissions questions
        if "chmod" in msg or "permission" in msg or "permissions" in msg:
            return (
                "Pour changer les permissions d'un fichier en Linux, on utilise `chmod`.\n"
                "- `chmod 600 fichier` : Donne tous les droits (lecture/écriture) au propriétaire uniquement.\n"
                "- `chmod 755 dossier` : Permet au propriétaire de tout faire, et aux autres de lire/exécuter.\n"
                "Dis-moi si tu veux en savoir plus !"
            )

        # General response
        return (
            "Intéressant ! N'oublie pas d'utiliser les commandes du terminal à gauche pour interagir avec le système.\n"
            "Tu peux taper `ls` pour lister, `cat <fichier>` pour lire un fichier ou `cd <chemin>` pour te déplacer.\n"
            "Continue comme ça, tu es sur la bonne voie !"
        )
