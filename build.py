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

sys.path.insert(0, HERE)
import setup  # noqa: E402  (knows which files it put in vendor/)


def vendor_files():
    """Only what setup.py wrote into vendor/. Plugins leave logs, caches and their own config (which can
    hold proxy settings or logins) next to themselves at runtime, and none of that may ship in the exe."""
    files = [os.path.join("vendor", "nova3", *f.split("/")) for f in setup.vendor_files()]
    missing = [f for f in files if not os.path.isfile(os.path.join(HERE, f))]
    if missing:
        sys.exit("run setup.py first; missing: " + ", ".join(missing))
    return files


def plugin_stdlib_imports():
    # Plugins are imported at runtime by name, so PyInstaller can't see what they need.
    mods = set()
    for f in vendor_files():
        if not f.endswith(".py"):
            continue
        with open(os.path.join(HERE, f), encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                mods.add(node.module)
    return sorted(m for m in mods if m.split(".")[0] in sys.stdlib_module_names)


def main():
    sep = os.pathsep
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
        "--name", "Zoro", "--console",
        "--add-data", f"ui.html{sep}.",
        "--add-data", f"ui.js{sep}.",
        "--add-data", f"assets{sep}assets",
        "--add-data", f"LICENSE{sep}.",
        "--add-data", f"THIRD_PARTY_NOTICES.md{sep}.",
        "--add-data", f"licenses{sep}licenses",
        *(x for f in vendor_files() for x in ("--add-data", f"{f}{sep}{os.path.dirname(f)}")),
        "--hidden-import", "run_engine",
        "--hidden-import", "certifi",
        "--exclude-module", "tkinter",
    ]
    if sys.platform == "win32":  # macOS wants .icns (or Pillow to convert); Linux executables have no icon
        args += ["--icon", os.path.join("assets", "icon.ico")]
    for m in plugin_stdlib_imports():
        args += ["--hidden-import", m]
    args.append("web.py")
    subprocess.run(args, cwd=HERE, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
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
