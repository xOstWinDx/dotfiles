"""CLI interface using Click.""" 
import sys 
import click
from bootstrap. models import ProfileType 
from bootstrap.detection import detect_system, auto_select_profile 
from bootstrap.logging import setup_logging 
from bootstrap.core.installer import BootstrapInstaller
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
@click.option('-v', '--verbose', is_flag=True, help='Verbose output') 
@click.option('-q', '--quiet', is_flag=True, help='Quiet output') 
def install(profile, dry_run, verbose, quiet): 
    """Install the dotfiles and system packages.""" 
    setup_logging(verbose=verbose, quiet=quiet) 
     
    # Detect system 
    system_info = detect_system() 
    click.echo(f"Detected platform: {system_info.platform.value}") 
    click.echo(f"Package manager: {system_info.package_manager.value}") 
    click.echo(f"SSH session: {system_info.is_ssh}") 
    click.echo(f"GUI available: {system_info.has_gui}") 
     
    # Auto-select profile if not specified 
    if profile is None: 
        profile = auto_select_profile(system_info) 
        click.echo(f"Auto-selected profile: {profile}") 
    else: 
        click.echo(f"Using profile: {profile}") 
     
    if dry_run: 
        click.echo("[DRY RUN] No changes will be made") 
     
    # Run installer 
    installer = BootstrapInstaller(system_info, dry_run=dry_run) 
    profile_type = ProfileType[profile.upper()] 
    success = installer.run(profile_type) 
     
    if success: 
        click.echo(click.style("Installation complete!", fg='green')) 
        sys.exit(0) 
    else: 
        click.echo(click.style("Installation failed!", fg='red'), err=True) 
        sys.exit(1)

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
     
    packages = get_profile_profile_packages(profile_type) 
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
