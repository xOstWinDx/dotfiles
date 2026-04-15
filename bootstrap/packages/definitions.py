"""Package definitions - all packages with platform-specific names."""
from bootstrap.models import Package, PackageCategory

# All available packages in the registry
PACKAGES: dict[str, Package] = {
    # Core packages (all profiles)
    "git": Package(
        name="git",
        category=PackageCategory.CORE,
        description="Version control system",
        required=True,
        apt="git",
        pacman="git",
        dnf="git",
        brew="git",
        winget="Git.Git"
    ),
    "curl": Package(
        name="curl",
        category=PackageCategory.CORE,
        description="Command-line HTTP client",
        required=True,
        apt="curl",
        pacman="curl",
        dnf="curl",
        brew="curl",
        winget="cURL.cURL"
    ),
    "jq": Package(
        name="jq",
        category=PackageCategory.CORE,
        description="JSON processor",
        required=True,
        apt="jq",
        pacman="jq",
        dnf="jq",
        brew="jq",
        winget="jq.jq"
    ),
    
    # Shell packages
    "fish": Package(
        name="fish",
        category=PackageCategory.SHELL,
        description="Friendly interactive shell",
        apt="fish",
        pacman="fish",
        dnf="fish",
        brew="fish",
        install_script="install_fish"
    ),
    "starship": Package(
        name="starship",
        category=PackageCategory.SHELL,
        description="Cross-shell prompt",
        apt="starship",
        pacman="starship",
        dnf="starship",
        brew="starship",
        install_url="https://starship.rs/install.sh"
    ),
    "zsh": Package(
        name="zsh",
        category=PackageCategory.SHELL,
        description="Z shell (alternative to fish)",
        apt="zsh",
        pacman="zsh",
        dnf="zsh",
        brew="zsh",
        winget="Zsh.Zsh"
    ),
    
    # Terminal packages (desktop only)
    "kitty": Package(
        name="kitty",
        category=PackageCategory.TERMINAL,
        description="Modern GPU terminal",
        apt="kitty",
        pacman="kitty",
        dnf="kitty",
        brew="kitty"
    ),
    
    # File tools
    "eza": Package(
        name="eza",
        category=PackageCategory.FILE_TOOLS,
        description="Modern ls replacement",
        apt="eza",
        pacman="eza",
        dnf="eza",
        brew="eza",
        install_url="https://github.com/eza-community/eza/releases"
    ),
    "bat": Package(
        name="bat",
        category=PackageCategory.FILE_TOOLS,
        description="Cat clone with syntax highlighting",
        apt="bat",
        pacman="bat",
        dnf="bat",
        brew="bat",
        winget="sharkdp.bat"
    ),
    "fd": Package(
        name="fd",
        category=PackageCategory.FILE_TOOLS,
        description="Fast find alternative",
        apt="fd-find",
        pacman="fd",
        dnf="fd-find",
        brew="fd",
        winget="sharkdp.fd"
    ),
    
    # Navigation
    "fzf": Package(
        name="fzf",
        category=PackageCategory.NAVIGATION,
        description="Fuzzy finder",
        apt="fzf",
        pacman="fzf",
        dnf="fzf",
        brew="fzf"
    ),
    "zoxide": Package(
        name="zoxide",
        category=PackageCategory.NAVIGATION,
        description="Smarter cd command",
        apt="zoxide",
        pacman="zoxide",
        dnf="zoxide",
        brew="zoxide",
        install_url="https://github.com/ajeetdsouza/zoxide/releases"
    ),
    
    # Search
    "ripgrep": Package(
        name="ripgrep",
        category=PackageCategory.SEARCH,
        description="Fast grep alternative",
        apt="ripgrep",
        pacman="ripgrep",
        dnf="ripgrep",
        brew="ripgrep",
        winget="BurntSushi.ripgrep.MSVC"
    ),
    
    # Monitoring
    "btop": Package(
        name="btop",
        category=PackageCategory.MONITORING,
        description="Modern system monitor",
        apt="btop",
        pacman="btop",
        dnf="btop",
        brew="btop"
    ),
    "fastfetch": Package(
        name="fastfetch",
        category=PackageCategory.MONITORING,
        description="Fast system info display",
        apt="fastfetch",
        pacman="fastfetch",
        dnf="fastfetch",
        brew="fastfetch"
    ),
    
    # Git tools
    "lazygit": Package(
        name="lazygit",
        category=PackageCategory.GIT_TOOLS,
        description="TUI for git",
        apt="lazygit",
        pacman="lazygit",
        dnf="lazygit",
        brew="lazygit",
        install_url="https://github.com/jesseduffield/lazygit/releases"
    ),
    "lazydocker": Package(
        name="lazydocker",
        category=PackageCategory.GIT_TOOLS,
        description="TUI for docker",
        install_url="https://github.com/jesseduffield/lazydocker/releases"
    ),
    "gh": Package(
        name="gh",
        category=PackageCategory.GIT_TOOLS,
        description="GitHub CLI",
        apt="gh",
        pacman="github-cli",
        dnf="gh",
        brew="gh"
    ),
    "delta": Package(
        name="delta",
        category=PackageCategory.GIT_TOOLS,
        description="Git pager with syntax highlighting",
        apt="delta",
        pacman="delta",
        dnf="delta",
        brew="delta",
        install_url="https://github.com/dandavison/delta/releases"
    ),
    
    # Dev tools
    "micro": Package(
        name="micro",
        category=PackageCategory.DEV_TOOLS,
        description="Modern terminal editor",
        apt="micro",
        pacman="micro",
        dnf="micro",
        brew="micro",
        install_url="https://github.com/zyedidia/micro/releases"
    ),
    "tmux": Package(
        name="tmux",
        category=PackageCategory.DEV_TOOLS,
        description="Terminal multiplexer",
        apt="tmux",
        pacman="tmux",
        dnf="tmux",
        brew="tmux"
    ),
    "direnv": Package(
        name="direnv",
        category=PackageCategory.DEV_TOOLS,
        description="Environment per directory",
        apt="direnv",
        pacman="direnv",
        dnf="direnv",
        brew="direnv"
    ),
    
    # Quality of life
    "exa": Package(
        name="exa",
        category=PackageCategory.QUALITY_OF_LIFE,
        description="Modern ls (legacy, use eza instead)",
        apt="exa",
        pacman="exa",
        brew="exa"
    ),
    "lsd": Package(
        name="lsd",
        category=PackageCategory.QUALITY_OF_LIFE,
        description="Modern ls (deprecated, use eza)",
        apt="lsd",
        pacman="lsd",
        brew="lsd"
    ),
}


def get_package(name: str) -> Package | None:
    """Get package by name."""
    return PACKAGES.get(name)


def get_packages_by_category(category: PackageCategory) -> list[Package]:
    """Get all packages in a category."""
    return [p for p in PACKAGES.values() if p.category == category]


def get_all_package_names() -> list[str]:
    """Get list of all package names."""
    return list(PACKAGES.keys())
