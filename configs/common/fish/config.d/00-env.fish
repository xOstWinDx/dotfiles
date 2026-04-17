# Core environment

# Homebrew / Linuxbrew — GUI apps (e.g. Kitty) often start with a minimal PATH without these,
# so starship and other brew tools must be discoverable before conf.d/10-interactive.fish.
if test -d /opt/homebrew/bin
    fish_add_path /opt/homebrew/bin
end
if test -d /usr/local/bin
    fish_add_path /usr/local/bin
end
if test -d $HOME/.linuxbrew/bin
    fish_add_path $HOME/.linuxbrew/bin
end
if test -d /home/linuxbrew/.linuxbrew/bin
    fish_add_path /home/linuxbrew/.linuxbrew/bin
end

# Explicit config path (dotfiles symlink ~/.config/starship.toml)
if test -f $HOME/.config/starship.toml
    set -gx STARSHIP_CONFIG $HOME/.config/starship.toml
end

if test -d $HOME/.local/bin
    if not contains -- $HOME/.local/bin $PATH
        set -gx PATH $HOME/.local/bin $PATH
    end
end

if test -d $HOME/bin
    if not contains -- $HOME/bin $PATH
        set -gx PATH $HOME/bin $PATH
    end
end

if test -d /var/lib/snapd/snap/bin
    if not contains -- /var/lib/snapd/snap/bin $PATH
        set -gx PATH /var/lib/snapd/snap/bin $PATH
    end
end

set -gx EDITOR micro
set -gx VISUAL $EDITOR
set -gx PAGER less
set -gx BAT_PAGER "less -FRX"