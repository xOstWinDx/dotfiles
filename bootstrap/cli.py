"""CLI interface using Click."""

import sys
import click
from bootstrap.models import ProfileType
from bootstrap.detection import detect_system, auto_select_profile
from bootstrap.logging import setup_logging
from bootstrap.core.installer import BootstrapInstaller
from bootstrap.shell.pyenv import install_pyenv_for_profile
from bootstrap.ui import get_ui, is_rich_available, detect_ui_capabilities
from bootstrap import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """Bootstrap - Modern Dotfiles & System Installer"""
    pass


@cli.command()
@click.option('--profile', type=click.Choice(['minimal', 'server', 'desktop', 'full']),
              help='Installation profile')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
@click.option('--yes', '-y', is_flag=True, help='Non-interactive mode, assume yes to prompts')
@click.option('--pyenv', is_flag=True, help='Force pyenv installation (implies python setup)')
@click.option('--no-pyenv', is_flag=True, help='Skip pyenv installation prompt')
@click.option('--skip-packages', is_flag=True, help='Skip package installation')
@click.option('--skip-configs', is_flag=True, help='Skip config deployment')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-q', '--quiet', is_flag=True, help='Quiet output')
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
    
    # Detect UI capabilities
    capabilities = detect_ui_capabilities()
    interactive = yes or (sys.stdout.isatty() and not quiet)
    
    # Banner
    ui.print_header("Bootstrap Installation")
    ui.print_info(f"UI Level: {capabilities['ui_level']}")
    ui.print_info(f"Rich Available: {capabilities['rich_available']}")
    
    # Detect system
    system_info = detect_system()
    ui.print_info(f"Platform: {system_info.platform.value}")
    ui.print_info(f"Package Manager: {system_info.package_manager.value}")
    ui.print_info(f"SSH Session: {system_info.is_ssh}")
    ui.print_info(f"GUI Available: {system_info.has_gui}")
    
    # Auto-select profile if not specified
    if profile is None:
        profile = auto_select_profile(system_info)
        ui.print_info(f"Auto-selected profile: {profile}")
    else:
        ui.print_info(f"Using profile: {profile}")
    
    profile_type = ProfileType[profile.upper()]
    
    if dry_run:
        ui.print_dry_run("[DRY RUN] No changes will be made")
    
    # Run installer
    installer = BootstrapInstaller(system_info, dry_run=dry_run, interactive=interactive)
    
    # Step 1: Install packages
    if not skip_packages:
        from bootstrap.profiles.definitions import get_profile_packages
        packages = get_profile_packages(profile_type)
        ui.print_info(f"Installing {len(packages)} packages...")
        installer.package_registry.install_packages(packages, dry_run=dry_run)
    else:
        ui.print_info("Skipping package installation")
    
    # Step 2: Deploy configs
    if not skip_configs:
        installer._deploy_configs(profile_type)
    else:
        ui.print_info("Skipping config deployment")
    
    # Step 3: Setup shell
    installer._setup_shell(profile_type)
    
    # Step 4: Pyenv setup (if requested)
    if no_pyenv:
        ui.print_info("Skipping pyenv setup")
    elif pyenv or (interactive and profile in ('server', 'desktop', 'full')):
        ui.print_info("Setting up pyenv...")
        install_pyenv_for_profile(
            profile,
            dry_run=dry_run,
            interactive=interactive,
            force=pyenv,
        )
    
    ui.print_success("Installation complete!")
    
    if dry_run:
        ui.print_warning("This was a dry run. No changes were made.")
    
    sys.exit(0)

@cli.command() 
@click.option('-v', '--verbose', is_flag=True, help='Verbose output') 
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
    click.echo(f"  Current shell: {system_info.shell}") 

@cli.command() 
@click.option('--profile', type=click.Choice(['minimal', 'server', 'desktop', 'full']), 
              help='Profile to show plan for') 
def plan(profile): 
    """Show the installation plan without applying.""" 
    from bootstrap.profiles.definitions import get_profile_packages, get_profile_description 
    from bootstrap.detection import detect_system 
     
    system_info = detect_system() 
    if profile is None: 
        profile = auto_select_profile(system_info) 
    profile_type = ProfileType[profile.upper()] 
     
    packages = get_profile_packages(profile_type)
    description = get_profile_description(profile_type) 
     
    click.echo(f"Profile: {profile}") 
    click.echo(f"Description: {description}") 
    click.echo(f"Packages ({len(packages)}):") 
    for pkg in packages: 
        click.echo(f"  - {pkg}")

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

if __name__ == '__main__': 
    main() 
