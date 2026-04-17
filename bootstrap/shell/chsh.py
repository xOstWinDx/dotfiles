"""Set fish as the login shell via ``chsh`` (Unix)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import shutil

from bootstrap.logging import get_logger
from bootstrap.models import Platform, ShellType, SystemInfo

logger = get_logger("bootstrap.shell.chsh")


def resolve_fish_binary() -> str | None:
    """Return an absolute path to the fish executable, if any."""
    w = shutil.which("fish")
    if w:
        return str(Path(w).resolve())
    for cand in ("/usr/bin/fish", "/bin/fish", "/usr/local/bin/fish", "/opt/homebrew/bin/fish"):
        p = Path(cand)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p.resolve())
    return None


def _path_in_etc_shells(shell_path: str) -> bool:
    """``chsh`` only accepts shells listed in ``/etc/shells``."""
    try:
        lines = Path("/etc/shells").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        logger.warning("Cannot read /etc/shells: %s", e)
        return False
    want = Path(shell_path).resolve()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            if Path(line).resolve() == want:
                return True
        except OSError:
            if line == shell_path:
                return True
    return False


def run_chsh_fish(
    system_info: SystemInfo,
    *,
    dry_run: bool,
    interactive: bool,
    assume_yes: bool,
    chsh_fish_flag: bool,
) -> tuple[bool, str]:
    """
    Offer to set fish as the login shell using ``chsh -s <fish>``.

    - Interactive: prompts (default **yes**).
    - ``--yes`` without ``--chsh-fish``: skips (safe default for automation).
    - ``--yes --chsh-fish``: runs when fish is available.

    Returns (changed, message) where *changed* means chsh was invoked successfully.
    """
    if system_info.platform == Platform.WINDOWS:
        return False, "chsh is not used on Windows."

    fish_path = resolve_fish_binary()
    if not fish_path:
        return False, "fish is not installed or not on PATH; cannot change login shell."

    if system_info.shell == ShellType.FISH:
        return False, "Login shell is already fish (SHELL points to fish)."

    if not _path_in_etc_shells(fish_path):
        return (
            False,
            f"{fish_path} is not listed in /etc/shells — chsh will refuse. "
            "Install the fish package from your distro or add the path to /etc/shells as root.",
        )

    if dry_run:
        logger.info("[DRY RUN] Would run: chsh -s %s", fish_path)
        return False, f"[DRY RUN] Would run: chsh -s {fish_path}"

    from bootstrap.ui import get_ui

    ui = get_ui()

    if assume_yes:
        if not chsh_fish_flag:
            return False, "Skipping chsh (--yes without --chsh-fish). Re-run with --chsh-fish to set fish as login shell."
    elif interactive:
        if not ui.prompt_yes_no(
            f"Set your default login shell to fish?\n  command: chsh -s {fish_path}\n"
            "You may be prompted for your password. New sessions will use fish.",
            default=True,
        ):
            return False, "Login shell left unchanged (you declined chsh)."
    else:
        return False, "Non-interactive session: skipping chsh (use --chsh-fish with --yes)."

    logger.info("Running: chsh -s %s", fish_path)
    try:
        # Do not capture stdio: PAM / chsh may need the real TTY for the password.
        r = subprocess.run(["chsh", "-s", fish_path], check=False)
        if r.returncode == 0:
            return True, f"Default shell set to fish ({fish_path}). Log out and back in (or reboot) to apply everywhere."
        return False, f"chsh exited with code {r.returncode}. Try manually: chsh -s {fish_path}"
    except OSError as e:
        return False, f"chsh failed: {e}"
