"""Build dist/Zoro/Zoro.exe (PyInstaller, one-folder).

Usage: python -I setup.py && python -I build.py
One-folder, not one-file: every engine runs as a child process of the exe, and a one-file exe
would unpack itself again for each of them.
"""
import ast
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "vendor")
VENDOR_STAGE = os.path.join(HERE, "build", "vendor-stage")
RESIDUE = ("__pycache__", "*.pyc", "*.log")  # bytecode embeds the build path; logs come from local runs


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


def stage_vendor():
    # --add-data has no exclude option, so ship a filtered copy of vendor/.
    for root, dirs, files in os.walk(VENDOR, topdown=False):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
        for f in files:
            if f.endswith((".pyc", ".log")):
                os.remove(os.path.join(root, f))
    shutil.rmtree(VENDOR_STAGE, ignore_errors=True)
    shutil.copytree(VENDOR, VENDOR_STAGE, ignore=shutil.ignore_patterns(*RESIDUE))


def main():
    if not os.path.isdir(os.path.join(VENDOR, "nova3", "engines")):
        sys.exit("run setup.py first")
    stage_vendor()
    sep = os.pathsep
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
        "--name", "Zoro", "--console",
        "--add-data", f"{VENDOR_STAGE}{sep}vendor",
        "--add-data", f"ui.html{sep}.",
        "--add-data", f"ui.js{sep}.",
        "--add-data", f"assets{sep}assets",
        "--hidden-import", "run_engine",
        "--hidden-import", "certifi",
        "--exclude-module", "tkinter",
        "--icon", os.path.join("assets", "icon.ico"),
    ]
    for m in plugin_stdlib_imports():
        args += ["--hidden-import", m]
    args.append("web.py")
    subprocess.run(args, cwd=HERE, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    print(os.path.join(HERE, "dist", "Zoro", "Zoro.exe"))


if __name__ == "__main__":
    main()
