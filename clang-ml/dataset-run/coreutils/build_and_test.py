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

PROJECT_NAME = "coreutils"


def run_command(
    cmd: List[str], cwd: Path = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    print(f"[CMD] CWD: {cwd} | {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, text=True, capture_output=True
    )


def setup_paths(script_path: Path) -> Dict[str, Path]:
    root_dir = script_path.parents[2]
    project_src = root_dir / "dataset" / PROJECT_NAME
    build_dir = project_src / "build-clang"
    return {
        "root": root_dir,
        "project_src": project_src,
        "bench_src": root_dir / "dataset-bench" / PROJECT_NAME,
        "results_dir": root_dir / "results" / PROJECT_NAME,
        "build_dir": build_dir,
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

    print(f"[*] Copying source from {project_src} to {build_dir}")
    shutil.copytree(
        project_src,
        build_dir,
        ignore=shutil.ignore_patterns("build-clang"),
        dirs_exist_ok=True,
    )

    gnulib_dir = build_dir / "gnulib"
    if not gnulib_dir.exists():
        print("[*] gnulib not found, cloning it...")
        run_command(
            ["git", "clone", "https://git.savannah.gnu.org/git/gnulib.git"],
            cwd=build_dir,
        )
    else:
        print("[*] gnulib directory already exists.")

    print("[*] Running bootstrap...")
    run_command(["./bootstrap"], cwd=build_dir)

    env = os.environ.copy()
    env["CC"] = clang_path
    env["CFLAGS"] = " ".join(clang_flags)
    env["CPPFLAGS"] = "-I.."

    print(
        f"[*] Configuring with CFLAGS: '{env.get('CFLAGS', '')}' and CPPFLAGS: '{env.get('CPPFLAGS', '')}'"
    )
    run_command(["./configure", "--quiet"], cwd=build_dir, env=env)

    print("[*] Running initial make to generate config files...")
    run_command(["make", "-s"], cwd=build_dir, env=env)

    targets = ["echo", "cat", "head", "sort", "md5sum"]
    print(f"[*] Building targets: {', '.join(targets)}")
    run_command(["make", "-s", "-C", "src", *targets], cwd=build_dir, env=env)

    executables = [build_dir / "src" / target for target in targets]
    if not all(e.exists() for e in executables):
        raise RuntimeError("Not all coreutils targets were built successfully.")

    return executables


def run_benchmarks(
    executables: List[Path], runs: int, paths: Dict[str, Path]
) -> List[Dict[str, Any]]:
    results = []
    bench_src = paths["bench_src"]
    build_dir = paths["build_dir"]

    print(f"\n[*] Running benchmarks for {len(executables)} targets...")
    for exe_path in executables:
        bench_name = f"{exe_path.name}_bench"
        bench_script = bench_src / f"{bench_name}.py"
        if not bench_script.exists():
            print(f"[WARN] Benchmark script not found for {exe_path.name}, skipping.")
            continue

        run_dir = build_dir / f"run_{bench_name}"
        run_dir.mkdir(exist_ok=True)
        shutil.copy(exe_path, run_dir / exe_path.name)
        shutil.copy(bench_script, run_dir / "run_bench.py")

        for data_file in bench_src.iterdir():
            if data_file.is_file() and data_file.suffix != ".py":
                shutil.copy(data_file, run_dir)

        timings = []
        try:
            for i in range(runs):
                print(f"  - Running {bench_name} (run {i + 1}/{runs})...", end="\r")
                start_time = time.perf_counter()
                run_command(["python3", "run_bench.py"], cwd=run_dir)
                end_time = time.perf_counter()
                timings.append(end_time - start_time)
            print()
            avg_time = statistics.mean(timings)
            binary_size = exe_path.stat().st_size
            results.append(
                {"bench": bench_name, "bytes": binary_size, "seconds": avg_time}
            )
            print(f"    {bench_name:<25} {binary_size:8d} bytes, {avg_time:.6f}s avg")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[ERROR] Failed to run benchmark {bench_name}: {e}")
            if hasattr(e, "stderr"):
                print(e.stderr)
        finally:
            shutil.rmtree(run_dir)
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

    try:
        print("\n[*] Starting build...")
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
        print(f"[*] Cleaning up build directory: {paths['build_dir']}")
        shutil.rmtree(paths["build_dir"], ignore_errors=True)


if __name__ == "__main__":
    main()
