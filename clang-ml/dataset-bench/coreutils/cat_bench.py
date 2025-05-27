import subprocess

for _ in range(500):
    subprocess.run(["./cat", "small.txt"], stdout=subprocess.DEVNULL)
