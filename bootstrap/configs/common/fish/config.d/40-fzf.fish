status is-interactive; or return

if not type -q fzf
    return
end

# Load fish keybindings/completions if supported by installed fzf
fzf --fish 2>/dev/null | source

if type -q fd
    set -gx FZF_DEFAULT_COMMAND "fd --hidden --follow --exclude .git --strip-cwd-prefix"
    set -gx FZF_CTRL_T_COMMAND "$FZF_DEFAULT_COMMAND"
    set -gx FZF_ALT_C_COMMAND "fd --type d --hidden --follow --exclude .git --strip-cwd-prefix"
end

if type -q bat
    set -gx FZF_CTRL_T_OPTS "--preview 'bat --style=numbers --color=always --line-range :200 {}'"
end

if type -q eza
    set -gx FZF_ALT_C_OPTS "--preview 'eza --icons --all --tree --level=2 {} | head -200'"
else
    set -gx FZF_ALT_C_OPTS "--preview 'ls -la {} | head -200'"
end