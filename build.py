"""Build dist/Zoro/Zoro.exe (PyInstaller, one-folder). On Linux and macOS: dist/Zoro/Zoro, packed
into dist/Zoro-<os>-<arch>.tar.gz.

Usage: python -I setup.py && python -I build.py
One-folder, not one-file: every engine runs as a child process of the exe, and a one-file exe
would unpack itself again for each of them.
"""
import ast
import os
import platform
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "vendor")


def plugin_stdlib_imports():
    # Plugins are imported at runtime by name, so PyInstaller can't see what they need.
    mods = set()
    for root, _, files in os.walk(VENDOR):
        for f in files:
            if not f.endswith(".py"):
                continue
            with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    mods.update(a.name for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    mods.add(node.module)
    return sorted(m for m in mods if m.split(".")[0] in sys.stdlib_module_names)


def main():
    if not os.path.isdir(os.path.join(VENDOR, "nova3", "engines")):
        sys.exit("run setup.py first")
    sep = os.pathsep
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
        "--name", "Zoro", "--console",
        "--add-data", f"vendor{sep}vendor",
        "--add-data", f"ui.html{sep}.",
        "--add-data", f"ui.js{sep}.",
        "--add-data", f"assets{sep}assets",
        "--hidden-import", "run_engine",
        "--hidden-import", "certifi",
        "--exclude-module", "tkinter",
    ]
    if sys.platform == "win32":  # macOS wants .icns (or Pillow to convert); Linux executables have no icon
        args += ["--icon", os.path.join("assets", "icon.ico")]
    for m in plugin_stdlib_imports():
        args += ["--hidden-import", m]
    args.append("web.py")
    subprocess.run(args, cwd=HERE, check=True)
    dist = os.path.join(HERE, "dist")
    if sys.platform == "win32":
        print(os.path.join(dist, "Zoro", "Zoro.exe"))  # installer: ISCC installer.iss
        return
    # tar keeps the executable bit, which a zip made here would not reliably carry
    name = "macos" if sys.platform == "darwin" else sys.platform
    arch = {"amd64": "x86_64", "aarch64": "arm64"}.get(platform.machine().lower(), platform.machine().lower())
    print(shutil.make_archive(os.path.join(dist, f"Zoro-{name}-{arch}"), "gztar", dist, "Zoro"))


if __name__ == "__main__":
    main()
