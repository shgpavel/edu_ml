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

PROJECT_NAME = "task_serpas"


def run_command(
    cmd: List[str], cwd: Path = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    print(f"[CMD] CWD: {cwd} | {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, text=True, capture_output=True
    )


def setup_paths(script_path: Path) -> Dict[str, Path]:
    """Defines all necessary project paths using absolute paths for the source."""
    results_root = script_path.parents[2]

    project_src = Path("/home/main/dev/git/edu_nm/task_serpas/src")

    return {
        "root": results_root,
        "project_src": project_src,
        "executable_path": project_src / "stest_x86",
        "results_dir": results_root / "results" / PROJECT_NAME,
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
    executable_path = paths["executable_path"]

    print(f"\n--- Building Project: {PROJECT_NAME} ---")

    env = os.environ.copy()
    env["CC"] = clang_path
    env["CFLAGS"] = " ".join(clang_flags)

    print(f"[*] Building '{PROJECT_NAME}' executable...")
    run_command(["make", "clean"], cwd=project_src, env=env)
    run_command(["make", "-j", "20"], cwd=project_src, env=env)

    if not executable_path.is_file():
        raise RuntimeError(f"Build failed: Executable not found at {executable_path}")

    print(f"[*] Build successful. Executable at: {executable_path}")

    return [executable_path]


def run_benchmarks(executables: List[Path], runs: int) -> List[Dict[str, Any]]:
    if not executables:
        print("[WARN] No executable to benchmark.")
        return []

    main_executable = executables[0]
    results = []

    benchmark_cases = {
        "benchmark_t1": "-t1",
        "benchmark_t2": "-t2",
        "benchmark_t3": "-t3",
        "benchmark_t4": "-t4",
    }

    print(f"\n[*] Running {len(benchmark_cases)} benchmarks ({runs} runs each)...")

    for name, flag in benchmark_cases.items():
        command = [str(main_executable), flag]
        timings = []
        try:
            subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            for _ in range(runs):
                start_time = time.perf_counter()
                subprocess.run(command, stdout=subprocess.DEVNULL, check=True)
                timings.append(time.perf_counter() - start_time)

            avg_time = statistics.mean(timings)
            binary_size = main_executable.stat().st_size
            results.append({"bench": name, "bytes": binary_size, "seconds": avg_time})
            print(f"  - {name:<25} {binary_size:8d} bytes, {avg_time:.6f}s avg")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[ERROR] Failed to run benchmark {name}: {e}")

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
    print(f"[*] Source dir:   {paths['project_src']}")
    print(f"[*] Executable:   {paths['executable_path']}")
    print(f"[*] Clang flags:  {' '.join(args.flags) or '(none)'}")

    try:
        executables = build_project(paths, args.clang, args.flags)
        results = run_benchmarks(executables, args.runs)
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
        print(f"[*] Running 'make clean' in the source directory...")
        run_command(["make", "clean"], cwd=paths["project_src"])


if __name__ == "__main__":
    main()
