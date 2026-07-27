import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("astarote.ai")

class AIService:
    @staticmethod
    def _call_provider_api(provider: str, api_key: str, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Helper function to call different LLM Providers."""
        headers = {}
        payload = {}
        url = ""

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
            with httpx.Client(timeout=90.0) as client:
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

        domain = domain.lower() if domain else "linux"
        user_level = user_level.lower() if user_level else "beginner"

        if provider == "fallback" or not api_key:
            return cls._generate_fallback_level(domain, user_level, level_index, custom_prompt)

        # Build highly specific system prompt for AI Architect to enforce situation, consigne and support
        system_prompt = (
            "Tu es l'Architecte d'Astatarote, une plateforme d'apprentissage de la cybersécurité et de l'administration Linux.\n"
            "Ton rôle est de créer des niveaux de jeu adaptés à l'utilisateur sous forme de JSON structuré.\n"
            "Tu dois IMPÉRATIVEMENT respecter la thématique demandée par l'utilisateur (par exemple, s'il veut apprendre à hacker et protéger un Wi-Fi, génère des exercices cyber offensifs/défensifs de Wi-Fi, ne dévie JAMAIS vers de l'administration système ennuyeuse).\n"
            "Chaque niveau doit posséder un très fort degré d'inspiration, structuré comme suit :\n"
            "- situation_probleme : Une situation-problème cybernétique scénarisée, immersive, captivante (ex. : alerte intrusion, anomalie détectée sur les serveurs, fuite de données en cours).\n"
            "- consigne : Une consigne d'exécution claire et précise, détaillant les critères techniques à satisfaire dans le terminal.\n"
            "- support_technique : Un guide de support technique extrêmement précis, expliquant pas-à-pas les outils conseillés (ex. : iwconfig, airmon-ng, nmap) et les commandes pour résoudre le problème.\n"
            "Le JSON doit obligatoirement suivre cette structure exacte :\n"
            "{\n"
            '  "title": "Intitulé du défi",\n'
            '  "situation_probleme": "Scénario immersif détaillé en français...",\n'
            '  "consigne": "Consigne précise détaillant les actions à réaliser...",\n'
            '  "support_technique": "Manuel explicatif étape par étape pour aider à résoudre...",\n'
            '  "objective": "Objectif principal à atteindre",\n'
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
        prompt_lower = (custom_prompt or "").lower()
        if "wifi" in prompt_lower or "wi-fi" in prompt_lower or "pirat" in prompt_lower or "sans-fil" in prompt_lower:
            if level_index == 0:
                return {
                    "title": "Activation du mode Moniteur sans-fil",
                    "situation_probleme": "ALERTE INTRUSION : Le centre d'opérations de sécurité (SOC) d'Astatarote a détecté des requêtes suspectes d'authentification sur le réseau interne. Une machine pirate tente d'injecter des trames. En tant qu'analyste cyber d'élite, votre première étape consiste à placer votre carte réseau virtuelle 'wlan0' en mode écoute (monitor mode) afin d'intercepter ces trames radio malveillantes.",
                    "consigne": "Passez l'interface sans-fil wlan0 en mode moniteur à l'aide de la commande 'airmon-ng start wlan0'. Vérifiez son activation dans la foulée en lançant 'iwconfig' pour vous assurer que le mode est bien défini sur 'Monitor'.",
                    "support_technique": "### Manuel d'activation du mode Moniteur\n\n1. Lancez **`iwconfig`** pour inspecter vos cartes réseaux sans-fil disponibles.\n2. Exécutez l'utilitaire d'activation **`airmon-ng start wlan0`** pour basculer votre carte wlan0 en mode écoute.\n3. Relancez **`iwconfig`** : vous devez voir l'interface wlan0mon active et configurée avec le Mode 'Monitor'.",
                    "objective": "Activez le mode moniteur sur l'interface 'wlan0' en utilisant l'utilitaire 'airmon-ng start wlan0'.",
                    "scenario": {
                        "type": "simulation",
                        "initial_state": {
                            "cwd": "/home/user",
                            "fs": {
                                "/home/user": {}
                            },
                            "processes": []
                        },
                        "expected_state": {
                            "files_checks": [
                                {"path": "/sys/class/net/wlan0mon"}
                            ]
                        },
                        "commands_allowed": ["ls", "cd", "airmon-ng", "iwconfig", "ifconfig", "help"],
                        "forbidden_commands": ["rm -rf /"]
                    },
                    "hints": [
                        "Utilisez 'iwconfig' pour inspecter vos cartes réseaux sans-fil.",
                        "La commande 'airmon-ng' permet d'activer le mode moniteur.",
                        "Exécutez 'airmon-ng start wlan0' pour passer en mode écoute."
                    ],
                    "difficulty": 3,
                    "points": 100,
                    "time_limit": 600
                }
            elif level_index == 1:
                return {
                    "title": "Capture du Handshake WPA2",
                    "situation_probleme": "Vecteur d'écoute actif ! La carte virtuelle écoute désormais les ondes du lab. Un appareil suspect est actuellement connecté au point d'accès confidentiel 'AstaWifi_Secure'. Vous devez intercepter sa poignée de main cryptographique à 4 étapes (handshake WPA2) afin de collecter les preuves de chiffrement nécessaires à l'analyse de sa clé d'accès.",
                    "consigne": "Lancez l'écoute générale des réseaux à l'aide de 'airodump-ng wlan0mon'. L'outil va écouter le canal de transmission et, dès qu'un appareil effectuera une négociation, interceptera le handshake et générera automatiquement le fichier d'audit 'handshake.cap' dans votre répertoire.",
                    "support_technique": "### Manuel d'interception réseau\n\n1. Assurez-vous que votre interface 'wlan0mon' est active en tapant **`iwconfig`**.\n2. Exécutez l'outil de capture **`airodump-ng wlan0mon`**.\n3. L'outil affiche la liste des réseaux et stations. Attendez que la mention 'Handshake captured !' apparaisse en surbrillance. Cela génère le fichier cryptographique **`handshake.cap`** à la racine de votre répertoire.",
                    "objective": "Lancez l'outil de capture 'airodump-ng wlan0mon' pour intercepter les paquets et générer le fichier de capture 'handshake.cap' dans votre répertoire.",
                    "scenario": {
                        "type": "simulation",
                        "initial_state": {
                            "cwd": "/home/user",
                            "fs": {
                                "/home/user": {},
                                "/sys/class/net/wlan0mon": {"is_dir": True}
                            },
                            "processes": []
                        },
                        "expected_state": {
                            "files_checks": [
                                {"path": "/home/user/handshake.cap"}
                            ]
                        },
                        "commands_allowed": ["ls", "cd", "airodump-ng", "iwconfig", "ifconfig", "help"],
                        "forbidden_commands": ["rm -rf /"]
                    },
                    "hints": [
                        "Assurez-vous que votre interface 'wlan0mon' est active en tapant 'iwconfig'.",
                        "Exécutez 'airodump-ng wlan0mon' pour lancer l'écoute et intercepter le handshake.",
                        "Dès que le handshake est intercepté, l'outil créera automatiquement le fichier 'handshake.cap'."
                    ],
                    "difficulty": 4,
                    "points": 120,
                    "time_limit": 600
                }
            else: # level_index >= 2
                return {
                    "title": "Brute-Force et Déchiffrement de la Clé WPA",
                    "situation_probleme": "Preuve collectée ! Vous avez en votre possession le fichier de capture chiffré 'handshake.cap'. Pour identifier si le point d'accès d'Astatarote utilise un mot de passe vulnérable aux attaques de dictionnaires, vous devez exécuter une attaque par force brute combinée à un dictionnaire de mots de passe courants (wordlist.txt).",
                    "consigne": "Exécutez la phase de cassage de clé en utilisant l'utilitaire 'aircrack-ng -w wordlist.txt handshake.cap'. Si l'une des clés du dictionnaire correspond à la signature du handshake, l'outil déchiffrera la clé et l'écrira automatiquement dans 'key.txt' pour valider votre audit.",
                    "support_technique": "### Manuel d'audit de mot de passe\n\n1. Inspectez la liste de mots de passe de test contenue dans **`wordlist.txt`** en tapant **`cat wordlist.txt`**.\n2. Lancez le décryptage avec la commande : **`aircrack-ng -w wordlist.txt handshake.cap`**.\n3. Une fois le mot de passe cassé, la clé de sécurité s'affiche et s'écrit automatiquement dans **`key.txt`**.",
                    "objective": "Utilisez l'utilitaire 'aircrack-ng -w wordlist.txt handshake.cap' pour casser la clé et générer le fichier 'key.txt' contenant le mot de passe décrypté.",
                    "scenario": {
                        "type": "simulation",
                        "initial_state": {
                            "cwd": "/home/user",
                            "fs": {
                                "/home/user": {
                                    "handshake.cap": {
                                        "content": "WPA2 HANDSHAKE CAPTURED FROM BSSID 00:14:6C:7E:40:80",
                                        "perms": "644"
                                    },
                                    "wordlist.txt": {
                                        "content": "admin123\npassword\n12345678\nAstaSecure123\nqwerty",
                                        "perms": "644"
                                    }
                                }
                            },
                            "processes": []
                        },
                        "expected_state": {
                            "files_checks": [
                                {"path": "/home/user/key.txt", "content_contains": "AstaSecure123"}
                            ]
                        },
                        "commands_allowed": ["ls", "cd", "cat", "aircrack-ng", "help"],
                        "forbidden_commands": []
                    },
                    "hints": [
                        "Lisez le dictionnaire 'wordlist.txt' avec 'cat' pour voir les mots de passe de test.",
                        "Lancez le déchiffrement avec la commande : 'aircrack-ng -w wordlist.txt handshake.cap'.",
                        "Une fois la clé trouvée, elle sera écrite dans '/home/user/key.txt'."
                    ],
                    "difficulty": 5,
                    "points": 150,
                    "time_limit": 600
                }

        # Default Linux / System fallbacks if general
        if level_index == 0:
            return {
                "title": "Exploration du système et permissions",
                "situation_probleme": "ALERTE INTRUSION : Le système de détection des hôtes suspecte qu'un utilisateur 'suspect' a déposé un script d'écoute confidentiel sur notre serveur. Vous devez inspecter l'arborescence des fichiers pour localiser ce fichier secret et en restreindre immédiatement les privilèges.",
                "consigne": "Recherchez le fichier secret.txt dans le dossier /home/suspect. Modifiez ses permissions à l'aide de 'chmod 600' pour que seul le propriétaire puisse le lire et l'écrire afin d'interdire l'accès public.",
                "support_technique": "### Manuel de gestion de droits d'accès\n\n1. Déplacez-vous dans le répertoire cible avec **`cd /home/suspect`**.\n2. Tapez **`ls -la`** pour lister les fichiers et observer leurs permissions d'accès actuelles.\n3. Utilisez la commande **`chmod 600 secret.txt`** pour restreindre l'accès au propriétaire uniquement.",
                "objective": "Trouvez le fichier secret.txt sous /home/suspect et changez ses permissions pour que seul le propriétaire puisse le lire et l'écrire (chmod 600).",
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
            }
        elif level_index == 1:
            return {
                "title": "Analyse de logs et détection d'intrusion",
                "situation_probleme": "ALERTE FORCE BRUTE : Des milliers de tentatives de connexions infructueuses ont saturé notre service d'authentification SSH. Vous devez analyser l'historique des connexions système pour déceler l'adresse IP de la machine attaquante.",
                "consigne": "Parcourez les lignes d'authentification dans le fichier /var/log/auth.log. Écrivez l'adresse IP de l'attaquant qui a échoué à se connecter dans un fichier nommé /home/user/attacker_ip.txt.",
                "support_technique": "### Manuel d'analyse d'auth.log\n\n1. Inspectez les fichiers de logs avec **`cat /var/log/auth.log`**.\n2. Repérez l'adresse IP qui accumule les échecs de connexion (Failed password pour invalid user).\n3. Écrivez cette adresse IP dans le fichier cible avec : **`echo 192.168.1.150 > /home/user/attacker_ip.txt`**.",
                "objective": "Créez un fichier sous /home/user/attacker_ip.txt contenant uniquement l'adresse IP de l'attaquant qui a échoué le plus de fois.",
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
            }
        else: # level_index >= 2
            return {
                "title": "Gestion des processus et services",
                "situation_probleme": "ALERTE PROCESSEUR : Un script malveillant de minage de crypto-monnaies non autorisé tourne en tâche de fond sous le nom suspect 'miner_script'. Vous devez identifier son identifiant de processus (PID) pour le tuer et nettoyer l'exécutable.",
                "consigne": "Identifiez le PID du processus malveillant avec 'ps'. Tuez-le avec 'kill <PID>' puis supprimez son exécutable situé dans /tmp/miner_script.",
                "support_technique": "### Manuel de gestion de processus\n\n1. Listez les processus en cours d'exécution avec la commande **`ps`**.\n2. Repérez le PID de la ligne 'miner_script' (ex: PID 451).\n3. Tuez le processus avec la commande **`kill 451`**.\n4. Supprimez l'exécutable temporaire à l'aide de **`rm /tmp/miner_script`**.",
                "objective": "Arrêtez le processus malveillant nommé 'miner_script' et supprimez son exécutable de /tmp/miner_script.",
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
            "Tu es Nemesis, le coéquipier d'apprentissage d'Astatarote.\n"
            "Tu es un assistant pédagogique d'élite dans le terminal pour l'apprentissage de la cybersécurité.\n"
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
            return "Salut ! Prêt à relever le défi ? Je suis Nemesis. Je suis là pour t'accompagner. N'hésite pas si tu as besoin d'un indice ou si tu ne comprends pas une commande."

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
