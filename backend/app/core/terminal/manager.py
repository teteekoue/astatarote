import os
import re
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger("astarote.terminal")

class TerminalSimulator:
    """
    Simulates a Linux terminal by executing commands on a virtual file system.
    Maintains and modifies the state (files, directory, processes).
    """

    @classmethod
    def execute(cls, command_line: str, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Executes a command line on the given terminal state and returns (stdout, new_state).
        """
        # Ensure state is initialized
        if not state:
            state = {
                "cwd": "/home/user",
                "fs": {
                    "/home/user": {"is_dir": True, "perms": "755", "owner": "user"},
                    "/home/user/welcome.txt": {"content": "Bienvenue sur Astatarote ! Résolvez les défis en utilisant ce terminal.", "perms": "644", "owner": "user"}
                },
                "processes": [
                    {"pid": 1, "name": "systemd", "ppid": 0}
                ]
            }

        cwd = state.get("cwd", "/home/user")
        fs = state.get("fs", {})
        processes = state.get("processes", [])

        # Clean/Parse command line
        command_line = command_line.strip()
        if not command_line:
            return "", state

        # Handle redirection (e.g. echo "hello" > file.txt)
        redir_match = re.search(r'(.*?)\s*(>>|>)\s*(.*)', command_line)
        if redir_match:
            base_cmd = redir_match.group(1).strip()
            redir_type = redir_match.group(2).strip()
            dest_file = redir_match.group(3).strip()
            
            # Execute base command first
            stdout_base, temp_state = cls._execute_base(base_cmd, cwd, fs, processes)
            
            # Resolve destination file path
            dest_abs = cls._resolve_path(dest_file, cwd)
            dest_parent = os.path.dirname(dest_abs)
            
            # Check if parent directory exists
            if dest_parent not in fs or not fs[dest_parent].get("is_dir", True):
                return f"bash: {dest_file}: Aucun fichier ou dossier de ce type", state
                
            # Write or append
            content_to_write = stdout_base + "\n" if stdout_base else ""
            if not stdout_base and base_cmd.startswith("echo "):
                # Extract echo content
                content_to_write = cls._extract_echo_text(base_cmd)
                
            if redir_type == ">":
                fs[dest_abs] = {
                    "content": content_to_write,
                    "perms": "644",
                    "owner": "user",
                    "is_dir": False
                }
            else:  # >>
                existing = fs.get(dest_abs, {"content": "", "perms": "644", "owner": "user", "is_dir": False})
                if existing.get("is_dir"):
                    return f"bash: {dest_file}: est un dossier", state
                existing["content"] = existing.get("content", "") + content_to_write
                fs[dest_abs] = existing
                
            state["fs"] = fs
            return "", state

        # Normal command execution
        stdout, new_cwd, new_fs, new_processes = cls._execute_base_state(command_line, cwd, fs, processes)
        
        state["cwd"] = new_cwd
        state["fs"] = new_fs
        state["processes"] = new_processes
        return stdout, state

    @classmethod
    def _extract_echo_text(cls, echo_cmd: str) -> str:
        # e.g. echo "hello"
        match = re.match(r"^echo\s+['\"]?(.*?)['\"]?$", echo_cmd)
        if match:
            return match.group(1)
        return echo_cmd[5:].strip() if len(echo_cmd) > 5 else ""

    @classmethod
    def _resolve_path(cls, path: str, cwd: str) -> str:
        """Resolves absolute path relative to cwd."""
        if path.startswith("~"):
            path = "/home/user" + path[1:]
        if not path.startswith("/"):
            path = os.path.join(cwd, path)
        
        # Resolve .. and .
        parts = path.split("/")
        resolved_parts = []
        for part in parts:
            if part == "" or part == ".":
                continue
            if part == "..":
                if resolved_parts:
                    resolved_parts.pop()
            else:
                resolved_parts.append(part)
        return "/" + "/".join(resolved_parts)

    @classmethod
    def _execute_base(cls, command_line: str, cwd: str, fs: Dict[str, Any], processes: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        stdout, new_cwd, new_fs, new_procs = cls._execute_base_state(command_line, cwd, fs, processes)
        return stdout, new_fs

    @classmethod
    def _execute_base_state(
        cls, command_line: str, cwd: str, fs: Dict[str, Any], processes: List[Dict[str, Any]]
    ) -> Tuple[str, str, Dict[str, Any], List[Dict[str, Any]]]:
        parts = command_line.split()
        if not parts:
            return "", cwd, fs, processes
            
        cmd = parts[0]
        args = parts[1:]

        # List of dangerous commands to block as per constraints
        forbidden = ["rm -rf /", "dd", "mkfs", "chmod -R 777 /"]
        if command_line in forbidden or any(f in command_line for f in ["rm -rf /", "mkfs", "dd"]):
            return "Sécurité : Commande interdite détectée par le gardien Astatarote !", cwd, fs, processes

        # --- HIGHLY INSTRUCTED CYBERSECURITY / WIFI TOOLS SIMULATION ---
        if cmd == "airmon-ng":
            if not args:
                return (
                    "PHY\tInterface\tDriver\t\tChipset\n"
                    "phy0\twlan0\t\tath9k\t\tQualcomm Atheros QCA9565 (monitor mode disabled)"
                , cwd, fs, processes)
            
            sub = args[0]
            if sub == "start":
                if len(args) < 2:
                    return "Utilisation : airmon-ng start <interface>", cwd, fs, processes
                interface = args[1]
                if interface == "wlan0":
                    # Add virtual monitor interface
                    fs["/sys/class/net/wlan0mon"] = {"is_dir": True, "perms": "755"}
                    return (
                        "[*] Enabling monitor mode on wlan0...\n"
                        "[+] Monitor mode enabled on interface wlan0mon (mac80211 monitor mode vif enabled for [phy0]wlan0 on [phy0]wlan0mon)"
                    , cwd, fs, processes)
                else:
                    return f"Interface {interface} introuvable.", cwd, fs, processes
            elif sub == "stop":
                if len(args) < 2:
                    return "Utilisation : airmon-ng stop <interface>", cwd, fs, processes
                interface = args[1]
                if interface == "wlan0mon":
                    if "/sys/class/net/wlan0mon" in fs:
                        del fs["/sys/class/net/wlan0mon"]
                    return "[*] Disabling monitor mode. Interface wlan0mon stopped.", cwd, fs, processes
                return f"Interface {interface} non active en mode moniteur.", cwd, fs, processes
            else:
                return "Commande airmon-ng non reconnue.", cwd, fs, processes

        elif cmd == "airodump-ng":
            if not args:
                return "Utilisation : airodump-ng <interface_moniteur>", cwd, fs, processes
            interface = args[0]
            if "/sys/class/net/wlan0mon" not in fs and interface != "wlan0mon":
                return f"Interface {interface} n'est pas en mode moniteur ! Activez-le d'abord avec airmon-ng.", cwd, fs, processes
            
            # Print beautiful wireless networks table dump
            dump_output = (
                " CH  6 ][ Elapsed: 4 s ][ 2026-07-25 19:30 ][ WPA handshake: 00:14:6C:7E:40:80\n\n"
                " BSSID              PWR  Beacons    #Data, #/s  CH   MB   ENC CIPHER  AUTH ESSID\n"
                " 00:14:6C:7E:40:80  -42       84       412    8   6   54 . WPA2 CCMP   PSK  AstaWifi_Secure\n"
                " 00:1A:2B:3C:4D:5E  -71       20         0    0  11   54   WPA2 CCMP   PSK  NeighborNet_Guest\n"
                " 00:0F:B5:44:88:99  -85        5         0    0   1   54   WEP  WEP          FreeBox_32A\n\n"
                " BSSID              STATION            PWR   Rate    Lost    Frames  Notes\n"
                " 00:14:6C:7E:40:80  00:0F:B5:12:34:56  -31   0 - 1      0        14  Handshake captured !"
            )
            # Create a handshake cap file in root so user can run aircrack-ng on it!
            fs["/home/user/handshake.cap"] = {
                "content": "WPA2 HANDSHAKE CAPTURED FROM BSSID 00:14:6C:7E:40:80",
                "perms": "644",
                "owner": "user",
                "is_dir": False
            }
            return dump_output, cwd, fs, processes

        elif cmd == "aircrack-ng":
            if len(args) < 2:
                return "Utilisation : aircrack-ng -w <dictionnaire> <fichier.cap>", cwd, fs, processes
            
            wordlist_arg = ""
            capfile_arg = ""
            # parse arguments
            for i, arg in enumerate(args):
                if arg == "-w" and i + 1 < len(args):
                    wordlist_arg = cls._resolve_path(args[i+1], cwd)
                elif arg.endswith(".cap"):
                    capfile_arg = cls._resolve_path(arg, cwd)

            if not wordlist_arg or not capfile_arg:
                return "Syntaxe incorrecte. Exemple : aircrack-ng -w wordlist.txt handshake.cap", cwd, fs, processes

            if wordlist_arg not in fs:
                return f"Fichier dictionnaire '{args[1]}' introuvable dans le répertoire actuel.", cwd, fs, processes
            if capfile_arg not in fs:
                return f"Fichier de capture '{args[-1]}' introuvable.", cwd, fs, processes

            # Read wordlist to find matching key
            wl_content = fs[wordlist_arg].get("content", "")
            found_key = "AstaSecure123" # Default key
            for line in wl_content.splitlines():
                if "secure" in line.lower() or "password" in line.lower() or "asta" in line.lower():
                    found_key = line.strip()
                    break

            # Print beautiful brute-force decrypt output
            crack_output = (
                "Aircrack-ng 1.7\n\n"
                "      [00:00:03] 14210 keys tested (4736.6 k/s)\n\n"
                "      KEY FOUND! [ " + found_key + " ]\n\n"
                "            Master Key     : DE 23 A5 FD 41 B2 DE 93 F0 AC B1 3E 45 FE AD C2\n"
                "            Transient Key  : 4F BE B1 93 DE AC B3 12 CC D5 EE 19 4E BA D9 12"
            )
            # Create a success log key file in home dir to validate the level
            fs["/home/user/key.txt"] = {
                "content": found_key,
                "perms": "644",
                "owner": "user",
                "is_dir": False
            }
            return crack_output, cwd, fs, processes

        elif cmd == "iwconfig":
            is_mon = "/sys/class/net/wlan0mon" in fs
            output = (
                "lo        no wireless extensions.\n\n"
                "eth0      no wireless extensions.\n\n"
                "wlan0     IEEE 802.11  ESSID:off/any  \n"
                "          Mode:" + ("Monitor" if is_mon else "Managed") + "  Frequency:2.437 GHz  Access Point: Not-Associated   \n"
                "          Tx-Power=20 dBm   Sensitivity=0/3  \n"
                "          Retry short limit:7   RTS thr:off   Fragment thr:off\n"
                "          Power Management:off"
            )
            return output, cwd, fs, processes

        elif cmd == "ifconfig":
            is_mon = "/sys/class/net/wlan0mon" in fs
            mon_section = ""
            if is_mon:
                mon_section = (
                    "wlan0mon  Link encap:UNSPEC  HWaddr 00-14-6C-7E-40-80-00-00-00-00-00-00-00-00-00-00  \n"
                    "          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1\n"
                    "          RX packets:412 errors:0 dropped:0 overruns:0 frame:0\n"
                    "          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0\n"
                    "          collisions:0 txqueuelen:1000 \n"
                    "          RX bytes:45212 (45.2 KB)  TX bytes:0 (0.0 B)\n\n"
                )
            
            output = (
                "eth0      Link encap:Ethernet  HWaddr 00:0c:29:12:34:56  \n"
                "          inet addr:192.168.1.64  Bcast:192.168.1.255  Mask:255.255.255.0\n"
                "          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1\n"
                "          RX packets:142 errors:0 dropped:0 overruns:0 frame:0\n"
                "          TX packets:95 errors:0 dropped:0 overruns:0 carrier:0\n"
                "          collisions:0 txqueuelen:1000 \n"
                "          RX bytes:15214 (15.2 KB)  TX bytes:9512 (9.5 KB)\n\n" +
                mon_section +
                "lo        Link encap:Local Loopback  \n"
                "          inet addr:127.0.0.1  Mask:255.0.0.0\n"
                "          UP LOOPBACK RUNNING  MTU:65536  Metric:1\n"
                "          RX packets:10 errors:0 dropped:0 overruns:0 frame:0\n"
                "          TX packets:10 errors:0 dropped:0 overruns:0 carrier:0\n"
                "          collisions:0 txqueuelen:1000 \n"
                "          RX bytes:640 (640.0 B)  TX bytes:640 (640.0 B)"
            )
            return output, cwd, fs, processes

        # --- STANDARD SYSTEM COMMANDS ---
        if cmd == "pwd":
            return cwd, cwd, fs, processes

        elif cmd == "whoami":
            return "user", cwd, fs, processes

        elif cmd == "help":
            help_text = (
                "Astatarote - Terminal Virtuel d'Apprentissage\n"
                "Commandes disponibles :\n"
                "  pwd               Afficher le répertoire actuel\n"
                "  whoami            Afficher l'utilisateur actuel\n"
                "  ls [-la] [rep]    Lister les fichiers\n"
                "  cd [rep]          Changer de répertoire\n"
                "  cat [fichier]     Afficher le contenu d'un fichier\n"
                "  touch [fichier]   Créer un fichier vide\n"
                "  mkdir [dossier]   Créer un dossier\n"
                "  rm [-rf] [fich]   Supprimer un fichier ou un dossier\n"
                "  chmod [perm] [f]  Modifier les permissions (ex: 600, 755)\n"
                "  ps                Lister les processus actifs\n"
                "  kill [pid]        Arrêter un processus par son PID\n"
                "  clear             Effacer l'écran\n"
                "  help              Afficher ce menu"
            )
            return help_text, cwd, fs, processes

        elif cmd == "clear":
            # Let the frontend clear the UI, return a special clear marker or empty
            return "\033[2J\033[H", cwd, fs, processes

        elif cmd == "ls":
            # parse args
            show_details = False
            target_dir = cwd
            for arg in args:
                if arg.startswith("-"):
                    if "l" in arg or "a" in arg:
                        show_details = True
                else:
                    target_dir = cls._resolve_path(arg, cwd)
            
            target_dir = cls._resolve_path(target_dir, cwd)
            
            # Check if directory exists
            if target_dir not in fs and target_dir != "/":
                # Check if it is a file instead
                if target_dir in fs:
                    return target_dir.split("/")[-1], cwd, fs, processes
                return f"ls: impossible d'accéder à '{target_dir}': Aucun fichier ou dossier de ce type", cwd, fs, processes

            # Collect items in directory
            items = []
            for path, file_info in fs.items():
                if path == target_dir:
                    continue
                parent = os.path.dirname(path)
                if parent == target_dir or (target_dir == "/" and parent == ""):
                    name = os.path.basename(path)
                    if name:
                        items.append((name, file_info))

            if not items:
                return "", cwd, fs, processes

            if show_details:
                lines = []
                for name, info in items:
                    perms_str = "drwxr-xr-x" if info.get("is_dir") else f"-rwx------"
                    # format permissions nicely based on code
                    raw_perm = str(info.get("perms", "644"))
                    if len(raw_perm) == 3:
                        # simple octal parser
                        mapping = {"7": "rwx", "6": "rw-", "5": "r-x", "4": "r--", "0": "---"}
                        p1 = mapping.get(raw_perm[0], "rw-")
                        p2 = mapping.get(raw_perm[1], "r--")
                        p3 = mapping.get(raw_perm[2], "r--")
                        prefix = "d" if info.get("is_dir") else "-"
                        perms_str = f"{prefix}{p1}{p2}{p3}"
                        
                    owner = info.get("owner", "user")
                    size = len(info.get("content", "")) if not info.get("is_dir") else 4096
                    lines.append(f"{perms_str} 1 {owner} staff {size} Jul 25 12:00 {name}")
                return "\n".join(lines), cwd, fs, processes
            else:
                names = [name for name, _ in items]
                return "   ".join(names), cwd, fs, processes

        elif cmd == "cd":
            if not args:
                target = "/home/user"
            else:
                target = cls._resolve_path(args[0], cwd)

            if target in fs or target == "/":
                # Ensure it is a directory
                if target == "/" or fs.get(target, {}).get("is_dir", True):
                    return "", target, fs, processes
                else:
                    return f"bash: cd: {args[0]}: N'est pas un dossier", cwd, fs, processes
            return f"bash: cd: {args[0]}: Aucun fichier ou dossier de ce type", cwd, fs, processes

        elif cmd == "cat":
            if not args:
                return "cat: argument manquant", cwd, fs, processes
            target = cls._resolve_path(args[0], cwd)
            if target in fs:
                if fs[target].get("is_dir"):
                    return f"cat: {args[0]}: est un dossier", cwd, fs, processes
                # Check permissions
                perms = str(fs[target].get("perms", "644"))
                owner = fs[target].get("owner", "user")
                if perms.startswith("0") or perms == "600" and owner != "user":
                    return f"cat: {args[0]}: Permission non accordée", cwd, fs, processes
                return fs[target].get("content", ""), cwd, fs, processes
            return f"cat: {args[0]}: Aucun fichier ou dossier de ce type", cwd, fs, processes

        elif cmd == "touch":
            if not args:
                return "touch: argument manquant", cwd, fs, processes
            target = cls._resolve_path(args[0], cwd)
            
            parent = os.path.dirname(target)
            if parent not in fs and parent != "/":
                return f"touch: impossible de créer '{args[0]}': Aucun dossier de ce type", cwd, fs, processes
                
            if target not in fs:
                fs[target] = {
                    "content": "",
                    "perms": "644",
                    "owner": "user",
                    "is_dir": False
                }
            return "", cwd, fs, processes

        elif cmd == "mkdir":
            if not args:
                return "mkdir: argument manquant", cwd, fs, processes
            target = cls._resolve_path(args[0], cwd)
            parent = os.path.dirname(target)
            if parent not in fs and parent != "/":
                return f"mkdir: impossible de créer le dossier '{args[0]}': Aucun dossier de ce type", cwd, fs, processes
                
            fs[target] = {
                "is_dir": True,
                "perms": "755",
                "owner": "user"
            }
            return "", cwd, fs, processes

        elif cmd == "rm":
            if not args:
                return "rm: argument manquant", cwd, fs, processes
            # parse options
            recursive = False
            targets = []
            for arg in args:
                if arg.startswith("-"):
                    if "r" in arg or "f" in arg:
                        recursive = True
                else:
                    targets.append(arg)
            
            if not targets:
                return "rm: nom de fichier manquant", cwd, fs, processes

            output_msgs = []
            for t in targets:
                target_path = cls._resolve_path(t, cwd)
                if target_path in fs:
                    if fs[target_path].get("is_dir") and not recursive:
                        output_msgs.append(f"rm: impossible de supprimer '{t}': est un dossier")
                    else:
                        # delete target and any children if recursive
                        keys_to_del = [target_path]
                        if recursive:
                            for key in fs.keys():
                                if key.startswith(target_path + "/"):
                                    keys_to_del.append(key)
                        for key in keys_to_del:
                            if key in fs:
                                del fs[key]
                else:
                    output_msgs.append(f"rm: impossible de supprimer '{t}': Aucun fichier ou dossier de ce type")
            
            return "\n".join(output_msgs), cwd, fs, processes

        elif cmd == "chmod":
            if len(args) < 2:
                return "chmod: arguments manquants. Utilisation : chmod <octal> <fichier>", cwd, fs, processes
            perms_val = args[0]
            target = cls._resolve_path(args[1], cwd)
            if target in fs:
                fs[target]["perms"] = perms_val
                return "", cwd, fs, processes
            return f"chmod: impossible d'accéder à '{args[1]}': Aucun fichier ou dossier de ce type", cwd, fs, processes

        elif cmd == "ps":
            lines = ["PID  TTY          TIME CMD"]
            for proc in processes:
                lines.append(f"{str(proc.get('pid')).ljust(4)} ?        00:00:00 {proc.get('name')}")
            return "\n".join(lines), cwd, fs, processes

        elif cmd == "kill":
            if not args:
                return "kill: argument manquant (PID)", cwd, fs, processes
            try:
                target_pid = int(args[0])
            except ValueError:
                return f"kill: {args[0]}: PID non valide", cwd, fs, processes

            # Find and remove process
            found = False
            updated_processes = []
            for proc in processes:
                if proc.get("pid") == target_pid:
                    found = True
                else:
                    updated_processes.append(proc)

            if found:
                return "", cwd, fs, updated_processes
            return f"bash: kill: ({target_pid}) - Aucun processus de ce type", cwd, fs, processes

        elif cmd == "echo":
            # Simplistic echo without redirection handled here (redirections are parsed in execute())
            text = cls._extract_echo_text(command_line)
            return text, cwd, fs, processes

        elif cmd == "grep":
            if len(args) < 2:
                return "grep: arguments manquants. Utilisation : grep <pattern> <fichier>", cwd, fs, processes
            pattern = args[0].strip("'\"")
            target = cls._resolve_path(args[1], cwd)
            if target in fs:
                content = fs[target].get("content", "")
                matches = []
                for line in content.splitlines():
                    if pattern in line:
                        matches.append(line)
                return "\n".join(matches), cwd, fs, processes
            return f"grep: {args[1]}: Aucun fichier ou dossier de ce type", cwd, fs, processes

        else:
            return f"bash: {cmd}: commande introuvable", cwd, fs, processes


class DockerTerminalManager:
    """
    Manages connections to dynamic Docker containers via docker-py.
    Provides fallback simulation if Docker is not available.
    """
    @staticmethod
    def create_container(game_id: int, image_name: str = "ubuntu:20.04") -> Optional[str]:
        """Creates a secure Docker container for realistic exercises and returns container_id."""
        try:
            import docker
            client = docker.from_env()
            container_name = f"astarote_sandbox_{game_id}"
            
            # Remove any existing container with this name
            try:
                existing = client.containers.get(container_name)
                existing.remove(force=True)
            except Exception:
                pass

            # Create new isolated container
            container = client.containers.run(
                image_name,
                "sleep 3600",  # Keep alive for 1 hour
                name=container_name,
                detach=True,
                mem_limit="128m",
                nano_cpus=500000000, # 0.5 CPU limit
                network_disabled=True, # Securely isolate
                cap_drop=["ALL"], # Drop all capabilities
                read_only=False
            )
            return container.id
        except Exception as e:
            logger.warning(f"Docker API not fully configured or accessible. Falling back to emulation. Error: {str(e)}")
            return None

    @staticmethod
    def execute_in_container(container_id: str, command: str) -> str:
        """Executes a command inside the container and returns stdout/stderr."""
        try:
            import docker
            client = docker.from_env()
            container = client.containers.get(container_id)
            res = container.exec_run(command, user="nobody")
            return res.output.decode("utf-8", errors="ignore")
        except Exception as e:
            return f"Error executing inside container: {str(e)}"

    @staticmethod
    def stop_container(container_id: str):
        """Stops and cleans up the Docker container."""
        try:
            import docker
            client = docker.from_env()
            container = client.containers.get(container_id)
            container.stop(timeout=2)
            container.remove(force=True)
        except Exception:
            pass
