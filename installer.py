#!/usr/bin/env python3

import argparse
import colorama
from pathlib import Path
import os
import shutil
import subprocess
import typing
import tempfile

SCRIPT_DIR = Path(os.path.dirname(__file__))
HOME_DIR = Path.home()
SRC_CONFIG_DIR = SCRIPT_DIR.joinpath(".config")
DST_CONFIG_DIR = HOME_DIR.joinpath(".config")
DRY_RUN = False
UNINSTALL = False


def color_print(color: int, msg: str):
    print(color + msg + colorama.Style.RESET_ALL)


def run(cmd: typing.List[str]):
    color_print(colorama.Fore.YELLOW, " ".join(cmd))
    if not DRY_RUN:
        subprocess.run(cmd)


def su_run(cmd: typing.List[str]):
    run(["sudo", "-k"])  # clear sudo cache
    cmd.insert(0, "sudo")
    run(cmd)


def pac(packages: typing.List[str]):
    if UNINSTALL:
        su_run(["pacman", "-Rnsc",
                *packages])
    else:
        su_run(["pacman", "-S", "--noconfirm", "--needed",
                *packages])


def aur(packages: typing.List[str]):
    if UNINSTALL:
        su_run(["pacman", "-Rnsc",
                *packages])
    else:
        for package in packages:
            with tempfile.TemporaryDirectory(prefix=package) as tmpdir:
                old_dir = os.getcwd()
                run(
                    ["git", "clone", f"https://aur.archlinux.org/{package}.git", tmpdir])
                os.chdir(tmpdir)
                run(["makepkg", "-si", "--noconfirm"])
                os.chdir(old_dir)


def pkgman(installer, *args):
    installer(*args)


def rice(dirname: str, srcdir: Path, destdir: Path) -> None:

    src = srcdir.joinpath(dirname)
    dst = destdir.joinpath(dirname)

    if os.path.islink(dst):
        color_print(colorama.Fore.BLUE, f"Remove link {dst}")
        if not DRY_RUN:
            os.remove(dst)
    elif os.path.isdir(dst):
        color_print(colorama.Fore.BLUE,
                    f"Remove directory and contents {dst}")
        if not DRY_RUN:
            shutil.rmtree(dst)
    elif os.path.isfile(dst):
        color_print(colorama.Fore.BLUE, f"Remove file {dst}")
        if not DRY_RUN:
            os.remove(dst)

    if not UNINSTALL:
        color_print(colorama.Fore.BLUE,
                    f"Link dst: {dst} -> src: {src}")
        if not DRY_RUN:
            dst.symlink_to(src)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Beautify an arch linux desktop with sway wm and install useful wayland tools and linux apps")

    parser.add_argument("--dryrun", "-n", action="store_true", default=DRY_RUN)
    parser.add_argument("--norice", help="Don't rice. Use this to simply update packages.",
                        action="store_true", default=False)
    parser.add_argument("--nodeps", help="Don't install dependencies. Use this when you've edited a configuration file.",
                        action="store_true", default=False)

    ricing = parser.add_mutually_exclusive_group()
    ricing.add_argument("--install", "-i", action="store_true", default=(not UNINSTALL),
                        help="Link configuration files.")
    ricing.add_argument("--uninstall", "-u", action="store_true", default=UNINSTALL,
                        help="Revert configuration files and packages.")

    args = parser.parse_args()
    DRY_RUN = args.dryrun
    UNINSTALL = args.uninstall
    if not args.norice:
        rice("alacritty", SRC_CONFIG_DIR, DST_CONFIG_DIR)
        rice("sway", SRC_CONFIG_DIR, DST_CONFIG_DIR)
        rice("waybar", SRC_CONFIG_DIR, DST_CONFIG_DIR)
        rice("wofi", SRC_CONFIG_DIR, DST_CONFIG_DIR)
        rice(".images", SCRIPT_DIR, HOME_DIR)

    if not args.nodeps:
        color_print(colorama.Fore.GREEN, "#1. basic requirements")
        pkgman(pac, "cmake linux-headers ninja".split())

        color_print(colorama.Fore.GREEN, "#2. wayland stuff")
        pkgman(
            pac, "sway waybar wofi wl-clipboard slurp grim xorg-xwayland".split())

        color_print(colorama.Fore.GREEN, "#3. audio stuff")
        pkgman(pac, "bluez bluez-utils alsa-utils pipewire pipewire-alsa pipewire-pulse blueberry".split())

        color_print(colorama.Fore.GREEN, "#4. networking support")
        pkgman(pac, "networkmanager bluez bluez-utils blueberry".split())

        color_print(colorama.Fore.GREEN, "#5. desktop apps")
        pkgman(pac, ["discord", "alacritty"])
        pkgman(aur, ["google-chrome",
                     "visual-studio-code-bin"])

        color_print(colorama.Fore.GREEN, "#6. necessary fonts")
        pkgman(pac, ["noto-fonts-emoji", "otf-font-awesome"])
        pkgman(aur, ["ttf-iosevka", "ttf-meslo"])
