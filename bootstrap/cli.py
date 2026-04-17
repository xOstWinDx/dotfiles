"""CLI interface using Click."""

import sys
import click

from bootstrap.models import ProfileType
from bootstrap.detection import detect_system, auto_select_profile
from bootstrap.logging import setup_logging
from bootstrap.core.installer import run_bootstrap_install
from bootstrap.ui import get_ui, detect_ui_capabilities
from bootstrap import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """Bootstrap - Modern Dotfiles & System Installer"""
    pass


@cli.command()
@click.option(
    "--profile",
    type=click.Choice(["minimal", "server", "desktop", "full"]),
    help="Installation profile",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
@click.option("--yes", "-y", is_flag=True, help="Non-interactive mode: no prompts; safe defaults")
@click.option("--pyenv", is_flag=True, help="Force pyenv installation (implies Python setup)")
@click.option("--no-pyenv", is_flag=True, help="Skip pyenv installation")
@click.option("--skip-packages", is_flag=True, help="Skip package installation")
@click.option("--skip-configs", is_flag=True, help="Skip config deployment")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Quiet output")
def install(profile, dry_run, yes, pyenv, no_pyenv, skip_packages, skip_configs, verbose, quiet):
    """Install the dotfiles and system packages.

    Examples:

      bootstrap install                  # Auto-detect and install

      bootstrap install --profile desktop

      bootstrap install --dry-run        # Preview without changes

      bootstrap install --yes            # Non-interactive

      bootstrap install --pyenv          # Include pyenv setup
    """
    setup_logging(verbose=verbose, quiet=quiet)
    ui = get_ui()

    # --yes => non-interactive (no prompts). TTY alone does NOT imply consent.
    interactive = (not yes) and sys.stdout.isatty() and (not quiet)
    assume_yes = bool(yes)

    capabilities = detect_ui_capabilities()

    ui.print_header("Bootstrap Installation")
    ui.print_info(f"UI Level: {capabilities['ui_level']}")
    ui.print_info(f"Rich Available: {capabilities['rich_available']}")
    ui.print_info(f"Interactive prompts: {interactive}")

    system_info = detect_system()
    ui.print_info(f"Platform: {system_info.platform.value}")
    ui.print_info(f"Package Manager: {system_info.package_manager.value}")
    ui.print_info(f"SSH Session: {system_info.is_ssh}")
    ui.print_info(f"GUI Available: {system_info.has_gui}")

    if profile is None:
        profile = auto_select_profile(system_info)
        ui.print_info(f"Auto-selected profile: {profile}")
    else:
        ui.print_info(f"Using profile: {profile}")

    profile_type = ProfileType[profile.upper()]

    if dry_run:
        ui.print_dry_run("[DRY RUN] No changes will be made")

    code = run_bootstrap_install(
        profile_type,
        dry_run=dry_run,
        interactive=interactive,
        assume_yes=assume_yes,
        skip_packages=skip_packages,
        skip_configs=skip_configs,
        no_pyenv=no_pyenv,
        force_pyenv=pyenv,
    )

    ui.print_success("Bootstrap run finished.")
    if dry_run:
        ui.print_warning("This was a dry run. No changes were made.")

    sys.exit(code)


@cli.command()
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def doctor(verbose):
    """Check system and dependencies."""
    setup_logging(verbose=verbose)
    system_info = detect_system()

    click.echo("System Information:")
    click.echo(f"  Platform: {system_info.platform.value}")
    click.echo(f"  Distribution: {system_info.distro.value}")
    click.echo(f"  Package manager: {system_info.package_manager.value}")
    click.echo(f"  SSH session: {system_info.is_ssh}")
    click.echo(f"  GUI available: {system_info.has_gui}")
    click.echo(f"  Username: {system_info.username}")
    click.echo(f"  Hostname: {system_info.hostname}")
    click.echo(f"  Current shell: {system_info.shell.value if system_info.shell else 'unknown'}")


@cli.command()
@click.option(
    "--profile",
    type=click.Choice(["minimal", "server", "desktop", "full"]),
    help="Profile to show plan for",
)
def plan(profile):
    """Show the installation plan without applying."""
    from bootstrap.profiles.definitions import get_profile_packages, get_profile_description
    from bootstrap.detection import detect_system, list_present_terminal_emulators
    from configs.registry import filter_configs_for_system, CONFIG_MANIFEST

    system_info = detect_system()
    if profile is None:
        profile = auto_select_profile(system_info)
    profile_type = ProfileType[profile.upper()]

    packages = get_profile_packages(profile_type)
    description = get_profile_description(profile_type)
    configs = filter_configs_for_system(
        CONFIG_MANIFEST,
        system_info.platform,
        profile_type,
        system_info,
    )

    click.echo(f"Profile: {profile}")
    click.echo(f"Description: {description}")
    click.echo(f"SSH: {system_info.is_ssh}  GUI: {system_info.has_gui}")
    click.echo(f"Terminals on PATH: {', '.join(list_present_terminal_emulators()) or '(none detected)'}")
    click.echo(f"Packages ({len(packages)}):")
    for pkg in packages:
        click.echo(f"  - {pkg}")
    click.echo(f"Config manifest entries for this system/profile: {len(configs)}")


@cli.command()
def profile_ls():
    """List available profiles."""
    from bootstrap.profiles.definitions import get_profile_description

    for ptype in ProfileType:
        desc = get_profile_description(ptype)
        click.echo(f"  {ptype.value:10} - {desc}")


@cli.command()
def packages_ls():
    """List available packages."""
    from bootstrap.packages.definitions import get_all_package_names

    names = get_all_package_names()
    click.echo(f"Available packages ({len(names)}):")
    for name in names:
        click.echo(f"  - {name}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
