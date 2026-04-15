"""Package registry - package installation management."""
import shutil
import subprocess
from typing import Optional

from bootstrap.models import Package, PackageManager, Platform, SystemInfo
from bootstrap.exceptions import PackageError
from bootstrap.logging import get_logger
from bootstrap.privilege import get_privilege_manager
from bootstrap.packages.definitions import PACKAGES

logger = get_logger("bootstrap.packages")


class PackageRegistry:
    """Handles package installation across platforms."""

    def __init__(self, system_info: SystemInfo):
        self.system_info = system_info
        self.package_manager = system_info.package_manager
        self.privilege = get_privilege_manager()

    def is_installed(self, package: Package) -> bool:
        """Check if package is already installed."""
        return shutil.which(package.name) is not None

    def install_package(self, package: Package, dry_run: bool = False) -> bool:
        """Install a single package."""
        logger.info(f"Installing package: {package.name}")

        if self.is_installed(package):
            logger.info(f"  {package.name} is already installed")
            return True

        if dry_run:
            logger.info(f"  [DRY RUN] Would install {package.name}")
            return True

        # Try platform-specific installation
        if self._install_via_package_manager(package):
            return True

        logger.error(f"  No installation method available for {package.name}")
        return False

    def _install_via_package_manager(self, package: Package) -> bool:
        """Install package using system package manager."""
        pkg_name = package.get_package_name(self.package_manager)
        if not pkg_name:
            return False

        try:
            if self.package_manager == PackageManager.APT:
                return self._install_apt(pkg_name)
            elif self.package_manager == PackageManager.PACMAN:
                return self._install_pacman(pkg_name)
            elif self.package_manager == PackageManager.DNF:
                return self._install_dnf(pkg_name)
            elif self.package_manager == PackageManager.BREW:
                return self._install_brew(pkg_name)
            elif self.package_manager == PackageManager.WINGET:
                return self._install_winget(pkg_name)
        except Exception as e:
            logger.warning(f"  Failed to install {pkg_name}: {e}")
            return False

        return True

    def _install_apt(self, pkg_name: str) -> bool:
        """Install via apt."""
        logger.info(f"  Installing via apt: {pkg_name}")
        self.privilege.run_privileged(["apt", "update"], check=True)
        result = self.privilege.run_privileged(["apt", "install", "-y", pkg_name], check=False)
        return result.returncode == 0

    def _install_pacman(self, pkg_name: str) -> bool:
        """Install via pacman."""
        logger.info(f"  Installing via pacman: {pkg_name}")
        result = self.privilege.run_privileged(
            ["pacman", "-Sy", "--needed", "--noconfirm", pkg_name],
            check=False
        )
        return result.returncode == 0

    def _install_dnf(self, pkg_name: str) -> bool:
        """Install via dnf."""
        logger.info(f"  Installing via dnf: {pkg_name}")
        result = self.privilege.run_privileged(["dnf", "install", "-y", pkg_name], check=False)
        return result.returncode == 0

    def _install_brew(self, pkg_name: str) -> bool:
        """Install via Homebrew."""
        logger.info(f"  Installing via brew: {pkg_name}")
        result = subprocess.run(
            ["brew", "install", pkg_name],
            capture_output=True, text=True, check=False
        )
        return result.returncode == 0

    def _install_winget(self, pkg_name: str) -> bool:
        """Install via winget."""
        logger.info(f"  Installing via winget: {pkg_name}")
        result = subprocess.run(
            ["winget", "install", "--id", pkg_name, "-e", "--silent"],
            capture_output=True, text=True, check=False
        )
        return result.returncode == 0

    def install_packages(self, package_names: list[str], dry_run: bool = False) -> dict[str, bool]:
        """Install multiple packages."""
        results = {}
        for name in package_names:
            package = PACKAGES.get(name)
            if not package:
                logger.warning(f"Unknown package: {name}")
                results[name] = False
                continue
            results[name] = self.install_package(package, dry_run)
        return results
