"""Config deployment registry - maps source files to target paths."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from bootstrap.models import ConfigManifest, DeploymentStrategy, Platform, ProfileType

if TYPE_CHECKING:
    from bootstrap.models import SystemInfo

# Base directory for configs in the repository
CONFIGS_DIR = Path(__file__).parent.parent.parent / Path(r'configs')

# All config deployments
CONFIG_MANIFEST: list[ConfigManifest] = [
    # ============================================================================
    # FISH SHELL CONFIGURATION (Unix-like systems only)
    # ============================================================================
    ConfigManifest(
        source=r'common/fish/config.fish',
        target=r'.config/fish/config.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish main config',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/00-env.fish',
        target=r'.config/fish/conf.d/00-env.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish environment variables',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/10-interactive.fish',
        target=r'.config/fish/conf.d/10-interactive.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish interactive settings',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/20-aliases.fish',
        target=r'.config/fish/conf.d/20-aliases.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish aliases',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/30-python.fish',
        target=r'.config/fish/conf.d/30-python.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish Python/pyenv integration (conditional)',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/40-fzf.fish',
        target=r'.config/fish/conf.d/40-fzf.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish fzf integration',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/50-zoxide.fish',
        target=r'.config/fish/conf.d/50-zoxide.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish zoxide integration',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/60-functions.fish',
        target=r'.config/fish/conf.d/60-functions.fish',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Fish custom functions',
    ),
    ConfigManifest(
        source=r'common/fish/config.d/90-local.fish.example',
        target=r'.config/fish/conf.d/90-local.fish.example',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        optional=True,
        description='Fish local overrides template',
    ),

    # ============================================================================
    # STARSHIP PROMPT (All Unix-like platforms)
    # ============================================================================
    ConfigManifest(
        source=r'common/starship/starship.toml',
        target=r'.config/starship.toml',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.MINIMAL, ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Starship prompt configuration',
    ),

    # ============================================================================
    # KITTY TERMINAL (Desktop only, Unix-like systems)
    # ============================================================================
    ConfigManifest(
        source=r'common/kitty/kitty.conf',
        target=r'.config/kitty/kitty.conf',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.DESKTOP, ProfileType.FULL],
        condition='has_gui',
        description='Kitty terminal configuration',
    ),
    ConfigManifest(
        source=r'common/kitty/theme.conf',
        target=r'.config/kitty/theme.conf',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.DESKTOP, ProfileType.FULL],
        condition='has_gui',
        description='Kitty color theme',
    ),
    ConfigManifest(
        source=r'common/kitty/search.py',
        target=r'.config/kitty/search.py',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.DESKTOP, ProfileType.FULL],
        condition='has_gui',
        description='Kitty search kitten',
    ),
    ConfigManifest(
        source=r'common/kitty/scroll_mark.py',
        target=r'.config/kitty/scroll_mark.py',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.DESKTOP, ProfileType.FULL],
        condition='has_gui',
        description='Kitty scroll mark kitten',
    ),

    # ============================================================================
    # MICRO EDITOR (All platforms)
    # ============================================================================
    ConfigManifest(
        source=r'common/micro/settings.json',
        target=r'.config/micro/settings.json',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Micro editor settings',
    ),
    ConfigManifest(
        source=r'common/micro/bindings.json',
        target=r'.config/micro/bindings.json',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        description='Micro editor key bindings',
    ),
    ConfigManifest(
        source=r'common/micro/colorschemes/catppuccin-macchiato.micro',
        target=r'.config/micro/colorschemes/catppuccin-macchiato.micro',
        platforms=[Platform.LINUX, Platform.MACOS],
        profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
        optional=True,
        description='Micro editor colorscheme (Catppuccin Macchiato)',
    ),

    # ============================================================================
    # OPTIONAL: HYPRLAND INTEGRATION (Linux desktop only, Hyprland specific)
    # ============================================================================
    ConfigManifest(
        source=r'optional/hyprland/fish/conf.d/99-auto-hypr.fish',
        target=r'.config/fish/conf.d/99-auto-hypr.fish',
        platforms=[Platform.LINUX],
        profiles=[ProfileType.DESKTOP, ProfileType.FULL],
        condition='is_hyprland',
        optional=True,
        description='Hyprland auto-configuration for fish',
    ),

    # ============================================================================
    # WINDOWS CONFIGURATIONS
    # ============================================================================
    # Windows uses PowerShell, not fish. These configs are for Windows-native path.
]

# Add path import for CONFIGS_DIR
from pathlib import Path

def get_configs_dir() -> Path:
    return Path(__file__).parent.parent.parent / 'configs'

def get_source_path(manifest_entry: ConfigManifest) -> Path:
    return get_configs_dir() / manifest_entry.source

def get_target_path(manifest_entry: ConfigManifest, home_dir: Path) -> Path:
    return home_dir / manifest_entry.target

def filter_configs_for_system(
    manifest: list[ConfigManifest],
    platform: Platform,
    profile: ProfileType,
    system_info: 'SystemInfo',
) -> list[ConfigManifest]:
    filtered = []
    for entry in manifest:
        # Platform filter
        if entry.platforms and platform not in entry.platforms:
            continue
        
        # Profile filter
        if entry.profiles and profile not in entry.profiles:
            continue
        
        # Condition check (if specified)
        if entry.condition:
            if not _evaluate_condition(entry.condition, system_info):
                continue
        
        filtered.append(entry)
    
    return filtered

def _evaluate_condition(condition: str, system_info: 'SystemInfo') -> bool:
    condition_map = {
        'has_gui': lambda: system_info.has_gui,
        'is_ssh': lambda: system_info.is_ssh,
        'is_hyprland': lambda: bool(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')) or 
                              system_info.terminal_emulator == 'hyprland' or
                              (system_info.has_gui and os.environ.get('XDG_CURRENT_DESKTOP', '').lower().startswith('hypr')),
    }
    
    if condition in condition_map:
        return condition_map[condition]()
    
    return True