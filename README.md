# Bootstrap - Modern Dotfiles & System Installer

A cross-platform Python tool for bootstrapping development environments with support for Linux (Arch, Ubuntu), macOS, and Windows.

## Features

- **Auto-detection**: Automatically detects OS, distribution, SSH sessions, and GUI availability
- **Smart profiles**: minimal, server, desktop, full - or auto-selection based on environment
- **Package management**: Supports apt, pacman, dnf, brew, winget
- **Safe deployment**: Backup existing configs, dry-run mode, idempotent operations
- **Modern stack**: fish, starship, kitty, eza, fzf, zoxide and more

## Quick Start

```bash
# Clone repository
git clone https://github.com/xOstWinDx/dotfiles.git ~/dotfiles
cd ~/dotfiles

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install click

# Check system info
python -m bootstrap doctor

# Install with auto-detected profile
python -m bootstrap install

# Or specify profile
python -m bootstrap install --profile desktop --dry-run
```

## Profiles

| Profile | Description |
|---------|-------------|
| minimal | Core tools: git, curl, jq, starship |
| server | Server stack: +fish, fzf, zoxide, micro, ripgrep, fastfetch |
| desktop | Desktop stack: +btop, bat, fd, eza, lazygit |
| full | Complete stack: +lazydocker, gh, delta, tmux, direnv, kitty |

## CLI Commands

```bash
bootstrap doctor        # Check system and dependencies
bootstrap install       # Install dotfiles and packages
bootstrap plan         # Show installation plan
bootstrap profile-ls   # List available profiles
bootstrap packages-ls  # List available packages
```

## Architecture

```
bootstrap/
├── cli.py              # CLI interface (Click)
├── detection.py        # System detection
├── models.py           # Data models
├── privilege.py        # Sudo/UAC management
├── logging.py          # Logging setup
├── packages/
│   ├── definitions.py  # Package definitions
│   └── registry.py     # Installation logic
├── profiles/
│   └── definitions.py  # Profile definitions
├── configs/
│   └── symlinker.py   # Config deployment
└── core/
    └── installer.py   # Main orchestrator
```

## Packages

Core packages (all profiles):
- git, curl, jq

Shell packages:
- fish, starship

Desktop packages:
- kitty, eza, bat, fd, btop, fastfetch

Developer packages:
- fzf, zoxide, micro, ripgrep, lazygit, lazydocker, gh, delta, tmux, direnv

## License

MIT
