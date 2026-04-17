"""Managed shell integration for bash/zsh (fish is handled via repo fish configs)."""

from __future__ import annotations

import shutil
from pathlib import Path

from bootstrap.logging import get_logger
from bootstrap.models import ShellType, SystemInfo

logger = get_logger("bootstrap.shell.integration")

MARKER_BEGIN = "# BEGIN bootstrap-dotfiles managed block"
MARKER_END = "# END bootstrap-dotfiles managed block"


def _managed_block(tag: str, body: str) -> str:
    body = body.strip("\n")
    return f"{MARKER_BEGIN} ({tag})\n{body}\n{MARKER_END} ({tag})\n"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _write_text(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        logger.info(f"[DRY RUN] Would update {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _backup_rc(rc_path: Path, dry_run: bool) -> Path | None:
    if dry_run or not rc_path.exists():
        return None
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = rc_path.with_suffix(rc_path.suffix + f".{stamp}.bak")
    backup.write_bytes(rc_path.read_bytes())
    logger.info(f"Backed up {rc_path} -> {backup}")
    return backup


def ensure_managed_block(
    rc_path: Path,
    tag: str,
    body: str,
    *,
    dry_run: bool,
    backup: bool,
) -> bool:
    """
    Insert or replace a managed block in a POSIX rc file.

    Returns True if the file was changed (or would be changed in dry-run).
    """
    block = _managed_block(tag, body)
    content = _read_text(rc_path)

    begin = f"{MARKER_BEGIN} ({tag})"
    end = f"{MARKER_END} ({tag})"

    if begin in content and end in content:
        before, rest = content.split(begin, 1)
        middle, after = rest.split(end, 1)
        new_inner = "\n" + body.strip("\n") + "\n"
        if middle.strip("\n") == body.strip("\n"):
            return False
        new_content = before + begin + new_inner + end + after
    elif not content.endswith("\n") and content:
        new_content = content + "\n\n" + block
    else:
        new_content = (content + "\n" if content else "") + block

    if new_content == content:
        return False

    if backup:
        _backup_rc(rc_path, dry_run)
    _write_text(rc_path, new_content, dry_run)
    return True


def _starship_init_snippet(shell: str) -> str:
    return f'if command -v starship >/dev/null 2>&1; then eval "$(starship init {shell})"; fi'


def _zoxide_init_snippet(shell: str) -> str:
    return f'if command -v zoxide >/dev/null 2>&1; then eval "$(zoxide init {shell})"; fi'


def _pyenv_init_snippet() -> str:
    # ``pyenv init`` sets PYENV_ROOT and PATH correctly for both Homebrew and ~/.pyenv layouts.
    return 'if command -v pyenv >/dev/null 2>&1; then eval "$(pyenv init -)"; fi'


def setup_posix_shell_rc(
    system_info: SystemInfo,
    *,
    enable_starship: bool,
    enable_zoxide: bool,
    enable_pyenv: bool,
    dry_run: bool,
    backup: bool,
) -> list[str]:
    """
    Configure bash/zsh rc files for the *current* login shell only.

    Fish is intentionally excluded here: dotfiles ship fish snippets under ~/.config/fish.
    """
    notes: list[str] = []
    shell = system_info.shell

    if system_info.platform.value == "windows":
        return notes

    if shell == ShellType.FISH:
        notes.append("Fish shell: use ~/.config/fish/conf.d snippets from dotfiles (no ~/.rc patching).")
        return notes

    if shell not in (ShellType.BASH, ShellType.ZSH):
        notes.append("Shell integration is only auto-managed for bash/zsh/fish.")
        return notes

    rc = Path.home() / (".bashrc" if shell == ShellType.BASH else ".zshrc")
    if not rc.exists() and not dry_run:
        rc.touch()

    changed = False

    if enable_starship and shutil.which("starship"):
        sh = "bash" if shell == ShellType.BASH else "zsh"
        changed |= ensure_managed_block(
            rc,
            "starship",
            _starship_init_snippet(sh),
            dry_run=dry_run,
            backup=backup,
        )

    if enable_zoxide and shutil.which("zoxide"):
        sh = "bash" if shell == ShellType.BASH else "zsh"
        changed |= ensure_managed_block(
            rc,
            "zoxide",
            _zoxide_init_snippet(sh),
            dry_run=dry_run,
            backup=backup,
        )

    if enable_pyenv and shutil.which("pyenv"):
        changed |= ensure_managed_block(
            rc,
            "pyenv",
            _pyenv_init_snippet(),
            dry_run=dry_run,
            backup=backup,
        )

    if changed:
        notes.append(f"Updated {rc} (managed blocks). Open a new terminal or: source {rc.name}")
    else:
        notes.append(f"No POSIX rc changes needed for {rc.name}.")

    return notes


def fish_default_shell_hint() -> str:
    return (
        "Fish is installed but not your default login shell. "
        "To make it default (after reviewing implications): chsh -s "
        f"{shutil.which('fish') or '/usr/bin/fish'}"
    )
