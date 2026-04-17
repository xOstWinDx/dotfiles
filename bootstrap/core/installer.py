"""Main installer - orchestrates all installation steps."""
from __future__ import annotations

from pathlib import Path

from bootstrap.detection import (
    auto_select_profile,
    detect_system,
    list_present_terminal_emulators,
    should_propose_kitty_install,
)
from bootstrap.logging import get_logger, setup_logging
from bootstrap.models import (
    DeploymentResult,
    PackageInstallResult,
    Platform,
    ProfileType,
    ShellType,
    SystemInfo,
)
from bootstrap.packages.registry import PackageRegistry
from bootstrap.profiles.definitions import get_profile_packages, get_profile_description
from bootstrap.shell.integration import setup_posix_shell_rc
from bootstrap.shell.pyenv import install_pyenv_for_profile
from bootstrap.ui import get_ui
from configs.symlinker import Symlinker, TargetDisposition
from configs.registry import (
    CONFIG_MANIFEST,
    filter_configs_for_system,
    get_source_path,
    get_target_path,
)

logger = get_logger("bootstrap.core")


def _filter_profile_packages(
    package_names: list[str],
    system_info: SystemInfo,
    *,
    interactive: bool,
    assume_yes: bool,
) -> tuple[list[str], list[str]]:
    """Return (packages_to_install, notes). May drop kitty based on environment / policy."""
    if "kitty" not in package_names:
        return package_names, []

    notes: list[str] = []
    filtered = list(package_names)

    if not should_propose_kitty_install(system_info):
        filtered = [p for p in filtered if p != "kitty"]
        notes.append("Kitty omitted (SSH, headless, WSL, or unsupported platform).")
        return filtered, notes

    present = list_present_terminal_emulators()
    others = [t for t in present if t != "kitty"]

    if shutil_which("kitty"):
        return filtered, notes

    if others:
        msg = (
            f"Detected terminal emulator(s) already installed: {', '.join(others)}. "
            "Install Kitty as an additional terminal?"
        )
        ui = get_ui()
        if interactive and not assume_yes:
            if not ui.prompt_yes_no(msg, default=False):
                filtered = [p for p in filtered if p != "kitty"]
                notes.append("Kitty skipped (user choice; other terminals present).")
        else:
            filtered = [p for p in filtered if p != "kitty"]
            notes.append(
                "Kitty skipped by safe default: other terminals detected "
                "(--yes / non-interactive avoids installing Kitty automatically)."
            )

    return filtered, notes


def shutil_which(name: str) -> bool:
    from shutil import which

    return which(name) is not None


class BootstrapInstaller:
    """Main bootstrap installer orchestrator."""

    def __init__(
        self,
        system_info: SystemInfo,
        *,
        dry_run: bool = False,
        interactive: bool = True,
        assume_yes: bool = False,
    ):
        self.system_info = system_info
        self.dry_run = dry_run
        self.interactive = interactive
        self.assume_yes = assume_yes
        self.package_registry = PackageRegistry(system_info)
        self.symlinker = Symlinker()
        self.results: list[DeploymentResult] = []
        self.package_results: dict[str, PackageInstallResult] = {}
        self.notes: list[str] = []

    def print_plan(self, profile: ProfileType, packages: list[str], ui) -> None:
        """Show a concise installation plan."""
        configs = filter_configs_for_system(
            CONFIG_MANIFEST,
            self.system_info.platform,
            profile,
            self.system_info,
        )
        ui.print_header("Installation plan")
        ui.print_info(f"Profile: {profile.value} — {get_profile_description(profile)}")
        ui.print_info(f"Platform: {self.system_info.platform.value}")
        ui.print_info(f"Package manager: {self.system_info.package_manager.value}")
        ui.print_info(f"SSH session: {self.system_info.is_ssh}")
        ui.print_info(f"GUI heuristics: {self.system_info.has_gui}")
        ui.print_info(f"Current shell: {self.system_info.shell.value if self.system_info.shell else 'unknown'}")
        ui.print_info(f"Packages ({len(packages)}): {', '.join(packages)}")
        ui.print_info(f"Config entries: {len(configs)}")
        ui.print_info("Shell integration: POSIX rc managed blocks (bash/zsh) + fish via config deploy")
        ui.print_info("Fish login shell: use chsh when profile includes fish (see --chsh-fish with --yes)")
        ui.print_info("Pyenv: server/desktop/full profiles (use --no-pyenv to skip; --pyenv to force)")

    def confirm_phases(self, ui) -> tuple[bool, bool, bool]:
        """
        Returns (do_packages, do_configs, do_shell) for interactive installs.

        Pyenv is handled separately by ``install_pyenv_for_profile`` (profile + flags).
        """
        if self.dry_run or not self.interactive or self.assume_yes:
            return True, True, True

        do_packages = ui.prompt_yes_no("Install / upgrade OS packages now?", default=True)
        do_configs = ui.prompt_yes_no("Deploy dotfile configs (symlinks, with backups on conflict)?", default=True)
        do_shell = ui.prompt_yes_no("Configure bash/zsh rc snippets for starship / zoxide / pyenv?", default=True)
        return do_packages, do_configs, do_shell

    def install_packages_phase(self, packages: list[str]) -> None:
        outcomes = self.package_registry.install_packages(packages, dry_run=self.dry_run)
        self.package_results = outcomes
        for name, res in outcomes.items():
            logger.info(f"Package {name}: {res.status.value} — {res.detail}")

    def deploy_configs_phase(self, profile: ProfileType, replace_conflicts: bool) -> list[DeploymentResult]:
        logger.info("Deploying configuration files...")
        configs_to_deploy = filter_configs_for_system(
            CONFIG_MANIFEST,
            self.system_info.platform,
            profile,
            self.system_info,
        )
        logger.info(f"  {len(configs_to_deploy)} config entries selected")

        results: list[DeploymentResult] = []
        ui = get_ui()

        for manifest_entry in configs_to_deploy:
            source = get_source_path(manifest_entry)
            target = get_target_path(manifest_entry, self.system_info.home_dir)

            if self.dry_run:
                disp = self.symlinker.classify_target(source, target)
                logger.info(f"  [DRY RUN] {manifest_entry.description}: {disp.value}")
                results.append(
                    DeploymentResult(
                        success=True,
                        action="preview",
                        target=target,
                        message=f"[DRY RUN] {manifest_entry.source} -> {target} ({disp.value})",
                    )
                )
                continue

            if not source.exists():
                if manifest_entry.optional:
                    logger.info(f"  [SKIP] Optional config missing: {source}")
                    continue
                logger.warning(f"  [SKIP] Source missing: {source}")
                results.append(
                    DeploymentResult(
                        success=False,
                        action="skip",
                        target=target,
                        message=f"Source not found: {source}",
                        error="Source not found",
                    )
                )
                continue

            disposition = self.symlinker.classify_target(source, target)
            if disposition in (TargetDisposition.CORRECT_SYMLINK, TargetDisposition.IDENTICAL_FILE):
                results.append(
                    DeploymentResult(
                        success=True,
                        action="skip",
                        target=target,
                        message=f"{manifest_entry.description}: nothing to do",
                    )
                )
                continue

            replace_this = replace_conflicts
            if disposition in (TargetDisposition.WRONG_SYMLINK, TargetDisposition.DIFFERENT_FILE):
                if not replace_conflicts:
                    results.append(
                        DeploymentResult(
                            success=True,
                            action="skip",
                            target=target,
                            message=f"{manifest_entry.description}: conflict; skipped by policy",
                        )
                    )
                    continue
                if self.interactive and not self.assume_yes:
                    msg = f"{target} exists and differs from the repo source. Replace (backup old)?"
                    if not ui.prompt_yes_no(msg, default=False):
                        results.append(
                            DeploymentResult(
                                success=True,
                                action="skip",
                                target=target,
                                message="User declined overwrite",
                            )
                        )
                        continue

            result = self.symlinker.deploy(
                source,
                target,
                dry_run=False,
                replace_conflicts=replace_this,
            )
            results.append(result)
            if result.success:
                logger.info(f"  [{result.action.upper()}] {manifest_entry.description}")
            else:
                logger.warning(f"  [FAIL] {result.message}")

        self.results.extend(results)
        return results

    def shell_integration_phase(self, profile: ProfileType) -> None:
        if self.system_info.platform not in (Platform.LINUX, Platform.MACOS):
            logger.info("Shell integration: skipped on this platform")
            return

        notes = setup_posix_shell_rc(
            self.system_info,
            enable_starship=True,
            enable_zoxide=profile != ProfileType.MINIMAL,
            enable_pyenv=profile in (ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL),
            dry_run=self.dry_run,
            backup=not self.dry_run,
        )
        for n in notes:
            logger.info(n)

    def print_summary(self, ui) -> None:
        ui.print_header("Summary")
        if self.package_results:
            counts: dict[str, int] = {}
            for res in self.package_results.values():
                key = res.status.value
                counts[key] = counts.get(key, 0) + 1
            ui.print_info("Packages: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

        dep_actions: dict[str, int] = {}
        for r in self.results:
            dep_actions[r.action] = dep_actions.get(r.action, 0) + 1
        if dep_actions:
            ui.print_info("Configs: " + ", ".join(f"{k}={v}" for k, v in sorted(dep_actions.items())))

        for n in self.notes:
            ui.print_warning(n)


def run_bootstrap_install(
    profile: ProfileType,
    *,
    dry_run: bool,
    interactive: bool,
    assume_yes: bool,
    skip_packages: bool,
    skip_configs: bool,
    no_pyenv: bool,
    force_pyenv: bool,
    chsh_fish: bool = False,
) -> int:
    """High-level flow used by the CLI."""
    ui = get_ui()
    system_info = detect_system()
    installer = BootstrapInstaller(
        system_info,
        dry_run=dry_run,
        interactive=interactive,
        assume_yes=assume_yes,
    )

    packages, filter_notes = _filter_profile_packages(
        get_profile_packages(profile),
        system_info,
        interactive=interactive,
        assume_yes=assume_yes,
    )
    installer.notes.extend(filter_notes)

    installer.print_plan(profile, packages, ui)

    do_packages, do_configs, do_shell = installer.confirm_phases(ui)
    if skip_packages:
        do_packages = False
    if skip_configs:
        do_configs = False

    replace_conflicts = True
    if installer.interactive and not installer.assume_yes and not dry_run:
        replace_conflicts = ui.prompt_yes_no(
            "When a config file differs from the repo, back up and replace it?",
            default=True,
        )

    if do_packages:
        installer.install_packages_phase(packages)
        if "starship" in packages:
            from bootstrap.shell.starship import ensure_starship_installed

            if not ensure_starship_installed(dry_run=dry_run):
                installer.notes.append(
                    "Starship CLI missing after package step; prompt may be plain until you install starship."
                )

    config_results: list[DeploymentResult] = []
    if do_configs:
        config_results = installer.deploy_configs_phase(profile, replace_conflicts=replace_conflicts)

    if do_shell:
        if interactive and not assume_yes and not dry_run:
            if not ui.prompt_yes_no("Apply shell rc integration now?", default=True):
                do_shell = False
        if do_shell:
            installer.shell_integration_phase(profile)

    if "fish" in packages and system_info.platform in (Platform.LINUX, Platform.MACOS):
        from bootstrap.shell.chsh import run_chsh_fish

        changed, chsh_msg = run_chsh_fish(
            system_info,
            dry_run=dry_run,
            interactive=interactive,
            assume_yes=assume_yes,
            chsh_fish_flag=chsh_fish,
        )
        if chsh_msg:
            if changed:
                ui.print_success(chsh_msg)
            elif dry_run:
                ui.print_dry_run(chsh_msg)
            elif "Skipping chsh" in chsh_msg or "declined" in chsh_msg or "left unchanged" in chsh_msg:
                ui.print_info(chsh_msg)
            else:
                ui.print_warning(chsh_msg)
        if not changed and shutil_which("fish") and system_info.shell != ShellType.FISH:
            from bootstrap.shell.integration import fish_default_shell_hint

            hint = fish_default_shell_hint()
            installer.notes.append(hint)

    if not no_pyenv:
        install_pyenv_for_profile(
            profile.value,
            dry_run=dry_run,
            interactive=interactive and not assume_yes,
            assume_yes=assume_yes,
            force=force_pyenv,
        )
    else:
        ui.print_info("Skipping pyenv (--no-pyenv)")

    installer.print_summary(ui)
    return 0


def main(profile_name: str | None = None, dry_run: bool = False) -> int:
    """Alternate entry point (non-CLI)."""
    setup_logging()
    system_info = detect_system()
    if profile_name is None:
        profile_name = auto_select_profile(system_info)
    profile = ProfileType(profile_name.lower())
    return run_bootstrap_install(
        profile,
        dry_run=dry_run,
        interactive=True,
        assume_yes=False,
        skip_packages=False,
        skip_configs=False,
        no_pyenv=False,
        force_pyenv=False,
        chsh_fish=False,
    )
