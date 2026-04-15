"""Main installer - orchestrates all installation steps."""
from pathlib import Path

from bootstrap.detection import detect_system, auto_select_profile, should_install_kitty
from bootstrap.logging import get_logger, setup_logging
from bootstrap.models import Platform, ProfileType, SystemInfo
from bootstrap.packages.registry import PackageRegistry
from bootstrap.profiles.definitions import get_profile_packages
from bootstrap.configs.symlinker import Symlinker

logger = get_logger("bootstrap.core")


class BootstrapInstaller:
    """Main bootstrap installer orchestrator."""

    def __init__(self, system_info: SystemInfo, dry_run: bool = False):
        self.system_info = system_info
        self.dry_run = dry_run
        self.package_registry = PackageRegistry(system_info)
        self.symlinker = Symlinker()
        self.results = []

    def run(self, profile: ProfileType) -> bool:
        """Run the full bootstrap installation."""
        logger.info(f"Starting bootstrap installation")
        logger.info(f"  Platform: {self.system_info.platform.value}")
        logger.info(f"  Profile: {profile.value}")
        logger.info(f"  Dry run: {self.dry_run}")

        # Step 1: Install packages
        packages = get_profile_packages(profile)
        logger.info(f"Installing {len(packages)} packages...")
        
        self.package_registry.install_packages(packages, dry_run=self.dry_run)

        # Step 2: Deploy configs
        self._deploy_configs(profile)

        # Step 3: Setup shell
        self._setup_shell(profile)

        logger.info("Bootstrap installation complete!")
        return True

    def _deploy_configs(self, profile: ProfileType):
        """Deploy configuration files."""
        logger.info("Deploying configuration files...")
        # Config deployment will be implemented here

    def _setup_shell(self, profile: ProfileType):
        """Setup shell configuration."""
        logger.info("Setting up shell...")
        # Shell setup will be implemented here


def main(profile_name: str = None, dry_run: bool = False) -> int:
    """Main entry point for bootstrap."""
    # Setup logging
    setup_logging()

    # Detect system
    system_info = detect_system()
    
    # Auto-select profile if not specified
    if profile_name is None:
        profile_name = auto_select_profile(system_info)
    
    profile = ProfileType(profile_name)
    
    # Run installer
    installer = BootstrapInstaller(system_info, dry_run)
    success = installer.run(profile)
    
    return 0 if success else 1
