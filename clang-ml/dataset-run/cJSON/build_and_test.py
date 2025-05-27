#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"[{cmd}] failed:\n{result.stderr.decode()}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Build and run cJSON benchmarks with arbitrary CFLAGS using clang.")
    parser.add_argument("--runs", type=int, default=1,
                        help="How many times to run each benchmark (default: 1)")
    parser.add_argument("cflags", nargs=argparse.REMAINDER,
                        help="CFLAGS for clang, e.g. -O2 -march=native")

    args = parser.parse_args()

    clean_flags = [f for f in args.cflags if f != "--"]
    cflags = " ".join(clean_flags) if clean_flags else "-O2"
    runs = args.runs

    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    base_dir = root_dir.parent
    cjson_dir = base_dir / "dataset" / "cJSON"
    bench_dir = base_dir / "dataset-bench" / "cJSON"
    results_dir = base_dir / "results" / "cJSON"
    build_dir = cjson_dir / "build"

    results_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] CFLAGS      : {cflags}")
    print(f"[*] Bench runs  : {runs}")
    print(f"[*] cJSON dir   : {cjson_dir}")
    print(f"[*] Benchmarks  : {bench_dir}")
    print(f"[*] Results dir : {results_dir}")
    print(f"[*] Build dir   : {build_dir}")

    object_files = []
    for src in cjson_dir.glob("*.c"):
        if src.name == "test.c":
            continue
        with open(src, "r") as f:
            if "int main" in f.read():
                continue

        obj = build_dir / f"{src.stem}.o"
        run(f"clang -c {cflags} -I {cjson_dir} {src} -o {obj}")
        object_files.append(obj)

    objs_str = " ".join(str(o) for o in object_files)

    bench_sources = sorted(bench_dir.glob("*.c"))
    if not bench_sources:
        raise RuntimeError(f"No benchmark sources found in {bench_dir}")

    results = []

    for src in bench_sources:
        bench_name = src.stem
        bin_path = build_dir / f"{bench_name}.out"

        cmd_compile = f"clang {cflags} -I {cjson_dir} {src} {objs_str} -o {bin_path}"
        run(cmd_compile)
        bin_size = bin_path.stat().st_size

        total_time = 0.0
        for i in range(runs):
            t0 = time.perf_counter()
            run(str(bin_path))
            t1 = time.perf_counter()
            total_time += (t1 - t0)

        avg_time = total_time / runs

        results.append({
            "bench": bench_name,
            "bytes": bin_size,
            "seconds": avg_time
        })

        print(f"    {bench_name:20}  {bin_size:8d}  avg {avg_time:.6f}s over {runs} run(s)")

        bin_path.unlink()

    for o in object_files:
        o.unlink()

    out_file = results_dir / "results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_file}")

    shutil.rmtree(build_dir)


if __name__ == "__main__":
    main()

