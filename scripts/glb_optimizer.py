#!/usr/bin/env python3
"""
GLB Optimizer & USDZ Converter CLI (Cross-Platform)

Optimizes GLB/glTF 3D models with Draco mesh compression, WebP texture resizing,
and converts them into Apple AR Quick Look compliant .usdz files using Blender headless.
Zero third-party Python dependencies (runs on pure Python 3 stdlib).
"""

import argparse
import glob
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def find_blender(custom_path: str = None) -> str:
    """Finds the Blender executable across Windows, macOS, and Linux."""
    if custom_path and os.path.isfile(custom_path):
        return os.path.abspath(custom_path)

    env_path = os.environ.get("BLENDER_PATH")
    if env_path and os.path.isfile(env_path):
        return os.path.abspath(env_path)

    which_blender = shutil.which("blender")
    if which_blender:
        return os.path.abspath(which_blender)

    system = platform.system()
    candidates = []

    if system == "Windows":
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        local_app = os.environ.get("LOCALAPPDATA", "")
        candidates.extend([
            os.path.join(prog_files, r"Blender Foundation\Blender 5.1\blender.exe"),
            os.path.join(prog_files, r"Blender Foundation\Blender 5.0\blender.exe"),
            os.path.join(prog_files, r"Blender Foundation\Blender 4.2\blender.exe"),
            os.path.join(prog_files, r"Blender Foundation\Blender 4.1\blender.exe"),
            os.path.join(prog_files, r"Blender Foundation\Blender 4.0\blender.exe"),
        ])
        # Glob for any other installed version in Program Files
        candidates.extend(glob.glob(os.path.join(prog_files, r"Blender Foundation\Blender *\blender.exe")))
        if local_app:
            candidates.extend(glob.glob(os.path.join(local_app, r"Programs\Blender Foundation\Blender *\blender.exe")))

    elif system == "Darwin":  # macOS
        candidates.extend([
            "/Applications/Blender.app/Contents/MacOS/Blender",
        ])
        candidates.extend(glob.glob("/Applications/Blender*.app/Contents/MacOS/Blender"))
        candidates.extend(glob.glob(os.path.expanduser("~/Applications/Blender*.app/Contents/MacOS/Blender")))

    elif system == "Linux":
        candidates.extend([
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/snap/bin/blender",
            "/var/lib/flatpak/exports/bin/org.blender.Blender",
            os.path.expanduser("~/.local/bin/blender"),
        ])

    for path in candidates:
        if path and os.path.isfile(path):
            return os.path.abspath(path)

    return None


def find_npx() -> str:
    """Finds npx executable across platforms."""
    return shutil.which("npx")


def format_bytes(num_bytes: int) -> str:
    """Formats bytes to MB string."""
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def clean_filename(stem: str, no_clean_space: bool) -> str:
    """Cleans spaces and trims filename."""
    if no_clean_space:
        return stem
    import re
    return re.sub(r"\s+", "_", stem.strip())


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Runs a subprocess command with appropriate environment."""
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )


def optimize_glb(
    input_path: Path,
    output_path: Path,
    texture_size: int = 1024,
    compress_method: str = "draco",
) -> bool:
    """Optimizes GLB using gltf-transform CLI."""
    npx_bin = find_npx()
    if not npx_bin:
        raise RuntimeError("Command 'npx' not found in PATH. Please install Node.js.")

    cmd = [
        npx_bin,
        "--yes",
        "@gltf-transform/cli",
        "optimize",
        str(input_path),
        str(output_path),
        "--texture-compress",
        "webp",
        "--texture-size",
        str(texture_size),
        "--simplify-lock-border",
        "true",
    ]
    if compress_method in ["draco", "meshopt"]:
        cmd.extend(["--compress", compress_method])
        if compress_method == "meshopt":
            cmd.extend(["--meshopt-level", "high"])
    elif compress_method in ["none", "false"]:
        cmd.extend(["--compress", "false"])

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"Error optimizing {input_path.name}:\n{result.stdout}", file=sys.stderr)
        return False
    return True


def convert_to_usdz(
    input_path: Path,
    output_path: Path,
    blender_bin: str,
    python_script: Path,
    texture_size: int = 1024,
) -> bool:
    """Converts GLB to Apple AR Quick Look compliant USDZ."""
    npx_bin = find_npx()
    if not npx_bin:
        raise RuntimeError("Command 'npx' not found in PATH. Please install Node.js.")

    with tempfile.NamedTemporaryFile(suffix="_norm.glb", delete=False) as tmp:
        temp_glb = Path(tmp.name)

    try:
        # Step 1: Decode Draco and convert WebP textures to PNG
        subprocess.run(
            [npx_bin, "--yes", "@gltf-transform/cli", "png", str(input_path), str(temp_glb), "--formats", "webp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        source_file = temp_glb if temp_glb.exists() and temp_glb.stat().st_size > 0 else input_path

        # Step 2: Headless Blender export to USDZ
        cmd = [
            blender_bin,
            "--background",
            "--python",
            str(python_script),
            "--",
            str(source_file),
            str(output_path),
            str(texture_size),
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or not output_path.exists():
            print(f"Error converting to USDZ {input_path.name}:\n{result.stdout}", file=sys.stderr)
            return False
        return True
    finally:
        if temp_glb.exists():
            try:
                temp_glb.unlink()
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="GLB 3D Optimizer & Apple USDZ Converter (Cross-Platform)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to a .glb file or directory containing .glb files (default: current directory)",
    )
    parser.add_argument(
        "--out-folder",
        "-o",
        default="compressed",
        help="Subfolder or path where results are saved (default: 'compressed')",
    )
    parser.add_argument(
        "--suffix",
        "-s",
        default="_v1",
        help="Suffix added to optimized filenames (default: '_v1')",
    )
    parser.add_argument(
        "--texture-size",
        "-t",
        type=int,
        default=1024,
        help="Maximum texture dimension in pixels (default: 1024)",
    )
    parser.add_argument(
        "--no-clean-space",
        action="store_true",
        help="Do not replace spaces in filenames with underscores",
    )
    parser.add_argument(
        "--usdz",
        action="store_true",
        help="Also export Apple AR Quick Look compliant .usdz files",
    )
    parser.add_argument(
        "--usdz-only",
        action="store_true",
        help="Only convert GLB models directly to .usdz without GLB optimization",
    )
    parser.add_argument(
        "--compress",
        "-c",
        choices=["draco", "meshopt", "none"],
        default="draco",
        help="Geometry compression method: 'draco' (maximum compression, default), 'meshopt' (ultra-fast SIMD decode, zero UX lag), or 'none'",
    )
    parser.add_argument(
        "--meshopt",
        action="store_true",
        help="Shortcut to use meshopt compression (--compress meshopt)",
    )
    parser.add_argument(
        "--no-draco",
        action="store_true",
        help="Disable Draco geometry compression (equivalent to --compress none)",
    )
    parser.add_argument(
        "--blender-path",
        help="Path to blender executable (optional, auto-detected if omitted)",
    )

    args = parser.parse_args()

    # Determine compression method
    compress_method = args.compress
    if args.meshopt:
        compress_method = "meshopt"
    elif args.no_draco:
        compress_method = "none"

    # Locate helper script
    script_dir = Path(__file__).resolve().parent
    blender_helper = script_dir / "gltf_to_usdz.py"

    # Pre-checks
    if not find_npx():
        print("Error: 'npx' was not found in PATH. Node.js is required to run gltf-transform.", file=sys.stderr)
        sys.exit(1)

    blender_bin = None
    if args.usdz or args.usdz_only:
        blender_bin = find_blender(args.blender_path)
        if not blender_bin:
            print("Error: Blender executable not found. Install Blender (4.2+ or 5.x) or specify --blender-path.", file=sys.stderr)
            sys.exit(1)
        if not blender_helper.exists():
            print(f"Error: Blender export script not found at {blender_helper}", file=sys.stderr)
            sys.exit(1)

    target_path = Path(args.path).resolve()
    if target_path.is_file():
        if target_path.suffix.lower() != ".glb":
            print(f"Error: Specified file is not a .glb file: {target_path}", file=sys.stderr)
            sys.exit(1)
        files = [target_path]
        base_dir = target_path.parent
    elif target_path.is_dir():
        files = sorted(list(target_path.glob("*.glb")) + list(target_path.glob("*.GLB")))
        base_dir = target_path
    else:
        print(f"Error: Path does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"No .glb files found in {target_path}")
        return

    out_dir = Path(args.out_folder)
    if not out_dir.is_absolute():
        out_dir = base_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  GLB 3D Optimizer & USDZ Converter (Cross-Platform)")
    print("=" * 60)
    print(f"Files found   : {len(files)}")
    print(f"Source dir    : {base_dir}")
    print(f"Output dir    : {out_dir}")
    print(f"Texture max   : {args.texture_size}px")
    if not args.usdz_only:
        print(f"Compression   : {compress_method.upper()}")
    if args.usdz or args.usdz_only:
        print(f"Blender       : {blender_bin}")
    print("-" * 60)

    results = []

    for idx, file in enumerate(files, 1):
        clean_base = clean_filename(file.stem, args.no_clean_space)
        suffix = args.suffix if not args.usdz_only else ""
        out_glb_name = f"{clean_base}{suffix}.glb"
        out_glb_path = out_dir / out_glb_name
        out_usdz_name = f"{clean_base}{suffix}.usdz"
        out_usdz_path = out_dir / out_usdz_name

        orig_size = file.stat().st_size
        t0 = time.time()
        print(f"\n[{idx}/{len(files)}] Processing: {file.name}")

        glb_size = 0
        usdz_size = 0

        # Run GLB optimization unless usdz-only is requested
        if not args.usdz_only:
            success = optimize_glb(
                input_path=file,
                output_path=out_glb_path,
                texture_size=args.texture_size,
                compress_method=compress_method,
            )
            if success and out_glb_path.exists():
                glb_size = out_glb_path.stat().st_size
                red = (1 - (glb_size / orig_size)) * 100 if orig_size > 0 else 0
                print(f"  -> GLB:  {format_bytes(orig_size)} -> {format_bytes(glb_size)} (-{red:.1f}%)")
            else:
                print(f"  -> GLB optimization failed.")
                continue

        # Run USDZ conversion if requested
        if args.usdz or args.usdz_only:
            source_for_usdz = out_glb_path if (not args.usdz_only and out_glb_path.exists()) else file
            usdz_success = convert_to_usdz(
                input_path=source_for_usdz,
                output_path=out_usdz_path,
                blender_bin=blender_bin,
                python_script=blender_helper,
                texture_size=args.texture_size,
            )
            if usdz_success and out_usdz_path.exists():
                usdz_size = out_usdz_path.stat().st_size
                print(f"  -> USDZ: {format_bytes(usdz_size)} (Apple AR compliant)")
            else:
                print(f"  -> USDZ conversion failed.")

        duration = time.time() - t0
        results.append({
            "name": file.name,
            "orig_size": orig_size,
            "glb_size": glb_size,
            "usdz_size": usdz_size,
            "duration": duration,
        })

    # Summary table
    if results:
        print("\n" + "=" * 70)
        print("  SUMMARY REPORT")
        print("=" * 70)
        header = f"{'Input File':<35} {'Original':<10} {'GLB Opt':<10} {'USDZ':<10} {'Time':<6}"
        print(header)
        print("-" * 70)
        total_orig = sum(r["orig_size"] for r in results)
        total_glb = sum(r["glb_size"] for r in results)
        total_usdz = sum(r["usdz_size"] for r in results)

        for r in results:
            orig_str = format_bytes(r["orig_size"])
            glb_str = format_bytes(r["glb_size"]) if r["glb_size"] else "-"
            usdz_str = format_bytes(r["usdz_size"]) if r["usdz_size"] else "-"
            print(f"{r['name'][:34]:<35} {orig_str:<10} {glb_str:<10} {usdz_str:<10} {r['duration']:<5.1f}s")

        print("-" * 70)
        tot_orig_str = format_bytes(total_orig)
        tot_glb_str = format_bytes(total_glb) if total_glb else "-"
        tot_usdz_str = format_bytes(total_usdz) if total_usdz else "-"
        print(f"{'TOTAL':<35} {tot_orig_str:<10} {tot_glb_str:<10} {tot_usdz_str:<10}")
        if total_glb:
            saved = (1 - (total_glb / total_orig)) * 100 if total_orig > 0 else 0
            print(f"GLB Total Compression Saving: -{saved:.1f}%")
        print(f"Output folder: {out_dir}\n")


if __name__ == "__main__":
    main()
