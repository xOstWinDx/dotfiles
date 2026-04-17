"""System detection module - detects OS, SSH, GUI and other environment info."""

import os
import platform
import shutil
import socket
from pathlib import Path
from typing import Optional

from bootstrap.models import (
    Distro,
    PackageManager,
    Platform,
    ShellType,
    SystemInfo,
)
from bootstrap.exceptions import DetectionError


def detect_platform() -> Platform:
    """Detect the operating system platform."""
    system = platform.system().lower()
    if system == "linux":
        return Platform.LINUX
    elif system == "darwin":
        return Platform.MACOS
    elif system == "windows":
        return Platform.WINDOWS
    return Platform.UNKNOWN


def detect_linux_distro() -> Distro:
    """Detect Linux distribution from /etc/os-release."""
    os_release_path = Path("/etc/os-release")
    
    if not os_release_path.exists():
        return Distro.UNKNOWN
    
    try:
        content = os_release_path.read_text()
        for line in content.splitlines():
            if line.startswith("ID="):
                distro_id = line.split("=")[1].strip().strip('"')
                if distro_id in ("arch", "manjaro", "endeavouros", "cachyos", "arcolinux", "artix", "chimeraos"):
                    return Distro.ARCH
                elif distro_id in ("ubuntu", "linuxmint", "pop"):
                    return Distro.UBUNTU
                elif distro_id in ("debian"):
                    return Distro.DEBIAN
                elif distro_id in ("fedora", "rhel", "centos"):
                    return Distro.FEDORA
    except Exception:
        pass
    
    return Distro.UNKNOWN


def detect_package_manager() -> PackageManager:
    """Detect available package manager."""
    # Check in order of preference
    managers = [
        (PackageManager.APT, ["apt", "apt-get"]),
        (PackageManager.PACMAN, ["pacman"]),
        (PackageManager.DNF, ["dnf", "yum"]),
        (PackageManager.BREW, ["brew"]),
        (PackageManager.WINGET, ["winget"]),
    ]
    
    for pm, commands in managers:
        for cmd in commands:
            if shutil.which(cmd):
                return pm
    
    return PackageManager.UNKNOWN


def detect_ssh_session() -> bool:
    """Detect if running in an SSH session."""
    ssh_vars = ["SSH_CLIENT", "SSH_TTY", "SSH_CONNECTION", "SSH_TUNNEL"]
    return any(os.environ.get(var) for var in ssh_vars)


def detect_gui_session(platform: Platform | None = None) -> bool:
    """Detect if a GUI session is available (best-effort)."""
    plat = platform or detect_platform()

    # macOS Terminal/iTerm often run without DISPLAY/WAYLAND but are still local GUI sessions.
    if plat == Platform.MACOS:
        # Local macOS consoles (Terminal.app / iTerm) often lack DISPLAY/WAYLAND.
        if not detect_ssh_session():
            ci = os.environ.get("CI", "").lower() in ("1", "true", "yes")
            if not ci:
                return True

    # Check environment variables
    if os.environ.get("DISPLAY"):
        return True
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return True
    if os.environ.get("QT_QPA_PLATFORM"):
        return True

    # Check systemd session type (Linux)
    if os.environ.get("XDG_SESSION_TYPE") in ("x11", "wayland"):
        return True

    return False


def detect_wsl() -> bool:
    """Detect if running in WSL."""
    if platform.system().lower() != "linux":
        return False
    
    try:
        proc_version = Path("/proc/version").read_text().lower()
        return "microsoft" in proc_version or "wsl" in proc_version
    except Exception:
        return False


def get_shell_type() -> Optional[ShellType]:
    """Detect current shell type."""
    shell_path = os.environ.get("SHELL", "")
    
    if "fish" in shell_path:
        return ShellType.FISH
    elif "zsh" in shell_path:
        return ShellType.ZSH
    elif "bash" in shell_path:
        return ShellType.BASH
    
    return None


def get_terminal_emulator() -> Optional[str]:
    """Detect terminal emulator."""
    # Check common environment variables
    term_programs = [
        os.environ.get("TERMINAL"),
        os.environ.get("ALACRITTY_SOCKET"),
        os.environ.get("KITTY_WINDOW_ID"),
        os.environ.get("TERM"),
    ]
    
    for term in term_programs:
        if term:
            return term.lower()
    
    # Try to get from process tree (Unix)
    if platform.system() != "Windows":
        try:
            ppid = os.getppid()
            proc_path = Path(f"/proc/{ppid}/comm")
            if proc_path.exists():
                return proc_path.read_text().strip()
        except Exception:
            pass
    
    return None


def get_username() -> str:
    """Get current username."""
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def get_hostname() -> str:
    """Get current hostname."""
    return socket.gethostname() or "unknown"


def detect_system() -> SystemInfo:
    """Detect all system information at once."""
    sys_info = SystemInfo()
    
    # Platform
    sys_info.platform = detect_platform()
    
    # Distro (if Linux)
    if sys_info.platform == Platform.LINUX:
        sys_info.distro = detect_linux_distro()
        sys_info.is_wsl = detect_wsl()
    
    # Package manager
    sys_info.package_manager = detect_package_manager()
    
    # Session type
    sys_info.is_ssh = detect_ssh_session()
    sys_info.has_gui = detect_gui_session(sys_info.platform)
    
    # User info
    sys_info.home_dir = Path.home()
    sys_info.username = get_username()
    sys_info.hostname = get_hostname()
    
    # Shell and terminal
    sys_info.shell = get_shell_type()
    sys_info.terminal_emulator = get_terminal_emulator()
    
    return sys_info


def auto_select_profile(sys_info: SystemInfo) -> str:
    """Auto-select profile based on system info."""
    # Remote SSH session (typical headless server workflow)
    if sys_info.is_ssh:
        return "server"

    # No GUI heuristics (Linux CI/TTY-only, etc.)
    if not sys_info.has_gui:
        return "server"

    return "desktop"


# Terminal emulator binaries we treat as "user already has a modern terminal"
_OTHER_TERMINAL_BINARIES: tuple[str, ...] = (
    "alacritty",
    "wezterm",
    "wezterm-gui",
    "ghostty",
    "foot",
    "konsole",
    "gnome-terminal",
    "xfce4-terminal",
    "terminator",
    "kitty",
)


def list_present_terminal_emulators() -> list[str]:
    """Return names of detected terminal emulators available on PATH."""
    found: list[str] = []
    for name in _OTHER_TERMINAL_BINARIES:
        if shutil.which(name):
            found.append(name)
    return found


def should_propose_kitty_install(sys_info: SystemInfo) -> bool:
    """Whether Kitty is a reasonable default *candidate* (user may still decline)."""
    if sys_info.is_ssh:
        return False
    if not sys_info.has_gui:
        return False
    if sys_info.is_wsl:
        return False
    if sys_info.platform not in (Platform.LINUX, Platform.MACOS):
        return False
    return True


def should_install_kitty(sys_info: SystemInfo) -> bool:
    """Deprecated: use should_propose_kitty_install + user confirmation in the installer."""
    return should_propose_kitty_install(sys_info)
