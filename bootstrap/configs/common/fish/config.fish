# Interactive shell bootstrap config

if not status is-interactive
    exit
end

# No greeting
set fish_greeting

# Starship prompt
if type -q starship
    function starship_transient_prompt_func
        starship module character
    end

    if test "$TERM" != "linux"
        starship init fish | source

        if functions -q enable_transience
            enable_transience
        end
    end
end

# Core aliases
alias clear "printf '\033[2J\033[3J\033[1;1H'"
alias celar "printf '\033[2J\033[3J\033[1;1H'"
alias claer "printf '\033[2J\033[3J\033[1;1H'"

# OS/package-manager convenience aliases
if type -q pacman
    alias pamcan pacman
end

# Better ls
if type -q eza
    if test "$TERM" != "linux"
        alias ls 'eza --icons'
    else
        alias ls 'eza'
    end
end

# Better cat
if type -q bat
    alias cat 'bat --paging=never'
end

# Better cd
if type -q zoxide
    zoxide init fish | source
end

# Kitty-specific SSH integration
if test "$TERM" = "xterm-kitty"
    if type -q kitten
        alias ssh 'kitten ssh'
    end
end