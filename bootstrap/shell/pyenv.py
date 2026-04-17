"""Pyenv feature — install via OS package managers (no git clone to ~/.pyenv)."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from pathlib import Path

from bootstrap.logging import get_logger
from bootstrap.privilege import get_privilege_manager
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

    Prefer ``pyenv latest``, fall back to parsing ``pyenv install --list``, then a conservative default.
    """
    if not pyenv_bin.is_file():
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
            lines = (result.stdout or "").strip().splitlines()
            token = lines[-1].strip() if lines else ""
            if re.fullmatch(r"\d+\.\d+\.\d+", token):
                return token
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug("pyenv latest failed: %s", e)

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
        logger.debug("pyenv install --list parse failed: %s", e)

    return f"{minor_line}.0"


def _pyenv_root_from_bin(pyenv_bin: Path) -> Path | None:
    try:
        result = subprocess.run(
            [str(pyenv_bin), "root"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        root = (result.stdout or "").strip()
        if root:
            return Path(root).expanduser().resolve()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, FileNotFoundError) as e:
        logger.debug("pyenv root failed: %s", e)
    return None


def _common_pyenv_bin_candidates() -> list[Path]:
    """Typical locations when ``brew install pyenv`` just finished (same-process PATH may be stale)."""
    home = Path.home()
    return [
        Path("/opt/homebrew/bin/pyenv"),
        Path("/usr/local/bin/pyenv"),
        home / ".linuxbrew/bin/pyenv",
        home / ".local/share/linuxbrew/bin/pyenv",
        home / ".pyenv/bin/pyenv",
    ]


def discover_pyenv() -> tuple[Path | None, Path | None]:
    """
    Find pyenv executable and data root.

    Homebrew puts ``pyenv`` on PATH; versions still live under ``pyenv root`` (usually ~/.pyenv).
    """
    which = shutil.which("pyenv")
    if which:
        pyenv_bin = Path(which).resolve()
        root = _pyenv_root_from_bin(pyenv_bin)
        return pyenv_bin, root

    for candidate in _common_pyenv_bin_candidates():
        if candidate.is_file():
            pyenv_bin = candidate.resolve()
            root = _pyenv_root_from_bin(pyenv_bin)
            return pyenv_bin, root

    return None, None


class PyenvManager:
    """Install and use pyenv from distro / Homebrew packages (no git clone)."""

    def __init__(self, dry_run: bool = False, interactive: bool = True):
        self.dry_run = dry_run
        self.interactive = interactive
        self.pyenv_bin: Path = Path.home() / ".pyenv" / "bin" / "pyenv"
        self.pyenv_home: Path = Path.home() / ".pyenv"
        self.is_installed = False
        self._refresh_install_state()

    def _refresh_install_state(self) -> None:
        bin_path, root = discover_pyenv()
        if bin_path and bin_path.is_file():
            self.pyenv_bin = bin_path
            self.pyenv_home = root if root else Path.home() / ".pyenv"
            self.is_installed = True
        else:
            self.pyenv_bin = Path.home() / ".pyenv" / "bin" / "pyenv"
            self.pyenv_home = Path.home() / ".pyenv"
            self.is_installed = False

        self.has_python = len(self.list_installed_pythons()) > 0 if self.is_installed else False

    def list_installed_pythons(self) -> list[str]:
        if not self.is_installed or not self.pyenv_bin.is_file():
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
            logger.debug("Could not list pyenv versions: %s", e)

        return []

    def _dry_run_plan(self) -> str:
        plat = platform.system().lower()
        if plat == "darwin":
            return "brew install pyenv" if shutil.which("brew") else "(Homebrew not found — install brew.sh first)"
        if plat == "linux":
            if shutil.which("apt") or shutil.which("apt-get"):
                return "apt install pyenv (+ build deps if required by distro)"
            if shutil.which("pacman"):
                return "pacman -S pyenv"
            if shutil.which("dnf"):
                return "dnf install pyenv"
            if shutil.which("brew"):
                return "brew install pyenv (Linuxbrew)"
        return "no supported package manager for pyenv"

    def install(self) -> bool:
        """Install pyenv using Homebrew or native Linux packages."""
        self._refresh_install_state()
        if self.is_installed:
            logger.info("Pyenv already on PATH: %s (root: %s)", self.pyenv_bin, self.pyenv_home)
            return True

        if self.dry_run:
            logger.info("[DRY RUN] Would install pyenv via: %s", self._dry_run_plan())
            return True

        logger.info("Installing pyenv via system package manager…")

        plat = platform.system().lower()

        if plat == "darwin":
            self._install_macos_brew()
        elif plat == "linux":
            self._install_linux_distro()
        else:
            logger.error("Pyenv auto-install is only wired for macOS and Linux.")

        self._refresh_install_state()
        if self.is_installed:
            logger.info("Pyenv is ready: %s (root: %s)", self.pyenv_bin, self.pyenv_home)
            return True

        logger.error(
            "Pyenv is still missing after install attempts. "
            "On macOS install Homebrew, then: brew install pyenv. "
            "On Linux use your distro package (apt/pacman/dnf) or https://github.com/pyenv/pyenv#installation"
        )
        return False

    def _install_macos_brew(self) -> bool:
        if not shutil.which("brew"):
            logger.error("Homebrew not found. Install from https://brew.sh then re-run bootstrap.")
            return False
        logger.info("Running: brew install pyenv")
        try:
            result = subprocess.run(
                ["brew", "install", "pyenv"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error("brew install pyenv failed (exit %s)", result.returncode)
                if result.stderr:
                    logger.error(result.stderr.strip())
                if result.stdout:
                    logger.debug(result.stdout.strip())
                return False
        except OSError as e:
            logger.error("brew install pyenv failed: %s", e)
            return False

        # Recommended build deps for ``pyenv install`` of CPython (formula may pull some already).
        optional = ["openssl", "readline", "sqlite3", "xz", "zlib", "pkg-config"]
        logger.info("Ensuring common build dependencies for ``pyenv install``: %s", ", ".join(optional))
        subprocess.run(
            ["brew", "install", *optional],
            capture_output=True,
            text=True,
            check=False,
        )
        return True

    def _install_linux_distro(self) -> bool:
        """Prefer native package manager; fall back to Linuxbrew if present."""
        pm = get_privilege_manager()

        if shutil.which("apt-get") or shutil.which("apt"):
            logger.info("Trying: apt install pyenv")
            pm.run_privileged(["apt-get", "update"], check=False)
            result = pm.run_privileged(["apt-get", "install", "-y", "pyenv"], check=False)
            if result.returncode == 0:
                return True
            logger.warning(
                "apt install pyenv failed (old Debian/Ubuntu may lack the package). "
                "See https://github.com/pyenv/pyenv/wiki#suggested-build-environment"
            )

        if shutil.which("pacman"):
            logger.info("Trying: pacman -S pyenv")
            result = pm.run_privileged(
                ["pacman", "-Sy", "--needed", "--noconfirm", "pyenv"],
                check=False,
            )
            if result.returncode == 0:
                return True
            logger.warning("pacman install pyenv failed.")

        if shutil.which("dnf"):
            logger.info("Trying: dnf install pyenv")
            result = pm.run_privileged(["dnf", "install", "-y", "pyenv"], check=False)
            if result.returncode == 0:
                return True
            logger.warning("dnf install pyenv failed.")

        if shutil.which("brew"):
            logger.info("Trying: brew install pyenv (Linuxbrew)")
            try:
                result = subprocess.run(
                    ["brew", "install", "pyenv"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return result.returncode == 0
            except OSError as e:
                logger.warning("Linuxbrew pyenv install failed: %s", e)

        return False

    def install_python(self, version: str, set_global: bool = False) -> bool:
        if not self.is_installed or not self.pyenv_bin.is_file():
            logger.error("Pyenv is not installed")
            return False

        if self.dry_run:
            logger.info("[DRY RUN] Would install Python %s", version)
            if set_global:
                logger.info("[DRY RUN] Would set Python %s as global", version)
            return True

        logger.info("Installing Python %s (this may take a while)…", version)

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
                    logger.info("Python %s is already present in pyenv", version)
                else:
                    logger.error("Failed to install Python %s", version)
                    if result.stderr:
                        logger.error(result.stderr.strip())
                    return False

            if set_global:
                subprocess.run(
                    [str(self.pyenv_bin), "global", version],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                logger.info("Set Python %s as global default", version)

            return True

        except subprocess.TimeoutExpired:
            logger.error("Python installation timed out")
            return False
        except OSError as e:
            logger.error("Failed to install Python: %s", e)
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

    Pyenv itself comes from **Homebrew (macOS)** or **apt / pacman / dnf** (Linux), not from ``git clone``.
    """
    if not should_offer_pyenv(profile_name):
        logger.debug("Skipping pyenv for this profile")
        return False

    ui = get_ui()
    manager = PyenvManager(dry_run=dry_run, interactive=interactive)

    minor_line = DEFAULT_MINOR
    set_global_default = True

    if force or assume_yes:
        pass
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

    manager._refresh_install_state()
    if not manager.pyenv_bin.is_file():
        logger.error("pyenv binary missing after install")
        return False

    version = resolve_preferred_python_version(manager.pyenv_bin, minor_line)
    logger.info("Selected Python version: %s", version)

    installed = manager.list_installed_pythons()
    if version in installed:
        logger.info("Python %s is already installed via pyenv", version)
        if set_global_default and not dry_run:
            subprocess.run(
                [str(manager.pyenv_bin), "global", version],
                capture_output=True,
                text=True,
                check=False,
            )
            logger.info("Ensured pyenv global is %s", version)
    elif not manager.install_python(version, set_global=set_global_default):
        logger.error("Failed to install Python %s", version)
        return False

    logger.info("Pyenv setup complete")
    return True
