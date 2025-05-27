#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

def run(cmd, cwd=None, env=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"[{cmd}] failed:\n{result.stderr.decode()}")
    return result

def get_bin_size(path):
    return Path(path).stat().st_size if Path(path).exists() else 0

def main():
    parser = argparse.ArgumentParser(description="Build and benchmark coreutils with clang")
    parser.add_argument("--runs", type=int, default=1, help="Number of times to run each benchmark")
    parser.add_argument("cflags", nargs=argparse.REMAINDER, help="CFLAGS to pass to clang")
    args = parser.parse_args()

    clean_flags = [f for f in args.cflags if f != "--"]
    cflags = " ".join(clean_flags) if clean_flags else "-O2"
    runs = args.runs

    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    base_dir = root_dir.parent

    coreutils_dir = base_dir / "dataset" / "coreutils"
    bench_dir = base_dir / "dataset-bench" / "coreutils"
    results_dir = base_dir / "results" / "coreutils"
    build_dir = coreutils_dir / "build-clang"

    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Cleaning old build directory...")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    shutil.copytree(coreutils_dir, build_dir, dirs_exist_ok=True)

    # Ensure gnulib is cloned
    gnulib_dir = build_dir / "gnulib"
    if not gnulib_dir.exists():
        print("[*] Cloning gnulib...")
        run("git clone https://git.savannah.gnu.org/git/gnulib.git", cwd=build_dir)

    print(f"[*] Running bootstrap...")
    run("./bootstrap", cwd=build_dir)

    print(f"[*] Configuring with clang and CFLAGS='{cflags}'")
    env = os.environ.copy()
    env["CC"] = "clang"
    env["CFLAGS"] = cflags
    env["CPPFLAGS"] = "-I.."
    run("./configure --quiet", cwd=build_dir, env=env)

    print(f"[*] Running initial make to generate config.h")
    run("make -s", cwd=build_dir, env=env)

    print(f"[*] Building selected coreutils: echo cat head sort md5sum")
    run("make -s -C src echo cat head sort md5sum", cwd=build_dir, env=env)

    targets = {
        "echo_bench": "echo",
        "cat_bench": "cat",
        "head_bench": "head",
        "sort_bench": "sort",
        "md5sum_bench": "md5sum",
    }

    results = []

    for bench, binary in targets.items():
        bin_path = build_dir / "src" / binary
        size = get_bin_size(bin_path)

        temp_dir = build_dir / f"run_{bench}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(bin_path, temp_dir / binary)

        for input_file in ["small.txt", "large.txt", "numbers.txt", "medium.bin"]:
            source = bench_dir / input_file
            if source.exists():
                shutil.copy(source, temp_dir / source.name)

        bench_script = bench_dir / f"{bench}.py"
        shutil.copy(bench_script, temp_dir / "run_bench.py")

        total_time = 0.0
        for i in range(runs):
            t0 = time.perf_counter()
            run("python3 run_bench.py", cwd=temp_dir)
            t1 = time.perf_counter()
            total_time += (t1 - t0)

        avg_time = total_time / runs

        results.append({
            "bench": bench,
            "bytes": size,
            "seconds": avg_time
        })

        print(f"    {bench:15} {size:8d} bytes  avg {avg_time:.6f}s over {runs} run(s)")

        shutil.rmtree(temp_dir)

    out_path = results_dir / "results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")

    shutil.rmtree(build_dir)

if __name__ == "__main__":
    main()

