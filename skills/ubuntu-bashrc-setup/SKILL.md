---
name: "ubuntu-bashrc-profile"
description: "A high-performance, developer-centric bash profile for Ubuntu. Features include a smart directory navigator (cdd) with project detection (Node, Python, Rust, Go, Docker), automated daily system update checks, git branch integration, and optimized shell visuals. Designed to transform a standard terminal into a powerful productivity hub."
---

# Ubuntu Bashrc Profile Optimizer

This skill provides an advanced, production-ready `.bashrc` configuration tailored for Ubuntu users and developers. It moves beyond standard shell defaults to provide meaningful context, safety, and speed.

## Key Features

- **Smart Directory Navigation (`cdd`):** Automatically lists files, detects project types (Node.js, Python, Rust, etc.), and shows Git status upon entering a directory.
- **Automated Maintenance:** Checks for system updates once per day upon terminal launch.
- **Visual Enhancements:** Integrated `neofetch` (if available) for system overview and colorized `ls`, `grep`, and prompt.
- **Development Optimized:** Pre-configured paths and initializations for Miniconda and NVM.
- **Safe History:** Optimized history settings to prevent duplicate entries and ensure persistence.

## Usage

1. **Backup:** Always backup your existing `.bashrc` first: `cp ~/.bashrc ~/.bashrc.bak`.
2. **Implementation:** Copy the configuration below into your `~/.bashrc` file.
3. **Activation:** Reload your terminal or run `source ~/.bashrc`.
4. **Smart CD:** Use `cd` normally; it is aliased to the advanced `cdd` function.

## Configuration

```bash
# Section 1: Shell Behavior & Interaction
case $- in
    *i*) ;;
      *) return;;
esac

HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s checkwinsize

# Section 2: Environment
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# Section 3: Visuals & Prompt
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# Section 4: Ls & Grep Colors
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Section 5: Standard Aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Section 6: External Conguration & Completion
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# Section 7: Tool Initializations (Conda & NVM)
__conda_setup="$("$HOME/data/miniconda3/bin/conda" 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$HOME/data/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$HOME/data/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="$HOME/data/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"


# Section 9: Advanced Directory View
cdd() {
    builtin cd "$@" || return

    local COUNT=$(command ls -A | wc -l)
    if [[ ${COUNT} -gt 20 ]]; then
        command ls
    else
        command ls -lh
    fi

    local DIRS=$(command find . -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)
    local FILES=$((COUNT - DIRS))
    local LARGE=$(command find . -maxdepth 1 -type f -size +100M 2>/dev/null | wc -l)
    local SIZE_INFO=""
    [[ ${COUNT} -le 100 ]] && SIZE_INFO=", total size $(command du -sh . 2>/dev/null | builtin command cut -f1)"
    echo -e "\n[Stats] ${DIRS} dirs, ${FILES} files${SIZE_INFO}"

    if [[ ${COUNT} -gt 0 ]]; then
        echo -e "[Top Items]:"
        command du -sh ./* 2>/dev/null | sort -rh | head -n 3 | sed 's/^/   /'
    fi

    [[ ${LARGE} -gt 0 ]] && echo -e "   [Warning] ${LARGE} files over 100M"

    local PROJECT_TYPE=""
    [[ -f package.json ]] && PROJECT_TYPE="${PROJECT_TYPE}Node "
    [[ -f requirements.txt ]] || [[ -f setup.py ]] || [[ -f pyproject.toml ]] && PROJECT_TYPE="${PROJECT_TYPE}Python "
    [[ -f Cargo.toml ]] && PROJECT_TYPE="${PROJECT_TYPE}Rust "
    [[ -f go.mod ]] && PROJECT_TYPE="${PROJECT_TYPE}Go "
    [[ -f docker-compose.yml ]] || [[ -f Dockerfile ]] && PROJECT_TYPE="${PROJECT_TYPE}Docker "
    [[ -f .env ]] && PROJECT_TYPE="${PROJECT_TYPE}Env "
    [[ -n "${PROJECT_TYPE}" ]] && echo -e "[Project]: ${PROJECT_TYPE}"
    
    if command git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        local BRANCH=$(command git branch --show-current 2>/dev/null || echo "detached")
        echo -e "[Git Branch]: ${BRANCH}"
    fi
}

# Section 11: Daily System Update Check
LAST_UPDATE_FILE="$HOME/.cache/.last_apt_update"
TODAY=$(date +%Y-%m-%d)
if [[ ! -f "$LAST_UPDATE_FILE" ]] || [[ "$TODAY" != "$(cat "$LAST_UPDATE_FILE")" ]]; then
    echo -e "\n[System] First terminal run today. Checking for updates..."
    sudo apt update && sudo apt upgrade -y
    echo "$TODAY" > "$LAST_UPDATE_FILE"
fi

# Section 12: Final Activation
alias cd='cdd'
if [[ "$PWD" == "$HOME" ]]; then
    command neofetch --backend off --color_blocks off --disable packages wm wm_theme theme icons term_font de
fi
```