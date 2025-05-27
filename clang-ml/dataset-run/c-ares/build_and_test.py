#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import shutil
import subprocess
import sys
import time
import os
from pathlib import Path
from typing import List, Dict, Tuple

def run(cmd: List[str], *, cwd: Path | None = None) -> None:
    print("+", *cmd)
    subprocess.run(cmd, cwd=cwd, check=True)


def time_exec(exe: Path) -> Tuple[str, float]:
    try:
        args = [str(exe)]
        bench_name = exe.stem
        if bench_name in {"adig", "ahost"}:
            args.append("localhost")
            bench_name += "_localhost"
        start = time.perf_counter()
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return bench_name, time.perf_counter() - start
    except subprocess.CalledProcessError as e:
        print(f"[error] {exe.name} failed to run: {e}")
        return exe.stem, -1.0

def configure(src: Path, build: Path, cflags: List[str]) -> None:
    build.mkdir(parents=True, exist_ok=True)
    run([
        "cmake", "-G", "Unix Makefiles",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_C_COMPILER=clang",
        f"-DCMAKE_C_FLAGS={' '.join(cflags)}",
        str(src),
    ], cwd=build)


def build_lib(build: Path) -> None:
    run(["cmake", "--build", ".", "--parallel", str(mp.cpu_count())], cwd=build)


def compile_tests(src: Path, build: Path, cflags: List[str]) -> List[Path]:
    include_flags = [f"-I{src/'include'}", f"-I{src}"]
    lib_flags = [f"-L{build}", "-lcares", "-lpthread"]
    blacklist = {"ares-test-init", "ares_queryloop"}
    executables: List[Path] = []

    for cfile in sorted((src / "test").glob("*.c")):
        if cfile.stem in blacklist or "fuzz" in cfile.stem:
            continue
        exe = build / cfile.stem
        run([
            "clang", "-std=c99", *cflags, *include_flags, str(cfile),
            "-o", str(exe), *lib_flags,
        ])
        executables.append(exe)
    return executables


def collect_cmake_tools(build: Path) -> List[Path]:
    bin_dir = build / "bin"
    if not bin_dir.exists():
        print("[warn] bin directory not found:", bin_dir)
        return []
    tools = []
    for f in bin_dir.iterdir():
        print("[debug] bin entry:", f, "executable:", os.access(f, os.X_OK))
        if f.is_file() and os.access(f, os.X_OK):
            tools.append(f)
    return tools


def run_benchmarks(executables: List[Path], runs: int) -> List[dict]:
    timings: Dict[str, List[float]] = {}
    sizes: Dict[str, int] = {}

    for exe in executables:
        for _ in range(runs):
            bench_name, sec = time_exec(exe)
            if sec >= 0:
                timings.setdefault(bench_name, []).append(sec)
                sizes[bench_name] = exe.stat().st_size

    results = []
    for bench, times in timings.items():
        avg = sum(times) / len(times)
        results.append({"bench": bench, "bytes": sizes[bench], "seconds": avg})
        print(f"  • {bench}: {avg:.6f}s, {sizes[bench]} bytes")
    return results

def main() -> None:
    root = Path(__file__).resolve().parents[2]

    ap = argparse.ArgumentParser(description="Build c-ares and run its benchmarks")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--no-rebuild", dest="rebuild", action="store_false")
    ap.set_defaults(rebuild=True)
    ap.add_argument("--src", type=Path, default=root / "dataset" / "c-ares")
    ap.add_argument("--build", type=Path)
    args, extra = ap.parse_known_args()

    if extra and extra[0] == "--":
        extra = extra[1:]
    user_cflags: List[str] = extra

    src = args.src.resolve()
    if not src.exists():
        sys.exit(f"Source dir {src} not found")

    build = (args.build if args.build else src / "build").resolve()
    if args.rebuild and build.exists():
        print("[rebuild] removing", build)
        shutil.rmtree(build)

    configure(src, build, user_cflags)
    build_lib(build)

    test_executables = compile_tests(src, build, user_cflags)
    cmake_tools = collect_cmake_tools(build)
    all_executables = test_executables + cmake_tools

    if not all_executables:
        sys.exit("No executables built — nothing to benchmark")

    results_dir = root / "results" / "c-ares"
    results_dir.mkdir(parents=True, exist_ok=True)
    data = run_benchmarks(all_executables, args.runs)
    with open(results_dir / "results.json", "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)
    print("\n[done]", len(data), "records →", results_dir / "results.json")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
