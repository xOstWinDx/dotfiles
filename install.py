#!/usr/bin/env python3
import getpass
import shutil
import subprocess
import sys
from pathlib import Path

DOTFILES_DIR = Path(__file__).parent.resolve()
CONFIGS_DIR = DOTFILES_DIR / 'configs'
HOME = Path.home()

ZSH_CUSTOM = HOME / ".oh-my-zsh/custom"

sudo_pass = getpass.getpass()


def detect_package_manager():
    if shutil.which('apt'):
        return 'apt'
    elif shutil.which('pacman'):
        return 'pacman'
    else:
        print("Unsupported Linux distribution.")
        sys.exit(1)


def install_packages(manager):
    packages = ['zsh', 'curl', 'bat', 'micro', 'lsd', 'fzf', 'fastfetch', 'btop']

    if manager == 'apt':
        packages += ['fonts-powerline']

        print("Adding Fastfetch PPA repository...")
        subprocess.run(
            ['sudo', '-S', 'add-apt-repository', '-y', 'ppa:zhangsongcui3371/fastfetch'],
            input=(sudo_pass + '\n').encode(),
            check=True
        )

        cmds = [
            ['sudo', '-S', 'apt', 'update'],
            ['sudo', '-S', 'apt', 'install', '-y'] + packages
        ]

    elif manager == 'pacman':
        packages = ['powerline-fonts', 'lazygit']
        cmds = [
            ['sudo', '-S', 'pacman', '-Sy', '--needed', '--noconfirm'] + packages
        ]

    else:
        return

    for cmd in cmds:
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, input=(sudo_pass + '\n').encode(), check=True)


def install_oh_my_zsh():
    omz_dir = HOME / '.oh-my-zsh'
    if omz_dir.exists():
        print("Oh My Zsh уже установлен.")
        return

    print("Скачиваем скрипт установки Oh My Zsh...")

    import tempfile
    import urllib.request

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        url = "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"
        with urllib.request.urlopen(url) as response:
            script_data = response.read()
            temp_file.write(script_data)
            script_path = temp_file.name

    print(f"Запускаем скрипт: {script_path}")
    subprocess.run(['sh', script_path], check=True)


def install_zsh_plugins():
    plugins = {
        "zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions.git",
        "zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting.git"
    }

    for name, repo in plugins.items():
        plugin_path = ZSH_CUSTOM / "plugins" / name
        if plugin_path.exists():
            print(f"Plugin {name} уже установлен.")
            continue
        subprocess.run(["git", "clone", repo, str(plugin_path)], check=True)


def symlink(src: Path, dest: Path):
    if dest.exists() or dest.is_symlink():
        backup = dest.with_suffix('.bak')
        print(f"Backing up existing {dest} to {backup}")
        dest.rename(backup)
    print(f"Creating symlink: {dest} -> {src}")
    dest.symlink_to(src)


def setup_symlinks():
    symlink(CONFIGS_DIR / '.zshrc', HOME / '.zshrc')


def install_lazydocker():
    subprocess.run(
        [
            'bash',
            '-c',
            'curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash'],
        check=True)


def change_default_shell():
    zsh_path = shutil.which('zsh')
    subprocess.run(['chsh', '-s', zsh_path], check=True)
    print(f"Default shell changed to: {zsh_path}")


def main():
    pkg_manager = detect_package_manager()
    print(f"Detected package manager: {pkg_manager}")

    print("Installing packages...")
    install_packages(pkg_manager)

    print("Installing lazydocker...")
    install_lazydocker()

    print("Installing Oh My Zsh...")
    install_oh_my_zsh()

    print("Installing Zsh plugins...")
    install_zsh_plugins()

    print("Setting up symbolic links...")
    setup_symlinks()

    print("Changing default shell to Zsh...")
    change_default_shell()

    print("Setup complete!")


if __name__ == '__main__':
    main()
