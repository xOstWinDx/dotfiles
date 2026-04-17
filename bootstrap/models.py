"""Data models for Bootstrap."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Platform(Enum):
    """Supported platforms."""
    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class Distro(Enum):
    """Linux distributions."""
    ARCH = "arch"
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    FEDORA = "fedora"
    UNKNOWN = "unknown"


class PackageManager(Enum):
    """Package managers."""
    APT = "apt"
    PACMAN = "pacman"
    DNF = "dnf"
    BREW = "brew"
    WINGET = "winget"
    UNKNOWN = "unknown"


class ProfileType(Enum):
    """Deployment profiles."""
    MINIMAL = "minimal"
    SERVER = "server"
    DESKTOP = "desktop"
    FULL = "full"


class ShellType(Enum):
    """Shell types."""
    FISH = "fish"
    ZSH = "zsh"
    BASH = "bash"


class DeploymentStrategy(Enum):
    """Config deployment strategies."""
    SYMLINK = "symlink"
    COPY = "copy"
    MERGE = "merge"


class ConfigOverwritePolicy(Enum):
    """How to handle existing config targets that differ from the manifest."""
    ASK = "ask"
    SKIP = "skip"
    BACKUP_AND_REPLACE = "backup_and_replace"


class PackageInstallStatus(Enum):
    """Outcome of a single package install attempt."""
    SKIPPED_INSTALLED = "skipped_installed"
    SKIPPED_DRY_RUN = "skipped_dry_run"
    SKIPPED_FILTERED = "skipped_filtered"
    SKIPPED_UNKNOWN_PACKAGE = "skipped_unknown_package"
    INSTALLED = "installed"
    FAILED = "failed"


class PackageCategory(Enum):
    """Package categories."""
    CORE = "core"
    SHELL = "shell"
    TERMINAL = "terminal"
    NAVIGATION = "navigation"
    FILE_TOOLS = "file_tools"
    SEARCH = "search"
    MONITORING = "monitoring"
    GIT_TOOLS = "git_tools"
    DEV_TOOLS = "dev_tools"
    QUALITY_OF_LIFE = "quality_of_life"
    DESKTOP_ONLY = "desktop_only"
    SERVER_ONLY = "server_only"


@dataclass
class SystemInfo:
    """System information detected at runtime."""
    platform: Platform = Platform.UNKNOWN
    distro: Distro = Distro.UNKNOWN
    package_manager: PackageManager = PackageManager.UNKNOWN
    is_ssh: bool = False
    has_gui: bool = False
    is_wsl: bool = False
    home_dir: Path = field(default_factory=Path.home)
    username: str = ""
    hostname: str = ""
    shell: Optional[ShellType] = None
    terminal_emulator: Optional[str] = None


@dataclass
class Package:
    """Package definition with platform-specific names."""
    name: str
    category: PackageCategory
    description: str
    required: bool = False
    # Binaries used to detect an existing install (first match wins). Defaults to (name,).
    install_checks: tuple[str, ...] = ()
    
    # Platform-specific package names
    apt: Optional[str] = None
    pacman: Optional[str] = None
    dnf: Optional[str] = None
    brew: Optional[str] = None
    winget: Optional[str] = None
    
    def install_binary_candidates(self) -> tuple[str, ...]:
        """Return executable names that indicate the package is already usable."""
        if self.install_checks:
            return self.install_checks
        return (self.name,)
    
    def get_package_name(self, pm: PackageManager) -> Optional[str]:
        """Get package name for specific package manager."""
        mapping = {
            PackageManager.APT: self.apt,
            PackageManager.PACMAN: self.pacman,
            PackageManager.DNF: self.dnf,
            PackageManager.BREW: self.brew,
            PackageManager.WINGET: self.winget,
        }
        return mapping.get(pm)


@dataclass
class Config:
    """Configuration file definition."""
    name: str
    source_path: Path
    target_path: Path
    strategy: DeploymentStrategy = DeploymentStrategy.SYMLINK
    optional: bool = False
    description: str = ""
    create_parent_dirs: bool = True


@dataclass
class Profile:
    """Deployment profile definition."""
    name: ProfileType
    description: str
    packages: list[str] = field(default_factory=list)
    configs: list[str] = field(default_factory=list)
    shell_required: bool = True
    gui_required: bool = False


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    action: str
    target: Path
    message: str
    backup_path: Optional[Path] = None
    error: Optional[str] = None


@dataclass
class PackageInstallResult:
    """Structured result for package installation."""
    package_name: str
    status: PackageInstallStatus
    detail: str = ""


@dataclass
class ConfigManifest:
    """Config deployment manifest entry."""
    source: str  # Relative path in configs/
    target: str  # Target path in home/config
    platforms: list[Platform] = field(default_factory=list)  # Empty = all platforms
    profiles: list[ProfileType] = field(default_factory=list)  # Empty = all profiles
    strategy: DeploymentStrategy = DeploymentStrategy.SYMLINK
    optional: bool = False
    owner_only: bool = True  # Only deploy for current user (not system-wide)
    description: str = ""
    condition: Optional[str] = None  # Optional condition function name
