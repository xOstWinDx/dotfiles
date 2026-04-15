"""Main installer - orchestrates all installation steps."""
from pathlib import Path

from bootstrap.detection import detect_system, auto_select_profile, should_install_kitty
from bootstrap.logging import get_logger, setup_logging
from bootstrap.models import DeploymentResult, Platform, ProfileType, ShellType, SystemInfo
from bootstrap.packages.registry import PackageRegistry
from bootstrap.profiles.definitions import get_profile_packages
from bootstrap.configs.symlinker import Symlinker
from bootstrap.configs.registry import (
    CONFIG_MANIFEST,
    filter_configs_for_system,
    get_source_path,
    get_target_path,
)

logger = get_logger("bootstrap.core")


class BootstrapInstaller:
    """Main bootstrap installer orchestrator."""

    def __init__(self, system_info: SystemInfo, dry_run: bool = False, interactive: bool = True):
        self.system_info = system_info
        self.dry_run = dry_run
        self.interactive = interactive
        self.package_registry = PackageRegistry(system_info)
        self.symlinker = Symlinker()
        self.results: list[DeploymentResult] = []

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

    def _deploy_configs(self, profile: ProfileType) -> list[DeploymentResult]:
        """Deploy configuration files based on manifest."""
        logger.info("Deploying configuration files...")
        
        # Filter configs for current system
        configs_to_deploy = filter_configs_for_system(
            CONFIG_MANIFEST,
            self.system_info.platform,
            profile,
            self.system_info,
        )
        
        logger.info(f"  Found {len(configs_to_deploy)} configs to deploy")
        
        results = []
        for manifest_entry in configs_to_deploy:
            source = get_source_path(manifest_entry)
            target = get_target_path(manifest_entry, self.system_info.home_dir)
            
            if self.dry_run:
                logger.info(f"  [DRY RUN] Would deploy: {manifest_entry.description}")
                logger.info(f"    Source: {source}")
                logger.info(f"    Target: {target}")
                results.append(DeploymentResult(
                    success=True,
                    action="symlink",
                    target=target,
                    message=f"[DRY RUN] Would deploy {manifest_entry.source}",
                ))
                continue
            
            # Check if source exists
            if not source.exists():
                if manifest_entry.optional:
                    logger.info(f"  [SKIP] Optional config not found: {source}")
                    continue
                logger.warning(f"  [SKIP] Source not found: {source}")
                results.append(DeploymentResult(
                    success=False,
                    action="symlink",
                    target=target,
                    message=f"Source not found: {source}",
                    error="Source not found",
                ))
                continue
            
            # Deploy via symlinker
            result = self.symlinker.deploy(source, target, dry_run=self.dry_run)
            results.append(result)
            
            if result.success:
                logger.info(f"  [OK] Deployed: {manifest_entry.description}")
            else:
                logger.warning(f"  [FAIL] {result.message}")
        
        self.results.extend(results)
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"  Config deployment complete: {success_count}/{len(results)} successful")
        
        return results

    def _setup_shell(self, profile: ProfileType):
        """Setup shell configuration."""
        logger.info("Setting up shell...")
        
        # Only on Unix-like systems
        if self.system_info.platform not in (Platform.LINUX, Platform.MACOS):
            logger.info("  Shell setup only available on Linux/macOS")
            return
        
        # Check current shell
        current_shell = self.system_info.shell
        
        if current_shell == ShellType.FISH:
            logger.info(f"  Fish is already the current shell")
        else:
            logger.info(f"  Current shell: {current_shell}")
            logger.info("  Skipping shell change (would require manual 'chsh')")
        
        logger.info("  Shell setup complete")


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
