#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import sys

def run(cmd, cwd=None, env=None):
    """Run a command, raising RuntimeError on non-zero exit."""
    res = subprocess.run(
        cmd, cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed:\n"
            f"Out:\n{res.stdout}\nErr:\n{res.stderr}"
        )
    return res

def build_igraph(src: Path, build: Path, install: Path, cflags: str):
    """Configure, build, and install igraph with clang/OpenMP."""
    env = os.environ.copy()
    env.update({
        'CC': 'clang',
        'CXX': 'clang++',
    })
    cmake_cflags   = f"{cflags} -Wno-error -fopenmp"
    cmake_cxxflags = f"{cflags} -Wno-error -fopenmp"
    if build.exists():
        shutil.rmtree(build)
    if install.exists():
        shutil.rmtree(install)
    build.mkdir(parents=True)
    install.mkdir(parents=True)

    run([
        'cmake',
        '-S', str(src),
        '-B', str(build),
        '-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_C_COMPILER=clang',
        '-DCMAKE_CXX_COMPILER=clang++',
        f'-DCMAKE_C_FLAGS={cmake_cflags}',
        f'-DCMAKE_CXX_FLAGS={cmake_cxxflags}',
        f'-DCMAKE_INSTALL_PREFIX={install}',
    ], env=env)
    run(['cmake', '--build', str(build), '--', '-j'], env=env)
    run(['cmake', '--install', str(build), '--prefix', str(install)], env=env)

def discover_tests(src: Path):
    """Find all .c, .cc, .cpp under tests/."""
    tests_dir = src / 'tests'
    patterns = ['*.c', '*.cc', '*.cpp']
    sources = []
    for p in patterns:
        sources.extend(sorted(tests_dir.rglob(p)))
    if not sources:
        raise RuntimeError("No test source files found under tests/")
    return sources

def process_single(args):
    """
    Compile, link, and run a single test/benchmark.
    Returns a dict on success, or None to indicate skip.
    """
    src_file, exe_path, obj_path, cflags, runs, pkg_cflags, pkg_libs, install_lib = args
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = str(Path(install_lib) / 'pkgconfig')
    env['LD_LIBRARY_PATH'] = install_lib

    ext = Path(src_file).suffix
    compiler = 'clang++' if ext in ('.cc', '.cpp') else 'clang'

    # 1) compile to object
    try:
        run(
            [compiler] + cflags.split() + ['-fopenmp'] + pkg_cflags +
            ['-c', src_file, '-o', obj_path],
            env=env
        )
    except RuntimeError as e:
        # skip if header not found or other compile error
        print(f"[skip compile] {src_file}: {e}", file=sys.stderr)
        return None

    # 2) link to executable
    try:
        run(
            ['clang++', '-fopenmp', obj_path, '-o', exe_path] +
            pkg_libs + ['-lm', '-larpack', '-lblas', '-llapack'],
            env=env
        )
    except RuntimeError as e:
        # skip if link errors (missing symbols, etc.)
        print(f"[skip link] {src_file}: {e}", file=sys.stderr)
        return None

    # 3) run the executable runs times, measuring average time
    size = Path(exe_path).stat().st_size
    total = 0.0
    for _ in range(runs):
        t0 = time.perf_counter()
        try:
            run([exe_path], env=env)
        except RuntimeError as e:
            # skip benchmarks that hang waiting for input
            if "Select all vertices" in str(e):
                print(f"[skip run] {src_file}: waiting for input", file=sys.stderr)
                return None
            # skip other runtime failures
            print(f"[skip run error] {src_file}: {e}", file=sys.stderr)
            return None
        total += time.perf_counter() - t0

    avg = total / runs

    # cleanup
    for p_str in (exe_path, obj_path):
        try:
            Path(p_str).unlink()
        except FileNotFoundError:
            pass

    return {
        "bench": Path(src_file).stem,
        "bytes": size,
        "seconds": avg
    }

def compile_and_run(sources, build: Path, install: Path, cflags: str, runs: int):
    """Compile & run all sources in parallel, skipping failures."""
    pkg_env = {'PKG_CONFIG_PATH': str(install/'lib'/'pkgconfig')}
    pkg_cflags = subprocess.check_output(
        ['pkg-config', '--cflags', 'igraph'], env=pkg_env, text=True
    ).split()
    pkg_libs = subprocess.check_output(
        ['pkg-config', '--libs', 'igraph'], env=pkg_env, text=True
    ).split()

    exec_dir = build / 'execs'
    if exec_dir.exists():
        shutil.rmtree(exec_dir)
    exec_dir.mkdir(parents=True)

    install_lib = str(install / 'lib')
    tasks = []
    for src in sources:
        exe = exec_dir / src.stem
        obj = exec_dir / f"{src.stem}.o"
        tasks.append((
            str(src), str(exe), str(obj),
            cflags, runs, pkg_cflags, pkg_libs, install_lib
        ))

    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as pool:
        results = pool.map(process_single, tasks)
        # filter out the None values
        return [r for r in results if r is not None]

def main():
    parser = argparse.ArgumentParser(
        description="Build igraph with clang/OpenMP and run its tests in parallel")
    parser.add_argument('--runs', type=int, default=1,
                        help="Number of times to run each test")
    parser.add_argument('cflags', nargs=argparse.REMAINDER,
                        help="CFLAGS after --, e.g. -O3 -march=native")
    args = parser.parse_args()

    # clean up any stray "--"
    clean_flags = [f for f in args.cflags if f != "--"]
    cflags = " ".join(clean_flags) if clean_flags else "-O2"
    runs = args.runs

    me      = Path(__file__).resolve().parent
    root    = me.parent.parent
    src     = root / 'dataset' / 'igraph'
    build   = src  / 'build'
    install = src  / 'install'
    outdir  = root / 'results' / 'igraph'
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"CFLAGS: {cflags}")
    print(f"Runs:   {runs}")

    print("=== Building igraph ===")
    build_igraph(src, build, install, cflags)

    print("=== Discovering tests ===")
    sources = discover_tests(src)
    print(f"Found {len(sources)} test files")

    print("=== Compiling & running tests in parallel ===")
    results = compile_and_run(sources, build, install, cflags, runs)

    out = outdir / 'results.json'
    with open(out, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out}")

if __name__ == '__main__':
    main()

