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
    
    # Platform-specific package names
    apt: Optional[str] = None
    pacman: Optional[str] = None
    dnf: Optional[str] = None
    brew: Optional[str] = None
    winget: Optional[str] = None
    
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
