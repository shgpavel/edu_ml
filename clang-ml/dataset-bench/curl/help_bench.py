import subprocess

for _ in range(100):
    subprocess.run(["./curl", "--help"], stdout=subprocess.DEVNULL)
