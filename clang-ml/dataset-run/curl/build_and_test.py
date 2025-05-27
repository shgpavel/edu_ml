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
    parser = argparse.ArgumentParser(description="Build and benchmark curl with clang")
    parser.add_argument("--runs", type=int, default=1, help="How many times to run each benchmark")
    parser.add_argument("cflags", nargs=argparse.REMAINDER, help="CFLAGS for clang")
    args = parser.parse_args()

    clean_flags = [f for f in args.cflags if f != "--"]
    cflags = " ".join(clean_flags) if clean_flags else "-O2"
    runs = args.runs

    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    base_dir = root_dir.parent

    curl_dir = base_dir / "dataset" / "curl"
    bench_dir = base_dir / "dataset-bench" / "curl"
    results_dir = base_dir / "results" / "curl"
    build_dir = curl_dir / "build-clang"

    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Cleaning old build directory...")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    shutil.copytree(curl_dir, build_dir, dirs_exist_ok=True)

    # Run buildconf to generate configure
    print("[*] Running buildconf to generate configure script...")
    run("./buildconf", cwd=build_dir)

    print(f"[*] Configuring with clang and CFLAGS: {cflags}")
    env = os.environ.copy()
    env["CC"] = "clang"
    env["CFLAGS"] = cflags
    env["CPPFLAGS"] = "-I.."
    run("./configure --quiet --without-ssl", cwd=build_dir, env=env)

    print("[*] Building curl...")
    run("make -s -j$(nproc)", cwd=build_dir, env=env)

    curl_bin = build_dir / "src" / "curl"
    if not curl_bin.exists():
        raise RuntimeError("curl binary not found at expected location.")

    bin_size = get_bin_size(curl_bin)

    results = []

    benchmarks = sorted(bench_dir.glob("*_bench.py"))
    if not benchmarks:
        raise RuntimeError(f"No *_bench.py found in {bench_dir}")

    for bench_path in benchmarks:
        bench_name = bench_path.stem
        print(f"[*] Running benchmark: {bench_name}")

        temp_dir = build_dir / f"run_{bench_name}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy(curl_bin, temp_dir / "curl")
        bench_script = bench_path.name
        shutil.copy(bench_path, temp_dir / "run_bench.py")

        txt_path = bench_dir / "test.txt"
        if txt_path.exists():
            shutil.copy(txt_path, temp_dir / "test.txt")

        total_time = 0.0
        for _ in range(runs):
            t0 = time.perf_counter()
            run("python3 run_bench.py", cwd=temp_dir)
            t1 = time.perf_counter()
            total_time += (t1 - t0)

        avg_time = total_time / runs

        results.append({
            "bench": bench_name,
            "bytes": bin_size,
            "seconds": avg_time
        })

        print(f"    {bench_name:20}  {bin_size:8d} bytes  avg {avg_time:.6f}s over {runs} run(s)")

        shutil.rmtree(temp_dir)

    out_path = results_dir / "results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")

    shutil.rmtree(build_dir)


if __name__ == "__main__":
    main()

