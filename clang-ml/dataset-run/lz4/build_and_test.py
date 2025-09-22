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

PROJECT_NAME = "lz4"


def run_command(
    cmd: List[str], cwd: Path = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    print(f"[CMD] CWD: {cwd} | {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, text=True, capture_output=True
    )


def setup_paths(script_path: Path) -> Dict[str, Path]:
    """Определяет все необходимые пути проекта."""
    root_dir = script_path.parents[2]
    edu_ml_root = script_path.parents[3]
    install_dir = root_dir / "dataset" / "deps_install"
    return {
        "root": root_dir,
        "project_src": root_dir / "dataset" / PROJECT_NAME,
        "bench_src": root_dir / "dataset-bench" / PROJECT_NAME,
        "results_dir": root_dir / "results" / PROJECT_NAME,
        "build_dir": root_dir / "dataset" / f"{PROJECT_NAME}-build",
        "install_dir": install_dir,
        "test_data_dir": edu_ml_root / "task_1" / "tests",
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

    lib_dir = project_src / "lib"
    print(f"[*] Building {PROJECT_NAME} library...")
    run_command(["make", "-j", "20", "clean"], cwd=lib_dir, env=env)
    run_command(["make", "-j", "20", "all"], cwd=lib_dir, env=env)

    print(f"[*] Installing {PROJECT_NAME} to {install_dir}...")
    install_env = env.copy()
    install_env["DESTDIR"] = str(install_dir)
    install_env["prefix"] = "/usr/local"
    run_command(["make", "install"], cwd=project_src, env=install_env)

    print("\n--- Building Benchmarks ---")

    final_install_path = install_dir / "usr/local"
    include_path = final_install_path / "include"
    lib_path = final_install_path / "lib" / "liblz4.a"

    executables = []
    for bench_file in sorted(paths["bench_src"].glob("*_bench.c")):
        exe_path = build_dir / bench_file.stem
        cmd = [
            clang_path,
            *clang_flags,
            f"-I{include_path}",
            str(bench_file),
            str(lib_path),
            "-o",
            str(exe_path),
        ]
        run_command(cmd)
        executables.append(exe_path)

    return executables


def run_benchmarks(
    executables: List[Path], runs: int, paths: Dict[str, Path]
) -> List[Dict[str, Any]]:
    """Запускает бенчмарки на каждом из 7 тестовых файлов."""
    results = []
    test_data_dir = paths["test_data_dir"]

    if not test_data_dir.exists():
        raise FileNotFoundError(f"Test data directory not found: {test_data_dir}")

    test_files = sorted(
        [
            p
            for p in test_data_dir.iterdir()
            if p.name.isdigit() and 1 <= int(p.name) <= 7
        ]
    )

    if not test_files:
        raise FileNotFoundError(f"No test files named 1-7 found in {test_data_dir}")

    print(
        f"\n[*] Running {len(executables)} benchmarks on {len(test_files)} data files ({runs} runs each)..."
    )

    for exe_path in executables:
        for test_file in test_files:
            bench_name = f"{exe_path.stem}_on_file_{test_file.name}"
            command_to_run = [str(exe_path), str(test_file)]

            timings = []
            try:
                subprocess.run(
                    command_to_run,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                for _ in range(runs):
                    start_time = time.perf_counter()
                    subprocess.run(
                        command_to_run, stdout=subprocess.DEVNULL, check=True
                    )
                    timings.append(time.perf_counter() - start_time)

                avg_time = statistics.mean(timings)
                binary_size = exe_path.stat().st_size
                results.append(
                    {"bench": bench_name, "bytes": binary_size, "seconds": avg_time}
                )
                print(
                    f"  - {bench_name:<35} {binary_size:8d} bytes, {avg_time:.6f}s avg"
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"[ERROR] Failed to run benchmark {bench_name}: {e}")
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
    print(f"[*] Test data:    {paths['test_data_dir']}")
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
        print(f"[*] Cleaning up benchmark binaries directory...")
        shutil.rmtree(paths["build_dir"], ignore_errors=True)
        print(f"[*] Running 'make clean' in the source directory...")
        run_command(["make", "clean"], cwd=(paths["project_src"] / "lib"))


if __name__ == "__main__":
    main()
