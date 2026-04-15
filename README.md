# Bootstrap - Modern Dotfiles & System Installer

A cross-platform Python tool for bootstrapping development environments with support for Linux (Arch-based, Ubuntu, Debian, Fedora), macOS, and WSL.

**Production-ready v1** with real package management, config deployment, shell setup, and optional pyenv integration.

## Features

- **Auto-detection**: Automatically detects OS, distribution, SSH sessions, and GUI availability
- **Smart profiles**: `minimal`, `server`, `desktop`, `full` - or auto-selection based on environment
- **Package management**: Supports apt, pacman, dnf, brew (winget for core packages)
- **Safe deployment**: Backup existing configs, dry-run mode, idempotent operations
- **Modern stack**: fish, starship, kitty, eza, fzf, zoxide and more
- **Config manifest**: Platform and profile-aware config deployment via symlinks
- **Rich UI**: Beautiful output with Rich library, graceful fallback to plain CLI
- **Pyenv integration**: Optional Python version management
- **Cross-platform**: Works on Linux (including Arch-based), macOS, and WSL

## Quick Start

```bash
# Clone repository
git clone https://github.com/xOstWinDx/dotfiles.git ~/dotfiles
cd ~/dotfiles

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies (with Rich for pretty UI)
pip install click rich

# Check system info
python -m bootstrap doctor

# Install with auto-detected profile
python -m bootstrap install

# Or specify profile with dry-run preview
python -m bootstrap install --profile desktop --dry-run
```

## Installation Profiles

| Profile | Description | Packages |
|---------|-------------|----------|
| `minimal` | Core tools only | git, curl, jq, starship |
| `server` | Server-friendly stack | minimal + fish, fzf, zoxide, micro, ripgrep, fastfetch |
| `desktop` | Full desktop experience | server + btop, bat, fd, eza, lazygit |
| `full` | Complete development environment | desktop + lazydocker, gh, delta, tmux, direnv, kitty |

### Profile Auto-Selection Logic

- **SSH session detected** → `server` profile
- **No GUI available** → `server` profile  
- **Desktop with GUI** → `desktop` profile
- **WSL detected** → `desktop` profile (no Kitty by default)

## CLI Commands

```bash
# Install dotfiles and packages
bootstrap install               # Auto-detect profile
bootstrap install --profile desktop
bootstrap install --dry-run    # Preview without changes
bootstrap install --yes       # Non-interactive mode

# Pyenv setup (optional)
bootstrap install --pyenv      # Force pyenv installation
bootstrap install --no-pyenv   # Skip pyenv prompt

# Selective installation
bootstrap install --skip-packages  # Only deploy configs
bootstrap install --skip-configs   # Only install packages

# System info and planning
bootstrap doctor              # Check system dependencies
bootstrap plan               # Show what would be installed
bootstrap profile-ls          # List available profiles
bootstrap packages-ls         # List available packages
```

## Config Deployment

Bootstrap deploys configurations via symlinks from the repo to your home directory. The config manifest supports:

- **Platform filtering**: Linux, macOS, Windows
- **Profile filtering**: Only deploy configs relevant to selected profile
- **Conditional deployment**: GUI availability, Hyprland detection, etc.
- **Backup**: Existing files are backed up before replacement

### Deployable Configurations

#### Fish Shell (Linux/macOS)
- `~/.config/fish/config.fish` - Main config
- `~/.config/fish/conf.d/00-env.fish` - Environment variables
- `~/.config/fish/conf.d/10-interactive.fish` - Interactive settings
- `~/.config/fish/conf.d/20-aliases.fish` - Shell aliases
- `~/.config/fish/conf.d/40-fzf.fish` - FZF integration
- `~/.config/fish/conf.d/50-zoxide.fish` - Zoxide integration
- `~/.config/fish/conf.d/60-functions.fish` - Custom functions

#### Starship Prompt (Linux/macOS)
- `~/.config/starship.toml` - Cross-shell prompt configuration

#### Kitty Terminal (Desktop only, Linux/macOS)
- `~/.config/kitty/kitty.conf` - Terminal configuration
- `~/.config/kitty/theme.conf` - Color theme
- `~/.config/kitty/search.py` - Search kitten
- `~/.config/kitty/scroll_mark.py` - Scroll mark kitten

#### Micro Editor (Linux/macOS)
- `~/.config/micro/settings.json` - Editor settings
- `~/.config/micro/bindings.json` - Key bindings

#### Optional Hyprland Integration (Linux desktop)
- `~/.config/fish/conf.d/99-auto-hypr.fish` - Hyprland auto-configuration

## Shell Setup

### Unix-like Systems (Linux/macOS)

Bootstrap expects **fish shell** as the primary shell for server/desktop profiles:

1. Fish is installed via system package manager
2. Config files are deployed via symlinks
3. Starship prompt is configured
4. Shell change (`chsh`) is **NOT** performed automatically

To manually switch to fish:
```bash
# Check current shell
echo $SHELL

# Change to fish (requires logout/login)
chsh -s $(which fish)
```

### Windows Strategy

- **WSL**: Treated as Linux, full fish/kitty support
- **Native Windows**: Basic package installation via winget only. No fish/kitty/micro configs (future work)

## Pyenv Integration (Optional)

Pyenv is offered for `server`, `desktop`, and `full` profiles:

1. **Interactive mode**: User is prompted to install pyenv
2. **Non-interactive mode**: Requires `--pyenv` flag to install
3. **Minimal profile**: Pyenv is never offered automatically

When installed:
- Build prerequisites are installed automatically
- Latest recommended Python version is installed
- Option to set as global default
- Fish config is updated with pyenv initialization

## TUI / UX Strategy

Bootstrap uses **Rich** for beautiful output when available:

```
┌────────────────────────────────────────────────────────────┐
│  Bootstrap Installation                                    │
├────────────────────────────────────────────────────────────┤
│  UI Level: rich                                           │
│  Rich Available: True                                     │
│  Platform: linux                                          │
│  Package Manager: apt                                     │
└────────────────────────────────────────────────────────────┘
```

**Graceful degradation**:
- If Rich is installed → Rich-based UI with colors, tables, progress
- If Rich is not installed → Plain ANSI-colored CLI output
- If terminal is not interactive → Silent non-interactive mode

## Package Management

### Supported Package Managers

| Manager | Platforms | Install Method |
|---------|-----------|----------------|
| apt | Debian/Ubuntu | `sudo apt install` |
| pacman | Arch/Manjaro | `sudo pacman -S --needed` |
| dnf | Fedora/RHEL | `sudo dnf install` |
| brew | macOS | `brew install` |
| winget | Windows | `winget install` |

### Privilege Strategy

- **Sudo caching**: Privileges are cached for 5 minutes
- **Minimum privilege**: Only package installations require sudo
- **No root shell by default**: Commands run with specific privilege escalation

## Architecture

```
bootstrap/
├── cli.py                 # CLI interface (Click)
├── detection.py           # System detection (OS, SSH, GUI)
├── models.py              # Data models (Platform, ProfileType, etc.)
├── privilege.py          # Sudo/UAC management with caching
├── logging.py             # Structured logging with colors
├── ui.py                  # Rich UI layer with CLI fallback
├── core/
│   └── installer.py      # Main orchestrator
├── packages/
│   ├── definitions.py    # Package definitions with platform mappings
│   └── registry.py       # Installation logic
├── profiles/
│   └── definitions.py    # Profile definitions
├── configs/
│   ├── registry.py       # Config deployment manifest
│   └── symlinker.py      # Symlink-based deployment
└── shell/
    └── pyenv.py          # Pyenv installation manager
```

## Config Manifest Format

Configs are defined in `bootstrap/configs/registry.py`:

```python
ConfigManifest(
    source=r'common/fish/config.fish',
    target=r'.config/fish/config.fish',
    platforms=[Platform.LINUX, Platform.MACOS],
    profiles=[ProfileType.SERVER, ProfileType.DESKTOP, ProfileType.FULL],
    description='Fish main config',
)
```

## Dry Run Mode

Preview all changes without making them:

```bash
bootstrap install --dry-run
```

Output:
```
[DRY RUN] Would deploy: Fish main config
  Source: /home/user/dotfiles/configs/common/fish/config.fish
  Target: /home/user/.config/fish/config.fish
```

## Installation

### From Source

```bash
cd ~/dotfiles
pip install -e .
```

### With Rich UI Support

```bash
pip install -e ".[tui]"
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format bootstrap/
```

## License

MIT
