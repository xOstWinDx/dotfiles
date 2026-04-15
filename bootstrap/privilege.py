"""Privilege management - handles sudo/UAC for privileged operations."""
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from bootstrap.exceptions import PrivilegeError
from bootstrap.models import Platform


class PrivilegeManager:
    """Manages privilege escalation for system operations."""
    
    def __init__(self, platform: Platform = Platform.LINUX):
        self.platform = platform
        self._sudo_valid = False
        self._sudo_timestamp: Optional[float] = None
        self._sudo_timeout = 300  # 5 minutes cache
    
    def is_root(self) -> bool:
        """Check if running as root."""
        return os.geteuid() == 0 if self.platform != Platform.WINDOWS else False
    
    def validate_sudo(self) -> bool:
        """Validate sudo session (non-blocking check)."""
        if self.is_root():
            return True
        
        try:
            # Try non-blocking sudo check
            result = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True,
                timeout=1
            )
            self._sudo_valid = result.returncode == 0
            if self._sudo_valid:
                self._sudo_timestamp = time.time()
            return self._sudo_valid
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def request_sudo(self, timeout: int = 300) -> bool:
        """Request sudo privileges (with optional cache)."""
        if self.is_root():
            return True
        
        # Check cached session
        if self._sudo_valid and self._sudo_timestamp:
            elapsed = time.time() - self._sudo_timestamp
            if elapsed < self._sudo_timeout:
                return True
        
        # Need to request new sudo
        try:
            result = subprocess.run(
                ["sudo", "-v"],
                timeout=timeout
            )
            self._sudo_valid = result.returncode == 0
            if self._sudo_valid:
                self._sudo_timestamp = time.time()
            return self._sudo_valid
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise PrivilegeError(f"Failed to acquire sudo privileges: {e}")
    
    def run_privileged(self, cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run command with elevated privileges."""
        if self.is_root():
            return subprocess.run(cmd, check=check, capture_output=True, text=True)
        
        # Use sudo for the command
        return subprocess.run(
            ["sudo"] + cmd,
            check=check,
            capture_output=True,
            text=True
        )
    
    def run_privileged_interactive(self, cmd: list[str]) -> int:
        """Run command interactively (for package managers etc)."""
        if self.is_root():
            return subprocess.call(cmd)
        
        return subprocess.call(["sudo"] + cmd)


# Global instance
_privilege_manager: Optional[PrivilegeManager] = None


def get_privilege_manager() -> PrivilegeManager:
    """Get global privilege manager instance."""
    global _privilege_manager
    if _privilege_manager is None:
        from bootstrap.detection import detect_platform
        platform = detect_platform()
        _privilege_manager = PrivilegeManager(platform)
    return _privilege_manager


def needs_privilege(operation: str) -> bool:
    """Check if an operation requires elevated privileges."""
    # Package installations need sudo
    package_operations = ["apt", "pacman", "dnf", "brew", "winget", "install", "update"]
    if any(op in operation.lower() for op in package_operations):
        return True
    
    # System directories
    system_paths = ["/usr/bin", "/usr/local/bin", "/etc"]
    if any(operation.startswith(p) for p in system_paths):
        return True
    
    return False
