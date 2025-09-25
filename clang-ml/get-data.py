import os
import subprocess
import json
import random
import shutil
import glob
from typing import List, Dict, Optional

FLAG_VARIANTS: Dict[str, List[str]] = {
    "O": [
        "-O1",
        "-O2",
        "-O3",
        "-Os",
        "-Ofast",
    ],
    "flto": [
        "-flto",
        "-flto=full",
        "-flto=thin",
        "-flto=auto",
        "-funified-lto",
    ],
    "arch": [
        "-march=native",
        "-mtune=native",
    ],
    "vec_width": [
        "-mprefer-vector-width=128",
        "-mprefer-vector-width=256",
        "-mprefer-vector-width=none",
    ],
    "recip": [
        "-mrecip",
        "-mrecip=all",
    ],
    "branch_align": [
        "-malign-branch=fused,jcc",
        "-malign-branch-boundary=32",
    ],
    "inline": [
        "-finline-functions",
        "-finline-hint-functions",
        "-finline-max-stacksize=512",
        "-fno-inline-functions",
    ],
    "vectorize": [
        "-fvectorize",
        "-fslp-vectorize",
        "-fno-vectorize",
    ],
    "unroll": [
        "-funroll-loops",
        "-fno-unroll-loops",
    ],
    "sections": [
        "-ffunction-sections",
        "-fdata-sections",
        "-fmerge-all-constants",
    ],
    "fast_math": [
        "-ffast-math",
        "-funsafe-math-optimizations",
        "-fapprox-func",
        "-freciprocal-math",
        "-fno-signed-zeros",
        "-ffp-contract=fast",
        "-ffp-contract=off",
    ],
    "strict": [
        "-fstrict-aliasing",
        "-fno-strict-aliasing",
        "-fstrict-enums",
        "-fstrict-vtable-pointers",
        "-fno-delete-null-pointer-checks",
        "-fomit-frame-pointer",
        "-fno-omit-frame-pointer",
    ],
    "whole_prog": [
        "-fwhole-program-vtables",
        "-fvirtual-function-elimination",
        "-funique-basic-block-section-names",
    ],
    "stack_prot": [
        "-fstack-protector",
        "-fstack-protector-strong",
        "-fstack-protector-all",
        "-fstack-clash-protection",
    ],
}


def random_flags(max_flags: Optional[int] = 10, seed: Optional[int] = None) -> str:
    if seed is not None:
        random.seed(seed)

    while True:
        chosen: List[str] = []
        keys = list(FLAG_VARIANTS)
        random.shuffle(keys)
        for key in keys:
            if random.random() < 0.40:
                chosen.append(random.choice(FLAG_VARIANTS[key]))
                if max_flags and len(chosen) >= max_flags:
                    break
        if not any(flag.startswith("-O") for flag in chosen):
            chosen.insert(0, random.choice(FLAG_VARIANTS["O"]))

        flags_str = " ".join(chosen)

        test_file = os.path.join(ROOT_DIR, "flag_test.c")
        with open(test_file, "w") as f:
            f.write("int main() { return 0; }\n")

        try:
            subprocess.run(
                ["clang", "-c", test_file] + flags_str.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            os.remove(test_file)
            return flags_str
        except subprocess.CalledProcessError:
            os.remove(test_file)
            continue


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
DATASET_RUN_DIR = os.path.join(ROOT_DIR, "dataset-run")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
OUTPUT_DATASET_FILE = os.path.join(ROOT_DIR, "ml_dataset.json")
NUM_ITERATIONS = 155


def get_projects() -> List[str]:
    projects = []
    for subdir in os.listdir(DATASET_RUN_DIR):
        project_dir = os.path.join(DATASET_RUN_DIR, subdir)
        if os.path.isdir(project_dir) and os.path.exists(
            os.path.join(project_dir, "build_and_test.py")
        ):
            projects.append(subdir)
    if len(projects) != 16:
        raise ValueError(f"Expected 16 projects, found {len(projects)}")
    return projects


def clear_results():
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
    os.makedirs(RESULTS_DIR)


def run_project(project: str, flags_str: str) -> bool:
    project_dir = os.path.join(DATASET_RUN_DIR, project)
    cmd = ["python", "build_and_test.py", "--runs", "5", "--"] + flags_str.split()
    try:
        subprocess.run(cmd, cwd=project_dir, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Project {project} failed with flags: {flags_str}")
        print(f"    Error: {e}")
        return False


def collect_results(projects: List[str]) -> Dict[str, List[Dict]]:
    all_results = {}
    for project in projects:
        project_results_dir = os.path.join(RESULTS_DIR, project)
        if not os.path.exists(project_results_dir):
            raise ValueError(f"No results dir for {project}")
        json_files = glob.glob(os.path.join(project_results_dir, "*.json"))
        if len(json_files) != 1:
            raise ValueError(
                f"Expected exactly one JSON in {project_results_dir}, found {len(json_files)}"
            )
        with open(json_files[0], "r") as f:
            data = json.load(f)
        all_results[project] = data
    return all_results


def main():
    projects = get_projects()
    dataset = []

    i = 0
    while i < NUM_ITERATIONS:
        print(f"Iteration {i + 1}/{NUM_ITERATIONS}")
        clear_results()
        flags_str = random_flags()
        print(f"Generated flags: {flags_str}")

        success = True
        for project in projects:
            if not run_project(project, flags_str):
                success = False
                break

        if not success:
            print("[!] Skipping this flag set, will try another one...")
            continue

        results = collect_results(projects)
        dataset.append({"flags": flags_str, "results": results})

        with open(OUTPUT_DATASET_FILE, "w") as f:
            json.dump(dataset, f, indent=2)

        i += 1

    print(f"Dataset saved to {OUTPUT_DATASET_FILE}")


if __name__ == "__main__":
    main()
