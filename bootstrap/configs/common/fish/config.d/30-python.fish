status is-interactive; or return

if type -q pyenv
    set -gx PYENV_ROOT $HOME/.pyenv

    if test -d $PYENV_ROOT/bin
        if not contains -- $PYENV_ROOT/bin $PATH
            set -gx PATH $PYENV_ROOT/bin $PATH
        end
    end

    pyenv init - fish | source
end