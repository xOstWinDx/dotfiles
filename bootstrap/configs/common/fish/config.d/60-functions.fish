status is-interactive; or return

function mkcd --description "Create directory and enter it"
    if test (count $argv) -lt 1
        echo "usage: mkcd <directory>"
        return 1
    end

    mkdir -p -- $argv[1]; and cd -- $argv[1]
end

function take --description "Alias for mkcd"
    mkcd $argv
end

function bak --description "Create timestamped backup copy of file"
    if test (count $argv) -lt 1
        echo "usage: bak <file>"
        return 1
    end

    set ts (date "+%Y%m%d_%H%M%S")
    cp -a -- $argv[1] "$argv[1].$ts.bak"
end