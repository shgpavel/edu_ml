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

PROJECT_NAME = "libyaml"


def run_command(
    cmd: List[str], cwd: Path = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    print(f"[CMD] CWD: {cwd} | {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, text=True, capture_output=True
    )


def setup_paths(script_path: Path) -> Dict[str, Path]:
    root_dir = script_path.parents[2]
    install_dir = root_dir / "dataset" / "deps_install"
    return {
        "root": root_dir,
        "project_src": root_dir / "dataset" / PROJECT_NAME,
        "bench_src": root_dir / "dataset-bench" / PROJECT_NAME,
        "results_dir": root_dir / "results" / PROJECT_NAME,
        "build_dir": root_dir / "dataset" / f"{PROJECT_NAME}-build",
        "install_dir": install_dir,
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
    project_src = paths["project_src"]
    build_dir = paths["build_dir"]
    install_dir = paths["install_dir"]

    print(f"\n--- Building Project: {PROJECT_NAME} ---")

    env = os.environ.copy()
    env["CC"] = clang_path
    env["CFLAGS"] = " ".join(clang_flags)

    print(f"[*] Generating 'configure' script via bootstrap...")
    run_command(["./bootstrap"], cwd=project_src)

    configure_script = project_src / "configure"
    if not configure_script.is_file():
        raise RuntimeError(
            f"'configure' script not found at {configure_script} after running bootstrap."
        )

    print(f"[*] Configuring {PROJECT_NAME}...")
    configure_cmd = [
        str(configure_script),
        f"--prefix={install_dir}",
        "--enable-static",
        "--disable-shared",
    ]
    run_command(configure_cmd, cwd=build_dir, env=env)

    print(f"[*] Building and installing {PROJECT_NAME}...")
    run_command(["make", "-j", "20", "clean"], cwd=build_dir)
    run_command(["make", "-j", "20"], cwd=build_dir)
    run_command(["make", "install"], cwd=build_dir)

    print("\n--- Building Benchmarks ---")

    pkg_config_path = str(install_dir / "lib" / "pkgconfig")
    pkg_env = os.environ.copy()
    pkg_env["PKG_CONFIG_PATH"] = pkg_config_path

    cflags_proc = run_command(["pkg-config", "--cflags", "yaml-0.1"], env=pkg_env)
    libs_proc = run_command(
        ["pkg-config", "--libs", "--static", "yaml-0.1"], env=pkg_env
    )

    extra_cflags = cflags_proc.stdout.strip().split()
    extra_libs = libs_proc.stdout.strip().split()

    executables = []
    for bench_file in sorted(paths["bench_src"].glob("*_bench.c")):
        exe_path = build_dir / bench_file.stem
        cmd = [
            clang_path,
            *clang_flags,
            *extra_cflags,
            str(bench_file),
            "-o",
            str(exe_path),
            *extra_libs,
        ]
        run_command(cmd)
        executables.append(exe_path)

    return executables


def run_benchmarks(
    executables: List[Path], runs: int, paths: Dict[str, Path]
) -> List[Dict[str, Any]]:
    results = []
    print(f"\n[*] Running {len(executables)} benchmarks ({runs} runs each)...")

    shutil.copy(paths["bench_src"] / "config.yaml", paths["build_dir"])

    for exe_path in executables:
        timings = []
        try:
            subprocess.run(
                [str(exe_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                cwd=paths["build_dir"],
            )
            for _ in range(runs):
                start_time = time.perf_counter()
                subprocess.run(
                    [str(exe_path)],
                    stdout=subprocess.DEVNULL,
                    check=True,
                    cwd=paths["build_dir"],
                )
                timings.append(time.perf_counter() - start_time)

            avg_time = statistics.mean(timings)
            binary_size = exe_path.stat().st_size
            results.append(
                {"bench": exe_path.name, "bytes": binary_size, "seconds": avg_time}
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
    print(f"[*] Install dir:  {paths['install_dir']}")
    print(f"[*] Clang flags:  {' '.join(args.flags) or '(none)'}")

    shutil.rmtree(paths["build_dir"], ignore_errors=True)
    shutil.rmtree(paths["install_dir"], ignore_errors=True)
    paths["build_dir"].mkdir(parents=True)

    try:
        executables = build_project(paths, args.clang, args.flags)
        results = run_benchmarks(executables, args.runs, paths)
        save_results(results, paths)
    except (subprocess.CalledProcessError, RuntimeError) as e:
        print(f"\n[FATAL ERROR] An error occurred during the process.")
        if hasattr(e, "stderr") and e.stderr:
            print(
                "------- STDERR -------\n"
                + e.stderr.strip()
                + "\n----------------------"
            )
        else:
            print(e)
        exit(1)
    finally:
        print(f"[*] Cleaning up build directory...")
        shutil.rmtree(paths["build_dir"], ignore_errors=True)


if __name__ == "__main__":
    main()
