"""Pyenv feature - optional Python version management via pyenv."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from bootstrap.logging import get_logger
from bootstrap.ui import get_ui

logger = get_logger("bootstrap.pyenv")

DEFAULT_MINOR = "3.12"


def should_offer_pyenv(profile_name: str) -> bool:
    """Determine if pyenv should be offered for the given profile."""
    offer_profiles = {"server", "desktop", "full"}
    return profile_name.lower() in offer_profiles


def resolve_preferred_python_version(pyenv_bin: Path, minor_line: str = DEFAULT_MINOR) -> str:
    """
    Resolve a concrete CPython patch version for a minor line (e.g. 3.12 -> 3.12.7).

    Prefer `pyenv latest`, fall back to parsing `pyenv install --list`, then a conservative default.
    """
    if not pyenv_bin.exists():
        return f"{minor_line}.0"

    try:
        result = subprocess.run(
            [str(pyenv_bin), "latest", minor_line],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode == 0:
            line = (result.stdout or "").strip().splitlines()
            token = line[-1].strip() if line else ""
            if re.fullmatch(r"\d+\.\d+\.\d+", token):
                return token
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug(f"pyenv latest failed: {e}")

    try:
        result = subprocess.run(
            [str(pyenv_bin), "install", "--list"],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if result.returncode == 0:
            candidates: list[str] = []
            prefix = minor_line + "."
            for raw in (result.stdout or "").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.search(r"\b(\d+\.\d+\.\d+)\b", line)
                if not m:
                    continue
                ver = m.group(1)
                if ver.startswith(prefix):
                    candidates.append(ver)

            if candidates:
                def patch_key(v: str) -> tuple[int, int, int]:
                    a, b, c = v.split(".")
                    return int(a), int(b), int(c)

                return max(candidates, key=patch_key)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug(f"pyenv install --list parse failed: {e}")

    return f"{minor_line}.0"


class PyenvManager:
    """Manages pyenv installation and Python version management."""

    def __init__(self, dry_run: bool = False, interactive: bool = True):
        self.dry_run = dry_run
        self.interactive = interactive
        self.pyenv_home = Path.home() / ".pyenv"
        self.pyenv_bin = self.pyenv_home / "bin" / "pyenv"
        self.is_installed = self._check_installed()
        self.has_python = len(self.list_installed_pythons()) > 0

    def _check_installed(self) -> bool:
        return self.pyenv_home.is_dir() and self.pyenv_bin.is_file()

    def list_installed_pythons(self) -> list[str]:
        """List Python versions installed via pyenv."""
        if not self.is_installed:
            return []

        try:
            result = subprocess.run(
                [str(self.pyenv_bin), "versions", "--bare"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return []

            versions: list[str] = []
            for line in (result.stdout or "").splitlines():
                ver = line.strip()
                if ver and re.fullmatch(r"\d+\.\d+\.\d+", ver):
                    versions.append(ver)
            return versions
        except (subprocess.TimeoutExpired, OSError, FileNotFoundError) as e:
            logger.debug(f"Could not list pyenv versions: {e}")

        return []

    def install(self) -> bool:
        """Install pyenv."""
        if self.is_installed:
            logger.info("Pyenv is already installed")
            return True

        if self.dry_run:
            logger.info("[DRY RUN] Would install pyenv")
            return True

        logger.info("Installing pyenv...")

        if not self._install_prerequisites():
            logger.error("Failed to install pyenv prerequisites")
            return False

        try:
            if not self.pyenv_home.exists():
                subprocess.run(
                    ["git", "clone", "https://github.com/pyenv/pyenv.git", str(self.pyenv_home)],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            plugins_dir = self.pyenv_home / "plugins"
            pyenv_build = plugins_dir / "pyenv-build"
            if not pyenv_build.exists():
                plugins_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["git", "clone", "https://github.com/pyenv/pyenv-build.git", str(pyenv_build)],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            logger.info("Pyenv installed successfully")
            self.is_installed = self._check_installed()
            return self.is_installed

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install pyenv: {e}")
            return False

    def _install_prerequisites(self) -> bool:
        if self.dry_run:
            logger.info("  [DRY RUN] Would install pyenv prerequisites")
            return True

        plat = platform.system().lower()
        if plat == "darwin":
            return self._brew_install(["openssl", "readline", "sqlite3", "xz", "zlib"])
        if plat == "linux":
            if shutil.which("apt"):
                return self._apt_install(
                    [
                        "make",
                        "build-essential",
                        "libssl-dev",
                        "zlib1g-dev",
                        "libbz2-dev",
                        "libreadline-dev",
                        "libsqlite3-dev",
                        "libncursesw5-dev",
                        "xz-utils",
                        "tk-dev",
                        "libxml2-dev",
                        "libxmlsec1-dev",
                        "libffi-dev",
                        "liblzma-dev",
                    ]
                )
            if shutil.which("pacman"):
                return self._pacman_install(
                    [
                        "base-devel",
                        "openssl",
                        "zlib",
                        "bzip2",
                        "readline",
                        "sqlite",
                        "ncurses",
                        "xz",
                        "tk",
                        "libffi",
                    ]
                )

        logger.warning("Unknown Linux packaging for pyenv prerequisites; continuing anyway")
        return True

    def _apt_install(self, packages: list[str]) -> bool:
        logger.info("  Installing prerequisites via apt...")
        try:
            subprocess.run(["sudo", "apt", "update"], check=True, capture_output=True, text=True)
            subprocess.run(["sudo", "apt", "install", "-y", *packages], check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"  Failed to install prerequisites: {e}")
            return False

    def _pacman_install(self, packages: list[str]) -> bool:
        logger.info("  Installing prerequisites via pacman...")
        try:
            subprocess.run(
                ["sudo", "pacman", "-Sy", "--needed", "--noconfirm", *packages],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"  Failed to install prerequisites: {e}")
            return False

    def _brew_install(self, packages: list[str]) -> bool:
        logger.info("  Installing prerequisites via Homebrew...")
        try:
            subprocess.run(["brew", "install", *packages], check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"  Failed to install prerequisites: {e}")
            return False

    def install_python(self, version: str, set_global: bool = False) -> bool:
        if not self.is_installed:
            logger.error("Pyenv is not installed")
            return False

        if self.dry_run:
            logger.info(f"[DRY RUN] Would install Python {version}")
            if set_global:
                logger.info(f"[DRY RUN] Would set Python {version} as global")
            return True

        logger.info(f"Installing Python {version} (this may take a while)...")

        try:
            result = subprocess.run(
                [str(self.pyenv_bin), "install", version],
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if result.returncode != 0:
                combined = (result.stderr or "") + (result.stdout or "")
                if "already exists" in combined.lower():
                    logger.info(f"Python {version} is already present in pyenv")
                else:
                    logger.error(f"Failed to install Python {version}")
                    if result.stderr:
                        logger.error(result.stderr.strip())
                    return False

            if set_global:
                subprocess.run([str(self.pyenv_bin), "global", version], capture_output=True, text=True, check=False)
                logger.info(f"Set Python {version} as global default")

            return True

        except subprocess.TimeoutExpired:
            logger.error("Python installation timed out")
            return False
        except OSError as e:
            logger.error(f"Failed to install Python: {e}")
            return False


def _prompt_pyenv_plan(ui, interactive: bool) -> tuple[str, bool] | None:
    if not interactive:
        return None

    ui.print_info("Pyenv manages multiple Python versions side-by-side.")
    if not ui.prompt_yes_no("Install / update pyenv and a modern CPython via pyenv?", default=True):
        return None

    minor = DEFAULT_MINOR
    set_global = ui.prompt_yes_no("Set that version as pyenv global default?", default=True)
    return minor, set_global


def install_pyenv_for_profile(
    profile_name: str,
    *,
    dry_run: bool = False,
    interactive: bool = True,
    assume_yes: bool = False,
    force: bool = False,
) -> bool:
    """
    Install pyenv + a recent CPython for supported profiles.

    - Interactive: ask unless `assume_yes`.
    - Non-interactive + `assume_yes`: install sensible defaults without prompts.
    - `force`: skip decline paths (still respects dry-run).
    """
    if not should_offer_pyenv(profile_name):
        logger.debug("Skipping pyenv for this profile")
        return False

    ui = get_ui()
    manager = PyenvManager(dry_run=dry_run, interactive=interactive)

    minor_line = DEFAULT_MINOR
    set_global_default = True

    if force or assume_yes:
        pass  # use defaults
    elif interactive:
        plan = _prompt_pyenv_plan(ui, interactive=True)
        if plan is None:
            logger.info("User declined pyenv installation")
            return False
        minor_line, set_global_default = plan
    else:
        logger.info("Skipping pyenv (non-interactive session without --yes / --pyenv)")
        return False

    if not manager.install():
        logger.error("Failed to install pyenv")
        return False

    if not manager.pyenv_bin.exists():
        logger.error("pyenv binary missing after install")
        return False

    version = resolve_preferred_python_version(manager.pyenv_bin, minor_line)
    logger.info(f"Selected Python version: {version}")

    installed = manager.list_installed_pythons()
    if version in installed:
        logger.info(f"Python {version} is already installed via pyenv")
        if set_global_default and not dry_run:
            subprocess.run(
                [str(manager.pyenv_bin), "global", version],
                capture_output=True,
                text=True,
                check=False,
            )
            logger.info(f"Ensured pyenv global is {version}")
    elif not manager.install_python(version, set_global=set_global_default):
        logger.error(f"Failed to install Python {version}")
        return False

    logger.info("Pyenv setup complete")
    return True
