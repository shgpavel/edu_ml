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

PROJECT_NAME = "redis"


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
    install_dir = paths["install_dir"]

    print(f"\n--- Building Project: {PROJECT_NAME} ---")

    env = os.environ.copy()
    env["CC"] = clang_path
    env["OPTIMIZATION"] = " ".join(clang_flags)
    env["MALLOC"] = "libc"

    print(f"[*] Building {PROJECT_NAME} server...")
    run_command(["make", "distclean"], cwd=project_src, env=env)
    run_command(["make", "-j", "20"], cwd=project_src, env=env)

    print(f"[*] Installing {PROJECT_NAME} to {install_dir}...")
    run_command(["make", f"PREFIX={install_dir}", "install"], cwd=project_src, env=env)

    hiredis_dir = project_src / "deps" / "hiredis"
    print("[*] Building Hiredis library...")
    run_command(["make", "clean"], cwd=hiredis_dir, env=env)
    run_command(["make", "-j", "20", "static"], cwd=hiredis_dir, env=env)

    print("\n--- Building Benchmarks ---")

    hiredis_include_path = hiredis_dir
    hiredis_lib_path = hiredis_dir / "libhiredis.a"

    executables = []
    build_dir = paths["build_dir"]
    build_dir.mkdir(exist_ok=True)
    for bench_file in sorted(paths["bench_src"].glob("*_bench.c")):
        exe_path = build_dir / bench_file.stem
        cmd = [
            clang_path,
            *clang_flags,
            f"-I{hiredis_include_path}",
            str(bench_file),
            str(hiredis_lib_path),
            "-o",
            str(exe_path),
        ]
        run_command(cmd)
        executables.append(exe_path)

    redis_server_path = install_dir / "bin" / "redis-server"
    return [redis_server_path] + executables


def run_benchmarks(executables: List[Path], runs: int) -> List[Dict[str, Any]]:
    results = []

    redis_server_path = executables[0]
    client_executables = executables[1:]

    print(f"\n[*] Starting Redis server for benchmarking...")

    server_command = [
        str(redis_server_path),
        "--port",
        "6379",
        "--daemonize",
        "no",
        "--save",
        "",
    ]
    server_process = subprocess.Popen(server_command)

    time.sleep(1)

    try:
        print(
            f"\n[*] Running {len(client_executables)} benchmarks ({runs} runs each)..."
        )
        for exe_path in client_executables:
            timings = []
            try:
                subprocess.run(
                    [str(exe_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                for _ in range(runs):
                    start_time = time.perf_counter()
                    subprocess.run(
                        [str(exe_path)], stdout=subprocess.DEVNULL, check=True
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
    finally:
        print(f"\n[*] Shutting down Redis server...")
        server_process.terminate()
        server_process.wait()

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

    try:
        all_executables = build_project(paths, args.clang, args.flags)
        results = run_benchmarks(all_executables, args.runs)
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
        print(f"[*] Cleaning up benchmark binaries directory...")
        shutil.rmtree(paths["build_dir"], ignore_errors=True)
        print(f"[*] Running 'make distclean' in the source directory...")
        run_command(["make", "distclean"], cwd=paths["project_src"])


if __name__ == "__main__":
    main()
