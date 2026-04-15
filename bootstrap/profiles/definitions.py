"""Profile definitions - packages and configs for each profile."""
from bootstrap.models import ProfileType

# Profile definitions
PROFILES = {
    ProfileType.MINIMAL: {
        "packages": ["git", "curl", "jq", "starship"],
        "description": "Minimal core tools (git, curl, jq, starship)"
    },
    ProfileType.SERVER: {
        "packages": ["git", "curl", "jq", "fish", "starship", "fzf", "zoxide", "micro", "ripgrep", "fastfetch"],
        "description": "Server-friendly stack (no GUI apps)"
    },
    ProfileType.DESKTOP: {
        "packages": ["git", "curl", "jq", "fish", "starship", "fzf", "zoxide", "micro", "ripgrep", "fastfetch", "btop", "bat", "fd", "eza", "lazygit"],
        "description": "Full desktop experience"
    },
    ProfileType.FULL: {
        "packages": ["git", "curl", "jq", "fish", "starship", "fzf", "zoxide", "micro", "ripgrep", "fastfetch", "btop", "bat", "fd", "eza", "lazygit", "lazydocker", "gh", "delta", "tmux", "direnv", "kitty"],
        "description": "Complete development environment"
    }
}

def get_profile_packages(profile_type: ProfileType) -> list[str]:
    """Get package list for a profile."""
    profile = PROFILES.get(profile_type, PROFILES[ProfileType.MINIMAL])
    return profile["packages"]

def get_profile_description(profile_type: ProfileType) -> str:
    """Get description for a profile."""
    profile = PROFILES.get(profile_type, {"description": "Unknown profile"})
    return profile["description"]
