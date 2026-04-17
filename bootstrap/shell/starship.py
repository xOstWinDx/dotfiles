"""Ensure Starship CLI is available (brew first, then official install.sh → ~/.local/bin)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from bootstrap.logging import get_logger

logger = get_logger("bootstrap.shell.starship")

INSTALL_SCRIPT = "https://starship.rs/install.sh"


def _brew_install_starship() -> bool:
    if not shutil.which("brew"):
        return False
    logger.info("Trying: brew install starship")
    try:
        r = subprocess.run(
            ["brew", "install", "starship"],
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
        if r.returncode == 0 or shutil.which("starship"):
            return shutil.which("starship") is not None
        if r.stderr:
            logger.debug("brew stderr: %s", r.stderr.strip())
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning("brew install starship failed: %s", e)
    return False


def _curl_install_starship(local_bin: Path) -> bool:
    """Official installer: non-interactive, binaries into ~/.local/bin (matches fish 00-env)."""
    local_bin.mkdir(parents=True, exist_ok=True)
    logger.info("Installing Starship via %s → %s", INSTALL_SCRIPT, local_bin)
    try:
        curl = subprocess.Popen(
            ["curl", "-fsSL", INSTALL_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = curl.communicate(timeout=120)
        if curl.returncode != 0:
            logger.error("curl download failed: %s", err.decode(errors="replace")[:500] if err else "")
            return False
        script = out or b""
        r = subprocess.run(
            ["sh", "-s", "--", "-y", "-b", str(local_bin)],
            input=script,
            capture_output=True,
            timeout=300,
            check=False,
        )
        if r.returncode != 0:
            err = (r.stderr or b"").decode(errors="replace")[:800]
            logger.error("starship install.sh failed (exit %s): %s", r.returncode, err)
            return False
        if shutil.which("starship") or (local_bin / "starship").is_file():
            return True
        return False
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.error("Starship install script failed: %s", e)
        return False


def ensure_starship_installed(*, dry_run: bool = False) -> bool:
    """
    If ``starship`` is not on PATH, install via Homebrew or the official install script.

    Dotfiles deploy ``~/.config/starship.toml``; Starship reads that path by default on Unix.
    """
    if shutil.which("starship"):
        logger.debug("Starship already on PATH")
        return True

    if dry_run:
        logger.info("[DRY RUN] Would install Starship (brew or %s)", INSTALL_SCRIPT)
        return True

    if _brew_install_starship():
        logger.info("Starship installed via Homebrew: %s", shutil.which("starship"))
        return True

    local_bin = Path.home() / ".local" / "bin"
    if _curl_install_starship(local_bin):
        # Prefer newly installed binary if shell PATH not refreshed yet
        candidate = local_bin / "starship"
        if candidate.is_file() and not shutil.which("starship"):
            logger.info("Starship installed to %s (ensure ~/.local/bin is in PATH)", candidate)
        return True

    logger.error(
        "Could not install Starship. Install manually: brew install starship "
        "or curl -fsSL %s | sh -s -- -y -b ~/.local/bin",
        INSTALL_SCRIPT,
    )
    return False
