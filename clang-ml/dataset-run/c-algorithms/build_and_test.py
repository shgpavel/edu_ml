#!/usr/bin/env python3

import argparse, subprocess, pathlib, shutil, json, statistics, time, os, concurrent.futures, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATASET = ROOT / "dataset" / "c-algorithms"
BENCH_DIR = ROOT / "dataset-bench" / "c-algorithms" / "benchmarks"
RESULT_DIR = ROOT / "results"

MAX_WORKERS = 20

def run(cmd, **kw):
    kw.setdefault("check", True)
    kw.setdefault("text", False)
    return subprocess.run(cmd, **kw)

def compile_source(src: pathlib.Path, obj: pathlib.Path, clang: str, flags: list[str], include_path: pathlib.Path):
    cmd = [clang, *flags, f"-I{include_path}", "-c", str(src), "-o", str(obj)]
    run(cmd, cwd=DATASET)

def build_library(build_dir: pathlib.Path, clang: str, flags: list[str]) -> pathlib.Path:
    include_path = DATASET / "src"
    obj_dir = build_dir / "obj"
    obj_dir.mkdir(parents=True, exist_ok=True)

    src_files = list(DATASET.glob("src/**/*.c"))
    objs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = []
        for src in src_files:
            rel = src.relative_to(DATASET)
            obj = obj_dir / rel.with_suffix(".o").name
            obj.parent.mkdir(parents=True, exist_ok=True)
            futs.append(ex.submit(compile_source, src, obj, clang, flags, include_path))
            objs.append(obj)
        for f in concurrent.futures.as_completed(futs):
            f.result()

    lib = build_dir / "libcalg.a"
    if lib.exists():
        lib.unlink()
    run(["ar", "rcs", str(lib), *map(str, objs)])
    return lib

def build_binaries(build_dir: pathlib.Path, clang: str, flags: list[str], lib: pathlib.Path) -> list[pathlib.Path]:
    include_path = DATASET / "src"
    binaries = []
    for src in BENCH_DIR.glob("*_bench.c"):
        bin_path = build_dir / src.with_suffix("").name
        cmd = [
            clang,
            *flags,
            f"-I{include_path}",
            str(src),
            str(lib),
            "-lm", "-lpthread",
            "-o", str(bin_path)
        ]
        run(cmd)
        binaries.append(bin_path)
    return binaries

def measure(bin_path: pathlib.Path, runs: int) -> float:
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run([str(bin_path)], stdout=subprocess.DEVNULL, check=True)
        times.append(time.perf_counter() - start)
    return statistics.mean(times)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clang", default="clang", help="clang executable")
    ap.add_argument("--runs", type=int, default=5, help="repetitions of each benchmark")
    ap.add_argument("flags", nargs=argparse.REMAINDER, help="extra clang flags (precede with --)")
    args = ap.parse_args()
    args.flags = [f for f in args.flags if f != "--"]

    build_dir = DATASET / "build"
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir()

    print(f"[*] Parallel compiling on up to {MAX_WORKERS} cores…")
    lib = build_library(build_dir, args.clang, args.flags)

    print("[*] Building benchmarks…")
    binaries = build_binaries(build_dir, args.clang, args.flags, lib)

    
    print("[*] Running benchmarks")
    def run_bench(bin_path):
        size = bin_path.stat().st_size
        t0 = time.perf_counter()
        for _ in range(args.runs):
            subprocess.run([str(bin_path)], stdout=subprocess.DEVNULL, check=True)
        elapsed = (time.perf_counter() - t0) / args.runs
        return {"bench": bin_path.name, "bytes": size, "seconds": elapsed}

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        results = list(ex.map(run_bench, binaries))

    for bin in binaries:
        size = bin.stat().st_size
        sec = measure(bin, args.runs)
        results.append({"bench": bin.name, "bytes": size, "seconds": sec})

    RESULT_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = RESULT_DIR / f"c-algorithms/results_{ts}.json"
    with open(out_file, "w") as fp:
        json.dump(results, fp, indent=2)
    print(f"Saved results to {out_file.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
