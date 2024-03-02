#
# RiB Bashrc Configuration for Linux
#
# Note, functionality is meant for some simplification and automation. This
# Is not the main supported functionality and may change/break on release. Please
# Use the `rib command command` format for supported and stable RiB functionality
#

###
# Environmental Variables
###

# N/A

###
# Set Up Command Line/Prompt
###

export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

if [[ -z $RIB_MODE && -z $DEPLOYMENT_NAME ]]; then
    export PS1="\[\e[33m\]$BASHPID\[\e[m\]) \[\e[32m\]rib\[\e[m\]\[\e[32m\]:\[\e[m\]\[\e[32m\]$RIB_VERSION\[\e[m\]@\[\e[33m\]\W\[\e[m\]\\$ "
else
    export PS1="\[\e[33m\]$BASHPID\[\e[m\]) \[\e[32m\]rib\[\e[m\]\[\e[32m\]:\[\e[m\]\[\e[32m\]$RIB_VERSION\[\e[36m\]:$RIB_MODE:$DEPLOYMENT_NAME\[\e[m\]@\[\e[33m\]\W\[\e[m\]\\$ "
fi

###
# Aliases
###


alias aws="rib aws"
alias bashrc="vi ~/.bashrc"
alias config="rib config"
alias deployment="rib deployment"
alias editbash="vi ~/.bashrc"
alias help="rib --help"
alias init="rib config init"
alias ll="ls -lah"
alias loadbash="source ~/.bashrc"
alias reinit="rib config init"
alias system="rib system"
alias version="rib --version"


###
# RiB Shorthand Functions (Unsupported and May Change At Any Time)
###

# Deployments

function dcreate() {
    rib deployment create --name="$1" ${@:2}
}
function dinfo() {
    rib deployment info --name="$1" ${@:2}
}
function dlist() {
    rib deployment list $@
}
function dremove() {
    rib deployment remove --name="$1" ${@:2}
}
function drename() {
    rib deployment rename --old="$1" --new="$2" ${@:3}
}
function dstart() {
    rib deployment start --name="$1" ${@:2}
}
function dstatus() {
    rib deployment status --name="$1" ${@:2}
}
function dstop() {
    rib deployment stop --name="$1" ${@:2}
}

export -f dcreate
export -f dinfo
export -f dlist
export -f dremove
export -f dstart
export -f dstatus
export -f dstop


###
# RiB Autocomplete
###


_rib_completion() {
    local IFS=$'\t'
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _RIB_COMPLETE=complete-bash $1 ) )
    return 0
}

complete -F _rib_completion -o default rib

###
# Custom aliases
###

if [ -f ~/.race/rib/user-state/.bash_aliases ]; then
    . ~/.race/rib/user-state/.bash_aliases
fi

###
# Session messages/banners
###

if tty -s; then
    echo "RiB logs will be written to /root/.race/rib/logs/$RIB_START_TIME-$BASHPID.log"
fi
