"""Pyenv feature - optional Python version management via pyenv."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from bootstrap.logging import get_logger

logger = get_logger("bootstrap.pyenv")

# Recommended Python versions for different use cases
RECOMMENDED_PYTHON_VERSIONS = [
    "3.12.0",  # Latest stable
    "3.11.5",  # Most tested
    "3.10.13", # LTS
]


class PyenvManager:
    """Manages pyenv installation and Python version management."""

    def __init__(self, dry_run: bool = False, interactive: bool = True):
        self.dry_run = dry_run
        self.interactive = interactive
        self.pyenv_home = Path.home() / ".pyenv"
        self.is_installed = self._check_installed()
        self.has_python = len(self.list_installed_pythons()) > 0

    def _check_installed(self) -> bool:
        """Check if pyenv is already installed."""
        return (
            self.pyenv_home.exists() and
            (self.pyenv_home / "bin" / "pyenv").exists()
        )

    def list_installed_pythons(self) -> list[str]:
        """List Python versions installed via pyenv."""
        if not self.is_installed:
            return []
        
        try:
            result = subprocess.run(
                [str(self.pyenv_home / "bin" / "pyenv"), "versions"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                versions = []
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line and not line.startswith("*"):
                        # Parse "3.12.0 (set by /path/to/file)" or just "3.12.0"
                        version = line.split()[0]
                        versions.append(version)
                return versions
        except Exception as e:
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
        
        # Check for prerequisites
        if not self._install_prerequisites():
            logger.error("Failed to install pyenv prerequisites")
            return False
        
        # Clone pyenv repo
        try:
            if self.pyenv_home.exists():
                logger.info("pyenv directory already exists, skipping clone")
            else:
                subprocess.run(
                    ["git", "clone", "https://github.com/pyenv/pyenv.git", str(self.pyenv_home)],
                    check=True,
                    capture_output=True,
                )
            
            # Also install pyenv-build plugin
            plugins_dir = self.pyenv_home / "plugins"
            pyenv_build = plugins_dir / "pyenv-build"
            if not pyenv_build.exists():
                subprocess.run(
                    ["git", "clone", "https://github.com/pyenv/pyenv-build.git", str(pyenv_build)],
                    check=True,
                    capture_output=True,
                )
            
            logger.info("Pyenv installed successfully")
            self.is_installed = True
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install pyenv: {e}")
            return False

    def _install_prerequisites(self) -> bool:
        """Install pyenv prerequisites based on platform."""
        # Respect dry-run mode - skip actual installation
        if self.dry_run:
            logger.info("  [DRY RUN] Would install pyenv prerequisites")
            return True
        
        platform = self._detect_platform()
        
        if platform == "linux-apt":
            return self._apt_install([
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
            ])
        elif platform == "linux-pacman":
            return self._pacman_install([
                "base-devel",
                "openssl",
                "zlib",
                "bz2",
                "readline",
                "sqlite",
                "ncurses",
                "xz",
                "tk",
                "libffi",
            ])
        elif platform == "macos":
            return self._brew_install([
                "openssl",
                "readline",
                "sqlite3",
                "xz",
                "zlib",
            ])
        
        return True

    def _detect_platform(self) -> str:
        """Detect package manager."""
        if shutil.which("apt"):
            return "linux-apt"
        elif shutil.which("pacman"):
            return "linux-pacman"
        elif shutil.which("brew"):
            return "macos"
        return "unknown"

    def _apt_install(self, packages: list[str]) -> bool:
        """Install packages via apt."""
        logger.info("  Installing prerequisites via apt...")
        try:
            subprocess.run(["sudo", "apt", "update"], check=True, capture_output=True)
            subprocess.run(["sudo", "apt", "install", "-y"] + packages, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"  Failed to install prerequisites: {e}")
            return False

    def _pacman_install(self, packages: list[str]) -> bool:
        """Install packages via pacman."""
        logger.info("  Installing prerequisites via pacman...")
        try:
            subprocess.run(["sudo", "pacman", "-Sy", "--needed"] + packages, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"  Failed to install prerequisites: {e}")
            return False

    def _brew_install(self, packages: list[str]) -> bool:
        """Install packages via Homebrew."""
        logger.info("  Installing prerequisites via Homebrew...")
        try:
            subprocess.run(["brew", "install"] + packages, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"  Failed to install prerequisites: {e}")
            return False

    def install_python(self, version: str, set_global: bool = False) -> bool:
        """Install a specific Python version via pyenv."""
        if not self.is_installed:
            logger.error("Pyenv is not installed")
            return False
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would install Python {version}")
            if set_global:
                logger.info(f"[DRY RUN] Would set Python {version} as global")
            return True
        
        logger.info(f"Installing Python {version}...")
        
        pyenv_bin = self.pyenv_home / "bin" / "pyenv"
        
        try:
            # Build Python
            result = subprocess.run(
                [str(pyenv_bin), "install", version],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes for Python build
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to install Python {version}")
                logger.error(f"Error: {result.stderr}")
                return False
            
            logger.info(f"Python {version} installed successfully")
            
            # Set as global if requested
            if set_global:
                subprocess.run(
                    [str(pyenv_bin), "global", version],
                    capture_output=True,
                )
                logger.info(f"Set Python {version} as global default")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Python installation timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to install Python: {e}")
            return False

    def get_fish_init_snippet(self) -> str:
        """Get Fish shell init snippet for pyenv."""
        if not self.is_installed:
            return ""
        
        return f'''
# Pyenv initialization
set -gx PYENV_ROOT {self.pyenv_home}
set -gx PATH $PYENV_ROOT/bin $PATH
pyenv init - | source
'''


def should_offer_pyenv(profile_name: str) -> bool:
    """Determine if pyenv should be offered for the given profile."""
    # pyenv is only offered for dev-oriented profiles
    offer_profiles = {"server", "desktop", "full"}
    return profile_name.lower() in offer_profiles


def prompt_pyenv_version(interactive: bool = True) -> Optional[tuple[str, bool]]:
    """
    Prompt user for pyenv installation.
    
    Returns:
        Tuple of (python_version, set_global) or None if declined
    """
    if not interactive:
        return None
    
    try:
        print("\n" + "=" * 60)
        print("  Pyenv Setup")
        print("=" * 60)
        print("\nPyenv allows you to manage multiple Python versions.")
        print("\nRecommended versions:")
        for v in RECOMMENDED_PYTHON_VERSIONS:
            print(f"  - {v}")
        print("\n0. Skip pyenv installation")
        print("1. Install pyenv, set latest recommended as global")
        
        choice = input("\nSelect option (0-1): ").strip()
        
        if choice == "0":
            return None
        elif choice == "1":
            return (RECOMMENDED_PYTHON_VERSIONS[0], True)
        else:
            print("Invalid choice, skipping pyenv")
            return None
            
    except (EOFError, KeyboardInterrupt):
        return None


def install_pyenv_for_profile(
    profile_name: str,
    dry_run: bool = False,
    interactive: bool = True,
    force: bool = False,
) -> bool:
    """
    Main entry point for pyenv installation in bootstrap flow.
    
    Args:
        profile_name: Current profile (affects whether pyenv is offered)
        dry_run: Dry run mode
        interactive: Interactive prompts enabled
        force: Force pyenv installation without prompting
    
    Returns:
        True if pyenv was installed, False otherwise
    """
    # Check if pyenv should be offered for this profile
    if not should_offer_pyenv(profile_name):
        logger.debug(f"Skipping pyenv for {profile_name} profile")
        return False
    
    # Check if pyenv is already available
    pyenv_path = Path.home() / ".pyenv" / "bin" / "pyenv"
    if pyenv_path.exists() and not force:
        logger.info("Pyenv already installed, skipping")
        return True
    
    # If not force and interactive, prompt user
    if not force and interactive:
        result = prompt_pyenv_version(interactive=True)
        if result is None:
            logger.info("User declined pyenv installation")
            return False
        
        python_version, set_global = result
    elif force:
        # Force mode with sensible defaults
        python_version = RECOMMENDED_PYTHON_VERSIONS[0]
        set_global = True
    else:
        # Non-interactive without force
        logger.debug("Skipping pyenv (non-interactive mode)")
        return False
    
    # Install pyenv
    manager = PyenvManager(dry_run=dry_run, interactive=interactive)
    
    if not manager.install():
        logger.error("Failed to install pyenv")
        return False
    
    # Install requested Python version
    if python_version:
        if not manager.install_python(python_version, set_global=set_global):
            logger.error(f"Failed to install Python {python_version}")
            return False
    
    logger.info("Pyenv setup complete!")
    return True
