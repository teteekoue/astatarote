"""
Deterministic Linux engine — GNU-style command implementations.

Each command is a function (shell, args, stdin) -> (stdout, exit_status).
Outputs mimic real GNU coreutils / procps formatting so learners transfer
their skills directly to a production shell.
"""
from __future__ import annotations

import fnmatch
import posixpath
import re
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from .vfs import FileNode, VirtualFileSystem, perms_to_str

# Result of a command execution: (stdout, exit_status)
CmdResult = Tuple[str, int]

COMMANDS: Dict[str, Callable[..., CmdResult]] = {}
MAN_PAGES: Dict[str, str] = {}


def command(name: str, *aliases: str):
    def wrap(fn):
        COMMANDS[name] = fn
        for alias in aliases:
            COMMANDS[alias] = fn
        return fn
    return wrap


def man_page(name: str, content: str) -> None:
    MAN_PAGES[name] = content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_time(epoch: int) -> str:
    dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return dt.strftime("%b %e %H:%M")


def _fmt_date_full(epoch: int) -> str:
    dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S.000000000 +0000")


def _perm_str(node: FileNode) -> str:
    return node.permission_string()


def _display_path(shell, path: str) -> str:
    """Show a path the way bash would (home shortened to ~)."""
    home = shell.env.get("HOME", "/home/user")
    if path == home:
        return "~"
    if path.startswith(home + "/"):
        return "~/" + path[len(home) + 1:]
    return path


def _is_dir(shell: "DeterministicShell", path: str) -> bool:
    node = shell.vfs.get(path)
    return node is not None and node.kind == "dir"


def _readable_files(shell: "DeterministicShell", args: List[str]) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Resolve file arguments -> [(display_name, content)], errors."""
    pairs: List[Tuple[str, str]] = []
    errors: List[str] = []
    for arg in args:
        path = shell.resolve(arg)
        node = shell.vfs.get(path)
        if node is None:
            errors.append(f"cat: {arg}: No such file or directory")
            continue
        if node.kind == "dir":
            errors.append(f"cat: {arg}: Is a directory")
            continue
        if not shell.vfs.can("read", path, shell.user, shell.is_root):
            errors.append(f"cat: {arg}: Permission denied")
            continue
        target = shell.follow_link(path)
        pairs.append((arg, shell.vfs.get(target).content if shell.vfs.get(target) else node.content))
    return pairs, errors


# ---------------------------------------------------------------------------
# Navigation & information
# ---------------------------------------------------------------------------

@command("pwd")
def cmd_pwd(shell, args, stdin) -> CmdResult:
    return shell.cwd + "\n", 0


@command("cd")
def cmd_cd(shell, args, stdin) -> CmdResult:
    if not args or args[0] == "~":
        target = shell.env.get("HOME", "/home/user")
    else:
        target = shell.resolve(args[0])
    node = shell.vfs.get(target)
    if node is None:
        return f"bash: cd: {args[0]}: No such file or directory\n", 1
    if node.kind != "dir":
        return f"bash: cd: {args[0]}: Not a directory\n", 1
    if not shell.vfs.can("execute", target, shell.user, shell.is_root):
        return f"bash: cd: {args[0]}: Permission denied\n", 1
    shell.cwd = target
    shell.env["PWD"] = target
    return "", 0


@command("ls")
def cmd_ls(shell, args, stdin) -> CmdResult:
    long = False
    all_files = False
    recursive = False
    human = False
    targets: List[str] = []
    for arg in args:
        if arg.startswith("-") and arg != "-":
            if "l" in arg: long = True
            if "a" in arg: all_files = True
            if "R" in arg: recursive = True
            if "h" in arg: human = True
            if arg.strip("-") == "": continue
        else:
            targets.append(arg)

    if not targets:
        targets = ["."]

    out: List[str] = []
    status = 0
    multiple = len(targets) > 1

    def render_dir(path: str, header: Optional[str]):
        nonlocal status
        names = shell.vfs.list_dir(path)
        if not all_files:
            names = [n for n in names if not n.startswith(".")]
        if header:
            out.append(header)
        if not names:
            if long:
                out.append("total 0")
            return
        if long:
            total = sum(shell.vfs.get(posixpath.join(path, n)).reported_size() for n in names) // 1024
            out.append(f"total {max(total, 4)}")
            for name in names:
                node = shell.vfs.get(posixpath.join(path, name))
                link_count = 2 if node.kind == "dir" else 1
                suffix = f" -> {node.content}" if node.kind == "link" else ""
                out.append(
                    f"{_perm_str(node)} {link_count} {node.owner:<8} {node.group:<8} "
                    f"{node.reported_size():>6} {_fmt_time(node.mtime)} {name}{suffix}"
                )
        else:
            for name in names:
                out.append(name)

    def walk(path: str, display: str):
        nonlocal status
        node = shell.vfs.get(path)
        if node is None:
            out.append(f"ls: cannot access '{display}': No such file or directory")
            status = 2
            return
        if node.kind == "dir":
            if not shell.vfs.can("read", path, shell.user, shell.is_root):
                out.append(f"ls: cannot open directory '{display}': Permission denied")
                status = 2
                return
            header = f"{display}:" if (multiple or recursive) else None
            render_dir(path, header)
            if recursive:
                for name in shell.vfs.list_dir(path):
                    child = posixpath.join(path, name)
                    child_node = shell.vfs.get(child)
                    if child_node and child_node.kind == "dir":
                        out.append("")
                        walk(child, child)
        else:
            if multiple:
                out.append(display)
            elif long:
                out.append(
                    f"{_perm_str(node)} 1 {node.owner:<8} {node.group:<8} "
                    f"{node.reported_size():>6} {_fmt_time(node.mtime)} {display}"
                )
            else:
                out.append(display)

    for target in targets:
        path = shell.resolve(target)
        walk(path, target if target != "." else path)
        if len(targets) > 1 and target != targets[-1] and not recursive:
            out.append("")
    return "\n".join(out) + ("\n" if out else ""), status


@command("cat", "bat")
def cmd_cat(shell, args, stdin) -> CmdResult:
    number = False
    files: List[str] = []
    for arg in args:
        if arg.startswith("-") and arg not in ("-",):
            if "n" in arg: number = True
        else:
            files.append(arg)
    if not files:
        return (stdin or ""), 0
    pairs, errors = _readable_files(shell, files)
    out: List[str] = []
    for name, content in pairs:
        if number:
            for i, line in enumerate(content.splitlines(), 1):
                out.append(f"{i:>6}  {line}")
        else:
            out.append(content.rstrip("\n"))
    for err in errors:
        out.append(err)
    return ("\n".join(out) + "\n" if out else ""), 1 if errors else 0


@command("echo")
def cmd_echo(shell, args, stdin) -> CmdResult:
    return " ".join(args) + "\n", 0


@command("whoami")
def cmd_whoami(shell, args, stdin) -> CmdResult:
    return shell.user + "\n", 0


@command("id")
def cmd_id(shell, args, stdin) -> CmdResult:
    uid = 0 if shell.is_root else 1000
    user = shell.user
    if shell.is_root:
        groups = "0(root)"
    else:
        groups = f"1000({user}),27(sudo),1000({user})"
    return f"uid={uid}({user}) gid={uid}({'root' if shell.is_root else user}) groups={groups}\n", 0


@command("hostname")
def cmd_hostname(shell, args, stdin) -> CmdResult:
    return shell.host + "\n", 0


@command("uname")
def cmd_uname(shell, args, stdin) -> CmdResult:
    if any("a" in a for a in args if a.startswith("-")):
        return f"Linux {shell.host} 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux\n", 0
    if any("r" in a for a in args if a.startswith("-")):
        return "5.15.0-91-generic\n", 0
    return "Linux\n", 0


@command("date")
def cmd_date(shell, args, stdin) -> CmdResult:
    dt = datetime.fromtimestamp(shell.vfs.epoch, tz=timezone.utc)
    return dt.strftime("%a %b %d %H:%M:%S UTC %Y") + "\n", 0


@command("uptime")
def cmd_uptime(shell, args, stdin) -> CmdResult:
    return (
        f" {datetime.fromtimestamp(shell.vfs.epoch, tz=timezone.utc).strftime('%H:%M:%S')} up 2:03,  1 user,  "
        "load average: 0.42, 0.35, 0.29\n"
    ), 0


@command("free")
def cmd_free(shell, args, stdin) -> CmdResult:
    human = any("h" in a for a in args if a.startswith("-"))
    if human:
        return (
            "               total        used        free      shared  buff/cache   available\n"
            "Mem:           3.8Gi       1.1Gi       1.9Gi        26Mi       812Mi       2.4Gi\n"
            "Swap:             0B          0B          0B\n"
        ), 0
    return (
        "               total        used        free      shared  buff/cache   available\n"
        "Mem:         3861148     1122304     1945600       26624      793244     2511872\n"
        "Swap:              0           0           0\n"
    ), 0


@command("df")
def cmd_df(shell, args, stdin) -> CmdResult:
    human = any("h" in a for a in args if a.startswith("-"))
    if human:
        return (
            "Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1        40G   12G   26G  32% /\n"
            "tmpfs           1.9G     0  1.9G   0% /dev/shm\n"
            "/dev/sda2       100G   38G   57G  41% /data\n"
        ), 0
    return (
        "Filesystem     1K-blocks    Used Available Use% Mounted on\n"
        "/dev/sda1       41921536 12582912  27168896  32% /\n"
        "tmpfs            1976576        0   1976576   0% /dev/shm\n"
        "/dev/sda2      104857600 39845888  60011512  41% /data\n"
    ), 0


@command("du")
def cmd_du(shell, args, stdin) -> CmdResult:
    summary = any("s" in a for a in args if a.startswith("-"))
    human = any("h" in a for a in args if a.startswith("-"))
    targets = [a for a in args if not a.startswith("-")] or ["."]

    def size_of(path: str) -> int:
        node = shell.vfs.get(path)
        if node is None:
            return 0
        total = node.reported_size()
        prefix = "" if path == "/" else path
        for p, n in shell.vfs.nodes.items():
            if p.startswith(prefix + "/"):
                total += n.reported_size()
        return total

    out = []
    for target in targets:
        path = shell.resolve(target)
        if not shell.vfs.exists(path):
            out.append(f"du: cannot access '{target}': No such file or directory")
            continue
        total = size_of(path)
        if human:
            val = f"{total // 1024}K" if total < 1024 * 1024 else f"{round(total / 1024 / 1024, 1)}M"
        else:
            val = str(total // 1024 + 1)
        out.append(f"{val}\t{target}")
        if summary:
            continue
        if shell.vfs.get(path) and shell.vfs.get(path).kind == "dir":
            for name in shell.vfs.list_dir(path):
                child = posixpath.join(path, name)
                child_size = size_of(child)
                val = (f"{child_size // 1024}K" if human else str(child_size // 1024 + 1))
                out.append(f"{val}\t{posixpath.join(target.rstrip('/'), name)}")
    return "\n".join(out) + ("\n" if out else ""), 0


@command("tree")
def cmd_tree(shell, args, stdin) -> CmdResult:
    show_hidden = any("a" in a for a in args if a.startswith("-"))
    targets = [a for a in args if not a.startswith("-")] or ["."]
    out = []
    for target in targets:
        root_path = shell.resolve(target)
        if not shell.vfs.exists(root_path):
            out.append(f"tree: {target}: No such file or directory [error opening dir]")
            continue
        out.append(_display_path(shell, root_path) if target in (".",) else target)
        dirs_count, files_count = 0, 0

        def walk(path: str, prefix: str):
            nonlocal dirs_count, files_count
            names = shell.vfs.list_dir(path)
            if not show_hidden:
                names = [n for n in names if not n.startswith(".")]
            entries = []
            for name in names:
                node = shell.vfs.get(posixpath.join(path, name))
                if node and node.kind == "dir":
                    entries.append((name, True))
                else:
                    entries.append((name, False))
            for i, (name, is_dir) in enumerate(entries):
                connector = "├── " if i < len(entries) - 1 else "└── "
                out.append(prefix + connector + name + ("/" if is_dir else ""))
                if is_dir:
                    dirs_count += 1
                    extension = "│   " if i < len(entries) - 1 else "    "
                    walk(posixpath.join(path, name), prefix + extension)
                else:
                    files_count += 1

        walk(root_path, "")
        out.append("")
        out.append(f"{dirs_count} directories, {files_count} files")
    return "\n".join(out) + "\n", 0


# ---------------------------------------------------------------------------
# File creation / manipulation
# ---------------------------------------------------------------------------

@command("touch")
def cmd_touch(shell, args, stdin) -> CmdResult:
    if not args:
        return "touch: missing file operand\n", 1
    out, status = [], 0
    for arg in args:
        path = shell.resolve(arg)
        if shell.vfs.exists(path):
            shell.vfs.get(path).mtime = shell.vfs.epoch
            continue
        parent = shell.vfs.parent_of(path)
        if not shell.vfs.can("write", parent, shell.user, shell.is_root):
            out.append(f"touch: cannot touch '{arg}': Permission denied")
            status = 1
            continue
        shell.vfs.write_file(path, "", owner=shell.user)
    return "\n".join(out) + ("\n" if out else ""), status


@command("mkdir")
def cmd_mkdir(shell, args, stdin) -> CmdResult:
    parents = any("p" in a for a in args if a.startswith("-"))
    targets = [a for a in args if not a.startswith("-")]
    if not targets:
        return "mkdir: missing operand\n", 1
    out, status = [], 0
    for arg in targets:
        path = shell.resolve(arg)
        if shell.vfs.exists(path):
            out.append(f"mkdir: cannot create directory '{arg}': File exists")
            status = 1
            continue
        parent = shell.vfs.parent_of(path)
        if not shell.vfs.can("write", parent, shell.user, shell.is_root):
            out.append(f"mkdir: cannot create directory '{arg}': Permission denied")
            status = 1
            continue
        shell.vfs.ensure_dir(path, perms=0o755, owner=shell.user)
    return "\n".join(out) + ("\n" if out else ""), status


@command("rmdir")
def cmd_rmdir(shell, args, stdin) -> CmdResult:
    targets = [a for a in args if not a.startswith("-")]
    if not targets:
        return "rmdir: missing operand\n", 1
    out, status = [], 0
    for arg in targets:
        path = shell.resolve(arg)
        node = shell.vfs.get(path)
        if node is None:
            out.append(f"rmdir: failed to remove '{arg}': No such file or directory")
            status = 1
        elif node.kind != "dir":
            out.append(f"rmdir: failed to remove '{arg}': Not a directory")
            status = 1
        elif shell.vfs.list_dir(path):
            out.append(f"rmdir: failed to remove '{arg}': Directory not empty")
            status = 1
        elif not shell.vfs.can("write", shell.vfs.parent_of(path), shell.user, shell.is_root):
            out.append(f"rmdir: failed to remove '{arg}': Permission denied")
            status = 1
        else:
            del shell.vfs.nodes[path]
    return "\n".join(out) + ("\n" if out else ""), status


@command("rm")
def cmd_rm(shell, args, stdin) -> CmdResult:
    recursive = False
    force = False
    targets: List[str] = []
    for arg in args:
        if arg.startswith("-") and arg != "-":
            if "r" in arg or "R" in arg: recursive = True
            if "f" in arg: force = True
        else:
            targets.append(arg)
    if not targets:
        if force:
            return "", 0
        return "rm: missing operand\n", 1
    out, status = [], 0
    for arg in targets:
        path = shell.resolve(arg)
        node = shell.vfs.get(path)
        if node is None:
            if not force:
                out.append(f"rm: cannot remove '{arg}': No such file or directory")
                status = 1
            continue
        if node.kind == "dir" and not recursive:
            out.append(f"rm: cannot remove '{arg}': Is a directory")
            status = 1
            continue
        if path == "/":
            out.append("rm: it is dangerous to operate recursively on '/'")
            out.append("rm: use --no-preserve-root to override this failsafe")
            status = 1
            continue
        if not shell.vfs.can("write", shell.vfs.parent_of(path), shell.user, shell.is_root):
            out.append(f"rm: cannot remove '{arg}': Permission denied")
            status = 1
            continue
        for p in list(shell.vfs.nodes):
            if p == path or p.startswith(path + "/"):
                del shell.vfs.nodes[p]
    return "\n".join(out) + ("\n" if out else ""), status


def _copy_node(shell, src: str, dst: str) -> Optional[str]:
    """Copy src (file or dir) to dst. Returns error message or None."""
    src_node = shell.vfs.get(src)
    if src_node is None:
        return None
    dst_node = shell.vfs.get(dst)
    if dst_node is not None and dst_node.kind == "dir":
        dst = posixpath.join(dst, posixpath.basename(src))
        dst_node = shell.vfs.get(dst)
    if src_node.kind == "dir":
        shell.vfs.ensure_dir(dst, perms=src_node.perms, owner=shell.user)
        prefix = "" if src == "/" else src
        for p, node in shell.vfs.nodes.items():
            if p.startswith(prefix + "/"):
                rel = p[len(prefix) + 1:]
                target = posixpath.join(dst, rel)
                if node.kind == "dir":
                    shell.vfs.ensure_dir(target, perms=node.perms, owner=shell.user)
                else:
                    shell.vfs.write_file(target, node.content, perms=node.perms, owner=shell.user)
        return None
    shell.vfs.write_file(dst, src_node.content, perms=src_node.perms, owner=shell.user, size=src_node.size)
    return None


@command("cp")
def cmd_cp(shell, args, stdin) -> CmdResult:
    recursive = any(("r" in a or "R" in a) for a in args if a.startswith("-"))
    targets = [a for a in args if not a.startswith("-")]
    if len(targets) < 2:
        return "cp: missing destination file operand after '" + (targets[0] if targets else "") + "'\n", 1
    srcs, dst = targets[:-1], targets[-1]
    out, status = [], 0
    dst_path = shell.resolve(dst)
    dst_is_dir = _is_dir(shell, dst_path)
    if len(srcs) > 1 and not dst_is_dir:
        return f"cp: target '{dst}' is not a directory\n", 1
    for src in srcs:
        src_path = shell.resolve(src)
        node = shell.vfs.get(src_path)
        if node is None:
            out.append(f"cp: cannot stat '{src}': No such file or directory")
            status = 1
            continue
        if node.kind == "dir" and not recursive:
            out.append(f"cp: -r not specified; omitting directory '{src}'")
            status = 1
            continue
        target_path = posixpath.join(dst_path, posixpath.basename(src_path)) if dst_is_dir else dst_path
        if not shell.vfs.can("write", shell.vfs.parent_of(target_path), shell.user, shell.is_root):
            out.append(f"cp: cannot create '{dst}': Permission denied")
            status = 1
            continue
        err = _copy_node(shell, src_path, target_path)
        if err:
            out.append(err)
            status = 1
    return "\n".join(out) + ("\n" if out else ""), status


@command("mv")
def cmd_mv(shell, args, stdin) -> CmdResult:
    targets = [a for a in args if not a.startswith("-")]
    if len(targets) < 2:
        return "mv: missing destination file operand after '" + (targets[0] if targets else "") + "'\n", 1
    srcs, dst = targets[:-1], targets[-1]
    out, status = [], 0
    dst_path = shell.resolve(dst)
    dst_is_dir = _is_dir(shell, dst_path)
    if len(srcs) > 1 and not dst_is_dir:
        return f"mv: target '{dst}' is not a directory\n", 1
    for src in srcs:
        src_path = shell.resolve(src)
        node = shell.vfs.get(src_path)
        if node is None:
            out.append(f"mv: cannot stat '{src}': No such file or directory")
            status = 1
            continue
        target_path = posixpath.join(dst_path, posixpath.basename(src_path)) if dst_is_dir else dst_path
        if not shell.vfs.can("write", shell.vfs.parent_of(target_path), shell.user, shell.is_root):
            out.append(f"mv: cannot move '{src}' to '{dst}': Permission denied")
            status = 1
            continue
        # move the whole subtree
        moved = {p: n for p, n in shell.vfs.nodes.items() if p == src_path or p.startswith(src_path + "/")}
        for p in moved:
            del shell.vfs.nodes[p]
        for p, n in moved.items():
            new_p = target_path + p[len(src_path):]
            shell.vfs.nodes[new_p] = n
    return "\n".join(out) + ("\n" if out else ""), status


@command("ln")
def cmd_ln(shell, args, stdin) -> CmdResult:
    symbolic = any("s" in a for a in args if a.startswith("-"))
    targets = [a for a in args if not a.startswith("-")]
    if len(targets) < 2:
        return "ln: missing file operand\n", 1
    src, dst = targets[-2], targets[-1]
    src_path, dst_path = shell.resolve(src), shell.resolve(dst)
    if not symbolic:
        return "ln: hard links are not supported in this simulated environment (use -s)\n", 1
    if shell.vfs.exists(dst_path):
        return f"ln: failed to create symbolic link '{dst}': File exists\n", 1
    shell.vfs.write_link(dst_path, src, owner=shell.user)
    return "", 0


# ---------------------------------------------------------------------------
# Text processing
# ---------------------------------------------------------------------------

@command("head")
def cmd_head(shell, args, stdin) -> CmdResult:
    n = 10
    files: List[str] = []
    i = 0
    while i < len(args):
        if args[i] == "-n" and i + 1 < len(args):
            n = int(args[i + 1]); i += 2; continue
        if args[i].startswith("-") and args[i][1:].isdigit():
            n = int(args[i][1:]); i += 1; continue
        if args[i].startswith("-"):
            i += 1; continue
        files.append(args[i]); i += 1
    chunks = []
    if files:
        pairs, errors = _readable_files(shell, files)
        for name, content in pairs:
            chunks.append("\n".join(content.splitlines()[:n]))
        for e in errors:
            chunks.append(e)
            return "\n".join(chunks) + "\n", 1
    elif stdin:
        chunks.append("\n".join(stdin.splitlines()[:n]))
    return ("\n".join(chunks) + "\n" if chunks else ""), 0


@command("tail")
def cmd_tail(shell, args, stdin) -> CmdResult:
    n = 10
    files: List[str] = []
    i = 0
    while i < len(args):
        if args[i] == "-n" and i + 1 < len(args):
            n = int(args[i + 1]); i += 2; continue
        if args[i].startswith("-") and args[i][1:].isdigit():
            n = int(args[i][1:]); i += 1; continue
        if args[i].startswith("-"):
            i += 1; continue
        files.append(args[i]); i += 1
    chunks = []
    if files:
        pairs, errors = _readable_files(shell, files)
        for name, content in pairs:
            chunks.append("\n".join(content.splitlines()[-n:]) if content.strip() else "")
        for e in errors:
            chunks.append(e)
            return "\n".join(chunks) + "\n", 1
    elif stdin:
        chunks.append("\n".join(stdin.splitlines()[-n:]))
    return ("\n".join(chunks) + "\n" if chunks else ""), 0


@command("grep")
def cmd_grep(shell, args, stdin) -> CmdResult:
    ignore_case = False
    line_numbers = False
    invert = False
    count_only = False
    recursive = False
    extended = False
    pattern: Optional[str] = None
    files: List[str] = []
    for arg in args:
        if arg.startswith("-") and len(arg) > 1:
            if "i" in arg: ignore_case = True
            if "n" in arg: line_numbers = True
            if "v" in arg: invert = True
            if "c" in arg: count_only = True
            if "r" in arg or "R" in arg: recursive = True
            if "E" in arg: extended = True
            if "l" in arg: pass  # -l simplified as list handled below
            if arg in ("-rn", "-nr"): pass
            continue
        if pattern is None:
            pattern = arg
        else:
            files.append(arg)
    if pattern is None:
        return "Usage: grep [OPTION]... PATTERN [FILE]...\n", 2

    flags = re.IGNORECASE if ignore_case else 0
    try:
        rx = re.compile(pattern, flags)
    except re.error as e:
        return f"grep: invalid regular expression: {e}\n", 2

    def search_content(content: str) -> List[str]:
        matched = []
        for idx, line in enumerate(content.splitlines(), 1):
            hit = bool(rx.search(line))
            if hit != invert:
                matched.append((idx, line))
        return matched

    out: List[str] = []
    status = 0
    sources: List[Tuple[str, str]] = []

    if not files and stdin is not None:
        sources.append(("", stdin))
    else:
        for fname in files:
            path = shell.resolve(fname)
            node = shell.vfs.get(path)
            if node is None:
                out.append(f"grep: {fname}: No such file or directory")
                status = 2
                continue
            if node.kind == "dir" and not recursive:
                out.append(f"grep: {fname}: Is a directory")
                status = 2
                continue
            if node.kind == "dir" and recursive:
                prefix = "" if path == "/" else path
                for p, n in sorted(shell.vfs.nodes.items()):
                    if p.startswith(prefix + "/") and n.kind == "file":
                        if not shell.vfs.can("read", p, shell.user, shell.is_root):
                            continue
                        sources.append((posixpath.join(fname, p[len(prefix) + 1:]), n.content))
            else:
                if not shell.vfs.can("read", path, shell.user, shell.is_root):
                    out.append(f"grep: {fname}: Permission denied")
                    status = 2
                    continue
                target = shell.follow_link(path)
                tnode = shell.vfs.get(target) if target else node
                sources.append((fname, tnode.content if tnode else node.content))

    show_filename = len(sources) > 1
    for name, content in sources:
        matches = search_content(content)
        if count_only:
            out.append(f"{name + ':' if show_filename else ''}{len(matches)}")
        else:
            for idx, line in matches:
                prefix = f"{name}:" if show_filename else ""
                number = f"{idx}:" if line_numbers else ""
                out.append(f"{prefix}{number}{line}")
    return ("\n".join(out) + "\n" if out else ""), status


@command("wc")
def cmd_wc(shell, args, stdin) -> CmdResult:
    lines_only = any("l" in a for a in args if a.startswith("-"))
    words_only = any("w" in a for a in args if a.startswith("-"))
    chars_only = any(("c" in a or "m" in a) for a in args if a.startswith("-"))
    files = [a for a in args if not a.startswith("-")]
    results: List[Tuple[str, int, int, int]] = []
    out: List[str] = []
    if files:
        pairs, errors = _readable_files(shell, files)
        for name, content in pairs:
            ls = len(content.splitlines())
            ws = len(content.split())
            cs = len(content.encode("utf-8"))
            results.append((name, ls, ws, cs))
        for e in errors:
            out.append(e)
    elif stdin is not None:
        ls = len(stdin.splitlines())
        ws = len(stdin.split())
        cs = len(stdin.encode("utf-8"))
        results.append(("", ls, ws, cs))
    for name, ls, ws, cs in results:
        label = f" {name}" if name else ""
        if lines_only:
            out.append(f"{ls:>7}{label}")
        elif words_only:
            out.append(f"{ws:>7}{label}")
        elif chars_only:
            out.append(f"{cs:>7}{label}")
        else:
            out.append(f"{ls:>7}{ws:>8}{cs:>8}{label}")
    return ("\n".join(out) + "\n" if out else ""), 0


@command("sort")
def cmd_sort(shell, args, stdin) -> CmdResult:
    reverse = any("r" in a for a in args if a.startswith("-"))
    files = [a for a in args if not a.startswith("-")]
    content = ""
    if files:
        pairs, errors = _readable_files(shell, files)
        content = "\n".join(c for _, c in pairs)
        if errors:
            return errors[0] + "\n", 1
    elif stdin:
        content = stdin
    lines = sorted([l for l in content.splitlines()], reverse=reverse)
    return ("\n".join(lines) + "\n" if lines else ""), 0


@command("uniq")
def cmd_uniq(shell, args, stdin) -> CmdResult:
    count = any("c" in a for a in args if a.startswith("-"))
    files = [a for a in args if not a.startswith("-")]
    content = ""
    if files:
        pairs, errors = _readable_files(shell, files)
        content = "\n".join(c for _, c in pairs)
        if errors:
            return errors[0] + "\n", 1
    elif stdin:
        content = stdin
    out: List[str] = []
    prev = None
    n = 0
    for line in content.splitlines() + [""]:
        if line == prev:
            n += 1
            continue
        if prev is not None:
            out.append(f"{n:>7} {prev}" if count else prev)
        prev, n = line, 1
    return ("\n".join(out) + "\n" if out else ""), 0


@command("cut")
def cmd_cut(shell, args, stdin) -> CmdResult:
    delimiter = None
    fields = None
    files: List[str] = []
    i = 0
    while i < len(args):
        if args[i] == "-d" and i + 1 < len(args):
            delimiter = args[i + 1]; i += 2; continue
        if args[i].startswith("-d"):
            delimiter = args[i][2:]; i += 1; continue
        if args[i] == "-f" and i + 1 < len(args):
            fields = args[i + 1]; i += 2; continue
        if args[i].startswith("-f"):
            fields = args[i][2:]; i += 1; continue
        if args[i].startswith("-"):
            i += 1; continue
        files.append(args[i]); i += 1
    if fields is None:
        return "cut: you must specify a list of fields with -f\n", 1
    if delimiter is None:
        return "cut: you must specify a list of bytes/characters/fields with -d\n", 1
    try:
        field_indices = [int(x) for part in fields.split(",") for x in (range(1, 2) if part == "1" else [part])][:5]
        field_indices = []
        for part in fields.split(","):
            if "-" in part:
                a, b = part.split("-")
                field_indices.extend(range(int(a), int(b) + 1))
            else:
                field_indices.append(int(part))
    except ValueError:
        return f"cut: invalid field value '{fields}'\n", 1
    content = ""
    if files:
        pairs, errors = _readable_files(shell, files)
        content = "\n".join(c for _, c in pairs)
        if errors:
            return errors[0] + "\n", 1
    elif stdin:
        content = stdin
    out = []
    for line in content.splitlines():
        cols = line.split(delimiter)
        out.append(delimiter.join(cols[f - 1] for f in field_indices if f - 1 < len(cols)))
    return ("\n".join(out) + "\n" if out else ""), 0


@command("find")
def cmd_find(shell, args, stdin) -> CmdResult:
    targets = [a for a in args if not a.startswith("-")]
    root = shell.resolve(targets[0]) if targets else shell.cwd
    if not shell.vfs.exists(root):
        return f"find: '{targets[0] if targets else '.'}': No such file or directory\n", 1
    name_pattern = None
    type_filter = None
    i = 0
    while i < len(args):
        if args[i] == "-name" and i + 1 < len(args):
            name_pattern = args[i + 1]; i += 2; continue
        if args[i] == "-type" and i + 1 < len(args):
            type_filter = args[i + 1]; i += 2; continue
        i += 1
    out = []
    prefix = "" if root == "/" else root
    candidates = [root] + [p for p in sorted(shell.vfs.nodes) if p.startswith(prefix + "/")]
    for p in candidates:
        node = shell.vfs.get(p)
        if node is None:
            continue
        if name_pattern and not fnmatch.fnmatch(posixpath.basename(p), name_pattern):
            continue
        if type_filter:
            kind_map = {"f": "file", "d": "dir", "l": "link"}
            if node.kind != kind_map.get(type_filter, type_filter):
                continue
        # find echoes the path exactly as it was given (absolute here)
        out.append(p if p != root else (targets[0] if targets else "."))
    return ("\n".join(out) + "\n" if out else ""), 0


# ---------------------------------------------------------------------------
# Permissions & ownership
# ---------------------------------------------------------------------------

def _apply_symbolic_chmod(node: FileNode, spec: str) -> Optional[str]:
    """Apply symbolic mode like u+x, go-w, a=rw. Returns error or None."""
    for clause in spec.split(","):
        m = re.fullmatch(r"([ugoa]*)([+-=])([rwx]*)", clause)
        if not m:
            return f"chmod: invalid mode: '{spec}'"
        who, op, perms = m.group(1) or "a", m.group(2), m.group(3)
        mask = 0
        for c in perms:
            mask |= {"r": 4, "w": 2, "x": 1}[c]
        targets = who if who != "a" else "ugo"
        for w in targets:
            shift = {"u": 6, "g": 3, "o": 0}[w]
            current = node.perms & (7 << shift)
            if op == "+":
                node.perms |= (mask << shift)
            elif op == "-":
                node.perms &= ~(mask << shift)
            else:  # =
                node.perms = (node.perms & ~(7 << shift)) | (mask << shift)
    return None


@command("chmod")
def cmd_chmod(shell, args, stdin) -> CmdResult:
    recursive = any("R" in a for a in args if a.startswith("-") and a != "-R")
    recursive = recursive or "-R" in args
    operands = [a for a in args if not a.startswith("-")]
    if len(operands) < 2:
        return "chmod: missing operand\n", 1
    mode, files = operands[0], operands[1:]
    out, status = [], 0
    for fname in files:
        path = shell.resolve(fname)
        node = shell.vfs.get(path)
        if node is None:
            out.append(f"chmod: cannot access '{fname}': No such file or directory")
            status = 1
            continue
        if not shell.is_root and shell.user != node.owner:
            out.append(f"chmod: changing permissions of '{fname}': Operation not permitted")
            status = 1
            continue
        targets = [node]
        if recursive and node.kind == "dir":
            prefix = "" if path == "/" else path
            targets += [n for p, n in shell.vfs.nodes.items() if p.startswith(prefix + "/")]
        for target in targets:
            if re.fullmatch(r"[0-7]{3,4}", mode):
                target.perms = int(mode, 8)
            else:
                err = _apply_symbolic_chmod(target, mode)
                if err:
                    out.append(err)
                    status = 1
                    break
    return "\n".join(out) + ("\n" if out else ""), status


@command("chown")
def cmd_chown(shell, args, stdin) -> CmdResult:
    recursive = "-R" in args or any("R" in a for a in args if a.startswith("-") and len(a) > 1)
    operands = [a for a in args if not a.startswith("-")]
    if len(operands) < 2:
        return "chown: missing operand\n", 1
    owner_spec, files = operands[0], operands[1:]
    owner = owner_spec.split(":")[0]
    group = owner_spec.split(":")[1] if ":" in owner_spec else None
    out, status = [], 0
    for fname in files:
        path = shell.resolve(fname)
        node = shell.vfs.get(path)
        if node is None:
            out.append(f"chown: cannot access '{fname}': No such file or directory")
            status = 1
            continue
        if not shell.is_root:
            out.append(f"chown: changing ownership of '{fname}': Operation not permitted")
            status = 1
            continue
        targets = [node]
        if recursive and node.kind == "dir":
            prefix = "" if path == "/" else path
            targets += [n for p, n in shell.vfs.nodes.items() if p.startswith(prefix + "/")]
        for target in targets:
            target.owner = owner
            if group:
                target.group = group
    return "\n".join(out) + ("\n" if out else ""), status


@command("stat")
def cmd_stat(shell, args, stdin) -> CmdResult:
    targets = [a for a in args if not a.startswith("-")]
    if not targets:
        return "stat: missing operand\n", 1
    out, status = [], 0
    for fname in targets:
        path = shell.resolve(fname)
        node = shell.vfs.get(path)
        if node is None:
            out.append(f"stat: cannot stat '{fname}': No such file or directory")
            status = 1
            continue
        kind = {"file": "regular file", "dir": "directory", "link": "symbolic link"}[node.kind]
        inode = (abs(hash(path)) % 900000) + 100000
        out.append(f"  File: {fname}" + (f" -> {node.content}" if node.kind == "link" else ""))
        out.append(f"  Size: {node.reported_size():<10}\tBlocks: 8          IO Block: 4096   {kind}")
        out.append(f"Device: 801h/2049d\tInode: {inode:<10}  Links: 1")
        uid = 0 if node.owner == "root" else 1000
        out.append(f"Access: ({oct(node.perms)[2:].zfill(4)}/{_perm_str(node)})  Uid: ({uid:>4}/{node.owner:>7})   Gid: ({uid:>4}/{node.group:>7})")
        out.append(f"Modify: {_fmt_date_full(node.mtime)}")
    return "\n".join(out) + "\n", status


@command("file")
def cmd_file(shell, args, stdin) -> CmdResult:
    targets = [a for a in args if not a.startswith("-")]
    if not targets:
        return "file: missing operand\n", 1
    out = []
    for fname in targets:
        path = shell.resolve(fname)
        node = shell.vfs.get(path)
        if node is None:
            out.append(f"{fname}: cannot open `{fname}' (No such file or directory)")
            continue
        if node.kind == "dir":
            out.append(f"{fname}: directory")
        elif node.kind == "link":
            out.append(f"{fname}: symbolic link to {node.content}")
        elif node.content.startswith("#!"):
            out.append(f"{fname}: {node.content.splitlines()[0][2:].strip()} script, ASCII text executable")
        elif node.content.startswith("\x7fELF"):
            out.append(f"{fname}: ELF 64-bit LSB executable, x86-64")
        elif any(ord(c) > 127 for c in node.content[:200]):
            out.append(f"{fname}: data")
        else:
            out.append(f"{fname}: ASCII text")
    return "\n".join(out) + "\n", 0


@command("which")
def cmd_which(shell, args, stdin) -> CmdResult:
    out, status = [], 0
    for name in args:
        if name in shell.available_commands:
            out.append(f"/usr/bin/{name}")
        else:
            status = 1
    return ("\n".join(out) + "\n" if out else ""), status


# ---------------------------------------------------------------------------
# Processes
# ---------------------------------------------------------------------------

@command("ps")
def cmd_ps(shell, args, stdin) -> CmdResult:
    if any("a" in a and "u" in a for a in args if a.startswith("-")) or "-aux" in args or "aux" in args:
        return shell.processes.ps_aux() + "\n", 0
    if any(a.startswith("-") and "e" in a and "f" in a for a in args) or "-ef" in args or "ef" in args:
        lines = ["UID          PID    PPID  C STIME TTY          TIME CMD"]
        for p in shell.processes.alive():
            lines.append(f"{p.user:<11} {p.pid:>5}      1  0 {p.start} {p.tty:>6}       {p.time} {p.command}")
        return "\n".join(lines) + "\n", 0
    # plain ps: processes of current user on current tty
    lines = ["    PID TTY          TIME CMD"]
    for p in shell.processes.alive():
        if p.user == shell.user:
            lines.append(f"  {p.pid:>5} {p.tty:>6}       {p.time} {p.command}")
    return "\n".join(lines) + "\n", 0


@command("kill")
def cmd_kill(shell, args, stdin) -> CmdResult:
    signal = "15"
    pids: List[int] = []
    for arg in args:
        if arg.startswith("-") and arg[1:].isdigit():
            signal = arg[1:]
            continue
        if arg.startswith("-") and arg[1:].isalpha():
            signal = {"TERM": "15", "KILL": "9", "HUP": "1", "INT": "2"}.get(arg[1:].upper(), "15")
            continue
        try:
            pids.append(int(arg))
        except ValueError:
            return f"kill: {arg}: arguments must be process or job IDs\n", 1
    if not pids:
        return "kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec\n", 1
    out, status = [], 0
    for pid in pids:
        proc = None
        for p in shell.processes.alive():
            if p.pid == pid:
                proc = p
                break
        if proc is None:
            out.append(f"kill: ({pid}) - No such process")
            status = 1
        elif proc.system and not shell.is_root:
            out.append(f"kill: ({pid}) - Operation not permitted")
            status = 1
        else:
            shell.processes.kill(proc)
            if signal in ("9",):
                proc.stat = "Killed"
    return "\n".join(out) + ("\n" if out else ""), status


@command("top")
def cmd_top(shell, args, stdin) -> CmdResult:
    return shell.processes.top_snapshot() + "\n", 0


# ---------------------------------------------------------------------------
# Environment / shell builtins
# ---------------------------------------------------------------------------

@command("history")
def cmd_history(shell, args, stdin) -> CmdResult:
    out = []
    for i, entry in enumerate(shell.history, 1):
        out.append(f"{i:>5}  {entry}")
    return "\n".join(out) + "\n", 0


@command("env")
def cmd_env(shell, args, stdin) -> CmdResult:
    out = [f"{key}={value}" for key, value in sorted(shell.env.items())]
    return "\n".join(out) + "\n", 0


@command("export")
def cmd_export(shell, args, stdin) -> CmdResult:
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            shell.env[key] = value
    return "", 0


@command("alias")
def cmd_alias(shell, args, stdin) -> CmdResult:
    if not args:
        return "".join(f"alias {k}='{v}'\n" for k, v in shell.aliases.items()), 0
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            shell.aliases[key] = value.strip("'\"")
    return "", 0


@command("sleep")
def cmd_sleep(shell, args, stdin) -> CmdResult:
    return "", 0


@command("true")
def cmd_true(shell, args, stdin) -> CmdResult:
    return "", 0


@command("false")
def cmd_false(shell, args, stdin) -> CmdResult:
    return "", 1


@command("clear")
def cmd_clear(shell, args, stdin) -> CmdResult:
    shell.pending_action = "clear"
    return "", 0


@command("exit", "logout")
def cmd_exit(shell, args, stdin) -> CmdResult:
    shell.pending_action = "exit_hint"
    return "logout\n", 0


@command("help")
def cmd_help(shell, args, stdin) -> CmdResult:
    return (
        "Commandes disponibles dans ce terminal simulé :\n"
        "  Navigation : ls, cd, pwd, tree, find, which, file, stat\n"
        "  Fichiers   : cat, touch, mkdir, rmdir, rm, cp, mv, ln, head, tail\n"
        "  Texte      : grep, wc, sort, uniq, cut, echo\n"
        "  Droits     : chmod, chown, ls -l\n"
        "  Processus  : ps, top, kill\n"
        "  Système    : whoami, id, uname, hostname, date, uptime, free, df, du, env, export\n"
        "  Divers     : history, man <cmd>, sudo <cmd>, clear, help\n"
        "Astuce : la touche Tab complète les commandes et les chemins.\n"
    ), 0


@command("man")
def cmd_man(shell, args, stdin) -> CmdResult:
    if not args:
        return "What manual page do you want?\nFor example, try 'man man'.\n", 1
    name = args[0]
    page = MAN_PAGES.get(name)
    if page:
        return page, 0
    return (
        f"No manual entry for {name}\n"
    ), 1


@command("nano", "vim", "vi", "emacs")
def cmd_editor(shell, args, stdin) -> CmdResult:
    editor = "nano" if args and args[0] == "nano" else "vi"
    return (
        f"[Terminal simulé] L'éditeur interactif {editor} n'est pas disponible ici.\n"
        "Pour écrire un fichier, utilisez :\n"
        "  echo \"votre texte\" > fichier.txt        (créer/écraser)\n"
        "  echo \"ligne ajoutée\" >> fichier.txt     (ajouter à la fin)\n"
        "  cat fichier1 fichier2 > fichier3         (concaténer)\n"
    ), 0


@command("less", "more")
def cmd_less(shell, args, stdin) -> CmdResult:
    files = [a for a in args if not a.startswith("-")]
    if files:
        pairs, errors = _readable_files(shell, files)
        content = "\n".join(c for _, c in pairs)
        if errors:
            return errors[0] + "\n", 1
        return content.rstrip("\n") + "\n", 0
    return (stdin or ""), 0


@command("sudo")
def cmd_sudo(shell, args, stdin) -> CmdResult:
    if not args:
        return "usage: sudo command\n", 1
    sub = args[0]
    if sub in ("su", "su-", "-i", "-s", "bash", "sh"):
        return (
            "[sudo] password for user: \n"
            "(Simulation) Le shell root interactif est désactivé dans cet exercice.\n"
            "Utilisez plutôt : sudo <commande> pour exécuter une tâche en tant que root.\n"
        ), 0
    if sub not in shell.available_commands:
        return f"sudo: {sub}: command not found\n", 127
    shell.sudo_depth += 1
    try:
        output, status = shell.run_command(sub, args[1:], stdin, as_root=True)
        return output, status
    finally:
        shell.sudo_depth -= 1


# ---------------------------------------------------------------------------
# Network / system (simulated, deterministic)
# ---------------------------------------------------------------------------

@command("ip")
def cmd_ip(shell, args, stdin) -> CmdResult:
    if "a" in args or "addr" in args:
        return (
            "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default\n"
            "    inet 127.0.0.1/8 scope host lo\n"
            "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default\n"
            "    inet 10.0.2.15/24 brd 10.0.2.255 scope global dynamic eth0\n"
        ), 0
    return "Usage: ip [options] object { command help }\n", 1


@command("ping")
def cmd_ping(shell, args, stdin) -> CmdResult:
    hosts = [a for a in args if not a.startswith("-")]
    host = hosts[0] if hosts else ""
    return (
        f"PING {host} (10.0.2.{abs(hash(host)) % 200 + 20}) 56(84) bytes of data.\n"
        "64 bytes from host: icmp_seq=1 ttl=64 time=0.042 ms\n"
        "64 bytes from host: icmp_seq=2 ttl=64 time=0.038 ms\n"
        "64 bytes from host: icmp_seq=3 ttl=64 time=0.041 ms\n"
        "\n"
        f"--- {host} ping statistics ---\n"
        "3 packets transmitted, 3 received, 0% packet loss, time 2003ms\n"
    ), 0


@command("curl", "wget")
def cmd_curl(shell, args, stdin) -> CmdResult:
    return (
        "[Simulation] L'accès réseau réel est désactivé dans ce laboratoire.\n"
        "Astuce pédagogique : certains exercices fournissent des réponses scriptées\n"
        "pour ces commandes — essayez, vous pourriez être surpris.\n"
    ), 0


@command("ssh")
def cmd_ssh(shell, args, stdin) -> CmdResult:
    return (
        "ssh: connect to host port 22: Connection refused\n"
        "(Simulation) — la connexion SSH sortante est désactivée dans ce laboratoire.\n"
    ), 255


@command("apt", "apt-get")
def cmd_apt(shell, args, stdin) -> CmdResult:
    if not args:
        return "apt 2.4.9 (amd64)\nUsage: apt [options] command\n", 0
    sub, rest = args[0], args[1:]
    if sub == "update":
        return (
            "Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease\n"
            "Reading package lists... Done\n"
            "All packages are up to date.\n"
        ), 0
    if sub == "install":
        return (
            "Reading package lists... Done\n"
            "Building dependency tree... Done\n"
            "Package installation is simulated in this lab environment.\n"
        ), 0
    if sub in ("search", "show"):
        return "apt search is simulated — consult the level's tech sheet.\n", 0
    return f"E: Invalid operation: {sub}\n", 100


@command("systemctl", "service")
def cmd_systemctl(shell, args, stdin) -> CmdResult:
    if not args:
        return "System has not been booted with systemd (simulated environment).\n", 1
    sub = args[0]
    name = args[1] if len(args) > 1 else "service"
    if sub == "status":
        return (
            f"● {name}.service - {name} daemon\n"
            f"     Loaded: loaded (/lib/systemd/system/{name}.service; enabled)\n"
            "     Active: active (running) since Thu 2026-01-01 08:00:12 UTC; 2h 13min ago\n"
            "   Main PID: 411 (code=exited, status=0/SUCCESS)\n"
            "      Tasks: 1 (limit: 4519)\n"
        ), 0
    return f"Systemctl '{sub}' handled by the simulated environment.\n", 0


@command("journalctl")
def cmd_journalctl(shell, args, stdin) -> CmdResult:
    return (
        "-- Journal begins at Thu 2026-01-01 08:00:01 UTC. --\n"
        "janv. 01 08:00:12 meridian systemd[1]: Started Session 1 of user user.\n"
        "Use 'cat /var/log/syslog' for the full simulated logs.\n"
    ), 0


@command("neofetch")
def cmd_neofetch(shell, args, stdin) -> CmdResult:
    return (
        f"       .--.      {shell.user}@{shell.host}\n"
        "      |o_o |     ---------------\n"
        "      |:_/ |     OS: Astatarote Linux x86_64 (simulated)\n"
        f"     //   \\ \\    Kernel: 5.15.0-91-generic\n"
        "    (|     | )   Shell: bash (deterministic engine)\n"
        "   /'\\_   _/`\\   Terminal: astatarote-lab\n"
        "   \\___)=(___/   CPU: Intel i7-9750H (simulated)\n"
    ), 0


@command("reboot", "shutdown", "poweroff", "halt", "init")
def cmd_power(shell, args, stdin) -> CmdResult:
    return (
        "[Garde-fou] Les commandes d'arrêt/redémarrage sont désactivées\n"
        "dans ce laboratoire. Votre session est précieuse !\n"
    ), 1


@command("passwd", "useradd", "adduser", "usermod", "groupadd")
def cmd_usermgmt(shell, args, stdin) -> CmdResult:
    return (
        "[Simulation] La gestion des comptes est hors périmètre pour cet exercice.\n"
        "Consultez /etc/passwd et /etc/group avec cat pour explorer les comptes.\n"
    ), 0


@command("tar", "gzip", "gunzip", "zip", "unzip")
def cmd_archive(shell, args, stdin) -> CmdResult:
    return "[Simulation] Les archives ne sont pas gérées dans ce laboratoire.\n", 1


@command("bash", "sh", "python3", "gcc", "make", "dd")
def cmd_runtime(shell, args, stdin) -> CmdResult:
    return "[Simulation] L'exécution de programmes arbitraires est désactivée ici.\n", 1


# ---------------------------------------------------------------------------
# French man pages (static, educational)
# ---------------------------------------------------------------------------

man_page("man", """MAN(1)                        Manual pages

NOM
       man - affiche le manuel d'une commande

SYNOPSIS
       man COMMANDE

DESCRIPTION
       Affiche la page de manuel de COMMANDE. Les pages sont regroupées en
       sections : 1 = commandes utilisateur, 5 = formats de fichiers,
       8 = administration système.
""")

man_page("ls", """LS(1)                          User Commands

NOM
       ls - lister le contenu d'un répertoire

SYNOPSIS
       ls [OPTION]... [FICHIER]...

DESCRIPTION
       -l     format long : permissions, propriétaire, taille, date
       -a     affiche aussi les fichiers cachés (commençant par .)
       -R     liste récursivement les sous-répertoires
       -h     tailles lisibles (K, M, G)

EXEMPLES
       ls -la /etc    liste détaillée y compris les fichiers cachés
""")

man_page("cd", """CD(1) Bash built-in

NOM
       cd - changer le répertoire courant

SYNOPSIS
       cd [RÉPERTOIRE]

DESCRIPTION
       Sans argument, retourne au répertoire personnel ($HOME).
       cd .. remonte d'un niveau. cd - revient au répertoire précédent.
""")

man_page("pwd", """PWD(1) Bash built-in

NOM
       pwd - afficher le répertoire de travail courant

SYNOPSIS
       pwd
""")

man_page("cat", """CAT(1)                        User Commands

NOM
       cat - afficher et concaténer des fichiers

SYNOPSIS
       cat [OPTION]... [FICHIER]...

DESCRIPTION
       -n   numérote les lignes affichées
       Sans fichier, lit l'entrée standard (utile avec les tubes).
""")

man_page("grep", """GREP(1)                       User Commands

NOM
       grep - chercher un motif dans des fichiers

SYNOPSIS
       grep [OPTION]... MOTIF [FICHIER]...

DESCRIPTION
       -i   ignore la casse
       -n   affiche les numéros de ligne
       -v   inverse la recherche (lignes SANS le motif)
       -r   recherche récursive dans un dossier
       -c   compte les lignes correspondantes
       -E   expressions régulières étendues
""")

man_page("chmod", """CHMOD(1)                      User Commands

NOM
       chmod - modifier les permissions d'un fichier

SYNOPSIS
       chmod [OPTION]... MODE FICHIER...

DESCRIPTION
       MODE numérique : 3 chiffres octaux (propriétaire, groupe, autres)
         r=4  w=2  x=1  →  7=rwx, 6=rw-, 5=r-x, 0=---
         Exemple : chmod 640 rapport.txt

       MODE symbolique : [ugoa][+-=][rwx]
         u=propriétaire g=groupe o=autres a=tous
         Exemple : chmod u+x script.sh
       -R   applique récursivement
""")

man_page("chown", """CHOWN(1)                      User Commands

NOM
       chown - changer le propriétaire d'un fichier

SYNOPSIS
       chown [OPTION]... [PROPRIÉTAIRE][:[GROUPE]] FICHIER...

DESCRIPTION
       Réservé à root (utilisez sudo). Exemple :
         sudo chown user:staff rapport.txt
       -R   applique récursivement
""")

man_page("ps", """PS(1)                         User Commands

NOM
       ps - afficher les processus en cours

SYNOPSIS
       ps aux

DESCRIPTION
       a = processus de tous les utilisateurs, u = format détaillé,
       x = y compris ceux sans terminal.
       Colonnes : PID, %CPU, %MEM, STAT, COMMAND.
""")

man_page("kill", """KILL(1)                       User Commands

NOM
       kill - envoyer un signal à un processus

SYNOPSIS
       kill [-9] PID...

DESCRIPTION
       Par défaut envoie SIGTERM (15) : demande un arrêt propre.
       kill -9 PID envoie SIGKILL : arrêt immédiat et forcé.
       Seul root peut tuer les processus système.
""")

man_page("mkdir", """MKDIR(1)                      User Commands

NOM
       mkdir - créer un répertoire

SYNOPSIS
       mkdir [OPTION]... RÉPERTOIRE...

DESCRIPTION
       -p   crée les parents manquants, sans erreur s'il existe
""")

man_page("rm", """RM(1)                         User Commands

NOM
       rm - supprimer des fichiers ou répertoires

SYNOPSIS
       rm [OPTION]... FICHIER...

DESCRIPTION
       -r   suppression récursive (dossiers)
       -f   forcer, ignorer les erreurs
       ATTENTION : la suppression est définitive, pas de corbeille.
""")

man_page("cp", """CP(1)                         User Commands

NOM
       cp - copier des fichiers et répertoires

SYNOPSIS
       cp [OPTION]... SOURCE... DEST

DESCRIPTION
       -r   copie récursive des dossiers
""")

man_page("mv", """MV(1)                         User Commands

NOM
       mv - déplacer ou renommer

SYNOPSIS
       mv SOURCE... DEST

DESCRIPTION
       Si DEST est un dossier, SOURCE y est déplacé.
       Sinon, SOURCE est renommé en DEST.
""")

man_page("find", """FIND(1)                       User Commands

NOM
       find - chercher des fichiers dans une arborescence

SYNOPSIS
       find [CHEMIN] [EXPRESSION]

DESCRIPTION
       -name MOTIF    nom de fichier (jokers * ? autorisés)
       -type f|d      fichier ou dossier
       Exemple : find /var -name "*.log" -type f
""")

man_page("head", """HEAD(1)                       User Commands

NOM
       head - afficher les premières lignes

SYNOPSIS
       head [-n N] [FICHIER]...

DESCRIPTION
       Affiche les 10 premières lignes par défaut, N avec -n.
""")

man_page("tail", """TAIL(1)                       User Commands

NOM
       tail - afficher les dernières lignes

SYNOPSIS
       tail [-n N] [FICHIER]...

DESCRIPTION
       Affiche les 10 dernières lignes par défaut, N avec -n.
       tail -n 20 syslog  →  20 dernières lignes de syslog
""")

man_page("wc", """WC(1)                         User Commands

NOM
       wc - compter les lignes, mots, caractères

SYNOPSIS
       wc [OPTION]... [FICHIER]...

DESCRIPTION
       -l lignes  -w mots  -c caractères
""")

man_page("sudo", """SUDO(8)                       System Admin

NOM
       sudo - exécuter une commande en tant que root

SYNOPSIS
       sudo COMMANDE

DESCRIPTION
       Le compte courant appartient au groupe sudo : les commandes
       préfixées par sudo s'exécutent avec les droits administrateur.
       Utilisez sudo avec parcimonie et conscience.
""")

man_page("history", """HISTORY(1) Bash built-in

NOM
       history - historique des commandes tapées

SYNOPSIS
       history

DESCRIPTION
       Les flèches haut/bas naviguent dans l'historique.
""")

man_page("tree", """TREE(1)                       User Commands

NOM
       tree - afficher l'arborescence d'un dossier

SYNOPSIS
       tree [OPTION]... [CHEMIN]

DESCRIPTION
       Montre l'arborescence sous forme graphique.
       -a inclut les fichiers cachés.
""")

man_page("stat", """STAT(1)                       User Commands

NOM
       stat - afficher l'état complet d'un fichier

SYNOPSIS
       stat FICHIER...

DESCRIPTION
       Affiche taille, permissions octales/symboliques,
       propriétaire, inode et dates.
""")

man_page("df", """DF(1)                         User Commands

NOM
       df - espace disque des systèmes de fichiers

SYNOPSIS
       df [-h]

DESCRIPTION
       -h   tailles lisibles (K, M, G)
""")

man_page("du", """DU(1)                         User Commands

NOM
       du - espace utilisé par un dossier

SYNOPSIS
       du [-sh] [CHEMIN]

DESCRIPTION
       -s   résumé uniquement  -h tailles lisibles
""")

man_page("file", """FILE(1)                       User Commands

NOM
       file - déterminer le type d'un fichier

SYNOPSIS
       file FICHIER...

DESCRIPTION
       Détecte le type réel (texte, exécutable, dossier...)
       indépendamment de l'extension.
""")

man_page("top", """TOP(1)                        User Commands

NOM
       top - processus en temps réel

SYNOPSIS
       top

DESCRIPTION
       Vue instantanée triée par %CPU. Cherchez la colonne %CPU pour
       repérer un processus gourmand, puis kill PID.
""")

man_page("free", """FREE(1)                       User Commands

NOM
       free - mémoire du système

SYNOPSIS
       free [-h]

DESCRIPTION
       -h   tailles lisibles. Surveillez la colonne available.
""")

man_page("echo", """ECHO(1) Bash built-in

NOM
       echo - afficher un texte

SYNOPSIS
       echo TEXTE

DESCRIPTION
       Avec la redirection : echo "texte" > fichier (écrase)
       ou echo "texte" >> fichier (ajoute).
""")
