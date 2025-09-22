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

PROJECT_NAME = "c-ares"


def run_command(
    cmd: List[str], cwd: Path = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    print(f"[CMD] {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, text=True, capture_output=True
    )


def setup_paths(script_path: Path) -> Dict[str, Path]:
    root_dir = script_path.parents[2]
    return {
        "root": root_dir,
        "project_src": root_dir / "dataset" / PROJECT_NAME,
        "bench_src": root_dir / "dataset-bench" / PROJECT_NAME,
        "results_dir": root_dir / "results" / PROJECT_NAME,
        "build_dir": root_dir / "dataset" / PROJECT_NAME / "build",
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Build and benchmark {PROJECT_NAME}.")
    parser.add_argument(
        "--clang", default="clang", help="Path to the clang executable."
    )
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of repetitions for each benchmark."
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
    """Сборка c-ares с помощью CMake и компиляция тестов."""
    project_src = paths["project_src"]
    build_dir = paths["build_dir"]

    print("[*] Configuring with CMake...")
    cmake_flags = " ".join(clang_flags)
    cmake_cmd = [
        "cmake",
        "-G",
        "Unix Makefiles",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_C_COMPILER={clang_path}",
        f"-DCMAKE_C_FLAGS={cmake_flags}",
        str(project_src),
    ]
    run_command(cmake_cmd, cwd=build_dir)

    print("[*] Building the library with CMake...")
    run_command(
        ["cmake", "--build", ".", "--parallel", str(mp.cpu_count())], cwd=build_dir
    )

    print("[*] Compiling custom benchmark tests...")
    executables = []
    include_flags = [f"-I{project_src / 'include'}", f"-I{project_src}"]
    lib_flags = [f"-L{build_dir}", "-lcares", "-lpthread"]
    blacklist = {"ares-test-init", "ares_queryloop"}

    for cfile in sorted(paths["bench_src"].glob("*.c")):
        if cfile.stem in blacklist or "fuzz" in cfile.stem:
            continue
        exe_path = build_dir / cfile.stem
        compile_cmd = [
            clang_path,
            *clang_flags,
            *include_flags,
            str(cfile),
            "-o",
            str(exe_path),
            *lib_flags,
        ]
        run_command(compile_cmd)
        executables.append(exe_path)

    cmake_bin_dir = build_dir / "bin"
    if cmake_bin_dir.exists():
        for f in cmake_bin_dir.iterdir():
            if f.is_file() and os.access(f, os.X_OK):
                executables.append(f)

    return executables


def run_benchmarks(executables: List[Path], runs: int) -> List[Dict[str, Any]]:
    results = []
    print(f"[*] Running {len(executables)} benchmarks ({runs} runs each)...")

    for exe_path in executables:
        timings = []
        bench_name = exe_path.stem

        args = [str(exe_path)]
        if bench_name in {"adig", "ahost"}:
            args.append("localhost")
            bench_name += "_localhost"

        try:
            for _ in range(runs):
                start_time = time.perf_counter()
                subprocess.run(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                end_time = time.perf_counter()
                timings.append(end_time - start_time)

            avg_time = statistics.mean(timings)
            binary_size = exe_path.stat().st_size

            results.append(
                {
                    "bench": bench_name,
                    "bytes": binary_size,
                    "seconds": avg_time,
                }
            )
            print(f"  - {bench_name:<25} {binary_size:8d} bytes, {avg_time:.6f}s avg")

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

    print(f"[*] Cleaning build directory: {paths['build_dir']}")
    shutil.rmtree(paths["build_dir"], ignore_errors=True)
    paths["build_dir"].mkdir(parents=True)

    try:
        print("\n[*] Starting build...")
        executables = build_project(paths, args.clang, args.flags)
        if not executables:
            raise RuntimeError("Build process failed or produced no executables.")
        print(f"[OK] Build successful. Found {len(executables)} executables.")

        print("\n[*] Starting benchmarks...")
        results = run_benchmarks(executables, args.runs)

        save_results(results, paths)

    except (subprocess.CalledProcessError, RuntimeError) as e:
        print(f"\n[FATAL ERROR] An error occurred during the process.")
        if hasattr(e, "stderr") and e.stderr:
            print("------- STDERR -------\n" + e.stderr + "\n----------------------")
        else:
            print(e)
        exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    main()
