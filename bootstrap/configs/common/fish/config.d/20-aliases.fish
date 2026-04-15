status is-interactive; or return

# Clear screen helpers
alias clear "printf '\033[2J\033[3J\033[1;1H'"
alias celar "printf '\033[2J\033[3J\033[1;1H'"
alias claer "printf '\033[2J\033[3J\033[1;1H'"

# Package manager convenience
if type -q pacman
    alias pamcan pacman
end

# Better ls family
if type -q eza
    if test "$TERM" != "linux"
        alias ls 'eza --icons --group-directories-first'
        alias l 'eza -l --icons --group-directories-first'
        alias la 'eza -a --icons --group-directories-first'
        alias ll 'eza -la --icons --group-directories-first'
        alias lt 'eza --tree --level=2 --icons --group-directories-first'
    else
        alias ls 'eza --group-directories-first'
        alias l 'eza -l --group-directories-first'
        alias la 'eza -a --group-directories-first'
        alias ll 'eza -la --group-directories-first'
        alias lt 'eza --tree --level=2 --group-directories-first'
    end
end

# Better cat
if type -q bat
    alias cat 'bat --paging=never --style=plain'
end

# Editor shortcuts
if type -q micro
    alias nano micro
    alias m micro
end

# Git / Docker / CLI helpers
if type -q git
    alias g git
end

if type -q lazygit
    alias lg lazygit
end

if type -q lazydocker
    alias ld lazydocker
end

# Directory navigation helpers
alias .. 'cd ..'
alias ... 'cd ../..'
alias .... 'cd ../../..'

# Kitty-specific SSH integration
if test "$TERM" = "xterm-kitty"
    if type -q kitten
        alias ssh 'kitten ssh'
    end
end