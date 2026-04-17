status is-interactive; or return

# Homebrew and git-style installs both put ``pyenv`` on PATH; ``pyenv init`` sets PYENV_ROOT.
if type -q pyenv
    pyenv init - fish | source
end
