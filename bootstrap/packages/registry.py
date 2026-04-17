"""Package registry - package installation management."""
import shutil
import subprocess
from typing import Iterable

from bootstrap.models import (
    Package,
    PackageInstallResult,
    PackageInstallStatus,
    PackageManager,
    SystemInfo,
)
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
        self._apt_updated = False
        self._pacman_synced = False

    def is_installed(self, package: Package) -> bool:
        """Return True if any known binary for this package is on PATH."""
        for name in package.install_binary_candidates():
            if shutil.which(name):
                return True
        return False

    def _ensure_apt_updated(self, dry_run: bool) -> None:
        if self.package_manager != PackageManager.APT:
            return
        if self._apt_updated:
            return
        if dry_run:
            logger.info("  [DRY RUN] Would run apt update (once per session)")
            self._apt_updated = True
            return
        logger.info("  Running apt update (once per bootstrap session)")
        try:
            self.privilege.run_privileged(["apt", "update"], check=True)
            self._apt_updated = True
        except Exception as e:
            logger.warning(f"  apt update failed: {e}")

    def _ensure_pacman_synced(self, dry_run: bool) -> None:
        if self.package_manager != PackageManager.PACMAN:
            return
        if self._pacman_synced:
            return
        if dry_run:
            logger.info("  [DRY RUN] Would sync pacman databases (once)")
            self._pacman_synced = True
            return
        logger.info("  Syncing pacman databases (once per bootstrap session)")
        try:
            self.privilege.run_privileged(["pacman", "-Sy"], check=False)
            self._pacman_synced = True
        except Exception as e:
            logger.warning(f"  pacman -Sy failed: {e}")

    def install_package(self, package: Package, dry_run: bool = False) -> PackageInstallResult:
        """Install a single package (legacy helper; prefer install_packages for batching)."""
        outcomes = self.install_packages([package.name], dry_run=dry_run)
        return outcomes.get(package.name) or PackageInstallResult(
            package.name, PackageInstallStatus.SKIPPED_UNKNOWN_PACKAGE, "not in registry"
        )

    def _install_via_package_manager(self, package: Package, pkg_name: str, dry_run: bool) -> bool:
        """Install package using system package manager."""
        try:
            if self.package_manager == PackageManager.APT:
                return self._install_apt([pkg_name], dry_run)
            if self.package_manager == PackageManager.PACMAN:
                return self._install_pacman([pkg_name], dry_run)
            if self.package_manager == PackageManager.DNF:
                return self._install_dnf([pkg_name], dry_run)
            if self.package_manager == PackageManager.BREW:
                return self._install_brew([pkg_name], dry_run)
            if self.package_manager == PackageManager.WINGET:
                return self._install_winget(pkg_name)
        except Exception as e:
            logger.warning(f"  Failed to install {pkg_name}: {e}")
            return False
        return False

    def _install_apt(self, pkg_names: list[str], dry_run: bool) -> bool:
        """Install one or more apt packages."""
        if not pkg_names:
            return True
        logger.info(f"  Installing via apt: {', '.join(pkg_names)}")
        self._ensure_apt_updated(dry_run)
        if dry_run:
            return True
        result = self.privilege.run_privileged(
            ["apt", "install", "-y", *pkg_names],
            check=False,
        )
        return result.returncode == 0

    def _install_pacman(self, pkg_names: list[str], dry_run: bool) -> bool:
        """Install one or more pacman packages."""
        if not pkg_names:
            return True
        logger.info(f"  Installing via pacman: {', '.join(pkg_names)}")
        self._ensure_pacman_synced(dry_run)
        if dry_run:
            return True
        result = self.privilege.run_privileged(
            ["pacman", "-S", "--needed", "--noconfirm", *pkg_names],
            check=False,
        )
        return result.returncode == 0

    def _install_dnf(self, pkg_names: list[str], dry_run: bool) -> bool:
        if not pkg_names:
            return True
        logger.info(f"  Installing via dnf: {', '.join(pkg_names)}")
        if dry_run:
            return True
        result = self.privilege.run_privileged(
            ["dnf", "install", "-y", *pkg_names],
            check=False,
        )
        return result.returncode == 0

    def _install_brew(self, pkg_names: list[str], dry_run: bool) -> bool:
        if not pkg_names:
            return True
        logger.info(f"  Installing via brew: {', '.join(pkg_names)}")
        if dry_run:
            return True
        result = subprocess.run(
            ["brew", "install", *pkg_names],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 and result.stderr:
            logger.debug(f"brew stderr: {result.stderr.strip()}")
        return result.returncode == 0

    def _install_winget(self, pkg_name: str) -> bool:
        logger.info(f"  Installing via winget: {pkg_name}")
        result = subprocess.run(
            ["winget", "install", "--id", pkg_name, "-e", "--silent"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def install_packages(self, package_names: list[str], dry_run: bool = False) -> dict[str, PackageInstallResult]:
        """Install multiple packages with batched package-manager calls where possible."""
        results: dict[str, PackageInstallResult] = {}

        resolved: list[tuple[str, Package, str]] = []
        for name in package_names:
            package = PACKAGES.get(name)
            if not package:
                logger.warning(f"Unknown package: {name}")
                results[name] = PackageInstallResult(
                    name, PackageInstallStatus.SKIPPED_UNKNOWN_PACKAGE, "not defined in registry"
                )
                continue
            pkg_name = package.get_package_name(self.package_manager)
            if not pkg_name:
                logger.warning(f"No {self.package_manager.value} mapping for {name}")
                results[name] = PackageInstallResult(
                    name, PackageInstallStatus.FAILED, f"unsupported on {self.package_manager.value}"
                )
                continue
            if self.is_installed(package):
                logger.info(f"  {name}: already installed ({', '.join(package.install_binary_candidates())})")
                results[name] = PackageInstallResult(
                    name, PackageInstallStatus.SKIPPED_INSTALLED, "binary already on PATH"
                )
                continue
            resolved.append((name, package, pkg_name))

        if not resolved:
            return results

        if dry_run:
            for name, package, pkg_name in resolved:
                logger.info(f"  [DRY RUN] Would install {name} ({pkg_name})")
                results[name] = PackageInstallResult(
                    name, PackageInstallStatus.SKIPPED_DRY_RUN, f"would install {pkg_name}"
                )
            return results

        # Batch installs per backend
        if self.package_manager == PackageManager.WINGET:
            for name, package, pkg_name in resolved:
                ok = self._install_via_package_manager(package, pkg_name, dry_run=False)
                status = PackageInstallStatus.INSTALLED if ok else PackageInstallStatus.FAILED
                results[name] = PackageInstallResult(
                    name, status, "winget install" if ok else "winget reported failure"
                )
            return results

        if self.package_manager == PackageManager.APT:
            names = [pkg_name for _, _, pkg_name in resolved]
            ok = self._install_apt(names, dry_run=False)
            for name, package, _ in resolved:
                now_installed = self.is_installed(package)
                if now_installed:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.INSTALLED, "apt")
                elif ok:
                    results[name] = PackageInstallResult(
                        name, PackageInstallStatus.FAILED, "apt succeeded but binary still missing"
                    )
                else:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.FAILED, "apt install failed")
            return results

        if self.package_manager == PackageManager.PACMAN:
            names = [pkg_name for _, _, pkg_name in resolved]
            ok = self._install_pacman(names, dry_run=False)
            for name, package, _ in resolved:
                now_installed = self.is_installed(package)
                if now_installed:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.INSTALLED, "pacman")
                elif ok:
                    results[name] = PackageInstallResult(
                        name, PackageInstallStatus.FAILED, "pacman succeeded but binary still missing"
                    )
                else:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.FAILED, "pacman install failed")
            return results

        if self.package_manager == PackageManager.DNF:
            names = [pkg_name for _, _, pkg_name in resolved]
            ok = self._install_dnf(names, dry_run=False)
            for name, package, _ in resolved:
                now_installed = self.is_installed(package)
                if now_installed:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.INSTALLED, "dnf")
                elif ok:
                    results[name] = PackageInstallResult(
                        name, PackageInstallStatus.FAILED, "dnf succeeded but binary still missing"
                    )
                else:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.FAILED, "dnf install failed")
            return results

        if self.package_manager == PackageManager.BREW:
            names = [pkg_name for _, _, pkg_name in resolved]
            ok = self._install_brew(names, dry_run=False)
            for name, package, _ in resolved:
                now_installed = self.is_installed(package)
                if now_installed:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.INSTALLED, "brew")
                elif ok:
                    results[name] = PackageInstallResult(
                        name, PackageInstallStatus.FAILED, "brew succeeded but binary still missing"
                    )
                else:
                    results[name] = PackageInstallResult(name, PackageInstallStatus.FAILED, "brew install failed")
            return results

        logger.error(f"Unsupported package manager: {self.package_manager}")
        for name, _, _ in resolved:
            results[name] = PackageInstallResult(
                name, PackageInstallStatus.FAILED, "no package manager backend"
            )
        return results
