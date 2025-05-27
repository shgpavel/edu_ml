import random

FLAG_VARIANTS: dict[str, list[str]] = {
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
    "flto-jobs": [
        "-flto-jobs=1",
        "-flto-jobs=4",
        "-flto-jobs=8",
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
    "sse2avx": [
        "-msse2avx",
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
        "-ffinite-math-only",
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

def random_flags(max_flags: int | None = 10, seed: int | None = None) -> str:
    if seed is not None:
        random.seed(seed)

    chosen: list[str] = []

    keys = list(FLAG_VARIANTS)
    random.shuffle(keys)

    for key in keys:
        if random.random() < 0.40:
            chosen.append(random.choice(FLAG_VARIANTS[key]))
            if max_flags and len(chosen) >= max_flags:
                break

    if not any(flag.startswith("-O") for flag in chosen):
        chosen.insert(0, random.choice(FLAG_VARIANTS["O"]))

    return " ".join(chosen)

if __name__ == "__main__":
    print(random_flags())
