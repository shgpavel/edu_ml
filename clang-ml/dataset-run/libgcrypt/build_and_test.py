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

PROJECT_NAME = "libgcrypt"

DEPS_NAME = "libgpg-error"
DEPS_URL = "https://gnupg.org/ftp/gcrypt/libgpg-error/libgpg-error-1.49.tar.bz2"
DEPS_ARCHIVE_NAME = "libgpg-error-1.49.tar.bz2"
DEPS_DIR_NAME = "libgpg-error-1.49"


def run_command(
    cmd: List[str], cwd: Path = None, env: Dict[str, str] = None
) -> subprocess.CompletedProcess:
    print(f"[CMD] CWD: {cwd} | {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, text=True, capture_output=True
    )


def setup_paths(script_path: Path) -> Dict[str, Path]:
    root_dir = script_path.parents[2]
    deps_dir = root_dir / "dataset" / "deps_src"
    install_dir = deps_dir / "install"
    return {
        "root": root_dir,
        "project_src": root_dir / "dataset" / PROJECT_NAME,
        "bench_src": root_dir / "dataset-bench" / PROJECT_NAME,
        "results_dir": root_dir / "results" / PROJECT_NAME,
        "build_dir": root_dir / "dataset" / f"{PROJECT_NAME}-build",
        "deps_root": deps_dir,
        "deps_src_dir": deps_dir / DEPS_DIR_NAME,
        "deps_archive": deps_dir / DEPS_ARCHIVE_NAME,
        "deps_build_dir": deps_dir / f"{DEPS_NAME}-build",
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


def build_dependency(paths: Dict[str, Path], clang_path: str):
    """Скачивает, собирает и устанавливает libgpg-error."""
    print("\n--- Building Dependency: libgpg-error ---")
    deps_root = paths["deps_root"]
    deps_src = paths["deps_src_dir"]
    deps_build = paths["deps_build_dir"]
    install_dir = paths["install_dir"]

    if not deps_src.exists():
        deps_root.mkdir(exist_ok=True, parents=True)
        if not paths["deps_archive"].exists():
            print(f"[*] Downloading {DEPS_URL}...")
            run_command(
                ["wget", "-O", str(paths["deps_archive"]), DEPS_URL], cwd=deps_root
            )
        print(f"[*] Unpacking {DEPS_ARCHIVE_NAME}...")
        run_command(["tar", "-xjf", str(paths["deps_archive"])], cwd=deps_root)

    shutil.rmtree(deps_build, ignore_errors=True)
    deps_build.mkdir(parents=True)

    print("[*] Configuring libgpg-error...")
    env = os.environ.copy()
    env["CC"] = clang_path
    configure_cmd = [str(deps_src / "configure"), f"--prefix={install_dir}"]
    run_command(configure_cmd, cwd=deps_build, env=env)

    print("[*] Building and installing libgpg-error...")
    run_command(["make", "-j", str(mp.cpu_count())], cwd=deps_build)
    run_command(["make", "install"], cwd=deps_build)
    print("--- Dependency build complete ---")


def build_project(
    paths: Dict[str, Path], clang_path: str, clang_flags: List[str]
) -> List[Path]:
    project_src = paths["project_src"]
    build_dir = paths["build_dir"]
    install_dir = paths["install_dir"]

    build_dependency(paths, clang_path)

    print("\n--- Building Project: libgcrypt ---")

    env = os.environ.copy()
    env["CC"] = clang_path
    env["CFLAGS"] = " ".join(clang_flags)
    env["CPPFLAGS"] = f"-I{install_dir}/include"
    env["LDFLAGS"] = f"-L{install_dir}/lib"

    print(f"[*] Configuring {PROJECT_NAME}...")
    if (project_src / "autogen.sh").exists():
        run_command([str(project_src / "autogen.sh")], cwd=project_src)

    configure_cmd = [
        str(project_src / "configure"),
        f"--prefix={install_dir}",
        f"--with-gpg-error-prefix={install_dir}",
        "--disable-doc",
    ]
    run_command(configure_cmd, cwd=build_dir, env=env)

    print(f"[*] Building and installing {PROJECT_NAME}...")
    run_command(["make", "-j", str(mp.cpu_count())], cwd=build_dir)
    run_command(["make", "install"], cwd=build_dir)

    print("\n--- Building Benchmarks ---")
    config_script = install_dir / "bin" / "libgcrypt-config"
    cflags_proc = run_command([str(config_script), "--cflags"])
    libs_proc = run_command([str(config_script), "--libs"])

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

    run_env = os.environ.copy()
    ld_path = str(paths["install_dir"] / "lib")
    run_env["LD_LIBRARY_PATH"] = (
        ld_path + os.pathsep + run_env.get("LD_LIBRARY_PATH", "")
    )

    for exe_path in executables:
        timings = []
        try:
            for _ in range(runs):
                start_time = time.perf_counter()
                subprocess.run(
                    [str(exe_path)], stdout=subprocess.DEVNULL, check=True, env=run_env
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

    shutil.rmtree(paths["build_dir"], ignore_errors=True)
    shutil.rmtree(paths["deps_build_dir"], ignore_errors=True)
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
        print(f"[*] Cleaning up build directories...")
        shutil.rmtree(paths["build_dir"], ignore_errors=True)
        shutil.rmtree(paths["deps_build_dir"], ignore_errors=True)


if __name__ == "__main__":
    main()
