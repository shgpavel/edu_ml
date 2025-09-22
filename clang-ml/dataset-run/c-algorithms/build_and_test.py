#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import time
import datetime
import statistics
from pathlib import Path
from typing import List, Dict, Any

PROJECT_NAME = "c-algorithms"


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
    build_dir = paths["build_dir"]
    project_src = paths["project_src"]
    bench_src = paths["bench_src"]

    include_path = project_src / "src"

    print("[*] Compiling library sources...")
    source_files = list(project_src.glob("src/**/*.c"))
    object_files = []
    for src in source_files:
        obj_path = build_dir / f"{src.stem}.o"
        cmd = [
            clang_path,
            *clang_flags,
            f"-I{include_path}",
            "-c",
            str(src),
            "-o",
            str(obj_path),
        ]
        run_command(cmd, cwd=project_src)
        object_files.append(obj_path)

    print("[*] Archiving library...")
    lib_path = build_dir / "libcalg.a"
    run_command(["ar", "rcs", str(lib_path), *map(str, object_files)])

    print("[*] Building benchmark binaries...")
    executables = []
    for bench_c_file in bench_src.glob("*_bench.c"):
        exe_path = build_dir / bench_c_file.stem
        cmd = [
            clang_path,
            *clang_flags,
            f"-I{include_path}",
            str(bench_c_file),
            str(lib_path),
            "-lm",
            "-lpthread",
            "-o",
            str(exe_path),
        ]
        run_command(cmd)
        executables.append(exe_path)

    return executables


def run_benchmarks(executables: List[Path], runs: int) -> List[Dict[str, Any]]:
    results = []
    print(f"[*] Running {len(executables)} benchmarks ({runs} runs each)...")

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


if __name__ == "__main__":
    main()
