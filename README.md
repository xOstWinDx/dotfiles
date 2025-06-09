# 🛠️ My Dotfiles & System Bootstrap

This repository contains my personal dotfiles and a Python-based installer script for setting up a comfortable terminal environment on Linux (tested on Ubuntu and Arch-based systems).

## ✨ Features

- Installs and configures:
  - `zsh` + Oh My Zsh
  - Useful plugins: `zsh-autosuggestions`, `zsh-syntax-highlighting`, etc.
  - Aliases and shell enhancements
- Installs terminal utilities:
  - `bat` (with custom config)
  - `micro` (as simple syntax-highlighted editor)
  - `lsd` / `exa` (modern `ls`)
  - `fzf` and `zoxide` (fast file and directory navigation)
  - `btop` (modern system monitor)
  - `lazygit` and `lazydocker` (TUI interfaces for Git and Docker)
- Automatically links or installs configuration files from `configs/`
- Works with both `apt` and `pacman`

## 🚀 Installation

### 1. Clone this repository

```bash
git clone https://github.com/xostwindx/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

### 2. Run the installer

```bash
make install
```

You'll be prompted for your `sudo` password to install system packages.

> 💡 If something fails, check the output logs — some packages might require additional steps depending on your distro/version.

### 3. Re-login (important)

If Docker was installed and you added your user to the `docker` group, re-login or run:

```bash
newgrp docker
```

to apply the changes.

## 🖥 Terminal Experience

The setup enables:

- Prompt with Git status, `user@host`, and working directory
- Syntax-highlighted file previews using `bat`
- Fast fuzzy history and file search with `fzf`
- Quick `cd` with `zoxide`
- Git and Docker TUI tools via `lazygit` and `lazydocker`

## 🔧 Customization

You can edit:

- `configs/.zshrc` — for prompt, aliases, plugins
- `install.py` — to add packages or logic
- `Makefile` — to add other tasks

## 📦 Requirements

- Python 3.7+
- Internet connection
- POSIX-compatible terminal (Alacritty, Kitty, Konsole, etc.)
- `make`

## 📄 License
MIT License — feel free to fork, adapt, and improve.
