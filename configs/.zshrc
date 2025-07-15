# If you come from bash you might have to change your $PATH.
export PATH=$HOME/bin:/usr/local/bin:$PATH
export PATH=$HOME/.local/bin:$PATH
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
export PATH="/var/lib/snapd/snap/bin:$PATH"
export ZSH="$HOME/.oh-my-zsh"
export BAT_PAGER="less -FRX"

export OLLAMA_MODELS="/mnt/llm/.ollama/models"

if [[ -n "$SSH_CLIENT" ]] || [[ -n "$SSH_TTY" ]]; then
    ZSH_THEME="risto"
else
    ZSH_THEME="awesomepanda"
fi

export TERMINAL=alacritty


plugins=(
    git
    archlinux
    zsh-autosuggestions
    zsh-syntax-highlighting
    poetry
    colored-man-pages
    ssh-agent
    autojump
    dirhistory
    zsh-interactive-cd
)

source $ZSH/oh-my-zsh.sh

# Set-up FZF key bindings (CTRL R for fuzzy history finder)
source <(fzf --zsh)

HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt appendhistory

fastfetch

export EDITOR=micro
# фикс для окна
#export WAYLAND_DISPLAY=wayland-0


eval "$(pyenv init -)"
alias ls='lsd'
alias l='ls -l'
alias la='ls -a'
alias lla='ls -la'
alias lt='ls --tree'
alias dj="python ./manage.py"
compdef _python dj
alias cat=bat
alias nano=micro
alias bat='bat --style=plain'
alias ld="lazydocker"
alias lg="lazygit"
export GOOGLE_CLOUD_PROJECT=yellduck
