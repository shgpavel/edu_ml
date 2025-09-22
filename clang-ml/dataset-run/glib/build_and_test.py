#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import time
import datetime
import statistics
import multiprocessing as mp
from pathlib import Path
from typing import List, Dict, Any

PROJECT_NAME = "glib"


def run_command(
    cmd: List[str], cwd: Path = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    print(f"[CMD] {' '.join(cmd[:4])} ...")
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, text=True, capture_output=True
    )


def setup_paths(script_path: Path) -> Dict[str, Path]:
    root_dir = script_path.parents[2]
    project_dir = root_dir / "dataset" / PROJECT_NAME
    return {
        "root": root_dir,
        "project_src": project_dir,
        "bench_src": root_dir / "dataset-bench" / PROJECT_NAME,
        "results_dir": root_dir / "results" / PROJECT_NAME,
        "build_dir": project_dir / "build",
        "install_dir": project_dir / "install",
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Build and benchmark {PROJECT_NAME}.")
    parser.add_argument(
        "--clang", default="clang", help="Path to the clang executable."
    )
    parser.add_argument(
        "--runs", type=int, default=3, help="Number of repetitions for each benchmark."
    )
    parser.add_argument(
        "flags", nargs=argparse.REMAINDER, help="Clang compiler flags (prefix with --)."
    )
    args = parser.parse_args()
    args.flags = [flag for flag in args.flags if flag != "--"]
    return args


def build_project(
    paths: Dict[str, Path], clang_path: str, clang_flags: List[str]
) -> List[Path]:
    """Сборка и локальная установка glib, затем компиляция тестов."""
    project_src = paths["project_src"]
    build_dir = paths["build_dir"]
    install_dir = paths["install_dir"]

    if build_dir.exists():
        shutil.rmtree(build_dir)
    if install_dir.exists():
        shutil.rmtree(install_dir)
    build_dir.mkdir()
    install_dir.mkdir()

    env = os.environ.copy()
    env["CC"] = clang_path
    env["CFLAGS"] = " ".join(clang_flags)

    if (project_src / "meson.build").exists():
        print("[*] Found meson.build, using Meson build system.")
        run_command(
            [
                "meson",
                "setup",
                str(build_dir),
                f"--prefix={install_dir}",
                "-Dbuildtype=release",
                "-Dlibmount=disabled",
                "-Dselinux=disabled",
            ],
            cwd=project_src,
            env=env,
        )
        run_command(
            ["meson", "compile", "-C", str(build_dir), "-j", str(mp.cpu_count())],
            env=env,
        )
        run_command(["meson", "install", "-C", str(build_dir)], env=env)
    elif (project_src / "configure").exists():
        print("[*] Found configure script, using Autotools.")
        run_command(
            [str(project_src / "configure"), f"--prefix={install_dir}", "--quiet"],
            cwd=project_src,
            env=env,
        )
        run_command(["make", "-j", str(mp.cpu_count())], cwd=project_src, env=env)
        run_command(["make", "install"], cwd=project_src, env=env)
    else:
        raise RuntimeError(
            "No supported build system found (meson.build or configure)."
        )

    print("[*] Compiling benchmark tests against installed glib...")

    build_env = env.copy()
    pkg_config_path = str(install_dir / "lib/pkgconfig")
    if "PKG_CONFIG_PATH" in build_env:
        build_env["PKG_CONFIG_PATH"] += os.pathsep + pkg_config_path
    else:
        build_env["PKG_CONFIG_PATH"] = pkg_config_path

    pkg_flags_proc = run_command(
        ["pkg-config", "--cflags", "--libs", "glib-2.0"], env=build_env
    )
    pkg_flags = pkg_flags_proc.stdout.strip().split()

    executables = []
    exec_dir = build_dir / "execs"
    exec_dir.mkdir()

    bench_sources = sorted(paths["bench_src"].glob("*.c"))
    if not bench_sources:
        raise RuntimeError(f"No benchmark sources found in {paths['bench_src']}")

    for src in bench_sources:
        exe = exec_dir / src.stem
        cmd = [clang_path, *clang_flags, str(src), "-o", str(exe), *pkg_flags]
        run_command(cmd, env=build_env)
        executables.append(exe)

    return executables


def run_benchmarks(
    executables: List[Path], runs: int, paths: Dict[str, Path]
) -> List[Dict[str, Any]]:
    results = []
    print(f"[*] Running {len(executables)} benchmarks ({runs} runs each)...")

    run_env = os.environ.copy()
    run_env["LD_LIBRARY_PATH"] = str(paths["install_dir"] / "lib")

    for exe_path in executables:
        timings = []
        try:
            for _ in range(runs):
                start_time = time.perf_counter()
                subprocess.run(
                    [str(exe_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    env=run_env,
                )
                end_time = time.perf_counter()
                timings.append(end_time - start_time)

            avg_time = statistics.mean(timings)
            binary_size = exe_path.stat().st_size

            results.append(
                {
                    "bench": exe_path.name,
                    "bytes": binary_size,
                    "seconds": avg_time,
                }
            )
            print(
                f"  - {exe_path.name:<25} {binary_size:8d} bytes, {avg_time:.6f}s avg"
            )

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[ERROR] Failed to run benchmark {exe_path.name}: {e}")

    return results


def save_results(results: List[Dict[str, Any]], paths: Dict[str, Path]):
    if not results:
        print("[WARN] No results to save.")
        return
    results_dir = paths["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"results_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[SUCCESS] Results saved to {output_file.relative_to(paths['root'])}")


def main():
    args = parse_arguments()
    paths = setup_paths(Path(__file__).resolve())
    print(f"[*] Project:      {PROJECT_NAME}")
    print(f"[*] Build dir:    {paths['build_dir']}")
    print(f"[*] Clang flags:  {' '.join(args.flags) or '(none)'}")

    try:
        print("\n[*] Starting build...")
        executables = build_project(paths, args.clang, args.flags)
        if not executables:
            raise RuntimeError("Build process failed or produced no executables.")
        print(f"[OK] Build successful.")

        print("\n[*] Starting benchmarks...")
        results = run_benchmarks(executables, args.runs, paths)

        save_results(results, paths)

    except (subprocess.CalledProcessError, RuntimeError) as e:
        print(f"\n[FATAL ERROR] An error occurred during the process.")
        if hasattr(e, "stderr") and e.stderr:
            print("------- STDERR -------\n" + e.stderr + "\n----------------------")
        else:
            print(e)
        exit(1)


if __name__ == "__main__":
    main()
