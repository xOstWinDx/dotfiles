# Core environment

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