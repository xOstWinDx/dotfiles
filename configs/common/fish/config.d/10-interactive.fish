status is-interactive; or return

# Starship prompt + transient prompt
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

# Fastfetch only on local interactive desktop-like terminals
if not set -q SSH_TTY
    and not set -q SSH_CONNECTION
    and test "$TERM" != "linux"
    and type -q fastfetch
    and not set -q DOTFILES_FASTFETCH_SHOWN

    set -gx DOTFILES_FASTFETCH_SHOWN 1
    fastfetch
end